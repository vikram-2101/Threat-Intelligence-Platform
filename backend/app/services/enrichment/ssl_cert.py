import uuid
import asyncio
import socket
import ssl
import hashlib
from typing import List, Any, Optional
from urllib.parse import urlparse
from datetime import datetime, timezone

from app.models.indicator import IndicatorType
from app.models.evidence import EvidenceType
from app.services.enrichment.base import BaseEnricher, EnrichmentResult
from app.services.enrichment.common import with_retry

class SSLEnricher(BaseEnricher):
    """
    Enriches domains and URLs with SSL/TLS certificate information.
    """

    def get_supported_types(self) -> List[IndicatorType]:
        return [IndicatorType.DOMAIN, IndicatorType.URL]

    def get_source_name(self) -> str:
        return "SSL Certificate Scanner"

    def get_evidence_type(self) -> EvidenceType:
        return EvidenceType.SSL_CERT

    def _extract_domain(self, value: str) -> str:
        if "://" in value:
            parsed = urlparse(value)
            return parsed.netloc
        return value

    def _fetch_cert_info(self, hostname: str, port: int = 443) -> dict:
        """
        Synchronous certificate fetch logic.
        """
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # We want info even if invalid/self-signed
        
        with socket.create_connection((hostname, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert_bin = ssock.getpeercert(binary_form=True)
                cert_dict = ssock.getpeercert()
                
                fingerprint = hashlib.sha256(cert_bin).hexdigest()
                
                # Format valid_until
                not_after = cert_dict.get('notAfter')
                valid_until = None
                if not_after:
                    # SSL dates are typically formatted like "Jan  1 00:00:00 2025 GMT"
                    valid_until = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").isoformat()

                return {
                    "fingerprint": fingerprint,
                    "issuer": dict(x[0] for x in cert_dict.get('issuer', [])),
                    "subject": dict(x[0] for x in cert_dict.get('subject', [])),
                    "alt_names": [x[1] for x in cert_dict.get('subjectAltName', [])],
                    "valid_until": valid_until,
                    "version": cert_dict.get('version')
                }

    @with_retry(max_retries=3, backoff_multipliers=[2, 4, 8], timeout=15)
    async def enrich(self, indicator_id: uuid.UUID, indicator_value: str) -> EnrichmentResult:
        hostname = self._extract_domain(indicator_value)
        
        try:
            # Wrap synchronous network call in to_thread
            cert_info = await asyncio.to_thread(self._fetch_cert_info, hostname)

            return EnrichmentResult(
                indicator_id=indicator_id,
                source_name=self.get_source_name(),
                evidence_type=self.get_evidence_type(),
                raw_payload=cert_info,
                confidence_delta=12.0, # From Agent.md section 11.1
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
