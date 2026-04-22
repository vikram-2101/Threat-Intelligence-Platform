"""
Phase 3.2 — Analyst action request/response schemas.
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NoteRequest(BaseModel):
    """POST /indicators/{id}/notes"""
    note: str = Field(..., min_length=1, max_length=5000, description="Analyst note text")


class NoteResponse(BaseModel):
    """Confirmation that the note was stored."""
    evidence_id: uuid.UUID
    indicator_id: uuid.UUID
    note: str
    created_at: datetime
    message: str = "Analyst note added"


class ConfidenceAdjustRequest(BaseModel):
    """PATCH /indicators/{id}/confidence"""
    direction: str = Field(..., pattern="^(promote|demote)$",
                           description="'promote' to increase, 'demote' to decrease")
    delta: float = Field(..., gt=0, le=50,
                         description="Score adjustment magnitude (1–50 points)")
    reason: str = Field(..., min_length=1, max_length=1000,
                        description="Mandatory justification for the adjustment")


class ConfidenceAdjustResponse(BaseModel):
    evidence_id: uuid.UUID
    indicator_id: uuid.UUID
    old_score: float
    new_score: float
    delta_applied: float
    message: str = "Confidence adjusted"


class RevokeRequest(BaseModel):
    """PATCH /indicators/{id}/revoke"""
    reason: str = Field(..., min_length=1, max_length=1000,
                        description="Mandatory reason for revoking this indicator")


class RevokeResponse(BaseModel):
    evidence_id: uuid.UUID
    indicator_id: uuid.UUID
    new_status: str
    new_score: float
    message: str = "Indicator revoked"


class TTLAdjustRequest(BaseModel):
    """PATCH /indicators/{id}/ttl"""
    new_ttl: datetime = Field(..., description="New expiry timestamp (ISO 8601 UTC)")
    reason: Optional[str] = Field(None, max_length=500,
                                  description="Optional justification for the TTL change")


class TTLAdjustResponse(BaseModel):
    indicator_id: uuid.UUID
    old_ttl: datetime
    new_ttl: datetime
    message: str = "TTL updated"
