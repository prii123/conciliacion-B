from pydantic import BaseModel, EmailStr
from typing import Optional

# ========== Schemas de Autenticación ==========
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ========== Schemas de Conciliación ==========
class ConciliacionSchema(BaseModel):
    id: int
    mes_conciliado: str
    año_conciliado: str
    cuenta_conciliada: str
    estado: str

    class Config:
        # orm_mode = True
        from_attributes = True