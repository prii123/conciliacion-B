from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

@router.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Inicio"})

@router.get("/guia", name="guia")
def guia(request: Request):
    return templates.TemplateResponse("guia.html", {"request": request})

@router.get("/index", name="index")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/error", name="error")
def error(request: Request):
    return templates.TemplateResponse("error.html", {"request": request})

@router.get("/success", name="success")
def success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})
