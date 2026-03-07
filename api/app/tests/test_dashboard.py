"""Tests for dashboard KPIs and portal summaries."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import (  # noqa: F401
    Agency,
    Chart,
    ChartTemplate,
    Client,
    Credential,
    Invoice,
    InvoiceLineItem,
    Message,
    Notification,
    PayrollEntry,
    PayrollPeriod,
    PushSubscription,
    Shift,
    User,
    Visit,
)
from app.models.client import ClientStatus, FamilyLink
from app.models.shift import ShiftStatus
from app.models.user import UserRole
from app.services.dashboard import DashboardService

TEST_DB_URL = "sqlite+aiosqlite:///./test_dashboard.db"
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


async def _seed_data(session: AsyncSession) -> tuple[User, User, Client]:
    """Create caregiver, family user, and client with shift."""
    cg = User(
        email="cg@test.com",
        first_name="CG",
        last_name="Test",
        role=UserRole.CAREGIVER,
        agency_id=AGENCY_ID,
    )
    family = User(
        email="family@test.com",
        first_name="Family",
        last_name="Test",
        role=UserRole.FAMILY,
        agency_id=AGENCY_ID,
    )
    client = Client(
        first_name="Test",
        last_name="Client",
        status=ClientStatus.ACTIVE,
        agency_id=AGENCY_ID,
    )
    session.add_all([cg, family, client])
    await session.commit()
    await session.refresh(cg)
    await session.refresh(family)
    await session.refresh(client)

    # Link family to client
    link = FamilyLink(
        client_id=client.id,
        user_id=family.id,
        relationship="parent",
        agency_id=AGENCY_ID,
    )
    session.add(link)

    # Create a shift for today
    shift = Shift(
        client_id=client.id,
        caregiver_id=cg.id,
        start_time=NOW - timedelta(hours=2),
        end_time=NOW + timedelta(hours=2),
        status=ShiftStatus.IN_PROGRESS,
        agency_id=AGENCY_ID,
    )
    session.add(shift)

    # Create a completed visit
    visit = Visit(
        shift_id=shift.id,
        caregiver_id=cg.id,
        clock_in=NOW - timedelta(hours=2),
        clock_out=NOW - timedelta(hours=1),
        agency_id=AGENCY_ID,
    )
    session.add(visit)
    await session.commit()

    return cg, family, client


@pytest.mark.asyncio
async def test_agency_kpis(session: AsyncSession) -> None:
    """Agency KPIs include client, caregiver, and shift counts."""
    cg, _, client = await _seed_data(session)
    service = DashboardService(session)

    kpis = await service.get_agency_kpis(AGENCY_ID)

    assert kpis.total_clients >= 1
    assert kpis.active_clients >= 1
    assert kpis.total_caregivers >= 1
    assert kpis.active_shifts_today >= 1


@pytest.mark.asyncio
async def test_platform_kpis(session: AsyncSession) -> None:
    """Platform KPIs include agency and user counts."""
    await _seed_data(session)
    service = DashboardService(session)

    kpis = await service.get_platform_kpis()

    assert kpis.total_agencies >= 1
    assert kpis.total_users >= 2


@pytest.mark.asyncio
async def test_caregiver_summary(session: AsyncSession) -> None:
    """Caregiver portal shows completed visits."""
    cg, _, _ = await _seed_data(session)
    service = DashboardService(session)

    summary = await service.get_caregiver_summary(cg.id)

    assert summary.completed_visits_this_week >= 1


@pytest.mark.asyncio
async def test_family_summary(session: AsyncSession) -> None:
    """Family portal shows linked clients."""
    _, family, _ = await _seed_data(session)
    service = DashboardService(session)

    summary = await service.get_family_summary(family.id)

    assert summary.linked_clients >= 1
