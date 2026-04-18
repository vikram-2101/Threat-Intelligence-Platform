import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Numeric, DateTime, func, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base

if TYPE_CHECKING:
    from .indicator import Indicator

class ConfidenceSnapshot(Base):
    __tablename__ = "confidence_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    indicator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("indicators.id"), nullable=False
    )
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reason_summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    trigger: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    indicator: Mapped["Indicator"] = relationship(back_populates="snapshots")
