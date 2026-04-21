import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.indicator import IndicatorType
from app.schemas.indicator import IngestionResponse, IndicatorResponse
from app.services.ingestion_service import IngestionService
from app.services.parser import IndicatorParser

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/{indicator_id}", response_model=IndicatorResponse)
async def get_indicator(
    indicator_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve indicator details including evidence and scoring history.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.indicator import Indicator

    result = await db.execute(
        select(Indicator)
        .where(Indicator.id == indicator_id)
        .options(
            selectinload(Indicator.evidence),
            selectinload(Indicator.snapshots)
        )
    )
    indicator = result.scalar_one_or_none()
    
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    return indicator


def normalize_type_to_enum(t_str: str) -> IndicatorType | str:
    """Safely converts a string to IndicatorType enum, or returns the raw string if unknown."""
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


@router.post("/", response_model=IngestionResponse, status_code=status.HTTP_202_ACCEPTED)
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

    # ── JSON branch ────────────────────────────────────────────────────────────
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

    # ── Multipart branch (file upload) ─────────────────────────────────────────
    elif "multipart/form-data" in content_type:
        try:
            form = await request.form()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse multipart form: {e}")

        # 1. Extract source_id — case-insensitive key lookup
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

        # 2. Find the file field — any key whose value is an UploadFile
        file_obj: Optional[UploadFile] = None
        for key in form.keys():
            val = form.get(key)
            # Starlette stores uploaded files as UploadFile; check by duck-typing
            if hasattr(val, "read") and hasattr(val, "filename"):
                file_obj = val  # type: ignore[assignment]
                break

        if file_obj is None:
            raise HTTPException(
                status_code=400,
                detail="No file found in multipart request. Include a CSV or TXT file in the 'file' field."
            )

        try:
            content = (await file_obj.read()).decode("utf-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read uploaded file: {e}")

        filename = (file_obj.filename or "").lower()
        if filename.endswith(".csv"):
            raw_indicators = IndicatorParser.parse_csv(content)
        else:
            # TXT or any other extension — one indicator per line
            raw_indicators = IndicatorParser.parse_txt(content)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type '{content_type}'. Use application/json or multipart/form-data.",
        )

    if not source_id:
        raise HTTPException(status_code=400, detail="source_id is missing")

    # Empty payload → return zeros (not an error)
    if not raw_indicators:
        return IngestionResponse(
            ingested=0, duplicates=0, errors=0, error_details=[], indicators=[]
        )

    return await IngestionService.ingest_bulk(db, source_id, raw_indicators)

