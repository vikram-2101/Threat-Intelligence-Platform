import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock
from app.models.indicator import IndicatorType
from app.models.evidence import EvidenceType, Evidence
from app.services.enrichment.base import BaseEnricher, EnrichmentResult
from app.services.enrichment.factory import EnrichmentEngineFactory
from app.services.enrichment.builder import EvidenceBuilder

# Override the setup_test_db and db_session fixtures for THIS file
# to prevent pytest from trying to connect to a real DB during collection.
@pytest.fixture(autouse=True)
def mock_db_setup(monkeypatch):
    # Monkeypatch settings or core db objects if necessary
    pass

class MockEnricher(BaseEnricher):
    def get_supported_types(self):
        return [IndicatorType.IPV4]
    
    def get_source_name(self):
        return "MockEnricher"
    
    def get_evidence_type(self):
        return EvidenceType.WHOIS

    async def enrich(self, indicator_id, indicator_value):
        return EnrichmentResult(
            indicator_id=indicator_id,
            source_name=self.get_source_name(),
            evidence_type=self.get_evidence_type(),
            raw_payload={"mock": "data"},
            confidence_delta=10.0
        )

@pytest.mark.asyncio
async def test_factory_registration():
    EnrichmentEngineFactory.clear_registry()
    enricher = MockEnricher()
    EnrichmentEngineFactory.register_enricher(enricher)
    
    enrichers = EnrichmentEngineFactory.get_enrichers_for_type(IndicatorType.IPV4)
    assert len(enrichers) == 1
    assert enrichers[0] == enricher
    
    enrichers_none = EnrichmentEngineFactory.get_enrichers_for_type(IndicatorType.DOMAIN)
    assert len(enrichers_none) == 0

@pytest.mark.asyncio
async def test_evidence_builder_success():
    # Mock DB Session
    mock_db = AsyncMock()
    # Mock the return value of db.execute(...).scalar_one_or_none()
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = uuid.uuid4()
    mock_db.execute.return_value = mock_execute_result
    
    indicator_id = uuid.uuid4()
    result = EnrichmentResult(
        indicator_id=indicator_id,
        source_name="MockEnricher",
        evidence_type=EvidenceType.WHOIS,
        raw_payload={"mock": "data"},
        confidence_delta=10.0,
        success=True
    )
    
    evidence = await EvidenceBuilder.save_enrichment_result(mock_db, result)
    
    assert evidence is not None
    assert evidence.indicator_id == indicator_id
    assert evidence.confidence_delta == 10.0
    assert evidence.evidence_type == EvidenceType.WHOIS
    assert evidence.raw_payload == {"mock": "data"}
    assert mock_db.add.called

@pytest.mark.asyncio
async def test_evidence_builder_failure():
    mock_db = AsyncMock()
    
    indicator_id = uuid.uuid4()
    result = EnrichmentResult(
        indicator_id=indicator_id,
        source_name="MockEnricher",
        evidence_type=EvidenceType.WHOIS,
        success=False,
        error_message="Test Error"
    )
    
    evidence = await EvidenceBuilder.save_enrichment_result(mock_db, result)
    assert evidence is None
    assert not mock_db.add.called
