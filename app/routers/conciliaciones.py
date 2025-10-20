from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List
import io, pandas as pd
from ..database import get_db
from ..models import Conciliacion, Movimiento, ConciliacionMatch
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()
package_dir = Path(__file__).resolve().parent.parent
templates_dir = package_dir / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@router.get("/conciliaciones")
def lista_conciliaciones(request: Request, db: Session = Depends(get_db)):
    # Query conciliaciones and group them by empresa name into 'en_proceso' and 'finalizadas'
    conciliaciones = db.query(Conciliacion).order_by(Conciliacion.id.desc()).all()

    conciliaciones_por_empresa = {}
    for c in conciliaciones:
        # get company display name
        empresa = c.empresa.razon_social if c.empresa and c.empresa.razon_social else (c.empresa.nombre_comercial if c.empresa else 'Desconocida')

        # compute stats
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

@router.post("/upload")
def upload_files(file_banco: UploadFile = File(...),
                 file_auxiliar: UploadFile = File(...),
                 mes: str = Form(...),
                 cuenta: str = Form(...),
                 anio: int = Form(...),
                 id_empresa: int = Form(...),
                 db: Session = Depends(get_db)):
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

    return RedirectResponse(url=f"/conciliacion/{conciliacion.id}", status_code=303)

@router.get("/conciliacion/{conciliacion_id}")
def detalle_conciliacion(request: Request, conciliacion_id: int, db: Session = Depends(get_db)):
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


@router.post("/conciliacion/{conciliacion_id}/procesar")
def procesar_conciliacion(conciliacion_id: int, request: Request, db: Session = Depends(get_db)):
    """Procesamiento automático básico: busca matches exactos por valor y tipo (es)
    Marca movimientos como conciliados y crea registros en ConciliacionMatch.
    Devuelve estadísticas sencillas utilizadas por la UI.
    """
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(404, "Conciliación no encontrada")

    # obtener movimientos no conciliados por origen
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
    # simple greedy matching: por igual valor y mismo tipo (es)
    for mb in list(movimientos_banco):
        # buscar un auxiliar que coincida exactamente en valor y tipo
        candidato = None
        for ma in movimientos_aux:
            if (ma.es or '').upper() == (mb.es or '').upper() and (ma.valor or 0.0) == (mb.valor or 0.0):
                candidato = ma
                break

        if candidato:
            # marcar conciliados
            mb.conciliado = 'si'
            candidato.conciliado = 'si'
            match = ConciliacionMatch(
                conciliacion_id=conciliacion_id,
                movimiento_banco_id=mb.id,
                movimiento_auxiliar_id=candidato.id,
                diferencia=abs((mb.valor or 0.0) - (candidato.valor or 0.0))
            )
            db.add(match)
            # evitar volver a usar el mismo auxiliar
            try:
                movimientos_aux.remove(candidato)
            except ValueError:
                pass
            matches_exactos += 1

    db.commit()

    stats = {
        'matches_exactos': matches_exactos,
        'matches_aproximados': 0,
        'total_matches': matches_exactos
    }

    # If request came from a normal browser form submit (Accept: text/html), redirect back to detalle page
    accept = request.headers.get('accept', '')
    if 'text/html' in accept.lower():
        return RedirectResponse(url=f"/conciliacion/{conciliacion_id}", status_code=303)

    # Default: return JSON for API/fetch clients
    return {"success": True, "stats": stats}

@router.post("/conciliacion/{conciliacion_id}/terminar_conciliacion")
def terminar_conciliacion(conciliacion_id: int, db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(404, "Conciliación no encontrada")
    conciliacion.estado = "finalizada"
    db.commit()
    return RedirectResponse(url=f"/conciliacion/{conciliacion_id}", status_code=303)

@router.post("/conciliacion/{conciliacion_id}/conciliar-manual")
def conciliar_manual(conciliacion_id: int, banco_ids: List[int] = Form(...), auxiliar_ids: List[int] = Form(...), db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
    if not conciliacion:
        raise HTTPException(404, "Conciliación no encontrada")

    for b_id, a_id in zip(banco_ids, auxiliar_ids):
        mb = db.query(Movimiento).filter(Movimiento.id == b_id, Movimiento.conciliacion_id==conciliacion_id).first()
        ma = db.query(Movimiento).filter(Movimiento.id == a_id, Movimiento.conciliacion_id==conciliacion_id).first()
        if not mb or not ma:
            continue
        mb.conciliado = "si"
        ma.conciliado = "si"
        match = ConciliacionMatch(conciliacion_id=conciliacion_id, movimiento_banco_id=mb.id, movimiento_auxiliar_id=ma.id, diferencia=abs((mb.valor or 0.0) - (ma.valor or 0.0)))
        db.add(match)
    db.commit()
    return RedirectResponse(url=f"/conciliacion/{conciliacion_id}", status_code=303)

@router.delete("/conciliacion/match/{match_id}/eliminar")
def eliminar_match_manual(match_id: int, db: Session = Depends(get_db)):
    match = db.query(ConciliacionMatch).filter(ConciliacionMatch.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match no encontrado")
    # optional: unmark movimientos if desired
    db.delete(match)
    db.commit()
    return {"ok": True}