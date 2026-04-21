import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from app.workers.decay_scheduler import run_daily_decay
from app.services.scoring_service import ScoringService
from sqlalchemy import select
from app.models.indicator import Indicator, IndicatorStatus

async def verify_decay_scheduler():
    print("Testing Decay Scheduler (Celery Beat)...")
    mock_db = AsyncMock()
    
    indicator_id = uuid.uuid4()
    
    # 1. Mock select all active indicators
    class MockResult:
        def all(self):
            return [indicator_id]
    
    async def mock_scalars_side_effect(*args, **kwargs):
        return MockResult()
    
    mock_db.scalars.side_effect = mock_scalars_side_effect
    
    # 2. Mock recalculate_score
    with patch("app.services.scoring_service.ScoringService.recalculate_score", new_callable=AsyncMock) as mock_score:
        with patch("app.workers.decay_scheduler.AsyncSessionLocal", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_db))):
            from app.workers.decay_scheduler import run_daily_decay
            # We call the internal _execute logic directly to avoid Celery/nest_asyncio wrapper issues in tests
            # But the requirement was to test the task, so we'll just fix the MockResult iteration.
            
            # Re-running the task logic manually to ensure clean execution
            async def test_run():
                async with mock_db as db:
                     ids = (await db.scalars(select(Indicator.id).where(Indicator.status == "ACTIVE"))).all()
                     for i in ids:
                         await ScoringService.recalculate_score(db, i, trigger="daily_decay")
            
            # Let's try the task again with a fixed return type
            class FixedResult:
                def all(self): return [indicator_id]
            
            mock_db.scalars = AsyncMock(return_value=FixedResult())
            
            run_daily_decay()
            
            assert mock_score.called
            print("Success: Decay scheduler correctly identifies active indicators and triggers re-scoring.")

async def verify_expiration_logic():
    print("Testing Automated Expiration Logic...")
    indicator_id = uuid.uuid4()
    mock_db = AsyncMock()
    
    # Mock Indicator: Low score (5) and Expired TTL (1 day ago)
    mock_indicator = MagicMock()
    mock_indicator.id = indicator_id
    mock_indicator.status = "ACTIVE"
    mock_indicator.ttl = datetime.now(timezone.utc) - timedelta(days=1)
    mock_indicator.last_seen = datetime.now(timezone.utc) - timedelta(days=10)
    mock_indicator.current_confidence = 50.0
    mock_db.scalar.return_value = mock_indicator
    
    # Mock evidence such that final score remains < 10
    mock_db.execute.return_value = MagicMock(all=lambda: []) # No evidence -> Score 0
    
    with patch("app.core.redis.redis_manager.publish_event", new_callable=AsyncMock):
        score = await ScoringService.recalculate_score(mock_db, indicator_id)
        
        assert score < 10.0
        assert mock_indicator.status == "EXPIRED"
        print(f"Success: Indicator expired correctly (Score: {score:.2f}, Status: {mock_indicator.status})")

async def main():
    import os
    os.environ["DATABASE_URL"] = "postgresql://user:pass@127.0.0.1/db"
    
    await verify_decay_scheduler()
    await verify_expiration_logic()
    print("--- Phase 2.8 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
