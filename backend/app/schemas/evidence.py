import uuid
from datetime import datetime
from typing import List, Dict, Union, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.evidence import EvidenceType

class WeightRationale(BaseModel):
    source_name: str
    base_weight: float
    trust_multiplier: float
    final_weight: float

class EnrichmentBonus(BaseModel):
    service: str
    bonus: float
    reason: str

class Rationale(BaseModel):
    base_score: float = Field(..., description="Weighted average of all evidence deltas")
    weighted_evidence: List[WeightRationale]
    enrichment_bonuses: List[EnrichmentBonus]
    correlation_bonus: float
    decay_factor: float = Field(..., description="Exponential decay multiplier applied")
    final_score: float

class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    indicator_id: uuid.UUID
    source_id: Optional[uuid.UUID] = None
    evidence_type: EvidenceType
    timestamp: datetime
    confidence_delta: float
    raw_payload: dict
    reversible: bool
    reversed: bool
    reversed_at: Optional[datetime] = None
    reversed_by: Optional[uuid.UUID] = None
