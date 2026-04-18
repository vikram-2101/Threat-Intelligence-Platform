import enum
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Enum, Numeric, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base

if TYPE_CHECKING:
    from .indicator import Indicator
    from .source import Source
    from .user import User

class EvidenceType(str, enum.Enum):
    WHOIS = "WHOIS"
    PASSIVE_DNS = "PASSIVE_DNS"
    ASN = "ASN"
    SSL_CERT = "SSL_CERT"
    CORRELATION_INFRA = "CORRELATION_INFRA"
    CORRELATION_SSL = "CORRELATION_SSL"
    MULTI_SOURCE_SIGHTING = "MULTI_SOURCE_SIGHTING"
    ANALYST_NOTE = "ANALYST_NOTE"
    ANALYST_ADJUSTMENT = "ANALYST_ADJUSTMENT"
    REVOCATION = "REVOCATION"
    INGESTION = "INGESTION"

class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    indicator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("indicators.id"), nullable=False
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("sources.id"), nullable=True
    )
    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, name="evidence_type"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    confidence_delta: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0.0, nullable=False
    )
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reversible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reversed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reversed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reversed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Relationships
    indicator: Mapped["Indicator"] = relationship(back_populates="evidence")
    source: Mapped[Optional["Source"]] = relationship(back_populates="evidence")
    reverser: Mapped[Optional["User"]] = relationship()
