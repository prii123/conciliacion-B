from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List, Dict, Any
from ..database import get_db
from ..models import Empresa, Conciliacion
from ..schemas import EmpresaSchema, ConciliacionSchema

router = APIRouter()
# Use absolute templates directory inside the app package
package_dir = Path(__file__).resolve().parent.parent
templates_dir = package_dir / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@router.get("/empresas", name="lista_empresas")
def lista_empresas(request: Request, db: Session = Depends(get_db)):
    empresas = db.query(Empresa).order_by(Empresa.id.desc()).all()
    return templates.TemplateResponse("lista_empresas.html", {"request": request, "empresas": empresas})

@router.get("/empresas/nueva", name="nueva_empresa")
def nueva_empresa_form(request: Request):
    return templates.TemplateResponse("nueva_empresa.html", {"request": request})

@router.post("/empresas/nueva", name="nueva_empresa_post")
def nueva_empresa_post(request: Request, nit: str = Form(...), razon_social: str = Form(...),
                       nombre_comercial: str = Form(None), ciudad: str = Form(None),
                       db: Session = Depends(get_db)):
    # Validate unique NIT
    existing = db.query(Empresa).filter(Empresa.nit == nit).first()
    if existing:
        # Return form with an error message
        return templates.TemplateResponse("nueva_empresa.html", {"request": request, "error": f"Ya existe una empresa con NIT {nit}", "nit": nit, "razon_social": razon_social, "nombre_comercial": nombre_comercial, "ciudad": ciudad})

    empresa = Empresa(nit=nit, razon_social=razon_social, nombre_comercial=nombre_comercial, ciudad=ciudad)
    db.add(empresa)
    db.commit()
    return RedirectResponse(url="/empresas", status_code=303)

@router.get("/empresas/{empresa_id}/conciliaciones", name="conciliaciones_empresas")
def conciliaciones_empresa(request: Request, empresa_id: int, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        return templates.TemplateResponse("lista_empresas.html", {"request": request, "error": "Empresa no encontrada"})

    conciliaciones = db.query(Conciliacion).filter(Conciliacion.id_empresa == empresa_id).order_by(Conciliacion.id.desc()).all()
    en_proceso = [ConciliacionSchema.from_orm(c).dict() for c in conciliaciones if c.estado == 'en_proceso']
    finalizadas = [ConciliacionSchema.from_orm(c).dict() for c in conciliaciones if c.estado == 'finalizada']

    # Log para depuración
    print("Empresa:", empresa)
    print("Conciliaciones en proceso:", en_proceso)
    print("Conciliaciones finalizadas:", finalizadas)

    return templates.TemplateResponse("conciliaciones_empresa.html", {
        "request": request,
        "empresa": empresa,
        "en_proceso": en_proceso,
        "finalizadas": finalizadas
    })

@router.get("/guia", name="guia")
def guia(request: Request):
    return templates.TemplateResponse("guia.html", {"request": request})




