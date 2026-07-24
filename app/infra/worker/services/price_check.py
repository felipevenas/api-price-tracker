import uuid
from datetime import datetime

from app.db.session import AsyncSessionLocal
from app.domain.product.repository import ProductRepository
from app.domain.worker.model import JobStatus
from app.infra.worker.runners.price_check import run_price_check
from app.infra.worker.utils.job_status import create_job, get_job_by_celery_id, update_status
from app.infra.logging.logger import logger


async def orchestrate_checks() -> int:
    """
    Busca produtos com intervalo expirado, registra jobs e despacha tarefas Celery individuais.
    Retorna o número de produtos despachados.
    """
    # Import tardio para evitar importação circular com Celery
    from app.infra.worker.tasks.price_check import check_product_price_task

    async with AsyncSessionLocal() as db:
        expired = await ProductRepository(db).get_expired_for_checking()

        if not expired:
            logger.info("Nenhum produto expirado no momento.")
            return 0

        logger.info(f"{len(expired)} produto(s) expirado(s). Despachando tarefas...")

        for product in expired:
            task = check_product_price_task.delay(str(product.id))
            await create_job(
                db,
                task_name="check_product_price_task",
                product_id=product.id,
                celery_task_id=task.id,
                payload={"product_id": str(product.id), "url": product.url},
            )

        await db.commit()
        return len(expired)


async def execute_price_check(product_id_str: str, celery_task_id: str) -> str:
    """
    Orquestra a execução da checagem de preço de um produto:
    1. Localiza o job pelo celery_task_id e marca como 'processing'
    2. Chama o runner (lógica pesada)
    3. Atualiza o job para 'completed' ou 'failed'
    """
    product_id = uuid.UUID(product_id_str)

    # Marca o job como 'processing'
    async with AsyncSessionLocal() as db:
        job = await get_job_by_celery_id(db, celery_task_id)
        if job:
            await update_status(db, job, JobStatus.processing, started_at=datetime.utcnow())
            await db.commit()

    # Executa o runner (abre sua própria sessão)
    result = await run_price_check(product_id)

    # Atualiza o status final do job
    async with AsyncSessionLocal() as db:
        job = await get_job_by_celery_id(db, celery_task_id)
        if job:
            final_status = JobStatus.failed if result.startswith("failed") else JobStatus.completed
            await update_status(
                db, job, final_status,
                result={"status": result},
                finished_at=datetime.utcnow(),
            )
            await db.commit()

    return result
