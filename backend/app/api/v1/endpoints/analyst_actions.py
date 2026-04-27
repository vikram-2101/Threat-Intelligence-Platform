"""
Phase 3.2 — Analyst Action API Endpoints

Endpoints (all ANALYST or ADMIN only, per Agent.md §10):
  POST   /api/v1/indicators/{id}/notes       — add analyst note
  PATCH  /api/v1/indicators/{id}/confidence  — manual promote/demote
  PATCH  /api/v1/indicators/{id}/revoke      — revoke indicator
  PATCH  /api/v1/indicators/{id}/ttl         — adjust TTL

All actions:
  - Append-only evidence INSERT (never UPDATE/DELETE)
  - Write to AUDIT_LOGS with full details
  - Dispatch async Celery re-score (except TTL which only affects lifecycle)
"""

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_roles
from app.models.evidence import Evidence, EvidenceType
from app.models.indicator import Indicator, IndicatorStatus
from app.models.user import User, RoleName
from app.schemas.analyst import (
    NoteRequest, NoteResponse,
    ConfidenceAdjustRequest, ConfidenceAdjustResponse,
    RevokeRequest, RevokeResponse,
    TTLAdjustRequest, TTLAdjustResponse,
)
from app.services.audit_service import AuditService
from app.workers.celery_app import celery_app

router = APIRouter()

# ── Policy constants ───────────────────────────────────────────────────────────
# Maximum TTL extension an analyst may set from today (per policy — configurable)
MAX_TTL_DAYS_FROM_NOW = 365


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For from nginx."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _get_indicator_or_404(db: AsyncSession, indicator_id: uuid.UUID) -> Indicator:
    """Fetch indicator by PK or raise 404."""
    result = await db.execute(
        select(Indicator).where(Indicator.id == indicator_id)
    )
    indicator = result.scalar_one_or_none()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return indicator


def _dispatch_rescore(indicator_id: uuid.UUID, trigger: str) -> None:
    """Fire-and-forget: dispatch Celery scoring task."""
    celery_app.send_task(
        "app.workers.scoring_worker.recalculate_indicator_score",
        kwargs={"indicator_id": str(indicator_id), "trigger": trigger},
    )


# ── POST /{id}/notes ──────────────────────────────────────────────────────────

@router.post(
    "/{indicator_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add analyst note",
)
async def add_note(
    indicator_id: uuid.UUID,
    body: NoteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMIN, RoleName.ANALYST)),
):
    """
    Add a free-text analyst note to an indicator.

    - Inserts an ANALYST_NOTE evidence row with confidence_delta=0 (notes never
      change the score directly per Agent.md §11).
    - Triggers re-scoring so the rationale timestamp stays current.
    - Writes a full audit row.
    """
    indicator = await _get_indicator_or_404(db, indicator_id)

    evidence = Evidence(
        indicator_id=indicator.id,
        source_id=None,        # system-generated; no external source
        evidence_type=EvidenceType.ANALYST_NOTE,
        confidence_delta=0.0,  # notes never alter score directly
        raw_payload={
            "note": body.note,
            "author": current_user.username,
        },
        reversible=False,
    )
    db.add(evidence)

    await AuditService.log(
        db=db,
        action="analyst.note.added",
        entity_type="indicators",
        entity_id=indicator.id,
        details={
            "note_preview": body.note[:200],
            "author": current_user.username,
        },
        user_id=current_user.id,
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    await db.refresh(evidence)

    # Trigger re-score so rationale timestamp is updated (delta is 0 so score won't change)
    _dispatch_rescore(indicator.id, trigger="analyst.note")

    return NoteResponse(
        evidence_id=evidence.id,
        indicator_id=indicator.id,
        note=body.note,
        created_at=evidence.timestamp,
    )


# ── PATCH /{id}/confidence ────────────────────────────────────────────────────

@router.patch(
    "/{indicator_id}/confidence",
    response_model=ConfidenceAdjustResponse,
    summary="Manually promote or demote indicator confidence",
)
async def adjust_confidence(
    indicator_id: uuid.UUID,
    body: ConfidenceAdjustRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMIN, RoleName.ANALYST)),
):
    """
    Manually adjust the confidence score of an indicator.

    - `direction`: 'promote' adds delta; 'demote' subtracts it.
    - Inserts an ANALYST_ADJUSTMENT evidence row (delta is signed by direction).
    - delta is stored as-is; the scoring engine applies it in the weighted sum.
    - Triggers an immediate async re-score so the new score is reflected quickly.
    - Writes a full audit row with old/new score context.

    Per Agent.md §11: ANALYST_ADJUSTMENT delta comes from the analyst's input.
    No automated blocking is allowed — this is advisory only.
    """
    indicator = await _get_indicator_or_404(db, indicator_id)

    signed_delta = body.delta if body.direction == "promote" else -body.delta
    old_score = float(indicator.current_confidence)

    evidence = Evidence(
        indicator_id=indicator.id,
        source_id=None,
        evidence_type=EvidenceType.ANALYST_ADJUSTMENT,
        confidence_delta=signed_delta,
        raw_payload={
            "direction": body.direction,
            "magnitude": body.delta,
            "reason": body.reason,
            "author": current_user.username,
            "score_at_adjustment": old_score,
        },
        reversible=True,   # analyst adjustments can be reversed
    )
    db.add(evidence)

    await AuditService.log(
        db=db,
        action="analyst.confidence.adjusted",
        entity_type="indicators",
        entity_id=indicator.id,
        details={
            "direction": body.direction,
            "delta": signed_delta,
            "reason": body.reason,
            "old_score": old_score,
            "author": current_user.username,
        },
        user_id=current_user.id,
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    await db.refresh(evidence)

    # Dispatch async re-score to compute the new weighted total
    _dispatch_rescore(indicator.id, trigger="analyst.adjustment")

    # Compute an optimistic new score for the response (clamped, pre-decay snapshot)
    # The real score will be stored by the Celery worker shortly after.
    optimistic_new = max(0.0, min(100.0, old_score + signed_delta))

    return ConfidenceAdjustResponse(
        evidence_id=evidence.id,
        indicator_id=indicator.id,
        old_score=old_score,
        new_score=optimistic_new,
        delta_applied=signed_delta,
    )


# ── PATCH /{id}/revoke ────────────────────────────────────────────────────────

@router.patch(
    "/{indicator_id}/revoke",
    response_model=RevokeResponse,
    summary="Revoke an indicator",
)
async def revoke_indicator(
    indicator_id: uuid.UUID,
    body: RevokeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMIN, RoleName.ANALYST)),
):
    """
    Revoke an indicator permanently.

    - Sets `indicator.status = REVOKED`.
    - Inserts a REVOCATION evidence row with `confidence_delta = -50`
      (hardcoded per Agent.md §11 `EVIDENCE_CONFIDENCE_DELTAS`).
    - Triggers an async re-score — the -50 delta plus decay will typically
      drive the score towards 0 quickly.
    - Writes a full audit row.

    A REVOKED indicator remains queryable for historical analysis but must
    not be used for blocking decisions.
    """
    indicator = await _get_indicator_or_404(db, indicator_id)

    if indicator.status == IndicatorStatus.REVOKED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Indicator is already revoked",
        )

    old_score = float(indicator.current_confidence)

    # 1. Mark indicator revoked
    indicator.status = IndicatorStatus.REVOKED

    # 2. Append-only REVOCATION evidence (delta = -50 per spec)
    evidence = Evidence(
        indicator_id=indicator.id,
        source_id=None,
        evidence_type=EvidenceType.REVOCATION,
        confidence_delta=-50.0,
        raw_payload={
            "reason": body.reason,
            "revoked_by": current_user.username,
            "score_at_revocation": old_score,
        },
        reversible=False,  # revocations are not reversible
    )
    db.add(evidence)

    await AuditService.log(
        db=db,
        action="analyst.indicator.revoked",
        entity_type="indicators",
        entity_id=indicator.id,
        details={
            "reason": body.reason,
            "old_status": "ACTIVE",
            "old_score": old_score,
            "author": current_user.username,
        },
        user_id=current_user.id,
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    await db.refresh(evidence)
    await db.refresh(indicator)

    # Re-score: -50 delta will be picked up by the scoring engine
    _dispatch_rescore(indicator.id, trigger="analyst.revocation")

    return RevokeResponse(
        evidence_id=evidence.id,
        indicator_id=indicator.id,
        new_status=indicator.status.value,
        new_score=max(0.0, old_score - 50.0),  # optimistic pre-decay estimate
    )


# ── PATCH /{id}/ttl ───────────────────────────────────────────────────────────

@router.patch(
    "/{indicator_id}/ttl",
    response_model=TTLAdjustResponse,
    summary="Adjust indicator TTL",
)
async def adjust_ttl(
    indicator_id: uuid.UUID,
    body: TTLAdjustRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMIN, RoleName.ANALYST)),
):
    """
    Adjust the TTL (time-to-live / expiry date) of an indicator.

    Policy limits:
    - New TTL must be in the future.
    - New TTL may not be more than 365 days from now (prevent infinite TTLs).

    TTL changes do NOT directly alter the confidence score but they DO reset the
    auto-expiry lifecycle: if the new TTL is in the future, an indicator previously
    eligible for EXPIRED will remain ACTIVE until the next decay run.

    Reason field is optional but highly recommended for audit clarity.
    """
    indicator = await _get_indicator_or_404(db, indicator_id)

    now = datetime.now(timezone.utc)
    max_allowed_ttl = now + timedelta(days=MAX_TTL_DAYS_FROM_NOW)

    # Normalise timezone: body.new_ttl may arrive as naive UTC
    new_ttl = body.new_ttl
    if new_ttl.tzinfo is None:
        new_ttl = new_ttl.replace(tzinfo=timezone.utc)

    if new_ttl <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New TTL must be in the future",
        )

    if new_ttl > max_allowed_ttl:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"New TTL may not exceed {MAX_TTL_DAYS_FROM_NOW} days from today",
        )

    old_ttl = indicator.ttl
    indicator.ttl = new_ttl

    await AuditService.log(
        db=db,
        action="analyst.ttl.adjusted",
        entity_type="indicators",
        entity_id=indicator.id,
        details={
            "old_ttl": old_ttl.isoformat(),
            "new_ttl": new_ttl.isoformat(),
            "reason": body.reason or "no reason provided",
            "author": current_user.username,
        },
        user_id=current_user.id,
        ip_address=_get_client_ip(request),
    )

    await db.commit()

    return TTLAdjustResponse(
        indicator_id=indicator.id,
        old_ttl=old_ttl,
        new_ttl=new_ttl,
    )
