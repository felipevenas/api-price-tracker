import uuid

from app.db.session import AsyncSessionLocal
from app.domain.product.repository import ProductRepository
from app.domain.price_history.repository import PriceHistoryRepository
from app.domain.audit_log.repository import AuditLogRepository
from app.domain.product.usecase import CheckProductPriceUseCase
from app.infra.logging.logger import logger


async def run_price_check(product_id: uuid.UUID) -> str:
    """
    Execução pesada da checagem de preço.
    Abre sua própria sessão de banco, executa o use case e retorna o status.
    """
    async with AsyncSessionLocal() as db:
        use_case = CheckProductPriceUseCase(
            product_repo=ProductRepository(db),
            audit_repo=AuditLogRepository(db),
            history_repo=PriceHistoryRepository(db),
        )
        result = await use_case.execute(product_id)
        await db.commit()
        logger.info(f"Runner finalizado para produto {product_id}: {result}")
        return result
