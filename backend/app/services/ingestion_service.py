import uuid
from typing import List, Tuple, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.indicator import Indicator, IndicatorSource
from app.models.evidence import Evidence, EvidenceType
from app.schemas.indicator import IngestionResponse, ValidationItem
from app.services.validator import IndicatorValidator
from app.core.redis import publish_indicator_created
from app.workers.celery_app import celery_app
from app.services.parser import IndicatorParser

from app.models.source import Source, SourceCategory, TrustTier

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
        # 0. Check if Source exists
        source_res = await db.execute(select(Source).where(Source.id == source_id))
        if not source_res.scalar_one_or_none():
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
            res_link = await db.execute(
                select(IndicatorSource).where(
                    IndicatorSource.indicator_id == indicator.id,
                    IndicatorSource.source_id == source_id
                )
            )
            link = res_link.scalar_one_or_none()
            if not link:
                link = IndicatorSource(
                    indicator_id=indicator.id,
                    source_id=source_id,
                    first_reported_at=datetime.now(timezone.utc),
                    last_reported_at=datetime.now(timezone.utc)
                )
                db.add(link)
            else:
                link.last_reported_at = datetime.now(timezone.utc)
            
            # 4. Create Evidence Record
            evidence = Evidence(
                indicator_id=indicator.id,
                source_id=source_id,
                evidence_type=EvidenceType.INGESTION,
                raw_payload={
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                    "original_value": item.raw
                },
                confidence_delta=0.0,
            )
            db.add(evidence)
            
            # 5. Emit Redis Event (PUBLISH per Phase 1.3)
            # This allows external consumers and the Correlation Engine to react in real-time
            await publish_indicator_created(
                indicator_id=str(indicator.id),
                itype=indicator.type.value,
                value=indicator.value
            )
            
            indicators_out.append(indicator)

        await db.commit()
        
        # 6. Trigger Scoring Engine (Celery)
        if indicators_out:
            indicator_ids = [str(ind.id) for ind in indicators_out]
            celery_app.send_task(
                "app.workers.scoring_worker.batch_update_confidence",
                args=[indicator_ids]
            )
        
        return IngestionResponse(
            ingested=new_count,
            duplicates=dup_count,
            errors=len(validation_res.invalid),
            error_details=validation_res.invalid,
            indicators=indicators_out
        )
