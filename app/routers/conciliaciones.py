from datetime import datetime
from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List
import io, pandas as pd

from app.utils.utils import validar_excel
from ..database import get_db
from ..models import Conciliacion, Movimiento, ConciliacionMatch, Empresa, ConciliacionManual, ConciliacionManualBanco, ConciliacionManualAuxiliar
from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from ..utils.conciliaciones import realizar_conciliacion_automatica, crear_conciliacion_manual

router = APIRouter()
package_dir = Path(__file__).resolve().parent.parent
templates_dir = package_dir / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@router.get("/conciliaciones")
def lista_conciliaciones_json(db: Session = Depends(get_db)):
    conciliaciones = db.query(Conciliacion).order_by(Conciliacion.id.desc()).all()

    conciliaciones_por_empresa = {}
    for c in conciliaciones:
        empresa = c.empresa.razon_social if c.empresa and c.empresa.razon_social else (c.empresa.nombre_comercial if c.empresa else 'Desconocida')
 
        movimientos = db.query(Movimiento).filter(Movimiento.id_conciliacion == c.id).all()
        total = len(movimientos)
        conciliados = db.query(ConciliacionMatch).filter(ConciliacionMatch.id_conciliacion == c.id).count()
        porcentaje = int((conciliados / total) * 100) if total else 0

        conc_obj = {
            'id': c.id,
            'mes_conciliado': c.mes_conciliado,
            'año_conciliado': getattr(c, 'anio_conciliado', None) or getattr(c, 'año_conciliado', None) or '',
            'cuenta_conciliada': c.cuenta_conciliada,
            'estado': c.estado,
            'total_movimientos': total,
            'conciliados': conciliados,
            'porcentaje_conciliacion': porcentaje,
        }

        if empresa not in conciliaciones_por_empresa:
            conciliaciones_por_empresa[empresa] = {'en_proceso': [], 'finalizadas': []}

        if c.estado and c.estado.lower() == 'finalizada':
            conciliaciones_por_empresa[empresa]['finalizadas'].append(conc_obj)
        else:
            conciliaciones_por_empresa[empresa]['en_proceso'].append(conc_obj)

    return jsonable_encoder(conciliaciones_por_empresa)


@router.get("/conciliacion/{conciliacion_id}")
def detalle_conciliacion_json(conciliacion_id: int, db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    movimientos = db.query(Movimiento).filter(Movimiento.id_conciliacion == conciliacion_id).all()
    movimientos_no_conciliados = {
        "banco": jsonable_encoder([m for m in movimientos if m.origen == "banco" and m.conciliado == "no"]),
        "auxiliar": jsonable_encoder([m for m in movimientos if m.origen == "auxiliar" and m.conciliado == "no"]),
    }
    movimientos_conciliados = db.query(ConciliacionMatch).filter(ConciliacionMatch.conciliacion_id == conciliacion_id).all()

    total = len(movimientos)
    conciliados = len(movimientos_conciliados)
    porcentaje = int((conciliados / total) * 100) if total else 0
    stats = {"porcentaje_conciliacion": porcentaje, "conciliados": conciliados, "total_movimientos": total}

    return {
        "conciliacion": jsonable_encoder(conciliacion),
        "movimientos_no_conciliados": movimientos_no_conciliados,
        "movimientos_conciliados": jsonable_encoder(movimientos_conciliados),
        "stats": stats
    }


@router.post("/upload", response_class=HTMLResponse)
async def upload_files(request: Request,
                       file_banco: UploadFile = File(...),
                       file_auxiliar: UploadFile = File(...),
                       mes: str = Form(...),
                       cuenta: str = Form(...),
                       anio: int = Form(...),
                       id_empresa: int = Form(...),
                       db: Session = Depends(get_db)):
    try:
        # Lectura y validación del archivo del banco
        try:
            banco_content = await file_banco.read()
            df_banco = pd.read_excel(io.BytesIO(banco_content))
            df_banco['fecha'] = pd.to_datetime(
                df_banco['fecha'], 
                format='%d-%m-%Y',      # <-- USAMOS EL FORMATO DE ENTRADA REAL (DD-MM-YYYY)
                errors='coerce'
            ).dt.strftime('%Y-%m-%d')   # <-- GUARDAMOS EL STRING ESTANDARIZADO (YYYY-MM-DD)
            df_banco.dropna(subset=['fecha'], inplace=True)

            validar_excel(df_banco, nombre_archivo=file_banco.filename, tipo_archivo="BANCO")
        except Exception as e:
            raise ValueError(f"Error en el archivo del BANCO ({file_banco.filename}): {str(e)}")
        
        # Lectura y validación del archivo auxiliar
        try:
            auxiliar_content = await file_auxiliar.read()
            df_auxiliar = pd.read_excel(io.BytesIO(auxiliar_content))
            df_auxiliar['fecha'] = pd.to_datetime(
                df_auxiliar['fecha'], 
                format='%d-%m-%Y',      # <-- USAMOS EL FORMATO DE ENTRADA REAL (DD-MM-YYYY)
                errors='coerce'
            ).dt.strftime('%Y-%m-%d')   # <-- GUARDAMOS EL STRING ESTANDARIZADO (YYYY-MM-DD)
            df_auxiliar.dropna(subset=['fecha'], inplace=True)

            validar_excel(df_auxiliar, nombre_archivo=file_auxiliar.filename, tipo_archivo="AUXILIAR")
        except Exception as e:
            raise ValueError(f"Error en el archivo AUXILIAR ({file_auxiliar.filename}): {str(e)}")
        
        # Si llegamos aquí, ambos archivos son válidos
        # Crear y guardar la nueva conciliación
        nueva_conciliacion = Conciliacion(
            id_empresa=id_empresa,
            fecha_proceso=datetime.now().strftime("%Y-%m-%d"),
            nombre_archivo_banco=file_banco.filename,
            nombre_archivo_auxiliar=file_auxiliar.filename,
            mes_conciliado=mes,
            cuenta_conciliada=cuenta,
            año_conciliado=anio
        )
        db.add(nueva_conciliacion)
        db.commit()
        
        # IMPORTANTE: Guardar el ID antes de continuar
        conciliacion_id = nueva_conciliacion.id

        # Procesar movimientos del banco
        movimientos_banco = []
        for index, row in df_banco.iterrows():
            movimientos_banco.append(Movimiento(
                id_conciliacion=conciliacion_id,  # Usar la variable guardada
                fecha=str(row['fecha']),
                descripcion=row['descripcion'],
                valor=abs(row['valor']),
                es=row['es'],
                tipo='banco'
            ))

        # Procesar movimientos auxiliar
        movimientos_auxiliar = []
        for index, row in df_auxiliar.iterrows():
            movimientos_auxiliar.append(Movimiento(
                id_conciliacion=conciliacion_id,  # Usar la variable guardada
                fecha=str(row['fecha']),
                descripcion=row['descripcion'],
                valor=abs(row['valor']),
                es=row['es'],
                tipo='auxiliar'
            ))

        # Guardar todos los movimientos
        db.bulk_save_objects(movimientos_banco)
        db.bulk_save_objects(movimientos_auxiliar)
        db.commit()

        # Mensaje de éxito (también usar la variable guardada)
        mensaje_exito = f"Archivos cargados exitosamente para la conciliación #{conciliacion_id} del mes de {mes}, año {anio} y cuenta {cuenta}"

        print(mensaje_exito)

        return templates.TemplateResponse("success.html", {"request": request, "conciliacion_id": conciliacion_id})
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error_message": str(e)})

@router.get("/conciliacion/{conciliacion_id}")
def detalle_conciliacion(conciliacion_id: int, request: Request, db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    movimientos = db.query(Movimiento).filter(Movimiento.id_conciliacion == conciliacion_id).all()
    movimientos_no_conciliados = {
        "banco": [m for m in movimientos if m.origen == "banco" and m.conciliado == "no"],
        "auxiliar": [m for m in movimientos if m.origen == "auxiliar" and m.conciliado == "no"],
    }
    movimientos_conciliados = db.query(ConciliacionMatch).filter(ConciliacionMatch.conciliacion_id == conciliacion_id).all()

    total = len(movimientos)
    conciliados = len(movimientos_conciliados)
    porcentaje = int((conciliados / total) * 100) if total else 0
    stats = {"porcentaje_conciliacion": porcentaje, "conciliados": conciliados, "total_movimientos": total}

    return templates.TemplateResponse("detalle_conciliacion.html", {
        "request": request,
        "conciliacion": conciliacion,
        "movimientos_no_conciliados": movimientos_no_conciliados,
        "movimientos_conciliados": movimientos_conciliados,
        "stats": stats
    })


@router.get('/descargar_plantilla')
def descargar_plantilla():
    """Devuelve el archivo plantilla_movimientos.xlsx ubicado en la raíz del proyecto."""
    # project package_dir is app/ so go up one more level to reach repo root
    repo_root = Path(__file__).resolve().parent.parent.parent
    candidate = repo_root / 'plantilla_movimientos.xlsx'
    if not candidate.exists():
        raise HTTPException(status_code=404, detail='Plantilla no encontrada')
    return FileResponse(str(candidate), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename='plantilla_movimientos.xlsx')


@router.post("/conciliacion/{conciliacion_id}/procesar", response_class=RedirectResponse)
def procesar_conciliacion(conciliacion_id: int, db: Session = Depends(get_db)):
    """
    Procesa automáticamente una conciliación utilizando los métodos de conciliación en utils/conciliaciones.py.
    """
    realizar_conciliacion_automatica(conciliacion_id, db)
    return RedirectResponse(url=f"/detalle_conciliacion/{conciliacion_id}", status_code=303)

@router.post("/conciliacion/{conciliacion_id}/terminar_conciliacion")
def terminar_conciliacion(conciliacion_id: int, db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(404, "Conciliación no encontrada")
    conciliacion.estado = "finalizada"
    db.commit()
    return RedirectResponse(url=f"/detalle_conciliacion/{conciliacion_id}", status_code=303)

class ConciliacionManualRequest(BaseModel):
    id_banco: List[int]
    id_auxiliar: List[int]

@router.post("/conciliacion/{conciliacion_id}/conciliar-manual")
def conciliar_manual(conciliacion_id: int, request: ConciliacionManualRequest, db: Session = Depends(get_db)):
    """
    Realiza una conciliación manual utilizando el método en utils/conciliaciones.py.
    """
    resultado = crear_conciliacion_manual(conciliacion_id, request.id_banco, request.id_auxiliar, db)
    return resultado

@router.delete("/conciliacion/match/{match_id}/eliminar")
def eliminar_match_manual(match_id: int, db: Session = Depends(get_db)):
    match = db.query(ConciliacionMatch).filter(ConciliacionMatch.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match no encontrado")
    # optional: unmark movimientos if desired
    db.delete(match)
    db.commit()
    return {"ok": True}

"""
genera el endpoint /lista_conciliaciones
que devuelva en formato HTML la lista de conciliaciones"""
@router.get("/lista_conciliaciones", name="lista_conciliaciones_html")
def lista_conciliaciones_html(request: Request, db: Session = Depends(get_db)):
    conciliaciones = db.query(Conciliacion).order_by(Conciliacion.id.desc()).all()

    conciliaciones_por_empresa = {}
    for c in conciliaciones:
        empresa = c.empresa.razon_social if c.empresa and c.empresa.razon_social else (c.empresa.nombre_comercial if c.empresa else 'Desconocida')

        movimientos = db.query(Movimiento).filter(Movimiento.id_conciliacion == c.id).all()
        total_movimientos = len(movimientos)

        # Filtrar movimientos conciliados directamente
        movimientos_conciliados = [m for m in movimientos if m.estado_conciliacion == "conciliado"]
        total_conciliados = len(movimientos_conciliados)

        porcentaje_conciliacion = (total_conciliados / total_movimientos * 100) if total_movimientos > 0 else 0

        conc_obj = {
            'id': c.id,
            'mes_conciliado': c.mes_conciliado,
            'año_conciliado': getattr(c, 'anio_conciliado', None) or getattr(c, 'año_conciliado', None) or '',
            'cuenta_conciliada': c.cuenta_conciliada,
            'estado': c.estado,
            'total_movimientos': total_movimientos,
            'conciliados': total_conciliados,
            'porcentaje_conciliacion': porcentaje_conciliacion,
        }

        if empresa not in conciliaciones_por_empresa:
            conciliaciones_por_empresa[empresa] = {'en_proceso': [], 'finalizadas': []}

        if c.estado and c.estado.lower() == 'finalizada':
            conciliaciones_por_empresa[empresa]['finalizadas'].append(conc_obj)
        else:
            conciliaciones_por_empresa[empresa]['en_proceso'].append(conc_obj)

    return templates.TemplateResponse("lista_conciliaciones.html", {"request": request, "conciliaciones_por_empresa": conciliaciones_por_empresa})

"""genera el endpoint /detalle_conciliacion/{conciliacion_id}
que devuelva en formato HTML el detalle de una conciliación específica,
incluyendo los movimientos no conciliados (separados por banco y auxiliar),
los movimientos conciliados, y las estadísticas de la conciliación."""
@router.get("/detalle_conciliacion/{conciliacion_id}", name="detalle_conciliacion_html")
def detalle_conciliacion_html(conciliacion_id: int, request: Request, db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(404, "Conciliación no encontrada")

    movimientos = db.query(Movimiento).filter(Movimiento.id_conciliacion == conciliacion_id).all()
    matches = db.query(ConciliacionMatch).filter(ConciliacionMatch.id_conciliacion == conciliacion_id).all()

    # Separar movimientos por estado y origen
    movimientos_no_conciliados = {
        "banco": [m.to_dict() for m in movimientos if m.estado_conciliacion == "no_conciliado" and m.tipo == "banco"],
        "auxiliar": [m.to_dict() for m in movimientos if m.estado_conciliacion == "no_conciliado" and m.tipo == "auxiliar"]
    }
    movimientos_conciliados = [m.to_dict() for m in movimientos if m.estado_conciliacion == "conciliado"]

    # Calcular estadísticas
    total_movimientos = len(movimientos)
    total_conciliados = len(movimientos_conciliados)
    porcentaje_conciliacion = (total_conciliados / total_movimientos * 100) if total_movimientos > 0 else 0

    stats = {
        "total_movimientos": total_movimientos,
        "total_conciliados": total_conciliados,
        "total_no_conciliados": len(movimientos_no_conciliados["banco"]) + len(movimientos_no_conciliados["auxiliar"]),
        "total_matches": len(matches),
        "porcentaje_conciliacion": porcentaje_conciliacion
    }

    return templates.TemplateResponse("detalle_conciliacion.html", {
        "request": request,
        "conciliacion": conciliacion,
        "movimientos_no_conciliados": movimientos_no_conciliados,
        "movimientos_conciliados": movimientos_conciliados,
        "matches": matches,
        "stats": stats
    })

"""genera el endpoint /conciliaciones_empresa/{empresa_id}
que devuelva en formato HTML las
conciliaciones de una empresa específica, separadas en dos listas:
- conciliaciones en proceso """

@router.get("/conciliaciones_empresa/{empresa_id}", name="conciliaciones_empresa_html")
def conciliaciones_empresa_html(request: Request, empresa_id: int, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    conciliaciones = db.query(Conciliacion).filter(Conciliacion.id_empresa == empresa_id).all()
    en_proceso = [c for c in conciliaciones if c.estado == 'en_proceso']
    finalizadas = [c for c in conciliaciones if c.estado == 'finalizada']

    # Log para depuración
    print("Conciliaciones en proceso:", en_proceso)
    print("Conciliaciones finalizadas:", finalizadas)

    return templates.TemplateResponse("conciliaciones_empresa.html", {
        "request": request,
        "empresa": empresa,
        "en_proceso": en_proceso,
        "finalizadas": finalizadas
    })


"""
genera el endpoint /nueva_empresa
que devuelva en formato HTML el formulario para crear una nueva empresa.
"""
@router.get("/nueva_empresa", name="nueva_empresa_html")
def nueva_empresa_html(request: Request):
    return templates.TemplateResponse("nueva_empresa.html", {"request": request})


"""
genera el endpoint /matches_conciliacion/{conciliacion_id}
que devuelva en formato HTML los matches de una conciliación específica que fueron Automaticos.
"""
@router.get("/matches_conciliacion/{conciliacion_id}", name="matches_conciliacion_html")
def matches_conciliacion_html(request: Request, conciliacion_id: int, db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    movimientos_banco = {mov.id: mov for mov in db.query(Movimiento).filter(Movimiento.tipo == 'banco').all()}
    movimientos_auxiliar = {mov.id: mov for mov in db.query(Movimiento).filter(Movimiento.tipo == 'auxiliar').all()}

    matches = [
        {
            "id": match.id,
            "movimiento_banco": movimientos_banco.get(match.id_movimiento_banco),
            "movimiento_auxiliar": movimientos_auxiliar.get(match.id_movimiento_auxiliar),
            "diferencia": match.diferencia_valor
        }
        for match in db.query(ConciliacionMatch).filter(ConciliacionMatch.id_conciliacion == conciliacion_id).all()
    ]

    print(matches)

    return templates.TemplateResponse("matches_conciliacion.html", {
        "request": request,
        "conciliacion": conciliacion,
        "matches": matches
    })





"""
genera el endpoint /conciliacion/{conciliacion_id}/matches_y_manuales
que devuelva en formato JSON los matches y las conciliaciones manuales de una conciliación específica.
"""
@router.get("/conciliacion/{conciliacion_id}/matches_y_manuales", name="matches_y_conciliaciones_manuales")
def obtener_matches_y_conciliaciones_manuales(conciliacion_id: int, db: Session = Depends(get_db)):
    """
    Endpoint para obtener los matches y las conciliaciones manuales de una conciliación específica.
    """
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    # Obtener los movimientos de banco y auxiliar
    movimientos_banco = {mov.id: mov.to_dict() for mov in db.query(Movimiento).filter(Movimiento.tipo == 'banco').all()}
    movimientos_auxiliar = {mov.id: mov.to_dict() for mov in db.query(Movimiento).filter(Movimiento.tipo == 'auxiliar').all()}

    # Obtener los matches
    matches = [
        {
            "id": match.id,
            "movimiento_banco": movimientos_banco.get(match.id_movimiento_banco),
            "movimiento_auxiliar": movimientos_auxiliar.get(match.id_movimiento_auxiliar),
            "diferencia": match.diferencia_valor
        }
        for match in db.query(ConciliacionMatch).filter(ConciliacionMatch.id_conciliacion == conciliacion_id).all()
    ]

    # Obtener las conciliaciones manuales
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

    return JSONResponse(content={"matches": matches, "conciliaciones_manuales": resultado_manuales})