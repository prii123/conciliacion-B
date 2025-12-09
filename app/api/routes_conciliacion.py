from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, Form, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import io, pandas as pd

from app.utils.utils import validar_excel
from app.utils.file_validation import validar_archivo_csv, validar_numeros_debito_credito, formatear_datos_para_movimientos, agrupar_movimientos_por_mes_y_guardar
from app.utils.auth import get_current_active_user
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
    
    conciliaciones = conciliacion_repo.get_all(order_by='id', desc_order=True)

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
            db
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




