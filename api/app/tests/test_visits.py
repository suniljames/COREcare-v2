"""Tests for shift offers and visit tracking."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, Client, Shift, User, Visit  # noqa: F401
from app.models.shift import ShiftStatus
from app.models.user import UserRole
from app.models.visit import ShiftOfferStatus
from app.schemas.visit import ClockInRequest, ClockOutRequest, ShiftOfferCreate
from app.services.visit import VisitService

TEST_DB_URL = "sqlite+aiosqlite:///./test_visits.db"
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
NOW = datetime.now(UTC).replace(microsecond=0)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
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


async def _setup(session: AsyncSession) -> tuple[Client, User, Shift]:
    """Create test client, caregiver, and shift."""
    client = Client(first_name="Test", last_name="Client", agency_id=AGENCY_ID)
    cg = User(
        email="cg@test.com",
        first_name="CG",
        last_name="Test",
        role=UserRole.CAREGIVER,
        agency_id=AGENCY_ID,
    )
    session.add_all([client, cg])
    await session.commit()
    await session.refresh(client)
    await session.refresh(cg)

    shift = Shift(
        client_id=client.id,
        start_time=NOW,
        end_time=NOW + timedelta(hours=4),
        status=ShiftStatus.OPEN,
        agency_id=AGENCY_ID,
    )
    session.add(shift)
    await session.commit()
    await session.refresh(shift)
    return client, cg, shift


# --- Shift Offer tests ---


@pytest.mark.asyncio
async def test_create_offer(session: AsyncSession) -> None:
    """VisitService.create_offer creates a pending offer."""
    _, cg, shift = await _setup(session)
    service = VisitService(session)

    offer = await service.create_offer(
        ShiftOfferCreate(shift_id=shift.id, caregiver_id=cg.id),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert offer.status == ShiftOfferStatus.PENDING
    assert offer.shift_id == shift.id


@pytest.mark.asyncio
async def test_accept_offer(session: AsyncSession) -> None:
    """Accepting offer assigns caregiver to shift."""
    _, cg, shift = await _setup(session)
    service = VisitService(session)

    offer = await service.create_offer(
        ShiftOfferCreate(shift_id=shift.id, caregiver_id=cg.id),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    accepted = await service.accept_offer(offer.id)
    await session.commit()

    assert accepted.status == ShiftOfferStatus.ACCEPTED
    assert accepted.responded_at is not None


@pytest.mark.asyncio
async def test_decline_offer(session: AsyncSession) -> None:
    """Declining offer updates status."""
    _, cg, shift = await _setup(session)
    service = VisitService(session)

    offer = await service.create_offer(
        ShiftOfferCreate(shift_id=shift.id, caregiver_id=cg.id),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    declined = await service.decline_offer(offer.id)
    await session.commit()

    assert declined.status == ShiftOfferStatus.DECLINED


# --- Visit clock-in/out tests ---


@pytest.mark.asyncio
async def test_clock_in(session: AsyncSession) -> None:
    """Clock-in creates a visit record."""
    _, cg, shift = await _setup(session)
    service = VisitService(session)

    visit = await service.clock_in(
        ClockInRequest(
            shift_id=shift.id,
            latitude=Decimal("37.7749295"),
            longitude=Decimal("-122.4194155"),
        ),
        caregiver_id=cg.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert visit.id is not None
    assert visit.clock_in is not None
    assert visit.clock_in_lat == Decimal("37.7749295")


@pytest.mark.asyncio
async def test_clock_out_calculates_duration(session: AsyncSession) -> None:
    """Clock-out calculates visit duration."""
    _, cg, shift = await _setup(session)
    service = VisitService(session)

    visit = await service.clock_in(
        ClockInRequest(shift_id=shift.id),
        caregiver_id=cg.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    completed = await service.clock_out(visit.id, ClockOutRequest(notes="All good"))
    await session.commit()

    assert completed.clock_out is not None
    assert completed.duration_minutes is not None
    assert completed.notes == "All good"


# --- Geofence tests ---


@pytest.mark.asyncio
async def test_geofence_within_radius() -> None:
    """GPS within geofence radius returns True."""
    result = VisitService.validate_geofence(
        visit_lat=Decimal("37.7749"),
        visit_lng=Decimal("-122.4194"),
        target_lat=37.7750,
        target_lng=-122.4195,
        radius_meters=200,
    )
    assert result is True


@pytest.mark.asyncio
async def test_geofence_outside_radius() -> None:
    """GPS outside geofence radius returns False."""
    result = VisitService.validate_geofence(
        visit_lat=Decimal("37.7749"),
        visit_lng=Decimal("-122.4194"),
        target_lat=37.8000,
        target_lng=-122.4500,
        radius_meters=200,
    )
    assert result is False


@pytest.mark.asyncio
async def test_geofence_no_gps() -> None:
    """Missing GPS returns False."""
    result = VisitService.validate_geofence(
        visit_lat=None,
        visit_lng=None,
        target_lat=37.7750,
        target_lng=-122.4195,
    )
    assert result is False
