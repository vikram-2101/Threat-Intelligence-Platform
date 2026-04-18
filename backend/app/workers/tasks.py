import httpx
import logging
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session
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
    This runs via Celery Beat on a scheduled interval.
    """
    db = SessionLocal()
    try:
        # Identify all active sources that have a pull URL configured
        sources = db.query(Source).filter(
            Source.is_active == True,
            Source.pull_url.isnot(None)
        ).all()
        
        if not sources:
            logger.debug("No active feeds with pull_urls found.")
            return

        for source in sources:
            try:
                logger.info(f"Pulling external feed for source: {source.name} ({source.pull_url})")
                
                # 1. Fetch content with timeout protection
                with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                    response = client.get(source.pull_url)
                    response.raise_for_status()
                    content = response.text
                
                # 2. Parse based on extension or content
                if source.pull_url.lower().endswith(".csv"):
                    indicators = IndicatorParser.parse_csv(content)
                else:
                    # Default to line-based TXT parsing
                    indicators = IndicatorParser.parse_txt(content)
                
                if not indicators:
                    logger.warning(f"Feed from {source.name} was empty.")
                    source.last_pull_at = datetime.now(timezone.utc)
                    source.last_pull_status = "Skipped: No data found"
                    db.commit()
                    continue

                # 3. Bridge the Synchronous Task to the Asynchronous Ingestion Engine
                async def run_ingest():
                    async with AsyncSessionLocal() as async_db:
                        # Re-use the high-performance IngestionService built in Phase 1.3
                        return await IngestionService.ingest_bulk(
                            async_db, 
                            source.id, 
                            indicators
                        )
                
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # Create a new loop if one doesn't exist for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                ingest_res = loop.run_until_complete(run_ingest())
                
                # 4. Record Success Metrics
                source.last_pull_at = datetime.now(timezone.utc)
                source.last_pull_status = f"Success: {ingest_res.ingested} New, {ingest_res.duplicates} Dups"
                db.commit()
                logger.info(f"Successfully processed feed for {source.name}")
                
            except httpx.HTTPError as he:
                logger.error(f"HTTP Error pulling {source.name}: {str(he)}")
                source.last_pull_at = datetime.now(timezone.utc)
                source.last_pull_status = f"HTTP Error: {response.status_code if 'response' in locals() else 'Connection failed'}"
                db.commit()
            except Exception as e:
                logger.error(f"Error in puller for {source.name}: {str(e)}")
                source.last_pull_at = datetime.now(timezone.utc)
                source.last_pull_status = f"System Error: {str(e)[:40]}..."
                db.commit()
                
    finally:
        db.close()
