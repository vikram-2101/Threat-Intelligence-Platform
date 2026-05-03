"""
Phase 3.1 — Indicator Query & Ingestion API

Endpoints:
  POST   /api/v1/indicators/           — ingest (existing)
  GET    /api/v1/indicators/           — paginated list with full filter suite
  GET    /api/v1/indicators/{id}       — full detail (evidence + snapshots + rationale)
  GET    /api/v1/indicators/{id}/correlations — correlation evidence for this indicator
"""

import uuid
from typing import Optional, List
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, UploadFile
from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.models.indicator import Indicator, IndicatorSource, IndicatorType, IndicatorStatus
from app.models.evidence import Evidence, EvidenceType
from app.models.source import Source
from app.models.confidence_snapshot import ConfidenceSnapshot
from app.models.user import User
from app.schemas.indicator import (
    IngestionResponse,
    IndicatorResponse,
    IndicatorListItem,
    PaginatedIndicatorResponse,
    PaginatedMeta,
    CorrelationDetail,
    CorrelationResponse,
    EvidenceResponse,
    ConfidenceSnapshotResponse,
)
from app.services.ingestion_service import IngestionService
from app.services.parser import IndicatorParser

router = APIRouter(dependencies=[Depends(get_current_user)])

# ── CORRELATION EVIDENCE TYPES ─────────────────────────────────────────────────
CORRELATION_TYPES = {
    EvidenceType.CORRELATION_INFRA,
    EvidenceType.CORRELATION_SSL,
    EvidenceType.MULTI_SOURCE_SIGHTING,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_type_to_enum(t_str: str) -> IndicatorType | str:
    """Safely converts a string to IndicatorType enum, or returns raw string if unknown."""
    if not t_str:
        return t_str
    norm = t_str.strip().upper()
    try:
        return IndicatorType(norm)
    except ValueError:
        for member in IndicatorType:
            if member.name == norm:
                return member
        return norm


async def _fetch_source_names(db: AsyncSession, indicator_id: uuid.UUID) -> List[str]:
    """Fetch all source names linked to an indicator via indicator_sources."""
    result = await db.execute(
        select(Source.name)
        .join(IndicatorSource, IndicatorSource.source_id == Source.id)
        .where(IndicatorSource.indicator_id == indicator_id)
        .order_by(Source.name)
    )
    return [r for r in result.scalars().all()]


async def _fetch_latest_rationale(db: AsyncSession, indicator_id: uuid.UUID) -> Optional[dict]:
    """Return the reason_summary from the most recent confidence snapshot."""
    result = await db.execute(
        select(ConfidenceSnapshot.reason_summary)
        .where(ConfidenceSnapshot.indicator_id == indicator_id)
        .order_by(ConfidenceSnapshot.calculated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ── GET /  (paginated list with filters) ─────────────────────────────────────

@router.get("", response_model=PaginatedIndicatorResponse)
async def list_indicators(
    db: AsyncSession = Depends(get_db),
    # ── Filters ──
    type: Optional[IndicatorType] = Query(None, description="Filter by indicator type (IPV4, DOMAIN, etc.)"),
    confidence_min: Optional[float] = Query(None, ge=0, le=100, description="Minimum confidence score"),
    confidence_max: Optional[float] = Query(None, ge=0, le=100, description="Maximum confidence score"),
    status: Optional[IndicatorStatus] = Query(None, description="Filter by status (ACTIVE, EXPIRED, REVOKED)"),
    source: Optional[str] = Query(None, description="Filter by source name (partial match, case-insensitive)"),
    value: Optional[str] = Query(None, description="Filter by indicator value substring"),
    # ── Pagination ──
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=200, description="Results per page (max 200)"),
):
    """
    Paginated indicator list with compound filtering.

    All filters are additive (AND). Returns lean IndicatorListItem objects that
    include the latest rationale summary so the UI can show the 'why' without
    a second request.

    Sort order: confidence DESC (highest-risk indicators first).
    """
    # ── Build base query ──────────────────────────────────────────────────────
    conditions = []

    if type is not None:
        conditions.append(Indicator.type == type)

    if status is not None:
        conditions.append(Indicator.status == status)

    if confidence_min is not None:
        conditions.append(Indicator.current_confidence >= confidence_min)

    if confidence_max is not None:
        conditions.append(Indicator.current_confidence <= confidence_max)

    if value is not None:
        conditions.append(Indicator.value.ilike(f"%{value}%"))

    # Source filter requires a join through indicator_sources → sources
    if source is not None:
        source_subq = (
            select(IndicatorSource.indicator_id)
            .join(Source, Source.id == IndicatorSource.source_id)
            .where(Source.name.ilike(f"%{source}%"))
            .scalar_subquery()
        )
        conditions.append(Indicator.id.in_(source_subq))

    where_clause = and_(*conditions) if conditions else True

    # ── Count total matching rows ─────────────────────────────────────────────
    count_q = await db.execute(
        select(func.count()).select_from(Indicator).where(where_clause)
    )
    total = count_q.scalar_one()

    # ── Fetch page ───────────────────────────────────────────────────────────
    offset = (page - 1) * limit
    rows_q = await db.execute(
        select(Indicator)
        .where(where_clause)
        .order_by(Indicator.current_confidence.desc(), Indicator.last_seen.desc())
        .offset(offset)
        .limit(limit)
    )
    indicators = rows_q.scalars().all()

    # Optimized batch queries
    indicator_ids = [ind.id for ind in indicators]
    sources_by_ind = {}
    rationale_by_ind = {}

    if indicator_ids:
        # Fetch source names
        sources_q = await db.execute(
            select(IndicatorSource.indicator_id, Source.name)
            .join(Source, Source.id == IndicatorSource.source_id)
            .where(IndicatorSource.indicator_id.in_(indicator_ids))
        )
        for ind_id, src_name in sources_q.all():
            sources_by_ind.setdefault(ind_id, []).append(src_name)

        # Fetch latest rationales
        snapshots_q = await db.execute(
            select(ConfidenceSnapshot)
            .where(ConfidenceSnapshot.indicator_id.in_(indicator_ids))
            .order_by(ConfidenceSnapshot.calculated_at.desc())
        )
        for snap in snapshots_q.scalars().all():
            if snap.indicator_id not in rationale_by_ind:
                rationale_by_ind[snap.indicator_id] = snap.reason_summary

    # ── Build response items (N+1 optimized) ───────────────────
    items: List[IndicatorListItem] = []
    for ind in indicators:
        source_names = sources_by_ind.get(ind.id, [])
        latest_rationale = rationale_by_ind.get(ind.id)

        items.append(IndicatorListItem(
            id=ind.id,
            type=ind.type,
            value=ind.value,
            status=ind.status,
            current_confidence=float(ind.current_confidence),
            first_seen=ind.first_seen,
            last_seen=ind.last_seen,
            ttl=ind.ttl,
            latest_rationale=latest_rationale,
            source_names=source_names,
        ))

    pages = math.ceil(total / limit) if total > 0 else 1

    return PaginatedIndicatorResponse(
        data=items,

        meta=PaginatedMeta(total=total, page=page, limit=limit, pages=pages),
        errors=[],
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_indicators(
    db: AsyncSession = Depends(get_db),
):
    """
    Delete all indicators. This also deletes all linked evidence, snapshots, and sources.
    """
    from app.models.indicator import Indicator, IndicatorSource
    from app.models.evidence import Evidence
    from app.models.confidence_snapshot import ConfidenceSnapshot

    await db.execute(delete(IndicatorSource))
    await db.execute(delete(Evidence))
    await db.execute(delete(ConfidenceSnapshot))
    await db.execute(delete(Indicator))
    await db.commit()
    return


@router.delete("/{indicator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_indicator(
    indicator_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a specific indicator.
    """
    from app.models.indicator import Indicator, IndicatorSource
    from app.models.evidence import Evidence
    from app.models.confidence_snapshot import ConfidenceSnapshot

    await db.execute(delete(IndicatorSource).where(IndicatorSource.indicator_id == indicator_id))
    await db.execute(delete(Evidence).where(Evidence.indicator_id == indicator_id))
    await db.execute(delete(ConfidenceSnapshot).where(ConfidenceSnapshot.indicator_id == indicator_id))
    await db.execute(delete(Indicator).where(Indicator.id == indicator_id))
    await db.commit()
    return



# ── GET /{id}  (full detail) ───────────────────────────────────────────────────

@router.get("/{indicator_id}", response_model=IndicatorResponse)

async def get_indicator(
    indicator_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Full indicator detail.

    Returns:
    - All evidence records (enrichment + correlation + analyst actions), ordered newest-first.
    - Full confidence snapshot history (timeline data for Recharts), newest-first.
    - latest_rationale: the reason_summary from the most recent snapshot, surfaced at the
      top level so the analyst UI 'why' panel needs no extra query.
    - source_names: all feeds that have reported this indicator.
    """
    result = await db.execute(
        select(Indicator)
        .where(Indicator.id == indicator_id)
        .options(
            selectinload(Indicator.evidence),
            selectinload(Indicator.snapshots),
        )
    )
    indicator = result.scalar_one_or_none()

    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")

    # Sort evidence and snapshots newest-first (ORM loads are unordered)
    sorted_evidence = sorted(indicator.evidence, key=lambda e: e.timestamp, reverse=True)
    sorted_snapshots = sorted(indicator.snapshots, key=lambda s: s.calculated_at, reverse=True)

    # Surface latest rationale at top level
    latest_rationale: Optional[dict] = None
    if sorted_snapshots:
        latest_rationale = sorted_snapshots[0].reason_summary

    source_names = await _fetch_source_names(db, indicator.id)

    return IndicatorResponse(
        id=indicator.id,
        type=indicator.type,
        value=indicator.value,
        status=indicator.status,
        current_confidence=float(indicator.current_confidence),
        first_seen=indicator.first_seen,
        last_seen=indicator.last_seen,
        ttl=indicator.ttl,
        evidence=[
            EvidenceResponse(
                id=ev.id,
                evidence_type=ev.evidence_type,
                timestamp=ev.timestamp,
                confidence_delta=float(ev.confidence_delta),
                raw_payload=ev.raw_payload,
                reversible=ev.reversible,
                reversed=ev.reversed,
                reversed_at=ev.reversed_at,
            )
            for ev in sorted_evidence
        ],
        confidence_history=[
            ConfidenceSnapshotResponse(
                id=snap.id,
                score=float(snap.score),
                reason_summary=snap.reason_summary,
                calculated_at=snap.calculated_at,
                trigger=snap.trigger,
            )
            for snap in sorted_snapshots
        ],
        latest_rationale=latest_rationale,
        source_names=source_names,
    )


# ── GET /{id}/correlations ────────────────────────────────────────────────────

@router.get("/{indicator_id}/correlations", response_model=CorrelationResponse)
async def get_indicator_correlations(
    indicator_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all correlation evidence for this indicator.

    Correlation evidence types:
      - CORRELATION_INFRA: shared ASN with another indicator
      - CORRELATION_SSL:   shared SSL certificate fingerprint
      - MULTI_SOURCE_SIGHTING: seen across multiple independent sources

    Only active (non-reversed) correlation rows are returned. Reversed rows are
    still stored in the DB for audit purposes (append-only) but are excluded here.
    """
    # Verify indicator exists
    exists_q = await db.execute(
        select(Indicator.id).where(Indicator.id == indicator_id)
    )
    if not exists_q.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Indicator not found")

    corr_q = await db.execute(
        select(Evidence)
        .where(
            Evidence.indicator_id == indicator_id,
            Evidence.evidence_type.in_([
                EvidenceType.CORRELATION_INFRA,
                EvidenceType.CORRELATION_SSL,
                EvidenceType.MULTI_SOURCE_SIGHTING,
            ]),
        )
        .order_by(Evidence.timestamp.desc())
    )
    corr_rows = corr_q.scalars().all()

    correlations = [
        CorrelationDetail(
            evidence_id=row.id,
            correlation_type=row.evidence_type.value,
            confidence_delta=float(row.confidence_delta),
            raw_payload=row.raw_payload,
            timestamp=row.timestamp,
            reversed=row.reversed,
        )
        for row in corr_rows
    ]

    return CorrelationResponse(
        indicator_id=indicator_id,
        correlations=correlations,
        total=len(correlations),
    )


# ── POST /  (ingestion — existing, unchanged logic) ───────────────────────────

@router.post("", response_model=IngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_indicators(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Main ingestion gateway. Supports JSON body and multipart/form-data (CSV/TXT file upload).

    JSON format:
        {"source_id": "<uuid>", "indicators": [{"type": "ipv4", "value": "1.2.3.4"}]}

    Multipart format:
        source_id=<uuid> (form field) + file=<CSV or TXT upload>
    """
    content_type = request.headers.get("Content-Type", "")
    source_id: Optional[uuid.UUID] = None
    raw_indicators = []

    # ── JSON branch ──────────────────────────────────────────────────────────
    if "application/json" in content_type:
        try:
            data = await request.json()
            source_id = uuid.UUID(str(data.get("source_id", "")))
            for ind in data.get("indicators", []):
                t_raw = str(ind.get("type", "")).strip().upper()
                itype = normalize_type_to_enum(t_raw)
                raw_indicators.append((itype, str(ind.get("value", ""))))
        except (ValueError, KeyError, TypeError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")

    # ── Multipart branch (file upload) ───────────────────────────────────────
    elif "multipart/form-data" in content_type:
        try:
            form = await request.form()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse multipart form: {e}")

        s_id_raw = None
        for k in form.keys():
            if k.lower() == "source_id":
                s_id_raw = form.get(k)
                break
        if not s_id_raw:
            raise HTTPException(status_code=400, detail="source_id is required in form data")
        try:
            source_id = uuid.UUID(str(s_id_raw))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid source_id UUID: {s_id_raw}")

        file_obj: Optional[UploadFile] = None
        for key in form.keys():
            val = form.get(key)
            if hasattr(val, "read") and hasattr(val, "filename"):
                file_obj = val  # type: ignore[assignment]
                break

        if file_obj is None:
            raise HTTPException(
                status_code=400,
                detail="No file found. Include a CSV or TXT file in the 'file' field.",
            )

        try:
            content = (await file_obj.read()).decode("utf-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read uploaded file: {e}")

        filename = (file_obj.filename or "").lower()
        if filename.endswith(".csv"):
            raw_indicators = IndicatorParser.parse_csv(content)
        else:
            raw_indicators = IndicatorParser.parse_txt(content)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type '{content_type}'. Use application/json or multipart/form-data.",
        )

    if not source_id:
        raise HTTPException(status_code=400, detail="source_id is missing")

    if not raw_indicators:
        return IngestionResponse(
            ingested=0, duplicates=0, errors=0, error_details=[], indicators=[]
        )

    return await IngestionService.ingest_bulk(db, source_id, raw_indicators)
