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

        # 2. Pre-fetch existing indicators in one single query
        valid_items = validation_res.valid
        valid_keys = [(item.type, item.normalized) for item in valid_items]

        existing_indicators = {}
        if valid_keys:
            from sqlalchemy import or_
            clause = or_(*((Indicator.type == t) & (Indicator.value == v) for t, v in valid_keys))
            res = await db.execute(select(Indicator).where(clause))
            for ind in res.scalars().all():
                existing_indicators[(ind.type, ind.value)] = ind

        # Pre-fetch existing IndicatorSource links
        existing_links = set()
        if existing_indicators:
            res_links = await db.execute(
                select(IndicatorSource.indicator_id).where(
                    IndicatorSource.indicator_id.in_([ind.id for ind in existing_indicators.values()]),
                    IndicatorSource.source_id == source_obj.id
                )
            )
            existing_links = {r for r in res_links.scalars().all()}
        
        import asyncio
        import logging
        logger = logging.getLogger(__name__)
        
        publish_tasks = []

        # 3. Process Valid Indicators
        for item in valid_items:
            # Find existing from local map
            indicator = existing_indicators.get((item.type, item.normalized))
            
            if not indicator:
                indicator = Indicator(
                    type=item.type,
                    value=item.normalized,
                    ttl=datetime.now(timezone.utc) + timedelta(days=30)
                )
                db.add(indicator)
                await db.flush()  # Generate ID
                existing_indicators[(item.type, item.normalized)] = indicator
                new_count += 1
            else:
                dup_count += 1
            
            # 4. Update Indicator-Source Link
            if indicator.id not in existing_links:
                link = IndicatorSource(
                    indicator_id=indicator.id,
                    source_id=source_obj.id,
                    first_reported_at=datetime.now(timezone.utc),
                    last_reported_at=datetime.now(timezone.utc)
                )
                db.add(link)
                existing_links.add(indicator.id)
            
            # 5. Add Redis Event Task to list
            publish_tasks.append(
                publish_indicator_created(
                    indicator_id=str(indicator.id),
                    itype=indicator.type.value,
                    value=indicator.value
                )
            )
            
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
        
        if publish_tasks:
            # Emit Redis events in background after DB commit
            # This ensures the API response is not blocked by Redis latency
            for task_coro in publish_tasks:
                asyncio.create_task(task_coro)

        return IngestionResponse(
            ingested=new_count,
            duplicates=dup_count,
            errors=len(validation_res.invalid),
            error_details=validation_res.invalid,
            indicators=indicators_out
        )

