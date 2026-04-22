"""
Audit log service — writes structured rows to AUDIT_LOGS.

Every analyst action calls `AuditService.log()` before returning.
System-level actions pass user_id=None.

This is the single source of truth for audit writes — do not use db.add(AuditLog(...))
directly anywhere else in the codebase.
"""
import uuid
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


class AuditService:

    @staticmethod
    async def log(
        db: AsyncSession,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        details: dict,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """
        Insert one immutable audit row.

        Args:
            db:          Active async DB session (caller must commit).
            action:      Verb describing what happened, e.g. "analyst.note.added".
            entity_type: The ORM table name, e.g. "indicators".
            entity_id:   PK of the affected row.
            details:     Arbitrary JSON payload — include every field the analyst changed.
            user_id:     UUID of the acting user; None for system-generated events.
            ip_address:  Client IP extracted from Request object (optional).
        """
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )
        db.add(entry)
        return entry
