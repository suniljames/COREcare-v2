"""Audit logging service for HIPAA compliance."""

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditEvent

logger = structlog.get_logger()


class AuditService:
    """Append-only audit event writer."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        *,
        action: AuditAction,
        resource_type: str,
        resource_id: str = "",
        user_id: uuid.UUID | None = None,
        agency_id: uuid.UUID | None = None,
        is_phi_access: bool = False,
        ip_address: str = "",
        user_agent: str = "",
        details: str = "",
        changes: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Create an audit event. All parameters are keyword-only for clarity."""
        event = AuditEvent(
            user_id=user_id,
            agency_id=agency_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            is_phi_access=is_phi_access,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            changes=changes,
        )
        self.session.add(event)
        await self.session.flush()
        await logger.ainfo(
            "audit_event",
            action=action.value,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=str(user_id) if user_id else None,
            is_phi=is_phi_access,
        )
        return event
