import enum
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Enum, Numeric, DateTime, func, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

if TYPE_CHECKING:
    from .source import Source
    from .evidence import Evidence
    from .confidence_snapshot import ConfidenceSnapshot

class IndicatorType(str, enum.Enum):
    IPV4 = "IPV4"
    IPV6 = "IPV6"
    DOMAIN = "DOMAIN"
    URL = "URL"
    MD5 = "MD5"
    SHA1 = "SHA1"
    SHA256 = "SHA256"

class IndicatorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"

class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    type: Mapped[IndicatorType] = mapped_column(
        Enum(IndicatorType, name="indicator_type"), nullable=False
    )
    value: Mapped[str] = mapped_column(String(2048), nullable=False)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ttl: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[IndicatorStatus] = mapped_column(
        Enum(IndicatorStatus, name="indicator_status"),
        default=IndicatorStatus.ACTIVE,
        nullable=False,
    )
    current_confidence: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0.0, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("type", "value", name="uix_indicator_type_value"),
    )

    # Relationships
    sources: Mapped[list["IndicatorSource"]] = relationship(back_populates="indicator")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="indicator")
    snapshots: Mapped[list["ConfidenceSnapshot"]] = relationship(
        back_populates="indicator"
    )

class IndicatorSource(Base):
    __tablename__ = "indicator_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    indicator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("indicators.id"), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), nullable=False)
    first_reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("indicator_id", "source_id", name="uix_indicator_source"),
    )

    # Relationships
    indicator: Mapped["Indicator"] = relationship(back_populates="sources")
    source: Mapped["Source"] = relationship(back_populates="indicator_sources")
