import math
import uuid
import structlog
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.indicator import Indicator, IndicatorStatus
from app.models.evidence import Evidence, EvidenceType
from app.models.source import Source, TrustTier
from app.models.confidence_snapshot import ConfidenceSnapshot
from app.core.redis import redis_manager

logger = structlog.get_logger()

TRUST_MULTIPLIERS = {
    TrustTier.LOW: 0.3,
    TrustTier.MEDIUM: 0.6,
    TrustTier.HIGH: 1.0
}

DECAY_LAMBDA = 0.05

class ScoringService:
    @classmethod
    async def recalculate_score(cls, db: AsyncSession, indicator_id: uuid.UUID | str, trigger: str = "automated") -> float:
        """
        Calculates and updates the confidence score for an indicator based on evidence and decay.
        """
        # Ensure we are working with a UUID object for consistent DB lookups
        if isinstance(indicator_id, str):
            try:
                indicator_id = uuid.UUID(indicator_id)
            except ValueError:
                logger.error("invalid_indicator_id_format", indicator_id=indicator_id)
                return 0.0

        # 1. Fetch indicator and its evidence (joining with source for trust tiers)
        indicator_q = await db.scalar(select(Indicator).where(Indicator.id == indicator_id))
        if not indicator_q:
            logger.error("indicator_not_found_for_scoring", indicator_id=str(indicator_id))
            return 0.0

        evidence_q = await db.execute(
            select(Evidence, Source.name, Source.trust_tier)
            .where(Evidence.indicator_id == indicator_id)
            .outerjoin(Source, Evidence.source_id == Source.id)
        )
        evidence_records = evidence_q.all()

        # 2. Base score (starting from 0, or could be initialized to a source default)
        weighted_sum = 0.0
        enrichment_types = set()
        correlation_sum = 0.0
        analyst_sum = 0.0
        factors = []

        for evidence, source_name, trust_tier in evidence_records:
            if evidence.reversed:
                continue  # reversed evidence contributes nothing

            current_delta = 0.0

            # 1a. Real enrichment evidence — weighted by source trust tier
            if evidence.evidence_type in (
                EvidenceType.WHOIS,
                EvidenceType.PASSIVE_DNS,
                EvidenceType.ASN,
                EvidenceType.SSL_CERT,
            ):
                multiplier = TRUST_MULTIPLIERS.get(trust_tier, 0.5)
                current_delta = float(evidence.confidence_delta) * multiplier
                weighted_sum += current_delta
                enrichment_types.add(evidence.evidence_type)

            # 1b. Correlation bonuses — added directly (no trust multiplier)
            elif evidence.evidence_type in (
                EvidenceType.CORRELATION_INFRA,
                EvidenceType.CORRELATION_SSL,
                EvidenceType.MULTI_SOURCE_SIGHTING,
            ):
                current_delta = float(evidence.confidence_delta)
                correlation_sum += current_delta

            # 1c. Analyst adjustments — delta comes from analyst input
            elif evidence.evidence_type == EvidenceType.ANALYST_ADJUSTMENT:
                current_delta = float(evidence.confidence_delta)
                analyst_sum += current_delta

            if current_delta != 0:
                factors.append({
                    "type": evidence.evidence_type,
                    "delta": round(current_delta, 2),
                    "evidence_id": str(evidence.id),
                    "source_name": source_name or "system",
                })

        # 3. Enrichment depth bonus — distinct enrichment types × 2
        # Excludes correlation/analyst types (per Agent.md Section 6 formula)
        depth_bonus = len(enrichment_types) * 2.0
        if depth_bonus > 0:
            factors.append({
                "type": "ENRICHMENT_DEPTH_BONUS",
                "delta": depth_bonus,
                "evidence_id": None,
                "source_name": "system",
            })

        # 4. Exponential time decay (λ = 0.05 per Agent.md)
        now = datetime.now(timezone.utc)
        days_elapsed = (now - indicator_q.last_seen).total_seconds() / (24 * 3600)
        decay_factor = math.exp(-DECAY_LAMBDA * days_elapsed)

        # 5. Final score — Agent.md formula exactly:
        #    final_score = clamp((weighted_sum + depth_bonus + correlation_sum + analyst_sum) × decay, 0, 100)
        # Note: file hashes (MD5/SHA1/SHA256) have no enrichers (ENRICHER_TYPE_MAP maps them to []).
        # That means zero evidence rows, so weighted_sum=0, depth_bonus=0 — score is naturally 0.
        # No explicit Verification Gate is needed; the math handles it.
        subtotal = weighted_sum + depth_bonus + correlation_sum + analyst_sum
        final_score = max(0.0, min(100.0, subtotal * decay_factor))

        old_score = float(indicator_q.current_confidence)
        indicator_q.current_confidence = final_score
        
        # 6. Immutable Snapshot with granular rationale
        # Requirement 2.7: {score, factors, decay_factor, days_elapsed, calculated_at}
        rationale = {
            "score": round(final_score, 2),
            "factors": factors,
            "decay_factor": round(decay_factor, 4),
            "days_elapsed": round(days_elapsed, 4),
            "calculated_at": now.isoformat(),
            "weighted_sum": round(subtotal, 2)
        }
        
        snapshot = ConfidenceSnapshot(
            indicator_id=indicator_id,
            score=final_score,
            trigger=trigger,
            reason_summary=rationale
        )
        db.add(snapshot)

        # 7. Notify if significant change (> 5 points)
        if abs(final_score - old_score) > 5:
            await redis_manager.publish_event(
                "score.updated",
                {
                    "indicator_id": str(indicator_id),
                    "old_score": old_score,
                    "new_score": final_score
                }
            )

        # 8. Auto-expire/lifecycle check
        # Score < 10 and TTL elapsed
        if final_score < 10.0 and indicator_q.ttl and indicator_q.ttl < now:
            indicator_q.status = IndicatorStatus.EXPIRED
            logger.info("indicator_expired", indicator_id=str(indicator_id), score=final_score, ttl=indicator_q.ttl.isoformat())

        return final_score
