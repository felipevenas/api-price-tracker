import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, or_, func, text, not_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.product.model import ProductMonitored
from app.domain.worker.model import WorkerJob, JobStatus


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
        Retorna APENAS os produtos ativos cujo intervalo de checagem INDIVIDUAL
        expirou com base no seu próprio check_interval_minutes e que não possuem
        nenhuma tarefa de checagem ativa (enqueued ou processing) recente na fila.

        Cada produto é avaliado individualmente pela fórmula:
          last_checked_at + (check_interval_minutes * interval '1 minute') <= NOW() UTC

        A comparação de tempo é normalizada em UTC naive com func.timezone('utc', func.now())
        para evitar problemas decorrentes de diferenças de fusos horários.
        Tarefas são consideradas ativas apenas se criadas nos últimos 10 minutos
        para evitar que jobs órfãos/presos de execuções passadas bloqueiem as checagens.
        """
        interval_per_product = (
            ProductMonitored.check_interval_minutes * text("interval '1 minute'")
        )

        utc_now = func.timezone('utc', func.now())

        # Define limite de tempo para considerar um job ativo como órfão (ex: 10 minutos)
        stale_threshold = utc_now - text("interval '10 minutes'")

        # Verifica se existe algum job recente ativo para o produto
        active_jobs_exists = exists().where(
            WorkerJob.product_id == ProductMonitored.id,
            WorkerJob.status.in_([JobStatus.enqueued, JobStatus.processing]),
            WorkerJob.enqueued_at >= stale_threshold
        )

        query = select(ProductMonitored).where(
            ProductMonitored.active == True,
            not_(active_jobs_exists),
            or_(
                ProductMonitored.last_checked_at == None,
                ProductMonitored.last_checked_at + interval_per_product <= utc_now
            )
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())
