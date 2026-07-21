import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# Esquema base com campos comuns
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=150)


# Schema recebido na criação de um usuário
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


# Schema recebido na atualização de um usuário
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=150)
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    is_active: Optional[bool] = None


# Schema de retorno de dados do usuário (Response)
class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
