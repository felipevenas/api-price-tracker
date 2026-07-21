import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.price_history.model import PriceHistory


class PriceHistoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, price_history: PriceHistory) -> PriceHistory:
        self.db.add(price_history)
        await self.db.flush()
        return price_history

    async def get_by_product(
        self, product_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[PriceHistory]:
        result = await self.db.execute(
            select(PriceHistory)
            .where(PriceHistory.product_id == product_id)
            .offset(skip)
            .limit(limit)
            .order_by(PriceHistory.checked_at.desc())
        )
        return list(result.scalars().all())
