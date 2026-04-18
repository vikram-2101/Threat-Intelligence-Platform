import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from app.models.source import SourceCategory, TrustTier

class SourceBase(BaseModel):
    name: str = Field(..., max_length=255)
    category: SourceCategory
    trust_tier: TrustTier
    default_weight: float = Field(..., ge=0, le=1.0)
    intent_description: Optional[str] = None
    pull_url: Optional[str] = Field(None, max_length=2048) # HttpUrl is more strict, but string is safer for some legacy URLs
    pull_schedule: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

class SourceCreate(SourceBase):
    pass

class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    category: Optional[SourceCategory] = None
    trust_tier: Optional[TrustTier] = None
    default_weight: Optional[float] = Field(None, ge=0, le=1.0)
    intent_description: Optional[str] = None
    pull_url: Optional[str] = Field(None, max_length=2048)
    pull_schedule: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class SourceResponse(SourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
