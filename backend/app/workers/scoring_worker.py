import uuid
import asyncio
import structlog
from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.scoring_service import ScoringService

logger = structlog.get_logger()

@celery_app.task(name="app.workers.scoring_worker.recalculate_indicator_score")
def recalculate_indicator_score(indicator_id: str, trigger: str = "automated"):
    """
    Celery task to recalculate the confidence score of an indicator.
    Triggered by evidence or correlation updates.
    """
    logger.info("recalculate_score_task_started", indicator_id=indicator_id, trigger=trigger)
    
    # Coerce to UUID object for SQLAlchemy compatibility
    if isinstance(indicator_id, str):
        indicator_id = uuid.UUID(indicator_id)

    async def _execute():
        async with AsyncSessionLocal() as db:
            score = await ScoringService.recalculate_score(db, indicator_id, trigger=trigger)
            await db.commit()
            logger.info("recalculate_score_task_completed", indicator_id=str(indicator_id), score=score)

    try:
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_execute())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_execute())
