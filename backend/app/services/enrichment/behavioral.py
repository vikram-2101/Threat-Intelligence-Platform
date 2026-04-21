import uuid
import re
from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.indicator import IndicatorType
from app.models.evidence import Evidence, EvidenceType
from app.services.enrichment.base import BaseEnricher, EnrichmentResult
from app.services.enrichment.common import with_retry

class BehavioralAnalyser(BaseEnricher):
    """
    Analyses behavioral patterns like domain age, infrastructure reuse, and suspicious URLs.
    """

    # Suspicious patterns from Agent.md section 11.3
    SUSPICIOUS_URL_PATTERNS = [
        r"\.php\?id=",
        r"/wp-admin/",
        r"/wp-content/plugins/",
        r"/login\.[a-z]+$",
        r"/signin\.[a-z]+$",
        r"cmd=.*",
        r"shell=.*",
        r"\.exe$",
        r"\.zip$"
    ]

    def get_supported_types(self) -> List[IndicatorType]:
        return [IndicatorType.DOMAIN, IndicatorType.URL]

    def get_source_name(self) -> str:
        return "Behavioral Analysis Engine"

    def get_evidence_type(self) -> EvidenceType:
        # Note: Behavioral analysis is a custom evidence type or mixed.
        # We'll use a generic marker or separate fields in raw_payload.
        return EvidenceType.INGESTION # Or define a BEHAVIORAL type if missed

    @with_retry(max_retries=1, backoff_multipliers=[2], timeout=5)
    async def enrich_with_db(self, db: AsyncSession, indicator_id: uuid.UUID, indicator_value: str) -> EnrichmentResult:
        """
        Special enrich method that has access to the DB for correlation/context.
        """
        flags = {
            "is_short_lived_domain": False,
            "infrastructure_reuse": False,
            "suspicious_url_patterns": []
        }
        
        # 1. Check for suspicious URL patterns
        if "://" in indicator_value:
            for pattern in self.SUSPICIOUS_URL_PATTERNS:
                if re.search(pattern, indicator_value, re.IGNORECASE):
                    flags["suspicious_url_patterns"].append(pattern)
        
        # 2. Check for domain age in existing WHOIS evidence
        whois_q = await db.execute(
            select(Evidence).where(
                Evidence.indicator_id == indicator_id,
                Evidence.evidence_type == EvidenceType.WHOIS
            )
        )
        whois_ev = whois_q.scalar_one_or_none()
        if whois_ev:
            age = whois_ev.raw_payload.get("domain_age_days")
            if age is not None and age < 30:
                flags["is_short_lived_domain"] = True

        # 3. Detect infrastructure reuse
        # Find ASN for this indicator
        asn_q = await db.execute(
            select(Evidence.raw_payload).where(
                Evidence.indicator_id == indicator_id,
                Evidence.evidence_type == EvidenceType.ASN
            )
        )
        current_asn_data = asn_q.scalar_one_or_none()
        
        if current_asn_data and current_asn_data.get("asn"):
            current_asn = current_asn_data.get("asn")
            # Check if this ASN appears in other indicators' evidence
            reuse_q = await db.execute(
                select(Evidence.indicator_id).where(
                    Evidence.indicator_id != indicator_id,
                    Evidence.evidence_type == EvidenceType.ASN,
                    Evidence.raw_payload.op('->>')('asn') == current_asn
                ).limit(1)
            )
            if reuse_q.scalar_one_or_none():
                flags["infrastructure_reuse"] = True

        return EnrichmentResult(
            indicator_id=indicator_id,
            source_name=self.get_source_name(),
            evidence_type=EvidenceType.INGESTION, # Re-using for now or mapping
            raw_payload=flags,
            confidence_delta=0.0, # Behavioral usually flags for correlation, doesn't add fixed delta
            success=True
        )

    async def enrich(self, indicator_id: uuid.UUID, indicator_value: str) -> EnrichmentResult:
        """
        Fallback for when DB isn't available (e.g. initial parallel dispatch).
        Only basic pattern matching is possible.
        """
        flags = {
            "is_short_lived_domain": False,
            "infrastructure_reuse": False,
            "suspicious_url_patterns": []
        }
        if "://" in indicator_value:
            for pattern in self.SUSPICIOUS_URL_PATTERNS:
                if re.search(pattern, indicator_value, re.IGNORECASE):
                    flags["suspicious_url_patterns"].append(pattern)
                    
        return EnrichmentResult(
            indicator_id=indicator_id,
            source_name=self.get_source_name(),
            evidence_type=EvidenceType.INGESTION,
            raw_payload=flags,
            success=True
        )
