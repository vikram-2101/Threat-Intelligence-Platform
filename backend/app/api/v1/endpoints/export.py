from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user, RoleChecker
from app.models.user import User, RoleName
from app.models.indicator import Indicator, IndicatorType
from app.models.audit_log import AuditLog
from app.schemas.indicator import IndicatorExportResponse
import csv
import io

router = APIRouter(dependencies=[Depends(RoleChecker([RoleName.ADMIN, RoleName.ANALYST, RoleName.API_CONSUMER]))])

@router.get("/")
async def export_indicators(
    format: str = Query("json", description="Export format: json or csv"),
    confidence_min: Optional[float] = None,
    type: Optional[IndicatorType] = None,
    status_param: Optional[str] = Query(None, alias="status"),
    approved: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Confidence Gating Rule
    if confidence_min is not None and confidence_min >= 70.0 and not approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Exports with confidence >= 70 require explicit approval (approved=true)."
        )

    # Build Query
    stmt = select(Indicator)
    if confidence_min is not None:
        stmt = stmt.where(Indicator.current_confidence >= confidence_min)
    if type:
        stmt = stmt.where(Indicator.type == type)
    if status_param:
        stmt = stmt.where(Indicator.status == status_param)

    result = await db.execute(stmt)
    indicators = result.scalars().all()

    # Log Audit Event
    audit_log = AuditLog(
        user_id=current_user.id,
        action="EXPORT_INDICATORS",
        entity_type="indicators",
        details={
            "format": format,
            "filters": {
                "confidence_min": confidence_min,
                "type": type.value if type else None,
                "status": status_param,
                "approved": approved
            },
            "exported_count": len(indicators)
        }
    )
    db.add(audit_log)
    await db.commit()

    # Format Data
    serialized = [IndicatorExportResponse.model_validate(ind) for ind in indicators]

    if format.lower() == "csv":
        stream = io.StringIO()
        if serialized:
            fieldnames = serialized[0].model_dump().keys()
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            for item in serialized:
                writer.writerow(item.model_dump())
        stream.seek(0)
        return StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=export.csv"}
        )

    return serialized
