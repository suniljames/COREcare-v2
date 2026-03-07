"""Tests for shift scheduling."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, Client, Shift, User  # noqa: F401
from app.models.shift import ShiftStatus
from app.models.user import UserRole
from app.schemas.shift import ShiftCreate, ShiftUpdate
from app.services.shift import ShiftService

TEST_DB_URL = "sqlite+aiosqlite:///./test_shifts.db"

AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
NOW = datetime.now(UTC).replace(microsecond=0)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh test database session with agency, client, caregiver."""
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


async def _make_client(session: AsyncSession) -> Client:
    client = Client(first_name="Test", last_name="Client", agency_id=AGENCY_ID)
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client


async def _make_caregiver(session: AsyncSession, email: str) -> User:
    user = User(
        email=email,
        first_name="CG",
        last_name="Test",
        role=UserRole.CAREGIVER,
        agency_id=AGENCY_ID,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


# --- Service tests ---


@pytest.mark.asyncio
async def test_create_shift(session: AsyncSession) -> None:
    """ShiftService.create_shift persists a new shift."""
    client = await _make_client(session)
    cg = await _make_caregiver(session, "cg@test.com")
    service = ShiftService(session)

    shift = await service.create_shift(
        ShiftCreate(
            client_id=client.id,
            caregiver_id=cg.id,
            start_time=NOW,
            end_time=NOW + timedelta(hours=4),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert shift.id is not None
    assert shift.status == ShiftStatus.ASSIGNED
    assert shift.caregiver_id == cg.id


@pytest.mark.asyncio
async def test_create_open_shift(session: AsyncSession) -> None:
    """Shift without caregiver starts as OPEN."""
    client = await _make_client(session)
    service = ShiftService(session)

    shift = await service.create_shift(
        ShiftCreate(
            client_id=client.id,
            start_time=NOW,
            end_time=NOW + timedelta(hours=4),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert shift.status == ShiftStatus.OPEN
    assert shift.caregiver_id is None


@pytest.mark.asyncio
async def test_conflict_detection(session: AsyncSession) -> None:
    """Creating overlapping shifts for same caregiver raises 409."""
    client = await _make_client(session)
    cg = await _make_caregiver(session, "conflict@test.com")
    service = ShiftService(session)

    await service.create_shift(
        ShiftCreate(
            client_id=client.id,
            caregiver_id=cg.id,
            start_time=NOW,
            end_time=NOW + timedelta(hours=4),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await service.create_shift(
            ShiftCreate(
                client_id=client.id,
                caregiver_id=cg.id,
                start_time=NOW + timedelta(hours=2),
                end_time=NOW + timedelta(hours=6),
            ),
            agency_id=AGENCY_ID,
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_list_shifts_date_range(session: AsyncSession) -> None:
    """List shifts filtered by date range."""
    client = await _make_client(session)
    service = ShiftService(session)

    # Create shifts on different days
    for i in range(3):
        await service.create_shift(
            ShiftCreate(
                client_id=client.id,
                start_time=NOW + timedelta(days=i),
                end_time=NOW + timedelta(days=i, hours=4),
            ),
            agency_id=AGENCY_ID,
        )
    await session.commit()

    # Filter to first 2 days
    shifts, total = await service.list_shifts(
        start_after=NOW,
        start_before=NOW + timedelta(days=1, hours=23),
    )
    assert total == 2


@pytest.mark.asyncio
async def test_update_shift_status(session: AsyncSession) -> None:
    """ShiftService.update_shift can change status."""
    client = await _make_client(session)
    cg = await _make_caregiver(session, "status@test.com")
    service = ShiftService(session)

    shift = await service.create_shift(
        ShiftCreate(
            client_id=client.id,
            caregiver_id=cg.id,
            start_time=NOW,
            end_time=NOW + timedelta(hours=4),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    updated = await service.update_shift(shift.id, ShiftUpdate(status=ShiftStatus.IN_PROGRESS))
    await session.commit()

    assert updated is not None
    assert updated.status == ShiftStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_cancel_shift(session: AsyncSession) -> None:
    """ShiftService.cancel_shift sets status=cancelled."""
    client = await _make_client(session)
    service = ShiftService(session)

    shift = await service.create_shift(
        ShiftCreate(
            client_id=client.id,
            start_time=NOW,
            end_time=NOW + timedelta(hours=4),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    cancelled = await service.cancel_shift(shift.id)
    await session.commit()

    assert cancelled is not None
    assert cancelled.status == ShiftStatus.CANCELLED
