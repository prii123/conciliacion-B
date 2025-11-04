from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, Form, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import io, pandas as pd

from app.utils.utils import validar_excel
from ..database import get_db
from ..models import Conciliacion, Movimiento, ConciliacionMatch, Empresa, ConciliacionManual, ConciliacionManualBanco, ConciliacionManualAuxiliar
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from ..utils.conciliaciones import realizar_conciliacion_automatica, crear_conciliacion_manual

router = APIRouter()

@router.get("/")
def lista_conciliaciones_json(db: Session = Depends(get_db)):
    conciliaciones = db.query(Conciliacion).order_by(Conciliacion.id.desc()).all()

    conciliaciones_por_empresa = {}
    for c in conciliaciones:
        empresa = c.empresa.razon_social if c.empresa and c.empresa.razon_social else (c.empresa.nombre_comercial if c.empresa else 'Desconocida')

        # Obtener estadísticas directamente desde la tabla Movimiento
        total = db.query(Movimiento).filter(Movimiento.id_conciliacion == c.id).count()
        conciliados = db.query(Movimiento).filter(
            Movimiento.id_conciliacion == c.id,
            Movimiento.estado_conciliacion == "conciliado"
        ).count()
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
def detalle_conciliacion_json(conciliacion_id: int, db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    movimientos = db.query(Movimiento).filter(Movimiento.id_conciliacion == conciliacion_id).all()
    movimientos_no_conciliados = {
        "banco": jsonable_encoder([m for m in movimientos if m.tipo == "banco" and m.estado_conciliacion == "no_conciliado"]),
        "auxiliar": jsonable_encoder([m for m in movimientos if m.tipo == "auxiliar" and m.estado_conciliacion == "no_conciliado"]),
    }

    movimientos_conciliados_automaticos = [
        {
            "id": match.id,
            "id_movimiento_banco": match.id_movimiento_banco,
            "id_movimiento_auxiliar": match.id_movimiento_auxiliar,
            "fecha_match": match.fecha_match,
            "criterio_match": match.criterio_match,
            "diferencia_valor": match.diferencia_valor
        }
        for match in db.query(ConciliacionMatch).filter(ConciliacionMatch.id_conciliacion == conciliacion_id).all()
    ]

    movimientos_conciliados_manuales = [
        {
            "id": cm.id,
            "id_movimiento_banco": banco.id,
            "id_movimiento_auxiliar": auxiliar.id,
            "fecha_match": cm.fecha_creacion,
            "criterio_match": "manual",
            "diferencia_valor": abs(banco.valor - auxiliar.valor)
        }
        for cm in db.query(ConciliacionManual).filter(ConciliacionManual.id_conciliacion == conciliacion_id).all()
        for banco in db.query(Movimiento).join(ConciliacionManualBanco).filter(ConciliacionManualBanco.id_conciliacion_manual == cm.id).all()
        for auxiliar in db.query(Movimiento).join(ConciliacionManualAuxiliar).filter(ConciliacionManualAuxiliar.id_conciliacion_manual == cm.id).all()
    ]

    movimientos_conciliados = movimientos_conciliados_automaticos + movimientos_conciliados_manuales

    # Calcular estadísticas directamente desde la tabla Movimiento
    total = len(movimientos)
    conciliados = len(movimientos_conciliados)
    pendientes = total - conciliados
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

@router.post("/upload")
async def upload_files(
    file_banco: UploadFile = File(...),
    file_auxiliar: UploadFile = File(...),
    mes: str = Form(...),
    cuenta: str = Form(...),
    anio: int = Form(...),
    id_empresa: int = Form(...),
    db: Session = Depends(get_db)
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
        conciliacion_id = nueva_conciliacion.id

        movimientos_banco = [
            Movimiento(
                id_conciliacion=conciliacion_id,
                fecha=str(row['fecha']),
                descripcion=row['descripcion'],
                valor=abs(row['valor']),
                es=row['es'],
                tipo='banco'
            )
            for _, row in df_banco.iterrows()
        ]

        movimientos_auxiliar = [
            Movimiento(
                id_conciliacion=conciliacion_id,
                fecha=str(row['fecha']),
                descripcion=row['descripcion'],
                valor=abs(row['valor']),
                es=row['es'],
                tipo='auxiliar'
            )
            for _, row in df_auxiliar.iterrows()
        ]

        db.bulk_save_objects(movimientos_banco)
        db.bulk_save_objects(movimientos_auxiliar)
        db.commit()

        return JSONResponse(content={"message": f"Archivos cargados exitosamente para la conciliación #{conciliacion_id}"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


@router.post("/{conciliacion_id}/procesar")
def procesar_conciliacion(conciliacion_id: int, db: Session = Depends(get_db)):
    """
    Procesa automáticamente una conciliación utilizando los métodos de conciliación en utils/conciliaciones.py.
    """
    realizar_conciliacion_automatica(conciliacion_id, db)
    return {"message": f"Conciliación #{conciliacion_id} procesada automáticamente."}

@router.post("/{conciliacion_id}/terminar_conciliacion")
def terminar_conciliacion(conciliacion_id: int, db: Session = Depends(get_db)):
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
def conciliar_manual(conciliacion_id: int, request: ConciliacionManualRequest, db: Session = Depends(get_db)):
    """
    Realiza una conciliación manual utilizando el método en utils/conciliaciones.py.
    """
    resultado = crear_conciliacion_manual(conciliacion_id, request.id_banco, request.id_auxiliar, db)
    return {"message": "Conciliación manual realizada con éxito.", "resultado": resultado}

@router.delete("/match/{match_id}/eliminar")
def eliminar_match_manual(match_id: int, db: Session = Depends(get_db)):
    match = db.query(ConciliacionMatch).filter(ConciliacionMatch.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match no encontrado")
    # optional: unmark movimientos if desired
    db.delete(match)
    db.commit()
    return {"message": f"Match #{match_id} eliminado con éxito."}

@router.get("/conciliaciones_empresa/{empresa_id}", name="conciliaciones_empresa_json") 
def conciliaciones_empresa_json(empresa_id: int, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    conciliaciones = db.query(Conciliacion).filter(Conciliacion.id_empresa == empresa_id).all()
    en_proceso = [c.to_dict() for c in conciliaciones if c.estado == 'en_proceso']
    finalizadas = [c.to_dict() for c in conciliaciones if c.estado == 'finalizada']

    return JSONResponse(content={"empresa": empresa.to_dict(), "en_proceso": en_proceso, "finalizadas": finalizadas})


@router.get("/{conciliacion_id}/matches_y_manuales", name="matches_y_conciliaciones_manuales")
def obtener_matches_y_conciliaciones_manuales(conciliacion_id: int, db: Session = Depends(get_db)):
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
            "criterio_match": match.criterio_match,  # Add criterio_match field
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

    return JSONResponse(content={"matches": matches, "conciliaciones_manuales": resultado_manuales})

