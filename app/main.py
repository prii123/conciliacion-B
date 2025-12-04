from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import routes_auth, routes_conciliacion, routes_empresas
from pathlib import Path

from app.api import routes_conciliacion, routes_empresas, routes_informes
from app.web import router_conciliaciones, router_home
from app.web import router_empresas
from .database import Base, engine, SessionLocal
from .models import Empresa


# create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Conciliaciones Bancarias")

# Mount static directory
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API routers
app.include_router(routes_auth.router, prefix="/api/auth", tags=["autenticacion"])
app.include_router(routes_conciliacion.router, prefix="/api/conciliaciones", tags=["conciliaciones"])
app.include_router(routes_empresas.router, prefix="/api/empresas", tags=["empresas"])
app.include_router(routes_informes.router, prefix="/api/informes", tags=["Informes"])


# Registrar rutas WEB
app.include_router(router_home.router, include_in_schema=False)
app.include_router(router_empresas.router, prefix="/empresas",  include_in_schema=False)
app.include_router(router_conciliaciones.router, prefix="/conciliaciones",  include_in_schema=False)



