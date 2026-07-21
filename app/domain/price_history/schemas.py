import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PriceHistoryResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    price: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    checked_at: datetime

    class Config:
        from_attributes = True
