import uuid
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel
from app.domain.worker.model import JobStatus


class WorkerJobResponse(BaseModel):
    id: uuid.UUID
    task_name: str
    product_id: Optional[uuid.UUID]
    celery_task_id: Optional[str]
    status: JobStatus
    payload: Optional[Any]
    result: Optional[Any]
    enqueued_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True
