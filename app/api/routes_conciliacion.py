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
    movimientos_conciliados = db.query(ConciliacionMatch).filter(ConciliacionMatch.id_conciliacion == conciliacion_id).all()

    total = len(movimientos)
    conciliados = len(movimientos_conciliados)
    porcentaje = int((conciliados / total) * 100) if total else 0
    stats = {"porcentaje_conciliacion": porcentaje, "conciliados": conciliados, "total_movimientos": total}

    return JSONResponse(content={
        "conciliacion": jsonable_encoder(conciliacion),
        "movimientos_no_conciliados": movimientos_no_conciliados,
        "movimientos_conciliados": jsonable_encoder(movimientos_conciliados),
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

