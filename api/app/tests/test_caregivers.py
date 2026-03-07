"""Tests for caregiver profile management."""

import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, CaregiverProfile, User  # noqa: F401
from app.models.user import UserRole
from app.schemas.caregiver import (
    CaregiverProfileCreate,
    CaregiverProfileResponse,
    CaregiverProfileUpdate,
)
from app.services.caregiver import CaregiverService

TEST_DB_URL = "sqlite+aiosqlite:///./test_caregivers.db"

AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh test database session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        agency = Agency(id=AGENCY_ID, name="Test Agency", slug="test-agency")
        s.add(agency)
        await s.commit()
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


async def _create_caregiver_user(session: AsyncSession, email: str) -> User:
    """Helper to create a caregiver user."""
    user = User(
        email=email,
        first_name="Test",
        last_name="Caregiver",
        role=UserRole.CAREGIVER,
        agency_id=AGENCY_ID,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


# --- Schema tests ---


@pytest.mark.asyncio
async def test_profile_create_schema() -> None:
    """CaregiverProfileCreate schema accepts valid data."""
    data = CaregiverProfileCreate(
        user_id=uuid.uuid4(),
        hourly_rate=Decimal("25.00"),
        skills=["CPR", "First Aid"],
    )
    assert data.hourly_rate == Decimal("25.00")
    assert data.skills == ["CPR", "First Aid"]


@pytest.mark.asyncio
async def test_profile_response_from_model() -> None:
    """CaregiverProfileResponse validates from model."""
    profile = CaregiverProfile(
        user_id=uuid.uuid4(),
        agency_id=AGENCY_ID,
        hourly_rate=Decimal("30.00"),
    )
    resp = CaregiverProfileResponse.model_validate(profile)
    assert resp.hourly_rate == Decimal("30.00")


# --- Service tests ---


@pytest.mark.asyncio
async def test_service_create_profile(session: AsyncSession) -> None:
    """CaregiverService.create_profile persists a new profile."""
    user = await _create_caregiver_user(session, "cg1@test.com")
    service = CaregiverService(session)
    data = CaregiverProfileCreate(
        user_id=user.id,
        bio="Experienced caregiver",
        hourly_rate=Decimal("25.00"),
        overtime_rate=Decimal("37.50"),
        skills=["CPR", "Wound Care"],
    )
    profile = await service.create_profile(data, agency_id=AGENCY_ID)
    await session.commit()

    assert profile.id is not None
    assert profile.user_id == user.id
    assert profile.hourly_rate == Decimal("25.00")
    assert profile.skills == ["CPR", "Wound Care"]


@pytest.mark.asyncio
async def test_service_update_profile(session: AsyncSession) -> None:
    """CaregiverService.update_profile modifies fields."""
    user = await _create_caregiver_user(session, "cg2@test.com")
    service = CaregiverService(session)
    profile = await service.create_profile(
        CaregiverProfileCreate(user_id=user.id, hourly_rate=Decimal("20.00")),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    updated = await service.update_profile(
        profile.id,
        CaregiverProfileUpdate(hourly_rate=Decimal("30.00"), bio="Updated"),
    )
    await session.commit()

    assert updated is not None
    assert updated.hourly_rate == Decimal("30.00")
    assert updated.bio == "Updated"


@pytest.mark.asyncio
async def test_service_list_profiles(session: AsyncSession) -> None:
    """CaregiverService.list_profiles returns paginated results."""
    service = CaregiverService(session)
    for i in range(4):
        user = await _create_caregiver_user(session, f"cg{i}@list.com")
        await service.create_profile(
            CaregiverProfileCreate(user_id=user.id),
            agency_id=AGENCY_ID,
        )
    await session.commit()

    profiles, total = await service.list_profiles(page=1, size=2)
    assert total == 4
    assert len(profiles) == 2


@pytest.mark.asyncio
async def test_service_get_by_user_id(session: AsyncSession) -> None:
    """CaregiverService.get_by_user_id returns profile for a user."""
    user = await _create_caregiver_user(session, "cg_lookup@test.com")
    service = CaregiverService(session)
    await service.create_profile(
        CaregiverProfileCreate(user_id=user.id, bio="Findable"),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    found = await service.get_by_user_id(user.id)
    assert found is not None
    assert found.bio == "Findable"
