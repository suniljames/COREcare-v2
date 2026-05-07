"""Multi-tenancy support: tenant context middleware and helpers.

PostgreSQL RLS policies read `app.current_tenant_id` from the session.
This module provides the dependency that sets that variable per-request.
"""

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_tenant_context(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Set the tenant context for the current database transaction.

    Calls SET LOCAL so the variable is scoped to the current transaction
    and automatically cleared when the transaction ends.
    """
    await session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))


async def clear_tenant_context(session: AsyncSession) -> None:
    """Clear tenant context (super-admin mode — RLS allows all rows)."""
    await session.execute(text("SET LOCAL app.current_tenant_id = ''"))


async def get_tenant_context(session: AsyncSession) -> uuid.UUID | None:
    """Return the current tenant_id, or None if unset (super-admin) / unavailable.

    On PostgreSQL this reads the SET LOCAL'd app.current_tenant_id. On SQLite
    or other backends without current_setting(), returns None.
    """
    try:
        result = await session.execute(
            text("SELECT current_setting('app.current_tenant_id', true)")
        )
        raw = result.scalar()
    except Exception:
        return None
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except (ValueError, AttributeError):
        return None
