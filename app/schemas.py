from pydantic import BaseModel
from typing import Optional

class ConciliacionSchema(BaseModel):
    id: int
    mes_conciliado: str
    año_conciliado: str
    cuenta_conciliada: str
    estado: str

    class Config:
        # orm_mode = True
        from_attributes = True