from pydantic import BaseModel
from typing import Optional

class EmpresaSchema(BaseModel):
    id: int
    nit: str
    razon_social: str
    nombre_comercial: Optional[str]
    ciudad: Optional[str]
    estado: str

    class Config:
        orm_mode = True

class ConciliacionSchema(BaseModel):
    id: int
    mes_conciliado: str
    año_conciliado: str
    cuenta_conciliada: str
    estado: str

    class Config:
        orm_mode = True
        from_attributes = True