import asyncio
import uuid
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.evidence import Evidence, EvidenceType
from app.models.source import TrustTier
from app.services.scoring_service import ScoringService

async def verify_scoring():
    print("Testing Confidence Scoring & Decay Engine...")
    indicator_id = uuid.uuid4()
    mock_db = AsyncMock()
    
    # 1. Mock Indicator (Created 10 days ago)
    mock_indicator = MagicMock()
    mock_indicator.id = indicator_id
    mock_indicator.last_seen = datetime.now(timezone.utc) - timedelta(days=10)
    mock_indicator.current_confidence = 50.0
    mock_db.scalar.return_value = mock_indicator
    
    # 2. Mock Evidence with distinct sources and tiers
    # Ev 1: WHOIS, +10 delta, HIGH trust (1.0 multiplier)
    ev1 = MagicMock(evidence_type=EvidenceType.WHOIS, confidence_delta=10.0)
    # Ev 2: PassiveDNS, +20 delta, LOW trust (0.3 multiplier)
    ev2 = MagicMock(evidence_type=EvidenceType.PASSIVE_DNS, confidence_delta=20.0)
    # Ev 3: Correlation SSL, +8.0
    ev3 = MagicMock(evidence_type=EvidenceType.CORRELATION_SSL, confidence_delta=8.0)
    
    # Return as (evidence, source_name, trust_tier)
    mock_db.execute.return_value = MagicMock(all=lambda: [
        (ev1, "Source Alpha", TrustTier.HIGH),   # 10 * 1.0 = 10
        (ev2, "Source Beta", TrustTier.LOW),    # 20 * 0.3 = 6
        (ev3, "System", None)                    # 8 / None -> is Correlation, so 8.0 directly
    ])
    
    # Expected weighted_sum = (10 * 1.0) + (20 * 0.3) = 16.0
    # Expected depth_bonus = 2 * 2 = 4.0
    # Expected correlation = 8.0
    # Subtotal = 16 + 4 + 8 = 28.0
    # Decay factor for 10 days: math.exp(-0.05 * 10) = e^-0.5 ~= 0.6065
    # Final Score = 28.0 * 0.6065 ~= 16.98
    
    with patch("app.core.redis.redis_manager.publish_event", new_callable=AsyncMock) as mock_pub:
        score = await ScoringService.recalculate_score(mock_db, indicator_id)
        
        expected_decay = math.exp(-0.05 * 10)
        expected_score = 28.0 * expected_decay
        
        print(f"Calculated Score: {score:.2f} (Expected: ~{expected_score:.2f})")
        assert abs(score - expected_score) < 0.1
        
        # Verify snapshot and notification
        assert mock_db.add.called
        assert mock_pub.called
        print("Success: Weighted sum, depth bonus, and decay applied correctly.")

async def main():
    import os
    os.environ["DATABASE_URL"] = "postgresql://user:pass@127.0.0.1/db"
    await verify_scoring()
    print("--- Phase 2.6 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
