import re
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo
from app.models.indicator import IndicatorType, IndicatorStatus

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
        
        # Hash rules as defined in implementation requirements
        rules = {
            IndicatorType.MD5:    (32,  r"^[a-fA-F0-9]{32}$"),
            IndicatorType.SHA1:   (40,  r"^[a-fA-F0-9]{40}$"),
            IndicatorType.SHA256: (64,  r"^[a-fA-F0-9]{64}$"),
        }
        
        if itype in rules:
            length, pattern = rules[itype]
            if not re.fullmatch(pattern, v):
                raise ValueError(f"{itype} must be {length} hex characters")
            return v.lower()
        
        # Domain normalization
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

class IndicatorResponse(IndicatorBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    first_seen: datetime
    last_seen: datetime
    ttl: datetime
    status: IndicatorStatus
    current_confidence: float

class IngestionResponse(BaseModel):
    ingested: int
    duplicates: int
    errors: int
    error_details: List[ValidationItem]
    indicators: List[IndicatorResponse]
