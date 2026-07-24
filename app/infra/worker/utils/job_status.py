import uuid
from datetime import datetime
from typing import Optional

from app.domain.worker.model import WorkerJob, JobStatus
from app.domain.worker.repository import WorkerJobRepository
from sqlalchemy.ext.asyncio import AsyncSession


async def create_job(
    db: AsyncSession,
    task_name: str,
    product_id: Optional[uuid.UUID] = None,
    celery_task_id: Optional[str] = None,
    payload: Optional[dict] = None,
) -> WorkerJob:
    """Registra um novo job com status 'enqueued'."""
    repo = WorkerJobRepository(db)
    job = WorkerJob(
        task_name=task_name,
        product_id=product_id,
        celery_task_id=celery_task_id,
        status=JobStatus.enqueued,
        payload=payload,
    )
    return await repo.create(job)


async def update_status(
    db: AsyncSession,
    job: WorkerJob,
    status: JobStatus,
    result: Optional[dict] = None,
    started_at: Optional[datetime] = None,
    finished_at: Optional[datetime] = None,
) -> WorkerJob:
    """Atualiza o status de um job existente."""
    return await WorkerJobRepository(db).update_status(
        job,
        status=status,
        result=result,
        started_at=started_at,
        finished_at=finished_at,
    )


async def get_job_by_celery_id(db: AsyncSession, celery_task_id: str) -> Optional[WorkerJob]:
    """Busca um job pelo Celery task ID."""
    return await WorkerJobRepository(db).get_by_celery_task_id(celery_task_id)
