import uuid
import asyncio
import whois
from typing import List, Any
from urllib.parse import urlparse
from datetime import datetime, timezone

from app.models.indicator import IndicatorType
from app.models.evidence import EvidenceType
from app.services.enrichment.base import BaseEnricher, EnrichmentResult
from app.services.enrichment.common import with_retry

class WHOISEnricher(BaseEnricher):
    """
    Enriches domains and URLs with WHOIS information.
    """

    def get_supported_types(self) -> List[IndicatorType]:
        return [IndicatorType.DOMAIN, IndicatorType.URL]

    def get_source_name(self) -> str:
        return "WHOIS Lookup"

    def get_evidence_type(self) -> EvidenceType:
        return EvidenceType.WHOIS

    def _extract_domain(self, value: str) -> str:
        """
        Extracts the domain from a URL or returns the string if it's already a domain.
        """
        if "://" in value:
            parsed = urlparse(value)
            return parsed.netloc
        return value

    @with_retry(max_retries=3, backoff_multipliers=[2, 4, 8], timeout=10)
    async def enrich(self, indicator_id: uuid.UUID, indicator_value: str) -> EnrichmentResult:
        domain = self._extract_domain(indicator_value)
        
        try:
            # whois.whois is synchronous, wrap in to_thread to keep loop async
            w = await asyncio.to_thread(whois.whois, domain)
            
            # Normalize dates (can be list or single datetime)
            def normalize_date(d: Any) -> Any:
                if isinstance(d, list):
                    return d[0].isoformat() if d[0] else None
                return d.isoformat() if hasattr(d, 'isoformat') else str(d)

            # Sub-phase 2.2: Domain age calculation
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            
            domain_age_days = None
            if creation_date and isinstance(creation_date, datetime):
                # Ensure creation_date is naive or localized to UTC for comparison
                now = datetime.now()
                delta = now - creation_date.replace(tzinfo=None) # simple comparison
                domain_age_days = delta.days

            raw_payload = {
                "registrar": w.registrar,
                "creation_date": normalize_date(w.creation_date),
                "updated_date": normalize_date(w.updated_date),
                "expiration_date": normalize_date(w.expiration_date),
                "registrant_country": w.country,
                "name_servers": w.name_servers if isinstance(w.name_servers, list) else [w.name_servers],
                "domain_age_days": domain_age_days
            }

            return EnrichmentResult(
                indicator_id=indicator_id,
                source_name=self.get_source_name(),
                evidence_type=self.get_evidence_type(),
                raw_payload=raw_payload,
                confidence_delta=10.0, # From Agent.md section 11.1
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
