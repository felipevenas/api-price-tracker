import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.helpers.url_parser import is_valid_url


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Nome identificador do produto")
    url: str = Field(..., max_length=1024, description="URL do produto no e-commerce")
    target_price: Optional[float] = Field(None, gt=0, description="Preço alvo para alerta de queda")
    check_interval_minutes: int = Field(60, ge=1, le=1440, description="Intervalo de checagem do preço em minutos")

    @field_validator("url")
    @classmethod
    def validate_product_url(cls, v: str) -> str:
        if not is_valid_url(v):
            raise ValueError("A URL informada não é válida ou não possui protocolo HTTP/HTTPS.")
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    target_price: Optional[float] = Field(None, gt=0)
    check_interval_minutes: Optional[int] = Field(None, ge=1, le=1440)
    active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: uuid.UUID
    user_id: uuid.UUID
    current_price: Optional[float] = None
    active: bool
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
        # Converte tipos complexos (Numeric do SQLAlchemy) para float
        json_encoders = {
            float: lambda v: float(v) if v is not None else None
        }
