import asyncio
import os
import uuid
import random
from datetime import datetime, timezone, timedelta

# Smart environment detection: MUST be set before app imports to initialize the engine correctly
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5433/tip"
if "REDIS_URL" not in os.environ:
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal
from app.services.ingestion_service import IngestionService
from app.services.correlation_service import CorrelationService
from app.services.scoring_service import ScoringService
from app.models.indicator import Indicator, IndicatorStatus, IndicatorType
from app.models.evidence import Evidence, EvidenceType
from app.models.source import Source, SourceCategory, TrustTier
from app.models.confidence_snapshot import ConfidenceSnapshot
from app.services.enrichment.asn import ASNEnricher
from app.services.enrichment.builder import EvidenceBuilder

async def setup_test_source(db, name=None):
    s_name = name or f"Integration Test Source {uuid.uuid4().hex[:6]}"
    # Find existing
    q = await db.execute(select(Source).where(Source.name == s_name))
    existing = q.scalar_one_or_none()
    if existing:
        return existing.id
        
    source_id = uuid.uuid4()
    source = Source(
        id=source_id,
        name=s_name,
        category=SourceCategory.internal,
        trust_tier=TrustTier.HIGH,
        default_weight=1.0,
        is_active=True
    )
    db.add(source)
    await db.commit()
    return source_id

async def run_e2e_test():
    print("--- Starting Phase 2.9 Intelligence Engine E2E Test ---")
    async with AsyncSessionLocal() as db:
        # 0. Setup ASN Source
        await setup_test_source(db, name="IP-API ASN Service")
        
        # STEP 1: Ingestion
        ingest_source_id = await setup_test_source(db, name="Main Ingestion Source")
        ip_value = f"1.2.3.{random.randint(1, 254)}"
        print(f"[Step 1] Ingesting IP: {ip_value}")
        
        with patch("app.core.redis.redis_manager.publish_event", new_callable=AsyncMock):
            ingest_res = await IngestionService.ingest_bulk(db, ingest_source_id, [(IndicatorType.IPV4, ip_value)])
            indicator_id = ingest_res.indicators[0].id
            print(f"Ingested Indicator ID: {indicator_id}")

        # STEP 2: Enrichment (Manual Simulation)
        print("[Step 2] Triggering Enrichment (ASN)...")
        with patch("httpx.AsyncClient.get", return_value=MagicMock(status_code=200, json=lambda: {"as": "AS15169 Google LLC", "status": "success"})):
            enricher = ASNEnricher()
            result = await enricher.enrich(indicator_id, ip_value)
            await EvidenceBuilder.save_enrichment_result(db, result)
            await db.commit()
        
        # Verify evidence exists
        ev_q = await db.execute(select(Evidence).where(Evidence.indicator_id == indicator_id, Evidence.evidence_type == EvidenceType.ASN))
        asn_evidence = ev_q.scalar_one()
        print(f"Evidence Created: {asn_evidence.evidence_type} (Delta: {asn_evidence.confidence_delta})")

        # STEP 3: Correlation
        print("[Step 3] Triggering Correlation Engine...")
        # Add another IP with same ASN to trigger correlation
        other_ip = f"1.2.3.{random.randint(1, 254)}"
        while other_ip == ip_value: other_ip = f"1.2.3.{random.randint(1, 254)}"
        
        other_res = await IngestionService.ingest_bulk(db, ingest_source_id, [(IndicatorType.IPV4, other_ip)])
        other_id = other_res.indicators[0].id
        
        with patch("httpx.AsyncClient.get", return_value=MagicMock(status_code=200, json=lambda: {"as": "AS15169 Google LLC", "status": "success"})):
            res_other = await enricher.enrich(other_id, other_ip)
            await EvidenceBuilder.save_enrichment_result(db, res_other)
            await db.commit()
        
        with patch("app.core.redis.redis_manager.publish_event", new_callable=AsyncMock):
            await CorrelationService.run_all_checks(db, indicator_id)
            await db.commit()
            
        # Verify correlation evidence (re-fetch)
        corr_ev = await db.scalar(select(Evidence).where(
            Evidence.indicator_id == indicator_id, 
            Evidence.evidence_type == EvidenceType.CORRELATION_INFRA
        ))
        assert corr_ev is not None
        print(f"Correlation Detected: {corr_ev.evidence_type} (Delta: {corr_ev.confidence_delta})")

        # STEP 4: Scoring & Rationale
        print("[Step 4] Calculating Confidence Scored & Rationale...")
        with patch("app.core.redis.redis_manager.publish_event", new_callable=AsyncMock):
            score = await ScoringService.recalculate_score(db, indicator_id, trigger="integration_test")
            await db.commit()
            
        snapshot = await db.scalar(select(ConfidenceSnapshot).where(ConfidenceSnapshot.indicator_id == indicator_id).order_by(ConfidenceSnapshot.calculated_at.desc()))
        print(f"Final Score: {score}")
        print(f"Rationale Factors: {len(snapshot.reason_summary['factors'])}")
        assert score > 0
        assert len(snapshot.reason_summary['factors']) > 0

        # STEP 5: Decay Simulation (modify indicator in cache or DB)
        print("[Step 5] Simulating Decay (10 days old)...")
        # We need to refresh the indicator object or use a direct update
        from sqlalchemy import update
        await db.execute(update(Indicator).where(Indicator.id == indicator_id).values(last_seen=datetime.now(timezone.utc) - timedelta(days=10)))
        await db.commit()
        
        decayed_score = await ScoringService.recalculate_score(db, indicator_id, trigger="decay_test")
        print(f"Decayed Score: {decayed_score:.2f}")
        assert decayed_score < score

        # STEP 6: Reversibility (Evidence Withdrawal)
        print("[Step 6] Testing Reversibility (Deleting ASN Evidence)...")
        await db.execute(delete(Evidence).where(Evidence.id == asn_evidence.id))
        await db.commit()
        
        reverted_score = await ScoringService.recalculate_score(db, indicator_id, trigger="reversibility_test")
        print(f"Reverted Score: {reverted_score:.2f}")
        assert reverted_score < decayed_score
        
        print("--- Integration Test PASSED ---")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
