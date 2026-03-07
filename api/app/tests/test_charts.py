"""Tests for charting — templates and patient charts."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, Chart, ChartTemplate, Client, Shift, User, Visit  # noqa: F401
from app.models.chart import ChartStatus
from app.models.shift import ShiftStatus
from app.models.user import UserRole
from app.schemas.chart import (
    ChartCreate,
    ChartTemplateCreate,
    ChartTemplateUpdate,
    ChartUpdate,
)
from app.services.chart import ChartService

TEST_DB_URL = "sqlite+aiosqlite:///./test_charts.db"
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


SAMPLE_SECTIONS = [
    {
        "title": "Vitals",
        "fields": [
            {"name": "bp", "type": "text"},
            {"name": "temp", "type": "number"},
        ],
    },
    {
        "title": "Notes",
        "fields": [{"name": "observation", "type": "textarea"}],
    },
]


# --- Template tests ---


@pytest.mark.asyncio
async def test_create_template(session: AsyncSession) -> None:
    """ChartService.create_template creates a v1 template."""
    service = ChartService(session)
    template = await service.create_template(
        ChartTemplateCreate(name="Daily Visit", sections=SAMPLE_SECTIONS),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert template.name == "Daily Visit"
    assert template.version == 1
    assert template.is_active is True


@pytest.mark.asyncio
async def test_update_template_bumps_version(session: AsyncSession) -> None:
    """Updating template content bumps the version number."""
    service = ChartService(session)
    template = await service.create_template(
        ChartTemplateCreate(name="Initial", sections=SAMPLE_SECTIONS),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    updated = await service.update_template(
        template.id,
        ChartTemplateUpdate(name="Updated Name"),
    )
    await session.commit()

    assert updated is not None
    assert updated.version == 2
    assert updated.name == "Updated Name"


@pytest.mark.asyncio
async def test_deactivate_template(session: AsyncSession) -> None:
    """Deactivating a template excludes it from active listings."""
    service = ChartService(session)
    template = await service.create_template(
        ChartTemplateCreate(name="Old Template", sections=[]),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    await service.update_template(
        template.id,
        ChartTemplateUpdate(is_active=False),
    )
    await session.commit()

    templates, total = await service.list_templates(active_only=True)
    assert total == 0


@pytest.mark.asyncio
async def test_list_templates_includes_inactive(session: AsyncSession) -> None:
    """Listing with active_only=False includes deactivated templates."""
    service = ChartService(session)
    template = await service.create_template(
        ChartTemplateCreate(name="Template A", sections=[]),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    await service.update_template(
        template.id,
        ChartTemplateUpdate(is_active=False),
    )
    await session.commit()

    templates, total = await service.list_templates(active_only=False)
    assert total == 1


# --- Chart tests ---


@pytest.mark.asyncio
async def test_create_chart(session: AsyncSession) -> None:
    """Creating a chart links to template, client, and caregiver."""
    client, cg, shift = await _setup(session)
    service = ChartService(session)

    template = await service.create_template(
        ChartTemplateCreate(name="Visit Note", sections=SAMPLE_SECTIONS),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    chart = await service.create_chart(
        ChartCreate(
            template_id=template.id,
            client_id=client.id,
            shift_id=shift.id,
            data={"bp": "120/80", "temp": 98.6},
        ),
        caregiver_id=cg.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert chart.status == ChartStatus.DRAFT
    assert chart.version == 1
    assert chart.template_id == template.id


@pytest.mark.asyncio
async def test_update_chart_bumps_version(session: AsyncSession) -> None:
    """Updating chart data bumps version."""
    client, cg, _ = await _setup(session)
    service = ChartService(session)

    template = await service.create_template(
        ChartTemplateCreate(name="Template", sections=[]),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    chart = await service.create_chart(
        ChartCreate(template_id=template.id, client_id=client.id, data={"v": 1}),
        caregiver_id=cg.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    updated = await service.update_chart(chart.id, ChartUpdate(data={"v": 2, "new_field": "val"}))
    await session.commit()

    assert updated is not None
    assert updated.version == 2


@pytest.mark.asyncio
async def test_sign_chart(session: AsyncSession) -> None:
    """Signing a chart sets status, timestamp, and signer."""
    client, cg, _ = await _setup(session)
    service = ChartService(session)

    template = await service.create_template(
        ChartTemplateCreate(name="Template", sections=[]),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    chart = await service.create_chart(
        ChartCreate(template_id=template.id, client_id=client.id),
        caregiver_id=cg.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    signed = await service.sign_chart(chart.id, signer_id=cg.id)
    await session.commit()

    assert signed is not None
    assert signed.status == ChartStatus.SIGNED
    assert signed.signed_at is not None
    assert signed.signed_by_id == cg.id


@pytest.mark.asyncio
async def test_list_charts_filter_by_client(session: AsyncSession) -> None:
    """Filtering charts by client_id returns only that client's charts."""
    client, cg, _ = await _setup(session)
    service = ChartService(session)

    template = await service.create_template(
        ChartTemplateCreate(name="Template", sections=[]),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    await service.create_chart(
        ChartCreate(template_id=template.id, client_id=client.id),
        caregiver_id=cg.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    charts, total = await service.list_charts(client_id=client.id)
    assert total == 1
    assert charts[0].client_id == client.id

    # No results for random client
    other_charts, other_total = await service.list_charts(client_id=uuid.uuid4())
    assert other_total == 0
