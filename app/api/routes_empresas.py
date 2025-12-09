from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List, Dict, Any
from app.utils.auth import get_current_active_user
from ..database import get_db
from ..models import Empresa, Conciliacion, User
from ..schemas import ConciliacionSchema
from .schemas.empresa_schemas import EmpresaCreate, EmpresaSchema
from ..repositories.factory import RepositoryFactory

router = APIRouter()

@router.get("/", name="lista_empresas")
def lista_empresas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    factory = RepositoryFactory(db)
    empresa_repo = factory.get_empresa_repository()
    empresas = empresa_repo.get_all(order_by='id', desc_order=True)
    return JSONResponse(content={"empresas": [EmpresaSchema.from_orm(e).dict() for e in empresas]})

@router.post("/nueva", name="nueva_empresa_post")
def nueva_empresa_post(
    empresa: EmpresaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    print(empresa)
    factory = RepositoryFactory(db)
    empresa_repo = factory.get_empresa_repository()
    
    existing = empresa_repo.get_by_nit(empresa.nit)
    if existing:
        raise HTTPException(status_code=400, detail=f"Ya existe una empresa con NIT {empresa.nit}")

    empresa_data = {
        "nit": empresa.nit,
        "razon_social": empresa.razon_social,
        "nombre_comercial": empresa.nombre_comercial,
        "ciudad": empresa.ciudad
    }
    nueva_empresa = empresa_repo.create(empresa_data)
    return JSONResponse(content={"message": "Empresa creada exitosamente", "empresa": EmpresaSchema.from_orm(nueva_empresa).dict()})

@router.get("/{empresa_id}/conciliaciones", name="conciliaciones_empresas")
def conciliaciones_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    factory = RepositoryFactory(db)
    empresa_repo = factory.get_empresa_repository()
    conciliacion_repo = factory.get_conciliacion_repository()
    
    empresa = empresa_repo.get_by_id(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    conciliaciones = conciliacion_repo.get_by_empresa(empresa_id)
    en_proceso = [ConciliacionSchema.from_orm(c).dict() for c in conciliaciones if c.estado == 'en_proceso']
    finalizadas = [ConciliacionSchema.from_orm(c).dict() for c in conciliaciones if c.estado == 'finalizada']
    print("Conciliaciones fetched:", len(en_proceso), "en proceso,", len(finalizadas), "finalizadas")
    return JSONResponse(content={
        "empresa": EmpresaSchema.from_orm(empresa).dict(),
        "conciliaciones": {
            "en_proceso": en_proceso,
            "finalizadas": finalizadas
        }
    })