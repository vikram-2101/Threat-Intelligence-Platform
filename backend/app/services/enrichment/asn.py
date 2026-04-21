import uuid
import httpx
import asyncio
from typing import List, Any
from app.models.indicator import IndicatorType
from app.models.evidence import EvidenceType
from app.services.enrichment.base import BaseEnricher, EnrichmentResult
from app.services.enrichment.common import with_retry

class ASNEnricher(BaseEnricher):
    """
    Enriches IP addresses and domains with ASN (Autonomous System Number) data.
    """

    def get_supported_types(self) -> List[IndicatorType]:
        return [IndicatorType.IPV4, IndicatorType.IPV6, IndicatorType.DOMAIN, IndicatorType.URL]

    def get_source_name(self) -> str:
        return "IP-API ASN Service"

    def get_evidence_type(self) -> EvidenceType:
        return EvidenceType.ASN

    @with_retry(max_retries=3, backoff_multipliers=[2, 4, 8], timeout=10)
    async def enrich(self, indicator_id: uuid.UUID, indicator_value: str) -> EnrichmentResult:
        # Note: In a real system, we'd resolve domain to IP first or use an API that handles both.
        # For MVP, we use ip-api.com (JSON endpoint).
        
        target = indicator_value
        if "://" in target:
            from urllib.parse import urlparse
            target = urlparse(target).netloc
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # ip-api.com/json/{query}?fields=status,message,country,countryCode,region,city,zip,lat,lon,timezone,isp,org,as
                response = await client.get(f"http://ip-api.com/json/{target}?fields=status,message,country,countryCode,isp,org,as,asname,mobile,proxy,hosting")
                response.raise_for_status()
                data = response.json()

            if data.get("status") == "fail":
                return EnrichmentResult(
                    indicator_id=indicator_id,
                    source_name=self.get_source_name(),
                    evidence_type=self.get_evidence_type(),
                    success=False,
                    error_message=data.get("message", "API returned failure")
                )

            return EnrichmentResult(
                indicator_id=indicator_id,
                source_name=self.get_source_name(),
                evidence_type=self.get_evidence_type(),
                raw_payload={
                    "asn": data.get("as"),
                    "asn_name": data.get("asname"),
                    "isp": data.get("isp"),
                    "org": data.get("org"),
                    "country": data.get("country"),
                    "country_code": data.get("countryCode"),
                    "is_hosting": data.get("hosting", False),
                    "is_proxy": data.get("proxy", False)
                },
                confidence_delta=5.0, # From Agent.md section 11.1
                success=True
            )
        except Exception as e:
            return EnrichmentResult(
                indicator_id=indicator_id,
                source_name=self.get_source_name(),
                evidence_type=self.get_evidence_type(),
                success=False,
                error_message=str(e)
            )
