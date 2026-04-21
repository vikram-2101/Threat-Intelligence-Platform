import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from app.workers.redis_bridge import redis_event_bridge
from app.workers.enrichment_worker import run_enrichment_pipeline, run_specific_enricher
from app.models.indicator import IndicatorType

async def verify_redis_bridge():
    print("Testing Redis Bridge...")
    mock_msg = {
        "type": "message",
        "channel": "indicator.created",
        "data": json.dumps({
            "indicator_id": str(uuid.uuid4()),
            "type": "DOMAIN",
            "value": "example.com"
        })
    }
    
    with patch("redis.asyncio.Redis.from_url") as mock_redis_factory:
        mock_redis = mock_redis_factory.return_value
        mock_redis.close = AsyncMock()
        mock_pubsub = mock_redis.pubsub.return_value
        # Ensure subscribe is awaitable
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        # Simulate one message then stop
        mock_pubsub.listen.return_value.__aiter__.return_value = [mock_msg]
        
        with patch("app.workers.celery_app.celery_app.send_task") as mock_send:
            # We run it in a task and cancel it after it processes the list
            try:
                await asyncio.wait_for(redis_event_bridge(), timeout=1.0)
            except (asyncio.TimeoutError, StopAsyncIteration):
                pass
            
            assert mock_send.called
            args, kwargs = mock_send.call_args
            assert args[0] == "app.workers.enrichment_worker.run_enrichment_pipeline"
            print("Success: Redis bridge correctly dispatches Celery task.")

def verify_pipeline_fanout():
    print("Testing Pipeline Fan-out...")
    indicator_id = str(uuid.uuid4())
    
    # We mock out the entire group and celery_app to avoid any backend connections
    with patch("app.workers.enrichment_worker.group") as mock_group, \
         patch("app.workers.enrichment_worker.celery_app") as mock_celery_app:
        
        mock_group_instance = mock_group.return_value
        mock_group_instance.apply_async = MagicMock()
        
        run_enrichment_pipeline(indicator_id, "DOMAIN", "example.com")
        
        assert mock_group.called
        tasks = mock_group.call_args[0][0]
        # We expect WHOIS, PassiveDNS, ASN, SSL, Behavioral for DOMAIN
        assert len(tasks) >= 5
        assert mock_group_instance.apply_async.called
        print(f"Success: Pipeline fanned out to {len(tasks)} enricher tasks.")

async def verify_worker_execution():
    print("Testing Worker Execution...")
    indicator_id = str(uuid.uuid4())
    
    # Mock DB, Builder and Redis
    mock_db = AsyncMock()
    # Mock execute result for source lookup
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = uuid.uuid4()
    mock_db.execute.return_value = mock_execute_result
    
    mock_evidence = MagicMock()
    mock_evidence.id = uuid.uuid4()
    
    with patch("app.workers.enrichment_worker.AsyncSessionLocal", return_value=mock_db), \
         patch("app.workers.enrichment_worker.EvidenceBuilder.save_enrichment_result", return_value=mock_evidence), \
         patch("app.workers.enrichment_worker.redis_manager.publish_event") as mock_publish:
        
        # Manually run the worker task logic
        # We mock WHOIS specifically
        with patch.object(run_specific_enricher, "s"): # Mock Celery signature
            run_specific_enricher("WHOIS Lookup", indicator_id, "example.com")
            
            assert mock_publish.called
            channel, payload = mock_publish.call_args[0]
            assert channel == "evidence.created"
            assert payload["indicator_id"] == indicator_id
            print("Success: Worker task executed, persisted, and published evidence.created.")

async def main():
    import os
    os.environ["DATABASE_URL"] = "postgresql://user:pass@127.0.0.1/db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    await verify_redis_bridge()
    verify_pipeline_fanout()
    await verify_worker_execution()
    print("--- Phase 2.4 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
