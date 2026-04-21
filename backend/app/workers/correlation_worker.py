import uuid
import asyncio
import structlog
from typing import Dict, Any
from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.correlation_service import CorrelationService

logger = structlog.get_logger()

@celery_app.task(name="app.workers.correlation_worker.run_correlation_engine")
def run_correlation_engine(indicator_id: str, evidence_id: str = None):
    """
    Celery task that executes the correlation engine checks for an indicator.
    Triggered by evidence.created events.
    """
    logger.info("correlation_engine_task_started", indicator_id=indicator_id, evidence_id=evidence_id)
    
    # Coerce to UUID objects for SQLAlchemy compatibility
    if isinstance(indicator_id, str):
        indicator_id = uuid.UUID(indicator_id)
    if evidence_id and isinstance(evidence_id, str):
        evidence_id = uuid.UUID(evidence_id)

    async def _execute():
        async with AsyncSessionLocal() as db:
            # 1. Execute all 3 correlation checks
            await CorrelationService.run_all_checks(db, indicator_id)
            
            # 2. Commit all correlation evidence to DB
            await db.commit()
            logger.info("correlation_engine_task_completed", indicator_id=str(indicator_id))

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
