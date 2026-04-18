import enum
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Enum, Numeric, Boolean, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

if TYPE_CHECKING:
    from .indicator import IndicatorSource
    from .evidence import Evidence

class SourceCategory(str, enum.Enum):
    community = "community"
    research = "research"
    commercial = "commercial"
    internal = "internal"

class TrustTier(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[SourceCategory] = mapped_column(
        Enum(SourceCategory, name="source_category"), nullable=False
    )
    trust_tier: Mapped[TrustTier] = mapped_column(
        Enum(TrustTier, name="trust_tier"), nullable=False
    )
    default_weight: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    intent_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pull_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    pull_schedule: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_pull_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_pull_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    indicator_sources: Mapped[list["IndicatorSource"]] = relationship(
        back_populates="source"
    )
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="source")
