import asyncio
import uuid
from datetime import datetime
from typing import Optional
from celery import shared_task
from app.db.session import AsyncSessionLocal

# Importa todos os modelos de domínio para registrar os metadados ORM no worker do Celery
from app.domain.user.model import User
from app.domain.product.model import ProductMonitored
from app.domain.price_history.model import PriceHistory
from app.domain.audit_log.model import AuditLog

from app.domain.product.repository import ProductRepository
from app.domain.price_history.repository import PriceHistoryRepository
from app.domain.audit_log.repository import AuditLogRepository
from app.infra.scrapers.factory import ScraperFactory
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
            # Busca produtos com verificação vencida
            expired_products = await product_repo.get_expired_products_for_checking()
            
            if not expired_products:
                logger.info("Nenhum produto expirado necessitando de checagem no momento.")
                return 0
                
            logger.info(f"Identificados {len(expired_products)} produtos expirados. Despachando tarefas individuais.")
            
            for product in expired_products:
                # Envia tarefa individual para a fila de execução assíncrona
                check_product_price_task.delay(str(product.id))
                
            return len(expired_products)

    count = run_async(_orchestrate())
    return f"Orquestração finalizada. Despachados {count} jobs de raspagem."


@shared_task(bind=True, name="app.infra.queue.tasks.check_product_price_task", max_retries=3)
def check_product_price_task(self, product_id_str: str) -> str:
    """
    Tarefa individual (Celery Worker) que instancia o Selenium, acessa a URL
    do produto, extrai o preço atual e atualiza a base de dados.
    """
    # Define o ID da task Celery no contexto de logs para correlação cruzada
    token = task_id_ctx.set(self.request.id)
    
    logger.info(f"Iniciando tarefa de checagem de preço para o Produto ID: {product_id_str}")
    
    product_uuid = uuid.UUID(product_id_str)
    
    async def _check_price():
        async with AsyncSessionLocal() as db:
            product_repo = ProductRepository(db)
            audit_repo = AuditLogRepository(db)
            history_repo = PriceHistoryRepository(db)
            
            product = await product_repo.get_by_id(product_uuid)
            if not product:
                logger.error(f"Tarefa abortada. Produto ID {product_id_str} não encontrado no banco.")
                return "abort_not_found"
                
            if not product.active:
                logger.warning(f"Tarefa abortada. Produto ID {product_id_str} está inativo no momento.")
                return "abort_inactive"

            logger.info(f"Processando URL: {product.url}")
            
            try:
                # Instancia o scraper correto via Factory
                scraper = ScraperFactory.get_scraper(product.url)
                logger.info(f"Scraper instanciado com sucesso. Iniciando execução do Selenium...")
                
                # Executa o scraping (operação síncrona do Selenium WebDriver)
                # Rodamos em thread pool se quisermos ser puristas, mas como Celery Worker roda
                # em processos isolados, a execução direta é perfeitamente adequada.
                price = scraper.scrape(product.url)
                
                if price is not None and price > 0:
                    # Sucesso na checagem
                    logger.info(f"Preço extraído com sucesso: R$ {price:.2f}")
                    
                    old_price = product.current_price
                    product.current_price = price
                    product.last_checked_at = datetime.now()
                    await product_repo.save(product)
                    
                    # Cria histórico
                    history = PriceHistory(
                        product_id=product.id,
                        price=price,
                        status="success"
                    )
                    await history_repo.create(history)
                    
                    # Gera log de auditoria do sistema
                    audit = AuditLog(
                        user_id=product.user_id,
                        action="PRICE_CHECK_SUCCESS",
                        details={
                            "product_id": str(product.id),
                            "name": product.name,
                            "old_price": float(old_price) if old_price is not None else None,
                            "new_price": float(price),
                            "price_dropped": (price < old_price) if old_price is not None else False
                        }
                    )
                    await audit_repo.create(audit)
                    
                    await db.commit()
                    return f"success_price_{price:.2f}"
                else:
                    raise ValueError("Scraper retornou preço nulo ou zero.")
                    
            except Exception as e:
                # Registro detalhado da falha
                error_msg = str(e)
                logger.error(f"Falha ao checar preço do produto {product_id_str}: {error_msg}")
                
                # Cria histórico de falha
                history = PriceHistory(
                    product_id=product.id,
                    price=None,
                    status="failed",
                    error_message=error_msg[:450]  # Trunca para caber no banco
                )
                await history_repo.create(history)
                
                # Registra auditoria de falha
                audit = AuditLog(
                    user_id=product.user_id,
                    action="PRICE_CHECK_FAILED",
                    details={
                        "product_id": str(product.id),
                        "url": product.url,
                        "error": error_msg
                    }
                )
                await audit_repo.create(audit)
                
                await db.commit()
                return f"failed_{error_msg[:100]}"

    try:
        status_result = run_async(_check_price())
        return f"Tarefa concluída com status: {status_result}"
    finally:
        # Limpa o contexto de logs ao finalizar a tarefa do Celery
        task_id_ctx.reset(token)
