import asyncio
import json
import structlog
from redis.asyncio import Redis
from app.core.config import settings
from app.workers.celery_app import celery_app

logger = structlog.get_logger()

async def redis_event_bridge():
    """
    Listens for Redis events and bridges them to Celery tasks.
    This fulfills the 'decoupled consumer' requirement in Agent.md.
    """
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()
    
    # Channels to monitor
    channels = ["indicator.created", "evidence.created"]
    await pubsub.subscribe(*channels)
    
    logger.info("redis_bridge_started", subscribed_to=channels)
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"]
                try:
                    payload = json.loads(message["data"])
                    logger.info("redis_event_received", channel=channel, payload=payload)
                    
                    if channel == "indicator.created":
                        # Dispatch enrichment pipeline as a Celery task
                        celery_app.send_task(
                            "app.workers.enrichment_worker.run_enrichment_pipeline",
                            kwargs={
                                "indicator_id": payload["indicator_id"],
                                "indicator_type": payload["type"],
                                "indicator_value": payload["value"]
                            }
                        )
                    elif channel == "evidence.created":
                        # Dispatch correlation engine
                        celery_app.send_task(
                            "app.workers.correlation_worker.run_correlation_engine",
                            kwargs={
                                "indicator_id": payload["indicator_id"],
                                "evidence_id": payload.get("evidence_id")
                            }
                        )
                        # Trigger score recalculation
                        celery_app.send_task(
                            "app.workers.scoring_worker.recalculate_indicator_score",
                            kwargs={"indicator_id": payload["indicator_id"], "trigger": "new_evidence"}
                        )
                    elif channel == "correlation.created":
                        # Trigger score recalculation after correlation engine finishes
                        celery_app.send_task(
                            "app.workers.scoring_worker.recalculate_indicator_score",
                            kwargs={"indicator_id": payload["indicator_id"], "trigger": "correlation_detected"}
                        )
                except Exception as e:
                    logger.error("redis_bridge_payload_error", error=str(e), data=message["data"])
    finally:
        await pubsub.unsubscribe(*channels)
        await redis.close()

if __name__ == "__main__":
    asyncio.run(redis_event_bridge())
