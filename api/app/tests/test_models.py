"""Tests for database models."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models.agency import Agency
from app.models.user import User, UserRole

# Use SQLite for fast unit tests; PostgreSQL parity tested via Docker
TEST_DB_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh test database session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_agency_create(session: AsyncSession) -> None:
    """Agency persists with auto-generated id and timestamps."""
    agency = Agency(name="Test Agency", slug="test-agency")
    session.add(agency)
    await session.commit()
    await session.refresh(agency)

    assert agency.id is not None
    assert isinstance(agency.id, uuid.UUID)
    assert agency.name == "Test Agency"
    assert agency.slug == "test-agency"
    assert agency.is_active is True
    assert agency.created_at is not None
    assert agency.updated_at is not None


@pytest.mark.asyncio
async def test_user_create_with_agency(session: AsyncSession) -> None:
    """GIVEN an agency WHEN creating a User with agency_id THEN user is linked to agency."""
    agency = Agency(name="Test Agency", slug="test-agency")
    session.add(agency)
    await session.commit()
    await session.refresh(agency)

    user = User(
        email="test@test.com",
        first_name="Test",
        last_name="User",
        role=UserRole.CAREGIVER,
        agency_id=agency.id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert user.id is not None
    assert user.email == "test@test.com"
    assert user.role == UserRole.CAREGIVER
    assert user.agency_id == agency.id


@pytest.mark.asyncio
async def test_super_admin_no_agency(session: AsyncSession) -> None:
    """GIVEN a super_admin WHEN agency_id is None THEN user is valid."""
    user = User(
        email="super@test.com",
        first_name="Super",
        last_name="Admin",
        role=UserRole.SUPER_ADMIN,
        agency_id=None,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert user.agency_id is None
    assert user.role == UserRole.SUPER_ADMIN


@pytest.mark.asyncio
async def test_user_query(session: AsyncSession) -> None:
    """GIVEN users in DB WHEN querying THEN returns all users."""
    agency = Agency(name="Test", slug="test")
    session.add(agency)
    await session.commit()
    await session.refresh(agency)

    for i in range(3):
        session.add(
            User(
                email=f"user{i}@test.com",
                first_name=f"User{i}",
                last_name="Test",
                agency_id=agency.id,
            )
        )
    await session.commit()

    result = await session.execute(text("SELECT COUNT(*) FROM users"))
    count = result.scalar()
    assert count == 3


@pytest.mark.asyncio
async def test_role_enum_values() -> None:
    """GIVEN UserRole enum WHEN checking values THEN hierarchy is correct."""
    roles = list(UserRole)
    assert UserRole.SUPER_ADMIN in roles
    assert UserRole.AGENCY_ADMIN in roles
    assert UserRole.CARE_MANAGER in roles
    assert UserRole.CAREGIVER in roles
    assert UserRole.FAMILY in roles
