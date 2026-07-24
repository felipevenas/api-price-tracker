import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SAEnum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


class JobStatus(str, enum.Enum):
    enqueued   = "enqueued"
    processing = "processing"
    completed  = "completed"
    failed     = "failed"


class WorkerJob(Base):
    __tablename__ = "worker_job"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    task_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_monitored.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    celery_task_id: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status"),
        default=JobStatus.enqueued,
        nullable=False,
        index=True
    )
    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=True
    )
    result: Mapped[dict] = mapped_column(
        JSON,
        nullable=True
    )
    enqueued_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )
    finished_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )
