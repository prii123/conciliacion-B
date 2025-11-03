from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

@router.get("/")
def home(request: Request):
    return templates.TemplateResponse("empresas.html", {"request": request, "title": "Inicio"})

@router.get("/empresas", name="empresas")
def empresas(request: Request):
    return templates.TemplateResponse("empresas.html", {"request": request})

@router.get("/lista_empresas", name="lista_empresas")
def lista_empresas(request: Request):
    return templates.TemplateResponse("lista_empresas.html", {"request": request})

@router.get("/nueva_empresa", name="nueva_empresa")
def nueva_empresa(request: Request):
    return templates.TemplateResponse("nueva_empresa.html", {"request": request})
