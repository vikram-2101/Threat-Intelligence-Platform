import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from app.models.evidence import Evidence, EvidenceType
from app.models.source import TrustTier
from app.services.scoring_service import ScoringService

async def verify_rationale():
    print("Testing RationaleBuilder (Explainability)...")
    indicator_id = uuid.uuid4()
    mock_db = AsyncMock()
    
    # Mock Indicator
    mock_indicator = MagicMock()
    mock_indicator.id = indicator_id
    mock_indicator.last_seen = datetime.now(timezone.utc)
    mock_indicator.current_confidence = 0.0
    mock_db.scalar.return_value = mock_indicator
    
    # Mock Evidence with source and trust tier
    ev1_id = uuid.uuid4()
    ev1 = MagicMock(id=ev1_id, evidence_type=EvidenceType.WHOIS, confidence_delta=10.0)
    
    # Return (evidence, source_name, trust_tier)
    mock_db.execute.return_value = MagicMock(all=lambda: [
        (ev1, "WhoisGuard", TrustTier.HIGH)
    ])
    
    with patch("app.core.redis.redis_manager.publish_event", new_callable=AsyncMock):
        await ScoringService.recalculate_score(mock_db, indicator_id)
        
        assert mock_db.add.called
        snapshot = mock_db.add.call_args[0][0]
        rationale = snapshot.reason_summary
        
        print("Checking rationale structure...")
        assert "score" in rationale
        assert "factors" in rationale
        assert "decay_factor" in rationale
        
        factors = rationale["factors"]
        # Expected: WHOIS factor + Depth Bonus factor
        assert len(factors) == 2
        
        whois_factor = next(f for f in factors if f["type"] == EvidenceType.WHOIS)
        assert whois_factor["delta"] == 10.0
        assert whois_factor["source_name"] == "WhoisGuard"
        assert whois_factor["evidence_id"] == str(ev1_id)
        
        depth_factor = next(f for f in factors if f["type"] == "ENRICHMENT_DEPTH_BONUS")
        assert depth_factor["delta"] == 2.0 # 1 type * 2
        
        print(f"Success: Rationale is granular and explainable. Factors: {[f['type'] for f in factors]}")

async def main():
    import os
    os.environ["DATABASE_URL"] = "postgresql://user:pass@127.0.0.1/db"
    await verify_rationale()
    print("--- Phase 2.7 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
