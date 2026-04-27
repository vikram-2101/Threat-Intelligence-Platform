import uuid
import structlog
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.evidence import Evidence, EvidenceType
from app.core.redis import redis_manager

logger = structlog.get_logger()

class CorrelationService:
    """
    Implements the Correlation Engine checks to link indicators and reward consistency.
    """

    @classmethod
    async def run_all_checks(cls, db: AsyncSession, indicator_id: uuid.UUID) -> None:
        """
        Runs the 3 standard correlation checks for the given indicator.
        """
        # 1. Infrastructure Reuse (ASN based)
        await cls.check_infrastructure_reuse(db, indicator_id)
        
        # 2. SSL Certificate Reuse
        await cls.check_ssl_reuse(db, indicator_id)
        
        # 3. Multi-Source Sighting
        await cls.check_multi_source_sighting(db, indicator_id)
        
        # Notify about correlation updates
        await redis_manager.publish_event(
            "correlation.created",
            {"indicator_id": str(indicator_id)}
        )

    @classmethod
    async def check_infrastructure_reuse(cls, db: AsyncSession, indicator_id: uuid.UUID) -> None:
        """
        SELECT indicators sharing same ASN, INSERT CORRELATION_INFRA evidence.
        Delta: +5.0, reversible: True.
        """
        # Get current ASN
        asn_q = await db.execute(
            select(Evidence.raw_payload).where(
                Evidence.indicator_id == indicator_id,
                Evidence.evidence_type == EvidenceType.ASN
            )
        )
        current_asn_data = asn_q.scalar_one_or_none()
        if not current_asn_data or not current_asn_data.get("asn"):
            return

        current_asn = current_asn_data.get("asn")

        # Find other indicators with same ASN
        others_q = await db.execute(
            select(Evidence.indicator_id).where(
                Evidence.indicator_id != indicator_id,
                Evidence.evidence_type == EvidenceType.ASN,
                Evidence.raw_payload.op('->>')('asn') == current_asn
            ).limit(1)
        )
        
        if others_q.scalar_one_or_none():
            # Check if we already have this correlation
            existing_q = await db.execute(
                select(Evidence.id).where(
                    Evidence.indicator_id == indicator_id,
                    Evidence.evidence_type == EvidenceType.CORRELATION_INFRA
                )
            )
            if not existing_q.scalar_one_or_none():
                logger.info("infrastructure_reuse_detected", indicator_id=str(indicator_id), asn=current_asn)
                db.add(Evidence(
                    indicator_id=indicator_id,
                    evidence_type=EvidenceType.CORRELATION_INFRA,
                    confidence_delta=5.0,
                    raw_payload={"asn": current_asn, "reason": "Shared infrastructure ASN detected"},
                    reversible=True
                ))

    @classmethod
    async def check_ssl_reuse(cls, db: AsyncSession, indicator_id: uuid.UUID) -> None:
        """
        Match cert fingerprint, +8 delta.
        """
        # Get current SSL Fingerprint
        ssl_q = await db.execute(
            select(Evidence.raw_payload).where(
                Evidence.indicator_id == indicator_id,
                Evidence.evidence_type == EvidenceType.SSL_CERT
            )
        )
        current_ssl_data = ssl_q.scalar_one_or_none()
        if not current_ssl_data or not current_ssl_data.get("fingerprint"):
            return

        fingerprint = current_ssl_data.get("fingerprint")

        # Find other indicators with same fingerprint
        others_q = await db.execute(
            select(Evidence.indicator_id).where(
                Evidence.indicator_id != indicator_id,
                Evidence.evidence_type == EvidenceType.SSL_CERT,
                Evidence.raw_payload.op('->>')('fingerprint') == fingerprint
            ).limit(1)
        )
        
        if others_q.scalar_one_or_none():
            existing_q = await db.execute(
                select(Evidence.id).where(
                    Evidence.indicator_id == indicator_id,
                    Evidence.evidence_type == EvidenceType.CORRELATION_SSL
                )
            )
            if not existing_q.scalar_one_or_none():
                logger.info("ssl_reuse_detected", indicator_id=str(indicator_id), fingerprint=fingerprint)
                db.add(Evidence(
                    indicator_id=indicator_id,
                    evidence_type=EvidenceType.CORRELATION_SSL,
                    confidence_delta=8.0,
                    raw_payload={"fingerprint": fingerprint, "reason": "Common SSL certificate found"},
                    reversible=True
                ))

    @classmethod
    async def check_multi_source_sighting(cls, db: AsyncSession, indicator_id: uuid.UUID) -> None:
        """
        Count DISTINCT source_ids, delta = source_count × 3.
        Per Agent.md §4.4 — append-only: reverses any previous MULTI_SOURCE_SIGHTING
        evidence row and inserts a fresh one with the updated delta.
        """
        sources_q = await db.execute(
            select(func.count(Evidence.source_id.distinct())).where(
                Evidence.indicator_id == indicator_id,
                Evidence.source_id.isnot(None)
            )
        )
        source_count = sources_q.scalar_one() or 0

        if source_count > 1:
            delta = source_count * 3.0

            # Reverse any existing MULTI_SOURCE_SIGHTING rows (append-only rule)
            existing_q = await db.execute(
                select(Evidence).where(
                    Evidence.indicator_id == indicator_id,
                    Evidence.evidence_type == EvidenceType.MULTI_SOURCE_SIGHTING,
                    Evidence.reversed == False,
                )
            )
            existing_rows = existing_q.scalars().all()
            now = datetime.now(timezone.utc)
            for row in existing_rows:
                row.reversed = True
                row.reversed_at = now

            logger.info(
                "multi_source_sighting_recorded",
                indicator_id=str(indicator_id),
                count=source_count,
                delta=delta,
            )
            db.add(Evidence(
                indicator_id=indicator_id,
                evidence_type=EvidenceType.MULTI_SOURCE_SIGHTING,
                confidence_delta=delta,
                raw_payload={"source_count": source_count},
                reversible=False,
            ))

