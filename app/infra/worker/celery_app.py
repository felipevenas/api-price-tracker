from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "price_monitor_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.infra.worker.tasks.price_check"]
)

celery_app.config_from_object("app.infra.worker.core.celery_config")

if __name__ == "__main__":
    celery_app.start()
