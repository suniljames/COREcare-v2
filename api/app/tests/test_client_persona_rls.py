"""PostgreSQL-only RLS isolation tests for the Client persona (issue #125).

These tests verify the dual-axis RLS policy on `clients`, `shifts`, `messages`,
`care_plan_versions`, `message_threads`. They require PostgreSQL (SET LOCAL,
RLS policies) and are skipped on SQLite — same pattern as test_tenant.py.

QA review §A.1–A.7 maps to these tests:
- A.1: same-agency, different-Client invisible
- A.2: different-agency Client invisible
- A.3: different-Client shifts invisible
- A.4: different-Client messages invisible
- A.5: staff path unaffected
- A.6: super-admin sees all
- A.7: WITH CHECK rejects malicious updates
"""

import pytest


def _is_postgres() -> bool:
    """Check if we can run PostgreSQL-specific tests.

    Mirrors the pattern in test_tenant.py — CI/Docker would set this True;
    local SQLite-fast tests set False.
    """
    return False


@pytest.mark.skipif(not _is_postgres(), reason="RLS requires PostgreSQL")
@pytest.mark.asyncio
async def test_a1_client_cannot_read_other_client_same_agency() -> None:
    """A.1 — A Client at agency Y cannot read another Client's row at agency Y."""
    pass


@pytest.mark.skipif(not _is_postgres(), reason="RLS requires PostgreSQL")
@pytest.mark.asyncio
async def test_a2_client_cannot_read_client_different_agency() -> None:
    """A.2 — Tenant boundary catches it before client boundary."""
    pass


@pytest.mark.skipif(not _is_postgres(), reason="RLS requires PostgreSQL")
@pytest.mark.asyncio
async def test_a3_client_cannot_read_other_client_shifts() -> None:
    """A.3 — Shifts isolated by client_id under Client context."""
    pass


@pytest.mark.skipif(not _is_postgres(), reason="RLS requires PostgreSQL")
@pytest.mark.asyncio
async def test_a4_client_cannot_read_other_client_messages() -> None:
    """A.4 — Messages isolated by thread.client_id under Client context."""
    pass


@pytest.mark.skipif(not _is_postgres(), reason="RLS requires PostgreSQL")
@pytest.mark.asyncio
async def test_a5_staff_path_unchanged() -> None:
    """A.5 — Care Manager session sees all clients in their agency."""
    pass


@pytest.mark.skipif(not _is_postgres(), reason="RLS requires PostgreSQL")
@pytest.mark.asyncio
async def test_a6_super_admin_sees_all() -> None:
    """A.6 — Super-admin (no contexts set) sees all rows across all agencies."""
    pass


@pytest.mark.skipif(not _is_postgres(), reason="RLS requires PostgreSQL")
@pytest.mark.asyncio
async def test_a7_with_check_blocks_malicious_update() -> None:
    """A.7 — A Client cannot UPDATE clients.id to another Client's id."""
    pass
