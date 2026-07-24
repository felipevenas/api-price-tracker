from typing import Optional
from pydantic import BaseModel, Field


class MercadoLivreItemResponse(BaseModel):
    id: str = Field(..., description="ID do anúncio no Mercado Livre (ex: MLB3388701977)")
    title: str = Field(..., description="Título do produto")
    price: float = Field(..., gt=0, description="Preço principal atual do anúncio")
    original_price: Optional[float] = Field(None, description="Preço original (de/por) caso haja desconto")
    currency_id: str = Field("BRL", description="Código da moeda (ex: BRL)")
    permalink: Optional[str] = Field(None, description="URL pública do anúncio no Mercado Livre")
    thumbnail: Optional[str] = Field(None, description="URL da imagem em miniatura do produto")
    status: Optional[str] = Field(None, description="Status do anúncio (ex: active, paused)")


class MercadoLivrePriceResponse(BaseModel):
    item_id: str = Field(..., description="ID do anúncio no Mercado Livre")
    title: str = Field(..., description="Título do produto")
    price: float = Field(..., gt=0, description="Preço principal atual")
    original_price: Optional[float] = Field(None, description="Preço original antes do desconto")
    currency_id: str = Field("BRL", description="Código da moeda")
