import re
import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo
from app.models.indicator import IndicatorType, IndicatorStatus


# ── Validation / Ingestion helpers ────────────────────────────────────────────

class ValidationItem(BaseModel):
    raw: str
    type: IndicatorType
    normalized: Optional[str] = None
    is_valid: bool = False
    error: Optional[str] = None


class ValidationBatchResult(BaseModel):
    valid: List[ValidationItem]
    invalid: List[ValidationItem]


class IndicatorBase(BaseModel):
    type: IndicatorType
    value: str = Field(..., max_length=2048)

    @field_validator("value")
    @classmethod
    def validate_indicator_value(cls, v: str, info: ValidationInfo) -> str:
        itype = info.data.get("type")
        if not itype:
            return v

        rules = {
            IndicatorType.MD5:    (32, r"^[a-fA-F0-9]{32}$"),
            IndicatorType.SHA1:   (40, r"^[a-fA-F0-9]{40}$"),
            IndicatorType.SHA256: (64, r"^[a-fA-F0-9]{64}$"),
        }

        if itype in rules:
            length, pattern = rules[itype]
            if not re.fullmatch(pattern, v):
                raise ValueError(f"{itype} must be {length} hex characters")
            return v.lower()

        if itype == IndicatorType.DOMAIN:
            return v.lower()

        return v


class IndicatorCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_id: uuid.UUID
    indicators: List[IndicatorBase]


class IndicatorUpdate(BaseModel):
    status: Optional[IndicatorStatus] = None
    current_confidence: Optional[float] = Field(None, ge=0, le=100)
    ttl: Optional[datetime] = None


# ── Evidence schema ────────────────────────────────────────────────────────────

class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    evidence_type: str
    timestamp: datetime
    confidence_delta: float
    raw_payload: dict
    reversible: bool
    reversed: bool
    reversed_at: Optional[datetime] = None


# ── Confidence snapshot schema ─────────────────────────────────────────────────

class ConfidenceSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    score: float
    reason_summary: dict
    calculated_at: datetime
    trigger: str


# ── Lean list-item schema (no nested arrays — fast for large pages) ────────────

class IndicatorListItem(BaseModel):
    """Lean schema for the paginated list view."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: IndicatorType
    value: str
    status: IndicatorStatus
    current_confidence: float
    first_seen: datetime
    last_seen: datetime
    ttl: datetime
    # Latest rationale surfaced at top-level so the UI can show "why" without a
    # second round-trip. Null when indicator has never been scored.
    latest_rationale: Optional[dict] = None
    # Source names this indicator has been sighted from
    source_names: List[str] = []


# ── Full detail schema ─────────────────────────────────────────────────────────

class IndicatorResponse(IndicatorBase):
    """Full detail: indicator + all evidence + full confidence history."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    first_seen: datetime
    last_seen: datetime
    ttl: datetime
    status: IndicatorStatus
    current_confidence: float
    evidence: List[EvidenceResponse] = []
    confidence_history: List[ConfidenceSnapshotResponse] = []
    # Latest rationale surfaced at top-level for the UI "why" panel
    latest_rationale: Optional[dict] = None
    source_names: List[str] = []


# ── Paginated list response — Agent.md §9 envelope ────────────────────────────

class PaginatedMeta(BaseModel):
    total: int
    page: int
    limit: int
    pages: int


class PaginatedIndicatorResponse(BaseModel):
    """Standard paginated response envelope per Agent.md §9."""
    data: List[IndicatorListItem]
    meta: PaginatedMeta
    errors: List[str] = []


# ── Correlation schemas ────────────────────────────────────────────────────────

class CorrelationDetail(BaseModel):
    """A single correlation evidence row for this indicator."""
    evidence_id: uuid.UUID
    correlation_type: str   # CORRELATION_INFRA | CORRELATION_SSL | MULTI_SOURCE_SIGHTING
    confidence_delta: float
    raw_payload: dict
    timestamp: datetime
    reversed: bool


class CorrelationResponse(BaseModel):
    """Response for GET /indicators/{id}/correlations."""
    indicator_id: uuid.UUID
    correlations: List[CorrelationDetail]
    total: int


# ── Ingestion response ─────────────────────────────────────────────────────────

class IngestionResponse(BaseModel):
    ingested: int
    duplicates: int
    errors: int
    error_details: List[ValidationItem]
    indicators: List[IndicatorResponse]


# ── Export schemas ─────────────────────────────────────────────────────────────

class IndicatorExportResponse(BaseModel):
    """Flat schema ensuring clean serialization to CSV and JSON."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: IndicatorType
    value: str
    status: IndicatorStatus
    current_confidence: float
    first_seen: datetime
    last_seen: datetime
