import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.indicator import PaginatedMeta

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[uuid.UUID]
    details: Dict[str, Any]
    ip_address: Optional[str]
    is_active: bool
    timestamp: datetime

class PaginatedAuditLogResponse(BaseModel):
    data: List[AuditLogResponse]
    meta: PaginatedMeta
    errors: List[str] = []
