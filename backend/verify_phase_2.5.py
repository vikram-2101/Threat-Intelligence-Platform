import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
from app.models.evidence import Evidence, EvidenceType
from app.services.correlation_service import CorrelationService

async def verify_infrastructure_reuse():
    print("Testing Infrastructure Reuse Check...")
    indicator_id = uuid.uuid4()
    mock_db = AsyncMock()
    
    # Mock current ASN
    mock_db.execute.side_effect = [
        # Call 1: Get current ASN
        MagicMock(scalar_one_or_none=lambda: {"asn": "AS15169"}),
        # Call 2: Check for others with same ASN
        MagicMock(scalar_one_or_none=lambda: uuid.uuid4()),
        # Call 3: Check if correlation evidence already exists
        MagicMock(scalar_one_or_none=lambda: None)
    ]
    
    await CorrelationService.check_infrastructure_reuse(mock_db, indicator_id)
    
    # Verify that Evidence was added
    assert mock_db.add.called
    added_ev = mock_db.add.call_args[0][0]
    assert added_ev.evidence_type == EvidenceType.CORRELATION_INFRA
    assert added_ev.confidence_delta == 5.0
    print("Success: Infrastructure reuse detected and evidence added.")

async def verify_ssl_reuse():
    print("Testing SSL Reuse Check...")
    indicator_id = uuid.uuid4()
    mock_db = AsyncMock()
    
    # Mock current SSL Fingerprint
    mock_db.execute.side_effect = [
        # Call 1: Get current Fingerprint
        MagicMock(scalar_one_or_none=lambda: {"fingerprint": "mock_thumbprint"}),
        # Call 2: Check for others
        MagicMock(scalar_one_or_none=lambda: uuid.uuid4()),
        # Call 3: Check if correlation evidence already exists
        MagicMock(scalar_one_or_none=lambda: None)
    ]
    
    await CorrelationService.check_ssl_reuse(mock_db, indicator_id)
    
    assert mock_db.add.called
    added_ev = mock_db.add.call_args[0][0]
    assert added_ev.evidence_type == EvidenceType.CORRELATION_SSL
    assert added_ev.confidence_delta == 8.0
    print("Success: SSL reuse detected and evidence added.")

async def verify_multi_source():
    print("Testing Multi-Source Sighting Check...")
    indicator_id = uuid.uuid4()
    mock_db = AsyncMock()
    
    # Mock source count = 3
    mock_db.execute.side_effect = [
        # Call 1: Count distinct sources
        MagicMock(scalar_one=lambda: 3),
        # Call 2: Delete old evidence
        MagicMock()
    ]
    
    await CorrelationService.check_multi_source_sighting(mock_db, indicator_id)
    
    assert mock_db.add.called
    added_ev = mock_db.add.call_args[0][0]
    assert added_ev.evidence_type == EvidenceType.MULTI_SOURCE_SIGHTING
    assert added_ev.confidence_delta == 9.0 # 3 * 3
    print("Success: Multi-source sighting recorded with correct delta.")

async def main():
    import os
    os.environ["DATABASE_URL"] = "postgresql://user:pass@127.0.0.1/db"
    
    with patch("app.core.redis.redis_manager.publish_event", new_callable=AsyncMock):
        await verify_infrastructure_reuse()
        await verify_ssl_reuse()
        await verify_multi_source()
        
    print("--- Phase 2.5 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
