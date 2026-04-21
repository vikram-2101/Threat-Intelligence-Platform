import uuid
import asyncio
import dns.resolver
from typing import List, Any
from urllib.parse import urlparse
from datetime import datetime, timezone

from app.models.indicator import IndicatorType
from app.models.evidence import EvidenceType
from app.services.enrichment.base import BaseEnricher, EnrichmentResult
from app.services.enrichment.common import with_retry

class PassiveDNSEnricher(BaseEnricher):
    """
    Enriches indicators with DNS resolution data.
    Note: In MVP, this performs live DNS lookups as a proxy for passive DNS.
    """

    def get_supported_types(self) -> List[IndicatorType]:
        return [IndicatorType.IPV4, IndicatorType.IPV6, IndicatorType.DOMAIN, IndicatorType.URL]

    def get_source_name(self) -> str:
        return "DNS Resolver"

    def get_evidence_type(self) -> EvidenceType:
        return EvidenceType.PASSIVE_DNS

    def _extract_domain(self, value: str) -> str:
        if "://" in value:
            parsed = urlparse(value)
            return parsed.netloc
        return value

    @with_retry(max_retries=3, backoff_multipliers=[2, 4, 8], timeout=10)
    async def enrich(self, indicator_id: uuid.UUID, indicator_value: str) -> EnrichmentResult:
        target = self._extract_domain(indicator_value)
        results = {}
        
        try:
            # We want to resolve A, AAAA, and MX records
            # dns.resolver is synchronous, wrap in thread
            for qtype in ['A', 'AAAA', 'MX', 'CNAME']:
                try:
                    answers = await asyncio.to_thread(dns.resolver.resolve, target, qtype)
                    results[qtype] = [str(rdata) for rdata in answers]
                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                    continue

            return EnrichmentResult(
                indicator_id=indicator_id,
                source_name=self.get_source_name(),
                evidence_type=self.get_evidence_type(),
                raw_payload={
                    "resolutions": results,
                    "queried_at": datetime.now(timezone.utc).isoformat()
                },
                confidence_delta=8.0, # From Agent.md section 11.1
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
