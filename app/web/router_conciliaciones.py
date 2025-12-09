from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Conciliacion
from app.repositories.factory import RepositoryFactory
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/{conciliacion_id}/empresa", name="conciliaciones_empresa")
def conciliaciones_empresa(request: Request, conciliacion_id: int):
    return templates.TemplateResponse("conciliaciones_empresa.html", {
        "request": request,
        "empresa_id": conciliacion_id  # Pasar el ID como empresa_id para el frontend
    })

@router.get("/detalle/{conciliacion_id}", name="detalle_conciliacion")
def detalle_conciliacion(request: Request, conciliacion_id: int, db: Session = Depends(get_db)):
    factory = RepositoryFactory(db)
    conciliacion_repo = factory.get_conciliacion_repository()
    
    conciliacion = conciliacion_repo.get_by_id(conciliacion_id)
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    return templates.TemplateResponse("detalle_conciliacion.html", {
        "request": request,
        "conciliacion_id": conciliacion_id,
        "conciliacion": conciliacion
    })

@router.get("/", name="lista_conciliaciones")
def lista_conciliaciones(request: Request):
    return templates.TemplateResponse("lista_conciliaciones.html", {"request": request}) 

@router.get("/matches_conciliacion/{conciliacion_id}", name="matches_conciliacion")
def matches_conciliacion(request: Request, conciliacion_id: int):
    return templates.TemplateResponse("matches_conciliacion.html", {
        "request": request,
        "conciliacion": {"id": conciliacion_id}
    })

@router.get("/agregar_movimientos/{conciliacion_id}", name="agregar_movimientos")
def agregar_movimientos(request: Request, conciliacion_id: int, db: Session = Depends(get_db)):
    factory = RepositoryFactory(db)
    conciliacion_repo = factory.get_conciliacion_repository()
    
    conciliacion = conciliacion_repo.get_by_id(conciliacion_id)
    if not conciliacion:
        raise HTTPException(status_code=404, detail="Conciliación no encontrada")

    return templates.TemplateResponse("agregar_movimientos.html", {
        "request": request,
        "conciliacion_id": conciliacion_id,
        "conciliacion": conciliacion
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