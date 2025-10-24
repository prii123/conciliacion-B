from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List
import io, pandas as pd
from ..database import get_db
from ..models import Conciliacion, Movimiento, ConciliacionMatch, Empresa
from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

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

        movimientos = db.query(Movimiento).filter(Movimiento.conciliacion_id == c.id).all()
        total = len(movimientos)
        conciliados = db.query(ConciliacionMatch).filter(ConciliacionMatch.conciliacion_id == c.id).count()
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

    movimientos = db.query(Movimiento).filter(Movimiento.conciliacion_id == conciliacion_id).all()
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
def upload_files(request: Request,
                 file_banco: UploadFile = File(...),
                 file_auxiliar: UploadFile = File(...),
                 mes: str = Form(...),
                 cuenta: str = Form(...),
                 anio: int = Form(...),
                 id_empresa: int = Form(...),
                 db: Session = Depends(get_db)):
    try:
        conciliacion = Conciliacion(id_empresa=id_empresa, mes_conciliado=mes, anio_conciliado=anio, cuenta_conciliada=cuenta)
        db.add(conciliacion)
        db.commit()
        db.refresh(conciliacion)

        def read_movs(upload, origen_label):
            upload.file.seek(0)
            content = upload.file.read()
            df = pd.read_excel(io.BytesIO(content))
            rows = []
            for _, r in df.iterrows():
                rows.append(Movimiento(
                    conciliacion_id=conciliacion.id,
                    fecha=str(r.get('fecha')),
                    descripcion=str(r.get('descripcion', '')),
                    valor=float(r.get('valor') or 0.0),
                    es=str(r.get('es', '')).upper(),
                    origen=origen_label,
                ))
            return rows

        movimientos = read_movs(file_banco, "banco") + read_movs(file_auxiliar, "auxiliar")
        db.add_all(movimientos)
        db.commit()

        return templates.TemplateResponse("success.html", {"request": request, "conciliacion_id": conciliacion.id})
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error_message": str(e)})

@router.get("/conciliacion/{conciliacion_id}")
def detalle_conciliacion(conciliacion_id: int, request: Request, db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    movimientos = db.query(Movimiento).filter(Movimiento.conciliacion_id == conciliacion_id).all()
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
    Procesa automáticamente una conciliación buscando matches exactos por valor y tipo (E/S).
    Marca movimientos como conciliados y crea registros en ConciliacionMatch.
    Redirige de vuelta a la vista de detalle de la conciliación.
    """
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    # Obtener movimientos no conciliados por origen
    movimientos_banco = db.query(Movimiento).filter(
        Movimiento.conciliacion_id == conciliacion_id,
        Movimiento.origen == 'banco',
        Movimiento.conciliado == 'no'
    ).all()
    movimientos_aux = db.query(Movimiento).filter(
        Movimiento.conciliacion_id == conciliacion_id,
        Movimiento.origen == 'auxiliar',
        Movimiento.conciliado == 'no'
    ).all()

    matches_exactos = 0
    # Buscar matches exactos por valor y tipo (E/S)
    for mb in list(movimientos_banco):
        candidato = next((ma for ma in movimientos_aux if ma.es == mb.es and ma.valor == mb.valor), None)
        if candidato:
            mb.conciliado = 'si'
            candidato.conciliado = 'si'
            match = ConciliacionMatch(
                conciliacion_id=conciliacion_id,
                movimiento_banco_id=mb.id,
                movimiento_auxiliar_id=candidato.id,
                diferencia=0.0
            )
            db.add(match)
            movimientos_aux.remove(candidato)
            matches_exactos += 1

    db.commit()

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
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(404, "Conciliación no encontrada")

    for b_id, a_id in zip(request.id_banco, request.id_auxiliar):
        mb = db.query(Movimiento).filter(Movimiento.id == b_id, Movimiento.conciliacion_id == conciliacion_id).first()
        ma = db.query(Movimiento).filter(Movimiento.id == a_id, Movimiento.conciliacion_id == conciliacion_id).first()
        if not mb or not ma:
            continue
        mb.conciliado = "si"
        ma.conciliado = "si"
        match = ConciliacionMatch(
            conciliacion_id=conciliacion_id,
            movimiento_banco_id=mb.id,
            movimiento_auxiliar_id=ma.id,
            diferencia=abs((mb.valor or 0.0) - (ma.valor or 0.0))
        )
        db.add(match)
    db.commit()
    return {"success": True, "mensaje": "Conciliación manual creada correctamente."}

@router.delete("/conciliacion/match/{match_id}/eliminar")
def eliminar_match_manual(match_id: int, db: Session = Depends(get_db)):
    match = db.query(ConciliacionMatch).filter(ConciliacionMatch.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match no encontrado")
    # optional: unmark movimientos if desired
    db.delete(match)
    db.commit()
    return {"ok": True}

@router.get("/lista_conciliaciones", name="lista_conciliaciones_html")
def lista_conciliaciones_html(request: Request, db: Session = Depends(get_db)):
    conciliaciones = db.query(Conciliacion).order_by(Conciliacion.id.desc()).all()

    conciliaciones_por_empresa = {}
    for c in conciliaciones:
        empresa = c.empresa.razon_social if c.empresa and c.empresa.razon_social else (c.empresa.nombre_comercial if c.empresa else 'Desconocida')

        movimientos = db.query(Movimiento).filter(Movimiento.conciliacion_id == c.id).all()
        total = len(movimientos)
        conciliados = db.query(ConciliacionMatch).filter(ConciliacionMatch.conciliacion_id == c.id).count()
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

    return templates.TemplateResponse("lista_conciliaciones.html", {"request": request, "conciliaciones_por_empresa": conciliaciones_por_empresa})

@router.get("/detalle_conciliacion/{conciliacion_id}", name="detalle_conciliacion_html")
def detalle_conciliacion_html(request: Request, conciliacion_id: int, db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    movimientos = db.query(Movimiento).filter(Movimiento.conciliacion_id == conciliacion_id).all()
    movimientos_no_conciliados = {
        "banco": [m.to_dict() for m in movimientos if m.origen == "banco" and m.conciliado == "no"],
        "auxiliar": [m.to_dict() for m in movimientos if m.origen == "auxiliar" and m.conciliado == "no"],
    }
    movimientos_conciliados = [m.to_dict() for m in movimientos if m.conciliado == "si"]

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

@router.get("/conciliaciones_empresa/{empresa_id}", name="conciliaciones_empresa_html")
def conciliaciones_empresa_html(request: Request, empresa_id: int, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    conciliaciones = db.query(Conciliacion).filter(Conciliacion.id_empresa == empresa_id).all()
    en_proceso = [c for c in conciliaciones if c.estado == 'en_proceso']
    finalizadas = [c for c in conciliaciones if c.estado == 'finalizada']

    return templates.TemplateResponse("conciliaciones_empresa.html", {
        "request": request,
        "empresa": empresa,
        "en_proceso": en_proceso,
        "finalizadas": finalizadas
    })

@router.get("/nueva_empresa", name="nueva_empresa_html")
def nueva_empresa_html(request: Request):
    return templates.TemplateResponse("nueva_empresa.html", {"request": request})

@router.get("/matches_conciliacion/{conciliacion_id}", name="matches_conciliacion_html")
def matches_conciliacion_html(request: Request, conciliacion_id: int, db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    movimientos_banco = {mov.id: mov for mov in db.query(Movimiento).filter(Movimiento.origen == 'banco').all()}
    movimientos_auxiliar = {mov.id: mov for mov in db.query(Movimiento).filter(Movimiento.origen == 'auxiliar').all()}

    matches = [
        {
            "id": match.id,
            "movimiento_banco": movimientos_banco.get(match.movimiento_banco_id),
            "movimiento_auxiliar": movimientos_auxiliar.get(match.movimiento_auxiliar_id),
            "diferencia": match.diferencia
        }
        for match in db.query(ConciliacionMatch).filter(ConciliacionMatch.conciliacion_id == conciliacion_id).all()
    ]

    print(matches)

    return templates.TemplateResponse("matches_conciliacion.html", {
        "request": request,
        "conciliacion": conciliacion,
        "matches": matches
    })