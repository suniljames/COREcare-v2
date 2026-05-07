"""Multi-tenancy support: tenant + Client context middleware and helpers.

PostgreSQL RLS policies read two session GUCs:
- `app.current_tenant_id` — agency-axis isolation (all personas).
- `app.current_client_id` — Client-persona row-level isolation (issue #125).

Three states (System Architect §2):
- Super-admin: both empty → RLS allows all rows.
- Staff: tenant set, client empty → tenant-scoped reads.
- Client: tenant + client both set → row-locked to one Client.

Order of operations matters: set tenant first, then client; clear client
first, then tenant. This module's helpers preserve that order.

SQLite has no RLS and no SET LOCAL syntax — these helpers are no-ops on
SQLite so service-layer tests can exercise application logic without a
PostgreSQL backend. Real RLS isolation is verified in PostgreSQL-only
tests (see test_client_persona_rls.py).
"""

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _is_postgres(session: AsyncSession) -> bool:
    """Whether the session's backend supports SET LOCAL + RLS."""
    return session.bind is not None and session.bind.dialect.name == "postgresql"


async def set_tenant_context(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Set the agency-axis tenant context for the current transaction."""
    if not _is_postgres(session):
        return
    await session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))


async def clear_tenant_context(session: AsyncSession) -> None:
    """Clear tenant context (super-admin mode — RLS allows all rows)."""
    if not _is_postgres(session):
        return
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


async def set_client_context(session: AsyncSession, client_id: uuid.UUID) -> None:
    """Set the Client-axis context for the Client persona.

    Caller must call set_tenant_context first; the dual-axis RLS policy
    requires both to be set together for the Client read path.
    """
    if not _is_postgres(session):
        return
    await session.execute(text(f"SET LOCAL app.current_client_id = '{client_id}'"))


async def clear_client_context(session: AsyncSession) -> None:
    """Clear Client-axis context. Caller should clear *before* clearing tenant."""
    if not _is_postgres(session):
        return
    await session.execute(text("SET LOCAL app.current_client_id = ''"))
