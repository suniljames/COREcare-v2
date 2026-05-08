"""End-to-end migration + seed regression tests (issue #240).

Spins up an ephemeral Postgres container, runs `alembic upgrade head` against
the empty DB, runs `app.seed.seed()`, and asserts:

- T1 — fresh-DB migrate + seed succeeds with the expected row counts
- T2 — `SQLModel.metadata` matches migration head (drift guard)
- T3 — RLS policy parity matches the post-0008 design state
- T4 — `messages.recipient_id` is nullable

Tests are marked `integration`. Skipped when Docker is unavailable.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import AsyncGenerator, Iterator
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

try:
    from testcontainers.postgres import PostgresContainer  # type: ignore[import-untyped]

    _TESTCONTAINERS_AVAILABLE = True
except ImportError:  # pragma: no cover — testcontainers may be skipped in CI
    _TESTCONTAINERS_AVAILABLE = False

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _TESTCONTAINERS_AVAILABLE,
        reason="testcontainers[postgres] not installed",
    ),
]


API_DIR = Path(__file__).resolve().parent.parent.parent  # api/
REPO_ROOT = API_DIR.parent


def _docker_available() -> bool:
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5, check=False)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.fixture(scope="module")
def postgres_container() -> Iterator[str]:
    """Boot an ephemeral Postgres 16 container, return its asyncpg URL."""
    if not _docker_available():
        pytest.skip("Docker daemon not reachable")

    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        url = pg.get_connection_url()
        yield url


@pytest.fixture(scope="module")
def migrated_database_url(postgres_container: str) -> str:
    """Run `alembic upgrade head` against the empty container DB.

    Returns the asyncpg URL once the schema is at head. T1 + T2 + T3 + T4 share
    this fixture so we pay the migration cost once per module.
    """
    env = os.environ.copy()
    env["DATABASE_URL"] = postgres_container
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=API_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"alembic upgrade head failed (rc={result.returncode})\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return postgres_container


@pytest.fixture
async def session(migrated_database_url: str) -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(migrated_database_url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


# ---------------------------------------------------------------------------
# T1 — fresh-DB migrate + seed
# ---------------------------------------------------------------------------


async def test_t1_seed_against_migrated_db(migrated_database_url: str) -> None:
    """`make api-seed` semantics: seed.seed() succeeds against migrated schema.

    Asserts the expected row counts after seed, locking the contract from
    api/app/seed.py (1 agency, 7 users including the demo agency).
    """
    env = os.environ.copy()
    env["DATABASE_URL"] = migrated_database_url
    result = subprocess.run(
        [sys.executable, "-m", "app.seed"],
        cwd=API_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"seed failed (rc={result.returncode})\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )

    engine = create_async_engine(migrated_database_url)
    async with engine.connect() as conn:
        # Seed bypasses RLS via empty tenant GUC; mirror that for assertions.
        await conn.execute(text("SET app.current_tenant_id = ''"))
        agency_count = (await conn.execute(text("SELECT count(*) FROM agencies"))).scalar()
        user_count = (await conn.execute(text("SELECT count(*) FROM users"))).scalar()
        demo = (
            await conn.execute(text("SELECT id FROM agencies WHERE slug = 'bay-area-elite'"))
        ).scalar()
    await engine.dispose()

    assert agency_count == 1, f"expected 1 seeded agency, got {agency_count}"
    assert user_count == 7, f"expected 7 seeded users, got {user_count}"
    assert demo is not None, "demo agency 'bay-area-elite' missing after seed"


# ---------------------------------------------------------------------------
# T2 — schema drift guard
# ---------------------------------------------------------------------------


async def test_t2_no_schema_drift_after_migration(migrated_database_url: str) -> None:
    """After `alembic upgrade head`, SQLModel.metadata must match the DB.

    Uses `alembic check` (Alembic 1.9+). Falls back to autogenerate-dry-run
    if `alembic check` is unavailable.
    """
    env = os.environ.copy()
    env["DATABASE_URL"] = migrated_database_url
    result = subprocess.run(
        ["uv", "run", "alembic", "check"],
        cwd=API_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "alembic check detected drift between SQLModel.metadata and migration head.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# T3 — RLS policy parity (post-0008 state)
# ---------------------------------------------------------------------------


# Single-axis tenant_isolation tables (post-0001 + 0002 design state).
SINGLE_AXIS_TABLES = {"users", "email_events"}

# Dual-axis tenant_and_client_isolation tables (post-0008 design state).
DUAL_AXIS_TABLES = {
    "clients",
    "shifts",
    "messages",
    "care_plan_versions",
    "message_threads",
}


async def test_t3_rls_policies_match_post_0008_state(session: AsyncSession) -> None:
    rows = (
        await session.execute(
            text("SELECT tablename, policyname FROM pg_policies WHERE schemaname='public'")
        )
    ).all()
    actual = {(t, p) for (t, p) in rows}

    expected = {
        *((t, "tenant_isolation") for t in SINGLE_AXIS_TABLES),
        *((t, "tenant_and_client_isolation") for t in DUAL_AXIS_TABLES),
    }
    assert actual == expected, (
        f"RLS policy set drift.\n  unexpected: {actual - expected}\n"
        f"  missing:    {expected - actual}"
    )


async def test_t3_rls_force_enabled_on_all_protected_tables(session: AsyncSession) -> None:
    """Every RLS-protected table must have rowsecurity AND forcerowsecurity."""
    protected = SINGLE_AXIS_TABLES | DUAL_AXIS_TABLES
    rows = (
        await session.execute(
            text(
                "SELECT relname, relrowsecurity, relforcerowsecurity "
                "FROM pg_class WHERE relname = ANY(:names)"
            ),
            {"names": list(protected)},
        )
    ).all()
    by_name = {r[0]: (r[1], r[2]) for r in rows}
    for table in protected:
        rls, force = by_name.get(table, (None, None))
        assert rls is True, f"{table}: ENABLE ROW LEVEL SECURITY missing"
        assert force is True, f"{table}: FORCE ROW LEVEL SECURITY missing"


# ---------------------------------------------------------------------------
# T4 — messages.recipient_id nullability (preserves 0009 correctness)
# ---------------------------------------------------------------------------


async def test_t4_messages_recipient_id_nullable(session: AsyncSession) -> None:
    is_nullable = (
        await session.execute(
            text(
                "SELECT NOT attnotnull "
                "FROM pg_attribute "
                "WHERE attrelid = 'messages'::regclass "
                "AND attname = 'recipient_id'"
            )
        )
    ).scalar()
    assert is_nullable is True, "messages.recipient_id must be nullable (post-0009)"
