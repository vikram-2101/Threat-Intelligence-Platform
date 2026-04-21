import httpx
import logging
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.db.session import SessionLocal, AsyncSessionLocal
from app.models.source import Source
from app.services.ingestion_service import IngestionService
from app.services.parser import IndicatorParser
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="app.workers.tasks.fetch_external_feeds")
def fetch_external_feeds():
    """
    Automated background task to pull threat intelligence from configured external feeds.
    """
    async def _execute():
        async with AsyncSessionLocal() as db:
            # 1. Identify all active sources that have a pull URL configured
            result = await db.execute(
                select(Source).where(
                    Source.is_active == True,
                    Source.pull_url.isnot(None)
                )
            )
            sources = result.scalars().all()
            
            if not sources:
                logger.debug("No active feeds with pull_urls found.")
                return

            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                for source in sources:
                    try:
                        logger.info(f"Pulling external feed for source: {source.name} ({source.pull_url})")
                        
                        response = await client.get(source.pull_url)
                        
                        # Handle failures (like 404)
                        if response.status_code >= 400:
                            source.consecutive_failures += 1
                            source.last_pull_status = "http_error"
                            source.last_pull_error = f"{response.status_code} {response.reason_phrase}: {source.pull_url}"
                            
                            if source.consecutive_failures >= 3:
                                source.is_active = False
                                logger.warning(f"Auto-deactivated source {source.name} after 3 consecutive failures.")
                            
                            await db.commit()
                            continue

                        # Success path
                        source.consecutive_failures = 0
                        source.last_pull_status = "success"
                        source.last_pull_error = None
                        content = response.text
                        
                        # Parse based on extension or content
                        if source.pull_url.lower().endswith(".csv"):
                            indicators = IndicatorParser.parse_csv(content)
                        else:
                            indicators = IndicatorParser.parse_txt(content)
                        
                        if indicators:
                            # Reuse high-performance ingestion engine
                            ingest_res = await IngestionService.ingest_bulk(db, source.id, indicators)
                            source.last_pull_status = f"success: {ingest_res.ingested} New"
                        else:
                            source.last_pull_status = "success: no data"
                            
                        source.last_pull_at = datetime.now(timezone.utc)
                        await db.commit()
                        
                    except httpx.HTTPError as he:
                        logger.error(f"HTTP Error pulling {source.name}: {str(he)}")
                        source.consecutive_failures += 1
                        source.last_pull_at = datetime.now(timezone.utc)
                        source.last_pull_status = "connection_failed"
                        source.last_pull_error = str(he)
                        if source.consecutive_failures >= 3:
                            source.is_active = False
                        await db.commit()
                    except Exception as e:
                        logger.error(f"Error in puller for {source.name}: {str(e)}")
                        source.last_pull_at = datetime.now(timezone.utc)
                        source.last_pull_status = "system_error"
                        source.last_pull_error = str(e)[:200]
                        await db.commit()

    # Bridge to sync Celery worker
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(_execute())
