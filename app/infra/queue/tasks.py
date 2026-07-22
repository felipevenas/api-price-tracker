import asyncio
import uuid
from celery import shared_task
from app.db.session import AsyncSessionLocal

from app.domain.user.model import User
from app.domain.product.model import ProductMonitored
from app.domain.price_history.model import PriceHistory
from app.domain.audit_log.model import AuditLog

from app.domain.product.repository import ProductRepository
from app.domain.price_history.repository import PriceHistoryRepository
from app.domain.audit_log.repository import AuditLogRepository
from app.domain.product.usecase import CheckProductPriceUseCase
from app.infra.logging.logger import logger, task_id_ctx


def run_async(coro):
    """
    Helper para executar corotinas assíncronas em ambiente de execução síncrona do Celery.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@shared_task(name="app.infra.queue.tasks.orchestrate_price_checks")
def orchestrate_price_checks() -> str:
    """
    Tarefa periódica (Celery Beat) que identifica produtos vencidos de acordo
    com o check_interval_minutes e despacha tarefas individuais de checagem.
    """
    logger.info("Orquestrador Celery Beat iniciado. Buscando produtos para checagem periódica...")
    
    async def _orchestrate():
        async with AsyncSessionLocal() as db:
            product_repo = ProductRepository(db)
            expired_products = await product_repo.get_expired_for_checking()
            
            if not expired_products:
                logger.info("Nenhum produto expirado necessitando de checagem no momento.")
                return 0
                
            logger.info(f"Identificados {len(expired_products)} produtos expirados. Despachando tarefas individuais.")
            
            for product in expired_products:
                check_product_price_task.delay(str(product.id))
                
            return len(expired_products)

    count = run_async(_orchestrate())
    return f"Orquestração finalizada. Despachados {count} jobs de raspagem."


@shared_task(bind=True, name="app.infra.queue.tasks.check_product_price_task", max_retries=3)
def check_product_price_task(self, product_id_str: str) -> str:
    """
    Tarefa individual (Celery Worker) que chama o UseCase para scraping,
    atualização de preço, registro de histórico e auditoria.
    """
    token = task_id_ctx.set(self.request.id)
    
    logger.info(f"Iniciando tarefa de checagem de preço para o Produto ID: {product_id_str}")
    product_uuid = uuid.UUID(product_id_str)
    
    async def _check_price():
        async with AsyncSessionLocal() as db:
            product_repo = ProductRepository(db)
            audit_repo = AuditLogRepository(db)
            history_repo = PriceHistoryRepository(db)
            use_case = CheckProductPriceUseCase(product_repo, audit_repo, history_repo)
            
            status_res = await use_case.execute(product_uuid)
            await db.commit()
            return status_res

    try:
        status_result = run_async(_check_price())
        return f"Tarefa concluída com status: {status_result}"
    finally:
        task_id_ctx.reset(token)
