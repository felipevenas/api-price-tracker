import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.worker.model import WorkerJob, JobStatus


class WorkerJobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, job: WorkerJob) -> WorkerJob:
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> Optional[WorkerJob]:
        result = await self.db.execute(
            select(WorkerJob).where(WorkerJob.id == job_id)
        )
        return result.scalars().first()

    async def get_by_celery_task_id(self, celery_task_id: str) -> Optional[WorkerJob]:
        result = await self.db.execute(
            select(WorkerJob).where(WorkerJob.celery_task_id == celery_task_id)
        )
        return result.scalars().first()

    async def get_by_product(
        self,
        product_id: uuid.UUID,
        limit: int = 50
    ) -> List[WorkerJob]:
        result = await self.db.execute(
            select(WorkerJob)
            .where(WorkerJob.product_id == product_id)
            .order_by(WorkerJob.enqueued_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[WorkerJob]:
        query = select(WorkerJob).order_by(WorkerJob.enqueued_at.desc()).limit(limit)
        if status:
            query = query.where(WorkerJob.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        job: WorkerJob,
        status: JobStatus,
        result: Optional[dict] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
    ) -> WorkerJob:
        job.status = status
        if result is not None:
            job.result = result
        if started_at is not None:
            job.started_at = started_at
        if finished_at is not None:
            job.finished_at = finished_at
        self.db.add(job)
        return job
