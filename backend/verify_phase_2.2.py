import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.indicator import IndicatorType
from app.models.evidence import EvidenceType
from app.services.enrichment.factory import EnrichmentEngineFactory
from app.services.enrichment.whois import WHOISEnricher
from app.services.enrichment.passive_dns import PassiveDNSEnricher
from datetime import datetime

async def verify_whois():
    print("Testing WHOISEnricher...")
    enricher = WHOISEnricher()
    indicator_id = uuid.uuid4()
    
    # Mocking whois.whois call
    mock_whois_data = MagicMock()
    mock_whois_data.registrar = "GoDaddy"
    mock_whois_data.creation_date = datetime(2020, 1, 1)
    mock_whois_data.updated_date = datetime(2023, 1, 1)
    mock_whois_data.expiration_date = datetime(2025, 1, 1)
    mock_whois_data.country = "US"
    mock_whois_data.name_servers = ["ns1.example.com", "ns2.example.com"]
    
    with patch("whois.whois", return_value=mock_whois_data):
        result = await enricher.enrich(indicator_id, "example.com")
        assert result.success is True
        assert result.raw_payload["registrar"] == "GoDaddy"
        assert result.raw_payload["domain_age_days"] > 1000
        print(f"Success: WHOISEnricher returned age {result.raw_payload['domain_age_days']} days.")

async def verify_dns():
    print("Testing PassiveDNSEnricher...")
    enricher = PassiveDNSEnricher()
    indicator_id = uuid.uuid4()
    
    # Mocking dns.resolver.resolve
    with patch("dns.resolver.resolve") as mock_resolve:
        mock_resolve.return_value = ["1.2.3.4"]
        result = await enricher.enrich(indicator_id, "example.com")
        assert result.success is True
        assert "A" in result.raw_payload["resolutions"]
        print(f"Success: PassiveDNSEnricher returned A records: {result.raw_payload['resolutions']['A']}")

async def verify_factory():
    print("Testing Factory with new enrichers...")
    EnrichmentEngineFactory.setup_default_enrichers()
    
    domain_enrichers = EnrichmentEngineFactory.get_enrichers_for_type(IndicatorType.DOMAIN)
    names = [e.get_source_name() for e in domain_enrichers]
    assert "WHOIS Lookup" in names
    assert "DNS Resolver" in names
    print(f"Success: Factory registered {len(domain_enrichers)} enrichers for DOMAIN.")

async def main():
    # Mock settings
    import os
    os.environ["DATABASE_URL"] = "postgresql://user:pass@127.0.0.1/db"
    
    await verify_whois()
    await verify_dns()
    await verify_factory()
    print("--- Phase 2.2 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
