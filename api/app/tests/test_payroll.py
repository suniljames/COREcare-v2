"""Tests for payroll periods, entries, and approval workflow."""

import uuid
from collections.abc import AsyncGenerator
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, Client, PayrollEntry, PayrollPeriod, Shift, User, Visit  # noqa: F401
from app.models.payroll import PayrollPeriodStatus
from app.models.user import UserRole
from app.schemas.payroll import PayrollEntryCreate, PayrollPeriodCreate
from app.services.payroll import PayrollService

TEST_DB_URL = "sqlite+aiosqlite:///./test_payroll.db"
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TODAY = date.today()


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


async def _create_caregiver(session: AsyncSession) -> User:
    cg = User(
        email="cg@test.com",
        first_name="CG",
        last_name="Test",
        role=UserRole.CAREGIVER,
        agency_id=AGENCY_ID,
    )
    session.add(cg)
    await session.commit()
    await session.refresh(cg)
    return cg


@pytest.mark.asyncio
async def test_create_period(session: AsyncSession) -> None:
    """Creating a payroll period sets draft status."""
    service = PayrollService(session)
    period = await service.create_period(
        PayrollPeriodCreate(
            start_date=TODAY,
            end_date=TODAY + timedelta(days=13),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert period.status == PayrollPeriodStatus.DRAFT
    assert period.total_hours == Decimal("0")
    assert period.total_amount == Decimal("0")


@pytest.mark.asyncio
async def test_add_entry_calculates_total(session: AsyncSession) -> None:
    """Adding an entry calculates total and updates period totals."""
    cg = await _create_caregiver(session)
    service = PayrollService(session)

    period = await service.create_period(
        PayrollPeriodCreate(
            start_date=TODAY,
            end_date=TODAY + timedelta(days=13),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    entry = await service.add_entry(
        period.id,
        PayrollEntryCreate(
            caregiver_id=cg.id,
            regular_hours=Decimal("40"),
            overtime_hours=Decimal("5"),
            hourly_rate=Decimal("25.00"),
            overtime_rate=Decimal("37.50"),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    # 40*25 + 5*37.50 = 1000 + 187.50 = 1187.50
    assert entry.total_amount == Decimal("1187.50")

    # Period totals should be updated
    updated_period = await service.get_period(period.id)
    assert updated_period is not None
    assert updated_period.total_hours == Decimal("45")
    assert updated_period.total_amount == Decimal("1187.50")


@pytest.mark.asyncio
async def test_approval_workflow(session: AsyncSession) -> None:
    """Period goes through draft -> pending -> approved."""
    cg = await _create_caregiver(session)
    service = PayrollService(session)

    period = await service.create_period(
        PayrollPeriodCreate(
            start_date=TODAY,
            end_date=TODAY + timedelta(days=13),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()
    assert period.status == PayrollPeriodStatus.DRAFT

    submitted = await service.submit_for_approval(period.id)
    await session.commit()
    assert submitted is not None
    assert submitted.status == PayrollPeriodStatus.PENDING_APPROVAL

    approved = await service.approve_period(period.id, approver_id=cg.id)
    await session.commit()
    assert approved is not None
    assert approved.status == PayrollPeriodStatus.APPROVED
    assert approved.approved_by_id == cg.id


@pytest.mark.asyncio
async def test_reject_period(session: AsyncSession) -> None:
    """Rejecting a period sets rejected status."""
    service = PayrollService(session)

    period = await service.create_period(
        PayrollPeriodCreate(
            start_date=TODAY,
            end_date=TODAY + timedelta(days=13),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    await service.submit_for_approval(period.id)
    await session.commit()

    rejected = await service.reject_period(period.id)
    await session.commit()

    assert rejected is not None
    assert rejected.status == PayrollPeriodStatus.REJECTED


@pytest.mark.asyncio
async def test_list_entries(session: AsyncSession) -> None:
    """Listing entries returns all entries for a period."""
    cg = await _create_caregiver(session)
    service = PayrollService(session)

    period = await service.create_period(
        PayrollPeriodCreate(
            start_date=TODAY,
            end_date=TODAY + timedelta(days=13),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    await service.add_entry(
        period.id,
        PayrollEntryCreate(
            caregiver_id=cg.id,
            regular_hours=Decimal("40"),
            hourly_rate=Decimal("25"),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    entries = await service.list_entries(period.id)
    assert len(entries) == 1
    assert entries[0].caregiver_id == cg.id
