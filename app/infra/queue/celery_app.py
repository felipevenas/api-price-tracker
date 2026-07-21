from celery import Celery
from app.core.config import settings

# Cria e configura a aplicação Celery
celery_app = Celery(
    "price_monitor_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.infra.queue.tasks"]  # Módulos onde as tasks estão declaradas
)

# Carrega configurações adicionais
celery_app.config_from_object("app.infra.queue.celery_config")

if __name__ == "__main__":
    celery_app.start()
