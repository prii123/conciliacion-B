from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import io, pandas as pd
import PyPDF2
import openai
import os
import pdfplumber
import json
import re

from app.utils.utils import validar_excel
from app.utils.file_validation import validar_archivo_csv, validar_numeros_debito_credito, formatear_datos_para_movimientos, agrupar_movimientos_por_mes_y_guardar
from app.utils.auth import get_current_active_user, verify_access_to_conciliacion
from ..database import get_db
from ..models import Conciliacion, Movimiento, ConciliacionMatch, Empresa, ConciliacionManual, ConciliacionManualBanco, ConciliacionManualAuxiliar, User
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from ..utils.conciliaciones import realizar_conciliacion_automatica, crear_conciliacion_manual
from ..repositories.factory import RepositoryFactory

router = APIRouter()




@router.get("/")
def lista_conciliaciones_json(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    factory = RepositoryFactory(db)
    conciliacion_repo = factory.get_conciliacion_repository()
    movimiento_repo = factory.get_movimiento_repository()
    
    # Filtrar conciliaciones según el rol del usuario
    if current_user.role == 'administrador':
        # Administrador ve todas las conciliaciones
        conciliaciones = conciliacion_repo.get_all(order_by='id', desc_order=True)
    else:
        # Usuario normal solo ve las suyas
        conciliaciones = conciliacion_repo.get_by_usuario(current_user.id)

    conciliaciones_por_empresa = {}
    for c in conciliaciones:
        empresa = c.empresa.razon_social if c.empresa and c.empresa.razon_social else (c.empresa.nombre_comercial if c.empresa else 'Desconocida')

        # Obtener estadísticas usando el repositorio
        total = movimiento_repo.count_by_conciliacion(c.id)
        conciliados = movimiento_repo.count_by_conciliacion(c.id, {'estado_conciliacion': 'conciliado'})
        pendientes = total - conciliados

        # Calcular el porcentaje de conciliación
        porcentaje = int((conciliados / total) * 100) if total else 0

        conc_obj = {
            'id': c.id,
            'mes_conciliado': c.mes_conciliado,
            'año_conciliado': getattr(c, 'anio_conciliado', None) or getattr(c, 'año_conciliado', None) or '',
            'cuenta_conciliada': c.cuenta_conciliada,
            'estado': c.estado,
            'total_movimientos': total,
            'conciliados': conciliados,
            'pendientes': pendientes,
            'porcentaje_conciliacion': porcentaje,
        }

        if empresa not in conciliaciones_por_empresa:
            conciliaciones_por_empresa[empresa] = {'en_proceso': [], 'finalizadas': []}

        if c.estado and c.estado.lower() == 'finalizada':
            conciliaciones_por_empresa[empresa]['finalizadas'].append(conc_obj)
        else:
            conciliaciones_por_empresa[empresa]['en_proceso'].append(conc_obj)

    return JSONResponse(content=jsonable_encoder(conciliaciones_por_empresa))

@router.get("/{conciliacion_id}")
def detalle_conciliacion_json(
    conciliacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    factory = RepositoryFactory(db)
    conciliacion_repo = factory.get_conciliacion_repository()
    movimiento_repo = factory.get_movimiento_repository()
    match_repo = factory.get_match_repository()
    manual_repo = factory.get_manual_repository()
    
    conciliacion = conciliacion_repo.get_by_id(conciliacion_id)
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")
    
    # Verificar acceso según rol
    if not verify_access_to_conciliacion(conciliacion, current_user):
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a esta conciliación"
        )

    movimientos = movimiento_repo.get_by_conciliacion(conciliacion_id)
    movimientos_no_conciliados = {
        "banco": jsonable_encoder([m for m in movimientos if m.tipo == "banco" and m.estado_conciliacion == "no_conciliado"]),
        "auxiliar": jsonable_encoder([m for m in movimientos if m.tipo == "auxiliar" and m.estado_conciliacion == "no_conciliado"]),
    }

    # Obtener matches automáticos usando repositorio
    matches_automaticos = match_repo.get_by_conciliacion(conciliacion_id)
    movimientos_conciliados_automaticos = [
        {
            "id": match.id,
            "id_movimiento_banco": match.id_movimiento_banco,
            "id_movimiento_auxiliar": match.id_movimiento_auxiliar,
            "fecha_match": match.fecha_match,
            "criterio_match": match.criterio_match,
            "diferencia_valor": match.diferencia_valor
        }
        for match in matches_automaticos
    ]

    # Obtener conciliaciones manuales usando repositorio
    manuales = manual_repo.get_by_conciliacion(conciliacion_id)
    movimientos_conciliados_manuales = []
    for cm in manuales:
        bancos = manual_repo.get_banco_items(cm.id)
        auxiliares = manual_repo.get_auxiliar_items(cm.id)
        for banco_item in bancos:
            banco = movimiento_repo.get_by_id(banco_item.id_movimiento_banco)
            for aux_item in auxiliares:
                auxiliar = movimiento_repo.get_by_id(aux_item.id_movimiento_auxiliar)
                movimientos_conciliados_manuales.append({
                    "id": cm.id,
                    "id_movimiento_banco": banco.id if banco else None,
                    "id_movimiento_auxiliar": auxiliar.id if auxiliar else None,
                    "fecha_match": cm.fecha_creacion,
                    "criterio_match": "manual",
                    "diferencia_valor": abs(banco.valor - auxiliar.valor) if banco and auxiliar else 0
                })

    movimientos_conciliados = movimientos_conciliados_automaticos + movimientos_conciliados_manuales

    # Calcular estadísticas usando el repositorio
    total = movimiento_repo.count_by_conciliacion(conciliacion_id)
    conciliados = movimiento_repo.count_by_conciliacion(conciliacion_id, {'estado_conciliacion': 'conciliado'})
    pendientes = total - conciliados

    # Calcular el porcentaje de conciliación
    porcentaje = int((conciliados / total) * 100) if total else 0

    stats = {
        "porcentaje_conciliacion": porcentaje,
        "conciliados": conciliados,
        "pendientes": pendientes,
        "total_movimientos": total
    }

    return JSONResponse(content={
        "conciliacion": jsonable_encoder(conciliacion),
        "movimientos_no_conciliados": movimientos_no_conciliados,
        "movimientos_conciliados": movimientos_conciliados,
        "stats": stats
    })

@router.get("/conciliaciones_empresa/{empresa_id}", name="conciliaciones_empresa_json") 
def conciliaciones_empresa_json(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    factory = RepositoryFactory(db)
    empresa_repo = factory.get_empresa_repository()
    conciliacion_repo = factory.get_conciliacion_repository()
    
    empresa = empresa_repo.get_by_id(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    conciliaciones = conciliacion_repo.get_by_empresa(empresa_id)
    en_proceso = [c.to_dict() for c in conciliaciones if c.estado == 'en_proceso']
    finalizadas = [c.to_dict() for c in conciliaciones if c.estado == 'finalizada']

    return JSONResponse(content={"empresa": empresa.to_dict(), "en_proceso": en_proceso, "finalizadas": finalizadas})


@router.get("/{conciliacion_id}/matches_y_manuales", name="matches_y_conciliaciones_manuales")
def obtener_matches_y_conciliaciones_manuales(
    conciliacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    movimientos_banco = {mov.id: mov.to_dict() for mov in db.query(Movimiento).filter(Movimiento.tipo == 'banco').all()}
    movimientos_auxiliar = {mov.id: mov.to_dict() for mov in db.query(Movimiento).filter(Movimiento.tipo == 'auxiliar').all()}

    matches = [
        {
            "id": match.id,
            "movimiento_banco": movimientos_banco.get(match.id_movimiento_banco),
            "movimiento_auxiliar": movimientos_auxiliar.get(match.id_movimiento_auxiliar),
            "diferencia": match.diferencia_valor,
            "criterio_match": match.criterio_match,
            "fecha": match.fecha_match
        }
        for match in db.query(ConciliacionMatch).filter(ConciliacionMatch.id_conciliacion == conciliacion_id).all()
    ]

    conciliaciones_manuales = db.query(ConciliacionManual).filter(ConciliacionManual.id_conciliacion == conciliacion_id).all()
    resultado_manuales = [
        {
            "id_conciliacion_manual": cm.id,
            "fecha_creacion": cm.fecha_creacion,
            "movimientos_banco": [m.to_dict() for m in db.query(Movimiento).join(ConciliacionManualBanco).filter(ConciliacionManualBanco.id_conciliacion_manual == cm.id).all()],
            "movimientos_auxiliar": [m.to_dict() for m in db.query(Movimiento).join(ConciliacionManualAuxiliar).filter(ConciliacionManualAuxiliar.id_conciliacion_manual == cm.id).all()],
        }
        for cm in conciliaciones_manuales
    ]

    # Calculate stats for matches
    stats = {
        "total_matches": len(matches) + len(resultado_manuales),
        "exact_matches": len([m for m in matches if m["criterio_match"] == "exacto_S"]),
        "approximate_matches": len([m for m in matches if m["criterio_match"] == "aproximado_S"]),
        "manual_matches": len(resultado_manuales)
    }

    return JSONResponse(content={
        "matches": matches,
        "conciliaciones_manuales": resultado_manuales,
        "stats": stats
    })


@router.post("/upload")
async def upload_files(
    file_banco: UploadFile = File(...),
    file_auxiliar: UploadFile = File(...),
    mes: str = Form(...),
    cuenta: str = Form(...),
    anio: int = Form(...),
    id_empresa: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
): 
    try:
        banco_content = await file_banco.read()
        df_banco = pd.read_excel(io.BytesIO(banco_content))
        df_banco['fecha'] = pd.to_datetime(df_banco['fecha'], format='%d-%m-%Y', errors='coerce').dt.strftime('%Y-%m-%d')
        df_banco.dropna(subset=['fecha'], inplace=True)
        validar_excel(df_banco, nombre_archivo=file_banco.filename, tipo_archivo="BANCO")

        auxiliar_content = await file_auxiliar.read()
        df_auxiliar = pd.read_excel(io.BytesIO(auxiliar_content))
        df_auxiliar['fecha'] = pd.to_datetime(df_auxiliar['fecha'], format='%d-%m-%Y', errors='coerce').dt.strftime('%Y-%m-%d')
        df_auxiliar.dropna(subset=['fecha'], inplace=True)
        validar_excel(df_auxiliar, nombre_archivo=file_auxiliar.filename, tipo_archivo="AUXILIAR")

        factory = RepositoryFactory(db)
        conciliacion_repo = factory.get_conciliacion_repository()
        movimiento_repo = factory.get_movimiento_repository()
        
        conciliacion_data = {
            "id_empresa": id_empresa,
            "id_usuario_creador": current_user.id,  # Asignar el usuario creador 
            "fecha_proceso": datetime.now().strftime("%Y-%m-%d"),
            "nombre_archivo_banco": file_banco.filename,
            "nombre_archivo_auxiliar": file_auxiliar.filename,
            "mes_conciliado": mes,
            "cuenta_conciliada": cuenta,
            "año_conciliado": anio
        }
        nueva_conciliacion = conciliacion_repo.create(conciliacion_data)
        conciliacion_id = nueva_conciliacion.id

        movimientos_banco_data = [
            {
                "id_conciliacion": conciliacion_id,
                "fecha": str(row['fecha']),
                "descripcion": row['descripcion'],
                "valor": abs(row['valor']),
                "es": row['es'],
                "tipo": 'banco'
            }
            for _, row in df_banco.iterrows()
        ]

        movimientos_auxiliar_data = [
            {
                "id_conciliacion": conciliacion_id,
                "fecha": str(row['fecha']),
                "descripcion": row['descripcion'],
                "valor": abs(row['valor']),
                "es": row['es'],
                "tipo": 'auxiliar'
            }
            for _, row in df_auxiliar.iterrows()
        ]

        movimiento_repo.create_bulk(movimientos_banco_data)
        movimiento_repo.create_bulk(movimientos_auxiliar_data)

        return JSONResponse(content={"message": f"Archivos cargados exitosamente para la conciliación #{conciliacion_id}"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@router.post("/carga_archivo_individual/{conciliacion_id}")
async def carga_archivo_individual(
    conciliacion_id: int,
    archivo: UploadFile = File(...),
    tipo_movimiento: str = Form(...),  # "banco" o "auxiliar" 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Carga un archivo individual a una conciliación existente.
    Valida usando validar_excel y agrega los movimientos.
    """
    # Verificar que la conciliación existe
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(404, "Conciliación no encontrada")
    
    try:
        # Leer archivo Excel
        contenido = await archivo.read()
        df = pd.read_excel(io.BytesIO(contenido))
        
        # Validar formato de fecha
        df['fecha'] = pd.to_datetime(df['fecha'], format='%d-%m-%Y', errors='coerce').dt.strftime('%Y-%m-%d')
        df.dropna(subset=['fecha'], inplace=True)
        
        # Validar archivo usando validar_excel de utils
        validar_excel(df, nombre_archivo=archivo.filename, tipo_archivo=tipo_movimiento.upper())
        
        # Crear movimientos
        nuevos_movimientos = [
            Movimiento(
                id_conciliacion=conciliacion_id,
                fecha=str(row['fecha']),
                descripcion=row['descripcion'],
                valor=abs(row['valor']),
                es=row['es'],
                tipo=tipo_movimiento,
                estado_conciliacion="no_conciliado"
            )
            for _, row in df.iterrows()
        ]
        
        # Guardar en base de datos
        db.bulk_save_objects(nuevos_movimientos)
        db.commit()
        
        return JSONResponse(content={
            "message": f"{len(nuevos_movimientos)} movimientos agregados exitosamente a la conciliación #{conciliacion_id}",
            "movimientos_agregados": len(nuevos_movimientos)
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar el archivo: {str(e)}")

@router.post("/upload_individual")
async def upload_individual(
    archivo: UploadFile = File(...),
    empresa_id: int = Form(...),
    cuenta_conciliada: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Leer el contenido del archivo
        contenido = await archivo.read()
        contenido_str = contenido.decode("utf-8")

        # Validar el archivo usando la primera validación
        resultado_validacion = validar_archivo_csv(contenido_str)

        if resultado_validacion["errores"]:
            return JSONResponse(content={
                "message": "Errores encontrados en el archivo.",
                "errores": resultado_validacion["errores"],
                "filas_invalidas": resultado_validacion["filas_invalidas"]
            }, status_code=400)

        movimientos = resultado_validacion["movimientos"]
        print(f"Movimientos obtenidos: {movimientos} registros")
        # Validar los valores de Debito y Credito
        errores_conversion = validar_numeros_debito_credito(contenido_str)

        if errores_conversion:
            return JSONResponse(content={
                    "message": "Errores encontrados en los valores de Debito y Credito.",
                    "errores_conversion": errores_conversion
                }, status_code=400)

        # Formatear los datos para la tabla movimientos
        resultado_formateo = formatear_datos_para_movimientos(contenido_str)
        movimientos_formateados = resultado_formateo.get("movimientos_formateados", [])

        if not movimientos_formateados:
            return JSONResponse(content={
                "message": "No se encontraron movimientos válidos para guardar."
            }, status_code=400)
        

        # Agrupar movimientos por mes y guardar en la base de datos
        resultado_guardado = agrupar_movimientos_por_mes_y_guardar(
            movimientos_formateados, 
            empresa_id, 
            cuenta_conciliada,
            archivo.filename,
            db,
            current_user.id
        )

        print("✓ Conciliaciones creadas:", resultado_guardado["conciliaciones_creadas"])
        print("✓ Movimientos guardados por mes:", resultado_guardado["resumen_por_mes"])

        return JSONResponse(content={
            "message": "Archivo procesado y conciliaciones creadas exitosamente.",
            "movimientos": movimientos,
            "conciliaciones_creadas": resultado_guardado["conciliaciones_creadas"],
            "guardado": resultado_guardado["resumen_por_mes"],
            "total_guardados": resultado_guardado["total_guardados"]
        })

    except Exception as e:
        # Log para capturar errores generales
        # print(f"Error general en upload_individual: {str(e)}")
        return HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")



@router.post("/{conciliacion_id}/agregar_movimientos")
async def agregar_movimientos_a_conciliacion(
    conciliacion_id: int,
    archivo: UploadFile = File(...),
    tipo_movimiento: str = Form(...),  # "banco" o "auxiliar"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Agrega movimientos de un archivo Excel a una conciliación existente.
    """
    # Verificar que la conciliación existe
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(404, "Conciliación no encontrada")
    
    try:
        # Leer archivo Excel
        contenido = await archivo.read()
        df = pd.read_excel(io.BytesIO(contenido))
        
        # Normalizar nombres de columnas a minúsculas
        df.columns = df.columns.str.lower().str.strip()
        
        # Validar formato de fecha - intentar múltiples formatos
        try:
            # Primero intentar con formato DD/MM/YYYY
            df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
        except:
            try:
                # Si falla, intentar con formato DD-MM-YYYY
                df['fecha'] = pd.to_datetime(df['fecha'], format='%d-%m-%Y', errors='coerce')
            except:
                # Si falla, usar inferencia automática
                df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        
        # Convertir a formato estándar YYYY-MM-DD
        df['fecha'] = df['fecha'].dt.strftime('%Y-%m-%d')
        df.dropna(subset=['fecha'], inplace=True)
        
        # Validar archivo
        validar_excel(df, nombre_archivo=archivo.filename, tipo_archivo=tipo_movimiento.upper())
        
        # Crear movimientos
        nuevos_movimientos = [
            Movimiento(
                id_conciliacion=conciliacion_id,
                fecha=str(row['fecha']),
                descripcion=row['descripcion'],
                valor=abs(row['valor']),
                es=row['es'],
                tipo=tipo_movimiento,
                estado_conciliacion="no_conciliado"
            )
            for _, row in df.iterrows()
        ]
        
        # Guardar en base de datos
        db.bulk_save_objects(nuevos_movimientos)
        db.commit()
        
        return JSONResponse(content={
            "message": f"{len(nuevos_movimientos)} movimientos agregados exitosamente a la conciliación #{conciliacion_id}",
            "movimientos_agregados": len(nuevos_movimientos)
        })
        
    except Exception as e:
        print(f"Error al agregar movimientos: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error al procesar el archivo: {str(e)}")


@router.post("/{conciliacion_id}/procesar")
def procesar_conciliacion(
    conciliacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Procesa automáticamente una conciliación utilizando los métodos de conciliación en utils/conciliaciones.py.
    """
    realizar_conciliacion_automatica(conciliacion_id, db)
    return {"message": f"Conciliación #{conciliacion_id} procesada automáticamente."}

@router.post("/{conciliacion_id}/terminar_conciliacion")
def terminar_conciliacion(
    conciliacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(404, "Conciliación no encontrada")
    conciliacion.estado = "finalizada"
    db.commit()
    return {"message": f"Conciliación #{conciliacion_id} marcada como finalizada."}

class ConciliacionManualRequest(BaseModel):
    id_banco: List[int]
    id_auxiliar: List[int]

@router.post("/{conciliacion_id}/conciliar-manual")
def conciliar_manual(
    conciliacion_id: int,
    request: ConciliacionManualRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Realiza una conciliación manual utilizando el método en utils/conciliaciones.py.
    """
    resultado = crear_conciliacion_manual(conciliacion_id, request.id_banco, request.id_auxiliar, db)
    return {"message": "Conciliación manual realizada con éxito.", "resultado": resultado}


@router.delete("/match/{match_id}/eliminar")
def eliminar_match_manual(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    match = db.query(ConciliacionMatch).filter(ConciliacionMatch.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match no encontrado")
    # optional: unmark movimientos if desired
    db.delete(match)
    db.commit()
    return {"message": f"Match #{match_id} eliminado con éxito."}

@router.delete("/{conciliacion_id}/eliminar")
def eliminar_conciliacion(
    conciliacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Elimina una conciliación completa junto con todos sus movimientos y matches asociados.
    """
    print("Eliminando conciliación y datos asociados...")
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(404, "Conciliación no encontrada")
    
    # Eliminar matches automáticos
    matches = db.query(ConciliacionMatch).filter(ConciliacionMatch.id_conciliacion == conciliacion_id).all()
    for match in matches:
        db.delete(match)
    
    # Eliminar conciliaciones manuales y sus relaciones
    conciliaciones_manuales = db.query(ConciliacionManual).filter(ConciliacionManual.id_conciliacion == conciliacion_id).all()
    for cm in conciliaciones_manuales:
        # Eliminar relaciones banco
        relaciones_banco = db.query(ConciliacionManualBanco).filter(ConciliacionManualBanco.id_conciliacion_manual == cm.id).all()
        for rel in relaciones_banco:
            db.delete(rel)
        
        # Eliminar relaciones auxiliar
        relaciones_auxiliar = db.query(ConciliacionManualAuxiliar).filter(ConciliacionManualAuxiliar.id_conciliacion_manual == cm.id).all()
        for rel in relaciones_auxiliar:
            db.delete(rel)
        
        # Eliminar conciliación manual
        db.delete(cm)
    
    # Eliminar movimientos
    movimientos = db.query(Movimiento).filter(Movimiento.id_conciliacion == conciliacion_id).all()
    for movimiento in movimientos:
        db.delete(movimiento)
    
    # Eliminar conciliación
    db.delete(conciliacion)
    
    db.commit()
    return {"message": f"Conciliación #{conciliacion_id} y todos sus datos asociados eliminados con éxito."}


@router.post("/upload-extracto/{conciliacion_id}")
async def upload_extracto_bancario(
    conciliacion_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    # prompt: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Sube un archivo PDF de extracto bancario y inicia el procesamiento asíncrono con DeepSeek.
    """
    print("🔍 Iniciando subida de extracto bancario...")
    try:
        print(f"👤 Usuario autenticado: {current_user.username if current_user else 'None'}")

        # Verificar que la conciliación existe y pertenece al usuario
        conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
        if not conciliacion:
            print(f"❌ Error: Conciliación #{conciliacion_id} no encontrada")
            raise HTTPException(status_code=404, detail="Conciliación no encontrada")

        # Verificar acceso según rol del usuario
        if current_user.role != 'administrador' and conciliacion.id_usuario_creador != current_user.id:
            print(f"❌ Error: Usuario {current_user.id} no tiene acceso a conciliación #{conciliacion_id}")
            raise HTTPException(status_code=403, detail="No tienes permiso para acceder a esta conciliación")

        print(f"✅ Conciliación #{conciliacion_id} validada para usuario {current_user.username}")

        # Verificar que sea PDF
        if not file.filename.lower().endswith('.pdf'):
            print("❌ Error: Archivo no es PDF")
            raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")
        print(f"✅ Archivo PDF válido: {file.filename}")

        # Leer el contenido del PDF
        content = await file.read()
        print(f"📄 Contenido leído: {len(content)} bytes")

        # Iniciar procesamiento en segundo plano
        background_tasks.add_task(
            process_and_load_extracto,
            conciliacion_id=conciliacion_id,
            content=content,
            user_id=current_user.id
        )

        print("✅ Respuesta enviada al cliente, procesamiento continúa en background")
        return JSONResponse(content={
            "message": "Procesamiento de extracto bancario iniciado. El análisis con DeepSeek y la carga de movimientos puede tardar varios minutos. Refresca la página para ver el progreso.",
            "conciliacion_id": conciliacion_id,
            "estado": "iniciado"
        })

    except HTTPException:
        # Re-lanzar excepciones HTTP sin modificar
        raise
    except Exception as e:
        print(f"❌ Error inesperado en upload_extracto: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


async def process_and_load_extracto(conciliacion_id: int, content: bytes, user_id: int):
    """
    Función de segundo plano que procesa el PDF con DeepSeek y carga los movimientos en la BD.
    """
    from app.database import SessionLocal
    db = SessionLocal()  # Crear nueva sesión independiente

    try:
        print(f"🔄 Iniciando procesamiento en segundo plano para conciliación #{conciliacion_id} - Background task started")

        # Verificar conciliación y usuario
        conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
        if not conciliacion:
            print(f"❌ Conciliación #{conciliacion_id} no encontrada")
            return

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"❌ Usuario #{user_id} no encontrado")
            return

        # Verificar acceso
        if user.role != 'administrador' and conciliacion.id_usuario_creador != user.id:
            print(f"❌ Usuario {user.id} no tiene acceso a conciliación #{conciliacion_id}")
            conciliacion.estado = 'error_acceso'
            db.commit()
            return

        # Actualizar estado inicial
        conciliacion.estado = 'procesando_extracto'
        db.commit()
        print(f"📝 Estado inicial establecido: procesando_extracto")

        print("📄 Extrayendo texto del PDF...")
        conciliacion.estado = 'extrayendo_texto'
        db.commit()

        # Extraer texto del PDF (igual que antes)
        text_pages = []
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                print(f"📖 PDF cargado con pdfplumber: {len(pdf.pages)} páginas")
                total_pages = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_pages.append(page_text.strip())
                        print(f"📝 Página {i+1}: {len(page_text)} caracteres extraídos")
                    else:
                        print(f"⚠️ Página {i+1}: No se pudo extraer texto")
                        
        except Exception as e:
            print(f"⚠️ Error con pdfplumber: {str(e)}, intentando con PyPDF2...")
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            print(f"📖 PDF cargado con PyPDF2: {len(pdf_reader.pages)} páginas")
            total_pages = len(pdf_reader.pages)
            
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_pages.append(page_text.strip())
                    print(f"📝 Página {i+1}: {len(page_text)} caracteres extraídos (PyPDF2)")
                else:
                    print(f"⚠️ Página {i+1}: No se pudo extraer texto")

        print(f"📝 Total páginas con texto: {len(text_pages)} de {total_pages}")

        if len(text_pages) < 1:
            print("❌ No se pudo extraer texto suficiente del PDF")
            conciliacion.estado = 'error_extraccion'
            db.commit()
            return

        # Configurar DeepSeek
        print("🤖 Configurando DeepSeek...")
        conciliacion.estado = 'configurando_deepseek'
        db.commit()
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("❌ DEEPSEEK_API_KEY no encontrada")
            conciliacion.estado = 'error_config'
            db.commit()
            return

        client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

        prompt = "Analiza el siguiente extracto bancario y extrae los movimientos financieros relevantes, incluyendo fecha, descripción y valor. Proporciona un resumen estructurado de los movimientos encontrados agrupado por ENTRADAS (debitos) y SALIDAS (creditos)."

        # Procesar con DeepSeek
        print("🧠 Procesando con DeepSeek...")
        conciliacion.estado = 'procesando_deepseek'
        db.commit()
        max_pages_single = 5
        pages_per_group = 5

        if len(text_pages) <= max_pages_single:
            print(f"📄 Procesando PDF pequeño ({len(text_pages)} páginas)")
            full_text = "\n\n".join(text_pages)
            result = await process_text_with_deepseek(full_text, prompt, client)
        else:
            print(f"📄 Procesando PDF grande ({len(text_pages)} páginas) en lotes")
            responses = []
            for i in range(0, len(text_pages), pages_per_group):
                group_pages = text_pages[i:i + pages_per_group]
                group_text = "\n\n".join(group_pages)
                group_number = (i // pages_per_group) + 1
                total_groups = (len(text_pages) + pages_per_group - 1) // pages_per_group
                print(f"🔄 Procesando grupo {group_number}/{total_groups}")

                group_prompt = f"{prompt}\n\n--- Grupo {group_number} de {total_groups} ---\nPáginas {i+1}-{min(i+pages_per_group, len(text_pages))} del documento total de {len(text_pages)} páginas."
                group_result = await process_text_with_deepseek(group_text, group_prompt, client)
                responses.append(group_result)

            result = combine_deepseek_responses(responses)

        if "error" in result:
            print(f"❌ Error en DeepSeek: {result['error']}")
            conciliacion.estado = 'error_deepseek'
            db.commit()
            return

        print("✅ Procesamiento con DeepSeek completado")

        # Cargar movimientos en BD (usando lógica de cargar_movimientos_deepseek)
        print("💾 Cargando movimientos en BD...")
        conciliacion.estado = 'cargando_movimientos'
        db.commit()
        
        movimientos_data = result
        if "movimientos" not in movimientos_data:
            print("❌ JSON inválido: falta campo 'movimientos'")
            conciliacion.estado = 'error_json'
            db.commit()
            return

        movimientos_json = movimientos_data["movimientos"]
        nuevos_movimientos = []
        total_entradas = 0
        total_salidas = 0

        # Procesar entradas
        if "entradas" in movimientos_json and isinstance(movimientos_json["entradas"], list):
            for entrada in movimientos_json["entradas"]:
                if not isinstance(entrada, dict):
                    continue
                fecha = entrada.get("fecha", "").strip()
                descripcion = entrada.get("descripcion", "").strip()
                valor = entrada.get("valor", 0)
                if not fecha or not descripcion:
                    continue
                try:
                    if isinstance(valor, str):
                        valor = float(valor.replace("$", "").replace(",", "").replace(" ", ""))
                    elif not isinstance(valor, (int, float)):
                        valor = 0.0
                except:
                    valor = 0.0

                movimiento = Movimiento(
                    id_conciliacion=conciliacion_id,
                    fecha=fecha,
                    descripcion=f"[DeepSeek] {descripcion}",
                    valor=abs(valor),
                    tipo="banco",
                    es="E",  # Entradas son E (crédito)
                    estado_conciliacion="no_conciliado"
                )
                nuevos_movimientos.append(movimiento)
                total_entradas += 1

        # Procesar salidas
        if "salidas" in movimientos_json and isinstance(movimientos_json["salidas"], list):
            for salida in movimientos_json["salidas"]:
                if not isinstance(salida, dict):
                    continue
                fecha = salida.get("fecha", "").strip()
                descripcion = salida.get("descripcion", "").strip()
                valor = salida.get("valor", 0)
                if not fecha or not descripcion:
                    continue
                try:
                    if isinstance(valor, str):
                        valor = float(valor.replace("$", "").replace(",", "").replace(" ", ""))
                    elif not isinstance(valor, (int, float)):
                        valor = 0.0
                except:
                    valor = 0.0

                movimiento = Movimiento(
                    id_conciliacion=conciliacion_id,
                    fecha=fecha,
                    descripcion=f"[DeepSeek] {descripcion}",
                    valor=abs(valor),
                    tipo="banco",
                    es="S",  # Salidas son S (débito)
                    estado_conciliacion="no_conciliado"
                )
                nuevos_movimientos.append(movimiento)
                total_salidas += 1

        if not nuevos_movimientos:
            print("❌ No se encontraron movimientos válidos")
            conciliacion.estado = 'error_sin_movimientos'
            db.commit()
            return

        # Guardar movimientos
        print(f"💾 Guardando {len(nuevos_movimientos)} movimientos...")
        db.bulk_save_objects(nuevos_movimientos)
        conciliacion.estado = 'completado_extracto'
        db.commit()

        print(f"✅ Procesamiento completado: {total_entradas} entradas, {total_salidas} salidas")

    except Exception as e:
        print(f"❌ Error en procesamiento en segundo plano: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            conciliacion.estado = 'error_procesamiento'
            db.commit()
        except:
            pass
    finally:
        db.close()


async def process_text_with_deepseek(text: str, prompt: str, client) -> dict:
    """
    Procesa texto con DeepSeek API y retorna la respuesta JSON.
    """
    try:
        print(f"📤 Enviando texto a DeepSeek ({len(text)} caracteres)...")

        # Crear el mensaje del sistema con el prompt del usuario
        system_message = f"""Eres un asistente especializado en análisis de extractos bancarios.
Tu tarea es analizar el texto proporcionado y extraer información financiera relevante.

Instrucciones específicas del usuario:
{prompt}

FORMATO DE RESPUESTA OBLIGATORIO:
Debes responder ÚNICAMENTE con un objeto JSON válido que tenga exactamente esta estructura:

{{
    "resumen": {{
        "saldo_inicial": 0.00,
        "total_abonos": 0.00,
        "total_cargos": 0.00,
        "saldo_final": 0.00
    }},
    "movimientos": {{
        "entradas": [
            {{
                "fecha": "DD/MM/YYYY",
                "descripcion": "texto descriptivo",
                "valor": 0.00
            }}
        ],
        "salidas": [
            {{
                "fecha": "DD/MM/YYYY",
                "descripcion": "texto descriptivo",
                "valor": 0.00
            }}
        ]
    }}
}}

REGLAS IMPORTANTES:
- NO incluyas NINGÚN texto adicional antes o después del JSON
- NO uses bloques de código markdown ```json
- NO agregues explicaciones o comentarios
- El JSON debe ser válido y parseable
- Si no encuentras información, usa arrays vacíos []
- Mantén las descripciones concisas pero completas"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Analiza este extracto bancario:\n\n{text}"}
            ],
            max_tokens=8192,  # Aumentado para reducir truncamiento
            temperature=0.0  # Temperatura más baja para consistencia
        )

        content = response.choices[0].message.content.strip()
        print(f"✅ Respuesta de DeepSeek recibida ({len(content)} caracteres)")
        print(f"📄 Contenido crudo: {content[:300]}...")

        # Función auxiliar para extraer JSON de la respuesta
        def extract_json_from_response(response_text: str) -> dict:
            """
            Intenta extraer un objeto JSON válido de la respuesta de DeepSeek.
            Maneja casos donde puede haber texto adicional o formato markdown.
            """
            # Primero intentar parsear directamente
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                pass

            # Buscar JSON dentro de bloques de código markdown
            import re

            # Buscar ```json ... ```
            json_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_block:
                try:
                    return json.loads(json_block.group(1))
                except json.JSONDecodeError:
                    pass

            # Buscar el primer { y el último } que formen un JSON válido
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                potential_json = response_text[start_idx:end_idx + 1]
                try:
                    return json.loads(potential_json)
                except json.JSONDecodeError as e:
                    # Intentar reparar JSON truncado de manera más inteligente
                    try:
                        repaired = potential_json.rstrip()

                        # Si termina con ... o comillas sin cerrar, intentar una reparación básica
                        if repaired.endswith('...'):
                            repaired = repaired[:-3]
                        elif repaired.endswith('"') and repaired.count('"') % 2 == 1:
                            # Si hay comillas sin cerrar al final, probablemente está truncado
                            # Buscar la última coma antes de la truncatura y cerrar ahí
                            last_comma = repaired.rfind(',')
                            if last_comma > repaired.rfind('{') and last_comma > repaired.rfind('['):
                                repaired = repaired[:last_comma] + '}'
                            else:
                                repaired += '}'

                        # Contar llaves y brackets para cerrar los pendientes
                        open_braces = repaired.count('{') - repaired.count('}')
                        open_brackets = repaired.count('[') - repaired.count(']')

                        # Solo cerrar si hay desbalance significativo
                        if abs(open_braces) <= 2 and abs(open_brackets) <= 2:
                            repaired += '}' * max(0, open_braces) + ']' * max(0, open_brackets)

                        return json.loads(repaired)
                    except json.JSONDecodeError:
                        # Si la reparación falla, intentar extraer información parcial
                        try:
                            # Buscar patrones comunes en el texto
                            resumen_match = re.search(r'"resumen"\s*:\s*\{([^}]+)\}', response_text, re.DOTALL)
                            movimientos_match = re.search(r'"movimientos"\s*:\s*\{([^}]+)\}', response_text, re.DOTALL)

                            partial_result = {}

                            if resumen_match:
                                # Intentar parsear el resumen
                                resumen_text = '{' + resumen_match.group(1) + '}'
                                try:
                                    partial_result['resumen'] = json.loads(resumen_text)
                                except:
                                    partial_result['resumen'] = {"error": "Resumen parcialmente truncado"}

                            if movimientos_match:
                                # Intentar parsear movimientos
                                movimientos_text = '{' + movimientos_match.group(1) + '}'
                                try:
                                    partial_result['movimientos'] = json.loads(movimientos_text)
                                except:
                                    partial_result['movimientos'] = {"error": "Movimientos parcialmente truncados"}

                            if partial_result:
                                partial_result['warning'] = 'JSON truncado - información parcial extraída'
                                return partial_result

                        except:
                            pass

            # Último intento: limpiar texto y buscar JSON
            # Remover líneas que no parecen JSON
            lines = response_text.split('\n')
            json_lines = []
            in_json = False

            for line in lines:
                line = line.strip()
                if line.startswith('{'):
                    in_json = True
                    json_lines.append(line)
                elif in_json:
                    json_lines.append(line)
                    if line.endswith('}'):
                        break

            if json_lines:
                potential_json = '\n'.join(json_lines)
                try:
                    return json.loads(potential_json)
                except json.JSONDecodeError:
                    pass

            # Si nada funciona, retornar el error
            raise json.JSONDecodeError("No se pudo extraer JSON válido", response_text, 0)

        # Intentar extraer JSON de la respuesta
        try:
            result = extract_json_from_response(content)
            print("✅ JSON parseado exitosamente")
            return result
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            print(f"Contenido recibido: {content[:1000]}...")

            # Intentar una segunda llamada con instrucciones más estrictas
            print("🔄 Intentando segunda llamada con instrucciones más estrictas...")
            try:
                strict_system_message = """Analiza el extracto bancario y responde ÚNICAMENTE con JSON válido.
Ejemplo de formato esperado:
{
    "resumen": {
        "saldo_inicial": 0.00,
        "total_abonos": 0.00,
        "total_cargos": 0.00,
        "saldo_final": 0.00
    },
    "movimientos": {
        "entradas": [
            {"fecha": "DD/MM/YYYY", "descripcion": "texto", "valor": 0.00}
        ],
        "salidas": [
            {"fecha": "DD/MM/YYYY", "descripcion": "texto", "valor": 0.00}
        ]
    }
}
NO agregues texto adicional."""

                response2 = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": strict_system_message},
                        {"role": "user", "content": f"Analiza este extracto bancario y devuelve solo JSON:\n\n{text}"}
                    ],
                    max_tokens=8192,  # Aumentado para reducir truncamiento
                    temperature=0.0  # Temperatura más baja para más consistencia
                )

                content2 = response2.choices[0].message.content.strip()
                print(f"📄 Segunda respuesta: {content2[:300]}...")

                result = extract_json_from_response(content2)
                print("✅ JSON parseado exitosamente en segunda llamada")
                return result

            except Exception as retry_error:
                print(f"❌ Error también en segunda llamada: {str(retry_error)}")
                return {
                    "error": "Respuesta no es JSON válido después de reintento",
                    "raw_content": content,
                    "second_attempt_content": content2 if 'content2' in locals() else None,
                    "parse_error": str(e),
                    "retry_error": str(retry_error)
                }

    except Exception as e:
        print(f"❌ Error en process_text_with_deepseek: {str(e)}")
        return {
            "error": f"Error procesando con DeepSeek: {str(e)}",
            "text_length": len(text)
        }


def combine_deepseek_responses(responses: list) -> dict:
    """
    Combina múltiples respuestas JSON de DeepSeek en una sola respuesta consolidada.
    """
    try:
        print(f"🔄 Combinando {len(responses)} respuestas de DeepSeek...")

        # Filtrar respuestas válidas (sin errores)
        valid_responses = [r for r in responses if "error" not in r]

        if not valid_responses:
            return {
                "error": "Todas las respuestas contienen errores",
                "responses": responses
            }

        # Si solo hay una respuesta, retornarla directamente
        if len(valid_responses) == 1:
            return valid_responses[0]

        # Combinar respuestas múltiples
        combined = {
            "total_pages_processed": len(responses),
            "valid_responses": len(valid_responses),
            "combined_data": {}
        }

        # Extraer y combinar datos comunes
        all_movimientos = []
        all_resumenes = []
        all_alertas = []

        for response in valid_responses:
            # Combinar movimientos si existen
            if "movimientos" in response and isinstance(response["movimientos"], list):
                all_movimientos.extend(response["movimientos"])

            # Combinar resúmenes
            if "resumen" in response:
                all_resumenes.append(response["resumen"])

            # Combinar alertas
            if "alertas" in response and isinstance(response["alertas"], list):
                all_alertas.extend(response["alertas"])

            # Copiar otros campos únicos
            for key, value in response.items():
                if key not in ["movimientos", "resumen", "alertas", "error"]:
                    if key not in combined["combined_data"]:
                        combined["combined_data"][key] = value
                    elif isinstance(combined["combined_data"][key], list) and isinstance(value, list):
                        combined["combined_data"][key].extend(value)
                    elif isinstance(combined["combined_data"][key], dict) and isinstance(value, dict):
                        combined["combined_data"][key].update(value)

        # Agregar secciones combinadas
        if all_movimientos:
            combined["movimientos"] = all_movimientos

        if all_resumenes:
            combined["resumenes_por_grupo"] = all_resumenes
            # Crear un resumen general
            combined["resumen_general"] = {
                "total_movimientos": len(all_movimientos),
                "grupos_procesados": len(valid_responses),
                "periodo_cubierto": "Múltiples grupos de páginas"
            }

        if all_alertas:
            combined["alertas"] = all_alertas

        print(f"✅ Respuestas combinadas exitosamente")
        return combined

    except Exception as e:
        print(f"❌ Error combinando respuestas: {str(e)}")
        return {
            "error": f"Error combinando respuestas: {str(e)}",
            "responses": responses
        }


@router.post("/cargar-movimientos-deepseek/{conciliacion_id}")
async def cargar_movimientos_deepseek(
    conciliacion_id: int,
    movimientos_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Carga movimientos extraídos por DeepSeek a la base de datos.
    Convierte el JSON estructurado en registros de Movimiento.
    """
    try:
        print(f"🔄 Iniciando carga de movimientos DeepSeek para conciliación #{conciliacion_id}")

        # Verificar que la conciliación existe y pertenece al usuario
        conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
        if not conciliacion:
            print(f"❌ Error: Conciliación #{conciliacion_id} no encontrada")
            raise HTTPException(status_code=404, detail="Conciliación no encontrada")

        # Verificar acceso según rol del usuario
        if current_user.role != 'administrador' and conciliacion.id_usuario_creador != current_user.id:
            print(f"❌ Error: Usuario {current_user.id} no tiene acceso a conciliación #{conciliacion_id}")
            raise HTTPException(status_code=403, detail="No tienes permiso para acceder a esta conciliación")

        print(f"✅ Conciliación #{conciliacion_id} validada para usuario {current_user.username}")

        # Validar estructura del JSON
        if not movimientos_data or "movimientos" not in movimientos_data:
            raise HTTPException(status_code=400, detail="JSON inválido: falta campo 'movimientos'")

        movimientos_json = movimientos_data["movimientos"]
        if not isinstance(movimientos_json, dict):
            raise HTTPException(status_code=400, detail="Campo 'movimientos' debe ser un objeto")

        nuevos_movimientos = []
        total_entradas = 0
        total_salidas = 0

        # Procesar entradas (créditos)
        if "entradas" in movimientos_json and isinstance(movimientos_json["entradas"], list):
            for entrada in movimientos_json["entradas"]:
                if not isinstance(entrada, dict):
                    continue

                # Validar campos requeridos
                fecha = entrada.get("fecha", "").strip()
                descripcion = entrada.get("descripcion", "").strip()
                valor = entrada.get("valor", 0)

                if not fecha or not descripcion:
                    print(f"⚠️ Entrada inválida omitida: fecha='{fecha}', desc='{descripcion[:50]}...'")
                    continue

                # Convertir valor a float si es string
                try:
                    if isinstance(valor, str):
                        # Remover símbolos de moneda y espacios
                        valor = float(valor.replace("$", "").replace(",", "").replace(" ", ""))
                    elif not isinstance(valor, (int, float)):
                        valor = 0.0
                except (ValueError, TypeError):
                    print(f"⚠️ Valor inválido en entrada: {valor}, usando 0.0")
                    valor = 0.0

                movimiento = Movimiento(
                    id_conciliacion=conciliacion_id,
                    fecha=fecha,
                    descripcion=f"[DeepSeek] {descripcion}",
                    valor=abs(valor),  # Siempre positivo
                    tipo="banco",
                    es="E",  # Entradas son E (crédito)
                    estado_conciliacion="no_conciliado"
                )
                nuevos_movimientos.append(movimiento)
                total_entradas += 1
                print(f"✅ Entrada procesada: {fecha} - {descripcion[:50]}... - ${valor}")

        # Procesar salidas (débitos)
        if "salidas" in movimientos_json and isinstance(movimientos_json["salidas"], list):
            for salida in movimientos_json["salidas"]:
                if not isinstance(salida, dict):
                    continue

                # Validar campos requeridos
                fecha = salida.get("fecha", "").strip()
                descripcion = salida.get("descripcion", "").strip()
                valor = salida.get("valor", 0)

                if not fecha or not descripcion:
                    print(f"⚠️ Salida inválida omitida: fecha='{fecha}', desc='{descripcion[:50]}...'")
                    continue

                # Convertir valor a float si es string
                try:
                    if isinstance(valor, str):
                        # Remover símbolos de moneda y espacios
                        valor = float(valor.replace("$", "").replace(",", "").replace(" ", ""))
                    elif not isinstance(valor, (int, float)):
                        valor = 0.0
                except (ValueError, TypeError):
                    print(f"⚠️ Valor inválido en salida: {valor}, usando 0.0")
                    valor = 0.0

                movimiento = Movimiento(
                    id_conciliacion=conciliacion_id,
                    fecha=fecha,
                    descripcion=f"[DeepSeek] {descripcion}",
                    valor=abs(valor),  # Siempre positivo
                    tipo="banco",
                    es="S",  # Salidas son S (débito)
                    estado_conciliacion="no_conciliado"
                )
                nuevos_movimientos.append(movimiento)
                total_salidas += 1
                print(f"✅ Salida procesada: {fecha} - {descripcion[:50]}... - ${valor}")

        if not nuevos_movimientos:
            raise HTTPException(status_code=400, detail="No se encontraron movimientos válidos para cargar")

        # Guardar movimientos en la base de datos
        print(f"💾 Guardando {len(nuevos_movimientos)} movimientos en la base de datos...")
        db.bulk_save_objects(nuevos_movimientos)
        db.commit()

        print(f"✅ Carga completada exitosamente: {total_entradas} entradas, {total_salidas} salidas")

        return JSONResponse(content={
            "message": f"Movimientos cargados exitosamente a la conciliación #{conciliacion_id}",
            "movimientos_cargados": len(nuevos_movimientos),
            "entradas": total_entradas,
            "salidas": total_salidas,
            "detalles": {
                "total_entradas": total_entradas,
                "total_salidas": total_salidas,
                "conciliacion_id": conciliacion_id
            }
        })

    except HTTPException:
        # Re-lanzar excepciones HTTP sin modificar
        raise
    except Exception as e:
        print(f"❌ Error inesperado en cargar_movimientos_deepseek: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()  # Revertir cambios en caso de error
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
