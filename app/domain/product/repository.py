import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.product.model import ProductMonitored


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, product_id: uuid.UUID) -> Optional[ProductMonitored]:
        result = await self.db.execute(
            select(ProductMonitored).where(ProductMonitored.id == product_id)
        )
        return result.scalars().first()

    async def get_by_user_and_id(self, user_id: uuid.UUID, product_id: uuid.UUID) -> Optional[ProductMonitored]:
        result = await self.db.execute(
            select(ProductMonitored).where(
                ProductMonitored.id == product_id,
                ProductMonitored.user_id == user_id
            )
        )
        return result.scalars().first()

    async def get_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ProductMonitored]:
        result = await self.db.execute(
            select(ProductMonitored)
            .where(ProductMonitored.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(ProductMonitored.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, product: ProductMonitored) -> ProductMonitored:
        self.db.add(product)
        await self.db.flush()
        return product

    async def save(self, product: ProductMonitored) -> ProductMonitored:
        self.db.add(product)
        return product

    async def delete(self, product: ProductMonitored) -> None:
        await self.db.delete(product)

    async def get_expired_for_checking(self) -> List[ProductMonitored]:
        """
        Retorna todos os produtos ativos cuja verificação de preço está vencida
        (last_checked_at + check_interval_minutes <= NOW() ou last_checked_at é nulo).
        """
        query = select(ProductMonitored).where(
            ProductMonitored.active == True,
            or_(
                ProductMonitored.last_checked_at == None,
                ProductMonitored.last_checked_at + text("INTERVAL '1 minute' * check_interval_minutes") <= func.now()
            )
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
