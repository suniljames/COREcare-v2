"""Tests for Client-persona RBAC behavior (issue #125).

Per System Architect §1: ROLE_HIERARCHY does NOT include CLIENT.
has_min_role(client, *) returns False — by design. Client-scoped routes use
require_client_self() instead of require_role().
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, Client, User  # noqa: F401
from app.models.user import UserRole
from app.rbac import has_min_role

TEST_DB_URL = "sqlite+aiosqlite:///./test_rbac_client.db"
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-00000000c001")


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        s.add(Agency(id=AGENCY_ID, name="Sunrise", slug="sunrise"))
        await s.commit()
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


# --- has_min_role: CLIENT is not in the hierarchy ---


def test_has_min_role_client_against_family_returns_false() -> None:
    """has_min_role(client, FAMILY) returns False — Client is not above Family."""
    assert has_min_role(UserRole.CLIENT, UserRole.FAMILY) is False


def test_has_min_role_client_against_caregiver_returns_false() -> None:
    assert has_min_role(UserRole.CLIENT, UserRole.CAREGIVER) is False


def test_has_min_role_client_against_super_admin_returns_false() -> None:
    assert has_min_role(UserRole.CLIENT, UserRole.SUPER_ADMIN) is False


def test_has_min_role_staff_unaffected_by_client() -> None:
    """Staff role hierarchy still works post-CLIENT addition."""
    assert has_min_role(UserRole.AGENCY_ADMIN, UserRole.CAREGIVER) is True
    assert has_min_role(UserRole.CAREGIVER, UserRole.AGENCY_ADMIN) is False


# --- require_client_self() dependency ---


@pytest.mark.asyncio
async def test_require_client_self_rejects_caregiver(session: AsyncSession) -> None:
    """A Caregiver hitting the dependency raises 403."""
    from app.rbac import require_client_self

    user = User(
        email="cg@test.com",
        first_name="Care",
        last_name="Giver",
        role=UserRole.CAREGIVER,
        agency_id=AGENCY_ID,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    dep = require_client_self()
    with pytest.raises(HTTPException) as exc_info:
        await dep(user=user, session=session)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_client_self_rejects_orphaned_client(
    session: AsyncSession,
) -> None:
    """A user with role=client but no Client.client_user_id row raises 403."""
    from app.rbac import require_client_self

    user = User(
        email="orphan@test.com",
        role=UserRole.CLIENT,
        agency_id=AGENCY_ID,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    dep = require_client_self()
    with pytest.raises(HTTPException) as exc_info:
        await dep(user=user, session=session)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_client_self_returns_linked_client(session: AsyncSession) -> None:
    """A user with role=client AND a linked Client returns the Client."""
    from app.rbac import require_client_self

    user = User(
        email="eleanor@test.com",
        role=UserRole.CLIENT,
        agency_id=AGENCY_ID,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    client = Client(
        first_name="Eleanor",
        last_name="X",
        agency_id=AGENCY_ID,
        client_user_id=user.id,
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)

    dep = require_client_self()
    result = await dep(user=user, session=session)
    # The dependency returns the Client row (so route handlers can use it)
    assert result.id == client.id
    assert result.client_user_id == user.id
