import asyncio
import structlog
from sqlalchemy import select
from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.scoring_service import ScoringService
from app.models.indicator import Indicator

logger = structlog.get_logger()

@celery_app.task(name="app.workers.decay_scheduler.run_daily_decay")
def run_daily_decay():
    """
    Scheduled task (via Celery Beat) to apply exponential decay to all active indicators.
    Indicators not updated recently will have their scores pulled down.
    This fulfills Requirement 2.8.
    """
    logger.info("daily_decay_job_started")
    
    async def _execute():
        async with AsyncSessionLocal() as db:
            # 1. Fetch all active indicator IDs
            indicator_ids = (await db.scalars(select(Indicator.id).where(Indicator.status == "ACTIVE"))).all()
            
            logger.info("decay_processing_list", count=len(indicator_ids))
            
            # 2. Re-score each one
            for indicator_id in indicator_ids:
                try:
                    # ScoringService.recalculate_score handles decay logic and EXPIRED status
                    await ScoringService.recalculate_score(db, indicator_id, trigger="daily_decay")
                except Exception as e:
                    logger.error("decay_score_failed", indicator_id=str(indicator_id), error=str(e))
            
            await db.commit()
            logger.info("daily_decay_job_completed", total=len(indicator_ids))

    try:
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_execute())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_execute())
