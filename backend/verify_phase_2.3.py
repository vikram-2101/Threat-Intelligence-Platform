import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.indicator import IndicatorType
from app.services.enrichment.factory import EnrichmentEngineFactory
from app.services.enrichment.asn import ASNEnricher
from app.services.enrichment.ssl_cert import SSLEnricher
from app.services.enrichment.behavioral import BehavioralAnalyser

async def verify_asn():
    print("Testing ASNEnricher...")
    enricher = ASNEnricher()
    indicator_id = uuid.uuid4()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "as": "AS15169",
        "asname": "GOOGLE",
        "country": "United States",
        "hosting": True
    }
    
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        result = await enricher.enrich(indicator_id, "8.8.8.8")
        assert result.success is True
        assert result.raw_payload["asn"] == "AS15169"
        print(f"Success: ASNEnricher returned {result.raw_payload['asn']}.")

async def verify_ssl():
    print("Testing SSLEnricher...")
    enricher = SSLEnricher()
    indicator_id = uuid.uuid4()
    
    mock_cert = {
        "fingerprint": "abc123sha256",
        "issuer": {"O": "DigiCert"},
        "valid_until": "2025-01-01T00:00:00"
    }
    
    with patch.object(SSLEnricher, "_fetch_cert_info", return_value=mock_cert):
        result = await enricher.enrich(indicator_id, "google.com")
        assert result.success is True
        assert result.raw_payload["fingerprint"] == "abc123sha256"
        print(f"Success: SSLEnricher returned fingerprint {result.raw_payload['fingerprint']}.")

async def verify_behavioral():
    print("Testing BehavioralAnalyser...")
    enricher = BehavioralAnalyser()
    indicator_id = uuid.uuid4()
    
    # Test pattern matching (no DB needed for this part)
    result = await enricher.enrich(indicator_id, "http://malicious.com/wp-admin/login.php?id=1")
    assert result.success is True
    assert len(result.raw_payload["suspicious_url_patterns"]) > 0
    print(f"Success: BehavioralAnalyser detected patterns: {result.raw_payload['suspicious_url_patterns']}.")

async def verify_factory():
    print("Testing Factory with Phase 2.3 enrichers...")
    EnrichmentEngineFactory.setup_default_enrichers()
    
    enrichers = EnrichmentEngineFactory.get_enrichers_for_type(IndicatorType.DOMAIN)
    names = [e.get_source_name() for e in enrichers]
    assert "IP-API ASN Service" in names
    assert "SSL Certificate Scanner" in names
    assert "Behavioral Analysis Engine" in names
    print(f"Success: Factory registered {len(enrichers)} enrichers for DOMAIN.")

async def main():
    import os
    os.environ["DATABASE_URL"] = "postgresql://user:pass@127.0.0.1/db"
    
    await verify_asn()
    await verify_ssl()
    await verify_behavioral()
    await verify_factory()
    print("--- Phase 2.3 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
