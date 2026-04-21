import uuid
from typing import List, Tuple, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.indicator import Indicator, IndicatorSource
from app.models.source import Source
from app.schemas.indicator import IngestionResponse, ValidationItem, IndicatorResponse
from app.services.validator import IndicatorValidator
from app.core.redis import publish_indicator_created
from app.services.parser import IndicatorParser


class IngestionService:
    @staticmethod
    async def ingest_bulk(
        db: AsyncSession, 
        source_id: uuid.UUID,
        raw_indicators: List[Tuple[Any, str]]
    ) -> IngestionResponse:
        """
        The core ingestion engine.
        - Validates and Normalizes raw inputs.
        - Merges duplicates via the "Find or Create" pattern.
        - Emits 'indicator.created' events to Redis for downstream consumption.
        - Triggers the async Scoring engine.
        """
        # 0. Check if Source exists and get the object
        if isinstance(source_id, str):
            source_id = uuid.UUID(source_id)

        source_res = await db.execute(select(Source).where(Source.id == source_id))
        source_obj = source_res.scalar_one_or_none()
        if not source_obj:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

        # 1. Validate and Normalize Batch
        validation_res = IndicatorValidator.validate_batch(raw_indicators)
        
        indicators_out = []
        new_count = 0
        dup_count = 0
        
        # 2. Process Valid Indicators
        for item in validation_res.valid:
            # Find existing by canonical (type, value)
            result = await db.execute(
                select(Indicator).where(
                    Indicator.type == item.type,
                    Indicator.value == item.normalized
                )
            )
            indicator = result.scalar_one_or_none()
            
            if not indicator:
                indicator = Indicator(
                    type=item.type,
                    value=item.normalized,
                    ttl=datetime.now(timezone.utc) + timedelta(days=30)
                )
                db.add(indicator)
                await db.flush()  # Generate ID
                new_count += 1
            else:
                dup_count += 1
            
            # 3. Update Indicator-Source Link
            # We use the relationship objects for better session management
            res_link = await db.execute(
                select(IndicatorSource).where(
                    IndicatorSource.indicator_id == indicator.id,
                    IndicatorSource.source_id == source_obj.id
                )
            )
            link = res_link.scalar_one_or_none()
            if not link:
                link = IndicatorSource(
                    indicator=indicator,
                    source=source_obj,
                    first_reported_at=datetime.now(timezone.utc),
                    last_reported_at=datetime.now(timezone.utc)
                )
                db.add(link)
            else:
                link.last_reported_at = datetime.now(timezone.utc)
            
            # 4. Emit Redis Event (PUBLISH per Phase 1.3 spec)
            # indicator.created triggers EnrichmentWorker, which creates Evidence rows.
            # No evidence is created at ingestion time — confidence starts at 0.
            # This allows external consumers and the Correlation Engine to react in real-time
            await publish_indicator_created(
                indicator_id=str(indicator.id),
                itype=indicator.type.value,
                value=indicator.value
            )
            
            # Convert ORM model to Pydantic Response DTO immediately while session is active
            # This prevents any downstream "Lazy Loading" errors in the async path.
            dto = IndicatorResponse(
                id=indicator.id,
                type=indicator.type,
                value=indicator.value,
                status=indicator.status,
                current_confidence=float(indicator.current_confidence or 0.0),
                first_seen=indicator.first_seen,
                last_seen=indicator.last_seen,
                ttl=indicator.ttl,
                evidence=[],
                confidence_history=[]
            )
            indicators_out.append(dto)

        await db.commit()
        
        return IngestionResponse(
            ingested=new_count,
            duplicates=dup_count,
            errors=len(validation_res.invalid),
            error_details=validation_res.invalid,
            indicators=indicators_out
        )
