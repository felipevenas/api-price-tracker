from celery import shared_task

from app.infra.worker.services.price_check import orchestrate_checks, execute_price_check
from app.infra.worker.utils.async_runner import run_async
from app.infra.logging.logger import task_id_ctx


@shared_task(name="app.infra.worker.tasks.price_check.orchestrate_price_checks")
def orchestrate_price_checks() -> str:
    """Beat periódico: despacha checagens individuais para produtos com intervalo expirado."""
    count = run_async(orchestrate_checks())
    return f"Orquestração finalizada. Despachados {count} jobs."


@shared_task(
    bind=True,
    name="app.infra.worker.tasks.price_check.check_product_price_task",
    max_retries=3,
)
def check_product_price_task(self, product_id_str: str) -> str:
    """Worker individual: executa a checagem de preço de um produto."""
    token = task_id_ctx.set(self.request.id)
    try:
        result = run_async(execute_price_check(product_id_str, self.request.id))
        return f"Concluído: {result}"
    finally:
        task_id_ctx.reset(token)
