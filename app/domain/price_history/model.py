import uuid
from datetime import datetime
from sqlalchemy import Numeric, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


class PriceHistory(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_monitored.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20),  # ex: success, failed
        nullable=False
    )
    error_message: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
