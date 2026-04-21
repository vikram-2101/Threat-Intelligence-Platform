import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.evidence import Evidence
from app.models.source import Source
from app.services.enrichment.base import EnrichmentResult

logger = structlog.get_logger()

class EvidenceBuilder:
    """
    Service responsible for persisting enrichment results as evidence records.
    """

    @staticmethod
    async def save_enrichment_result(db: AsyncSession, result: EnrichmentResult) -> Evidence:
        """
        Converts an EnrichmentResult into an Evidence DB record and persists it.
        Only successful results are persisted.
        """
        if not result.success:
            logger.warning(
                "enrichment_failed_skipping_evidence",
                indicator_id=str(result.indicator_id),
                enricher=result.source_name,
                error=result.error_message
            )
            return None

        # 1. Resolve source_id from name
        source_id = None
        source_query = await db.execute(
            select(Source.id).where(Source.name == result.source_name)
        )
        source_id = source_query.scalar_one_or_none()
        
        if not source_id:
            logger.warning(
                "enrichment_source_not_found",
                source_name=result.source_name,
                indicator_id=str(result.indicator_id),
                action="persisting_with_null_source"
            )

        # 2. Create Evidence row
        evidence = Evidence(
            indicator_id=result.indicator_id,
            source_id=source_id,
            evidence_type=result.evidence_type,
            timestamp=result.timestamp,
            confidence_delta=result.confidence_delta,
            raw_payload=result.raw_payload,
            reversible=False, # Default for now
        )

        db.add(evidence)
        # Note: We don't commit here. The caller (worker) should handle the transaction.
        return evidence
