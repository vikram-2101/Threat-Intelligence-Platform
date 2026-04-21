import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock
from app.models.indicator import IndicatorType
from app.models.evidence import EvidenceType
from app.services.enrichment.base import BaseEnricher, EnrichmentResult
from app.services.enrichment.factory import EnrichmentEngineFactory
from app.services.enrichment.builder import EvidenceBuilder

class MockEnricher(BaseEnricher):
    def get_supported_types(self): return [IndicatorType.IPV4]
    def get_source_name(self): return "MockSource"
    def get_evidence_type(self): return EvidenceType.WHOIS
    async def enrich(self, indicator_id, indicator_value):
        return EnrichmentResult(
            indicator_id=indicator_id,
            source_name=self.get_source_name(),
            evidence_type=self.get_evidence_type(),
            success=True
        )

async def main():
    print("--- Starting Enrichment Framework Verification ---")
    
    # 1. Test Factory
    enricher = MockEnricher()
    EnrichmentEngineFactory.register_enricher(enricher)
    enrichers = EnrichmentEngineFactory.get_enrichers_for_type(IndicatorType.IPV4)
    assert len(enrichers) == 1
    print("Success: Factory registered and retrieved enricher.")

    # 2. Test Builder with Mock DB
    mock_db = AsyncMock()
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = uuid.uuid4()
    mock_db.execute.return_value = mock_execute_result

    indicator_id = uuid.uuid4()
    result = await enricher.enrich(indicator_id, "1.2.3.4")
    evidence = await EvidenceBuilder.save_enrichment_result(mock_db, result)
    
    assert evidence is not None
    assert evidence.indicator_id == indicator_id
    assert mock_db.add.called
    print("Success: EvidenceBuilder processed result and called db.add.")
    
    print("--- Verification Complete ---")

if __name__ == "__main__":
    # Mock settings to avoid DNS lookup errors during import
    import os
    os.environ["DATABASE_URL"] = "postgresql://user:pass@127.0.0.1/db"
    asyncio.run(main())
