import uuid
import asyncio
import structlog
from celery import group
from typing import Dict, Any
from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.enrichment.factory import EnrichmentEngineFactory
from app.services.enrichment.builder import EvidenceBuilder
from app.core.redis import redis_manager
from app.models.indicator import IndicatorType

logger = structlog.get_logger()

# Ensure enrichers are registered when the worker module loads
EnrichmentEngineFactory.setup_default_enrichers()

@celery_app.task(name="app.workers.enrichment_worker.run_enrichment_pipeline")
def run_enrichment_pipeline(indicator_id: str, indicator_type: str, indicator_value: str):
    """
    Coordinator task that dispatches parallel enricher tasks (Fan-out pattern).
    """
    logger.info("enrichment_pipeline_started", indicator_id=indicator_id, type=indicator_type)
    
    # 1. Determine applicable enrichers
    itype = IndicatorType(indicator_type)
    enrichers = EnrichmentEngineFactory.get_enrichers_for_type(itype)
    
    if not enrichers:
        logger.info("no_enrichers_for_type_triggering_baseline_score", type=indicator_type, indicator_id=indicator_id)
        celery_app.send_task(
            "app.workers.scoring_worker.recalculate_indicator_score",
            kwargs={"indicator_id": indicator_id, "trigger": "no_enrichers"}
        )
        return

    # 2. Dispatch parallel tasks using a Celery group
    # Each task is independent; one failure doesn't block others.
    tasks = [
        run_specific_enricher.s(
            enricher_name=e.get_source_name(),
            indicator_id=indicator_id,
            indicator_value=indicator_value
        )
        for e in enrichers
    ]
    
    # Use simple group for parallel execution
    job = group(tasks)
    job.apply_async()
    
    logger.info("enrichment_pipeline_dispatched", count=len(tasks), indicator_id=indicator_id)

@celery_app.task(name="app.workers.enrichment_worker.run_specific_enricher")
def run_specific_enricher(enricher_name: str, indicator_id: str, indicator_value: str):
    """
    Worker task that executes a single enricher and persists the result.
    """
    logger.info("enricher_task_started", enricher=enricher_name, indicator_id=indicator_id)
    
    # Coerce to UUID object for SQLAlchemy compatibility
    if isinstance(indicator_id, str):
        indicator_id = uuid.UUID(indicator_id)

    async def _execute():
        async with AsyncSessionLocal() as db:
            # 1. Get the enricher instance
            enricher = EnrichmentEngineFactory.get_enricher_by_name(enricher_name)
            if not enricher:
                logger.error("enricher_not_found", name=enricher_name)
                return

            # 2. Execute enrichment
            result = await enricher.enrich(indicator_id, indicator_value)
            
            # 3. Persist result as evidence
            evidence = await EvidenceBuilder.save_enrichment_result(db, result)
            
            if evidence:
                await db.commit()
                # 4. Notify downstream (Correlation Engine)
                await redis_manager.publish_event(
                    "evidence.created",
                    {
                        "indicator_id": str(indicator_id),
                        "evidence_id": str(evidence.id),
                        "source": enricher_name,
                        "type": result.evidence_type
                    }
                )
                logger.info("enrichment_completed_and_published", enricher=enricher_name, indicator_id=str(indicator_id))

    # Bridge async logic to sync Celery task
    try:
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_execute())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_execute())
