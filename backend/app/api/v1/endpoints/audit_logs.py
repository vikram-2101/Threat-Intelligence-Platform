from typing import Optional
from datetime import datetime
import math
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.api.deps import get_db, RoleChecker
from app.models.user import RoleName
from app.models.audit_log import AuditLog
from app.schemas.audit_log import PaginatedAuditLogResponse, PaginatedMeta, AuditLogResponse

router = APIRouter(dependencies=[Depends(RoleChecker([RoleName.ADMIN]))])

@router.get("/", response_model=PaginatedAuditLogResponse)
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Exact or partial match for action type"),
    entity_type: Optional[str] = Query(None, description="Exact or partial match for entity type (e.g. indicators)"),
    date_start: Optional[datetime] = Query(None, description="Start boundary limit"),
    date_end: Optional[datetime] = Query(None, description="Ending boundary limit"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    conditions = []
    
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if action:
        conditions.append(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        conditions.append(AuditLog.entity_type.ilike(f"%{entity_type}%"))
    if date_start:
        conditions.append(AuditLog.timestamp >= date_start)
    if date_end:
        conditions.append(AuditLog.timestamp <= date_end)
        
    where_clause = and_(*conditions) if conditions else True
    
    count_q = await db.execute(select(func.count()).select_from(AuditLog).where(where_clause))
    total = count_q.scalar_one()
    
    offset = (page - 1) * limit
    logs_q = await db.execute(
        select(AuditLog)
        .where(where_clause)
        .order_by(AuditLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    
    logs = logs_q.scalars().all()
    
    pages = math.ceil(total / limit) if total > 0 else 1
    
    return PaginatedAuditLogResponse(
        data=[AuditLogResponse.model_validate(log) for log in logs],
        meta=PaginatedMeta(total=total, page=page, limit=limit, pages=pages),
        errors=[]
    )
