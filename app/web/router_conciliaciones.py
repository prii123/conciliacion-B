from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Conciliacion
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/conciliaciones_empresa", name="conciliaciones_empresa")
def conciliaciones_empresa(request: Request):
    return templates.TemplateResponse("conciliaciones_empresa.html", {"request": request})

@router.get("/detalle/{conciliacion_id}", name="detalle_conciliacion")
def detalle_conciliacion(request: Request, conciliacion_id: int, db: Session = Depends(get_db)):
    conciliacion = db.query(Conciliacion).filter(Conciliacion.id == conciliacion_id).first()
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