import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


class ProductMonitored(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    url: Mapped[str] = mapped_column(
        String(1024),
        nullable=False
    )
    current_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    target_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    check_interval_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )
