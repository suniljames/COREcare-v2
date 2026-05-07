"""Service-layer tests for the Client-as-user persona (issue #125).

Covers:
- Client model `client_user_id` FK + UserRole.CLIENT enum value (model-shape).
- CarePlanService active-version selection + Client-facing schema field exclusion.
- MessageThreadService thread get-or-create + message send/list for the Client.
- ShiftService.list_upcoming_for_client returns only that Client's shifts.

PostgreSQL-RLS isolation tests live in test_client_persona_rls.py and are
skipped on SQLite. These tests verify application-layer behavior.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import (  # noqa: F401 — register models for metadata
    Agency,
    AuditEvent,
    Client,
    Message,
    Shift,
    User,
)
from app.models.user import UserRole

TEST_DB_URL = "sqlite+aiosqlite:///./test_client_persona.db"
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-00000000a001")
OTHER_AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-00000000a002")


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Fresh SQLite test session with two agencies seeded."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        s.add(Agency(id=AGENCY_ID, name="Sunrise Home Care", slug="sunrise"))
        s.add(Agency(id=OTHER_AGENCY_ID, name="Other Agency", slug="other"))
        await s.commit()
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


# --- Model shape ---


def test_user_role_enum_includes_client() -> None:
    """UserRole enum has CLIENT value."""
    assert UserRole.CLIENT == "client"
    assert UserRole.CLIENT.value == "client"


def test_client_model_has_client_user_id_field() -> None:
    """Client model has client_user_id field, nullable UUID."""
    fields = Client.model_fields
    assert "client_user_id" in fields, "Client must declare client_user_id"


# --- CarePlanVersion ---


@pytest.mark.asyncio
async def test_care_plan_version_model_exists() -> None:
    """CarePlanVersion model is importable."""
    from app.models import CarePlanVersion  # noqa: F401

    assert CarePlanVersion is not None


@pytest.mark.asyncio
async def test_care_plan_service_returns_active_version(session: AsyncSession) -> None:
    """CarePlanService.get_active_for_client returns is_active=True version."""
    from app.models import CarePlanVersion
    from app.services.care_plan import CarePlanService

    client = Client(first_name="Eleanor", last_name="X", agency_id=AGENCY_ID)
    session.add(client)
    await session.commit()
    await session.refresh(client)

    author = User(
        email="cm@test.com",
        first_name="Care",
        last_name="Mgr",
        role=UserRole.CARE_MANAGER,
        agency_id=AGENCY_ID,
    )
    session.add(author)
    await session.commit()
    await session.refresh(author)

    v1 = CarePlanVersion(
        client_id=client.id,
        agency_id=AGENCY_ID,
        version_no=1,
        is_active=False,
        plain_summary="old plan",
        authored_by_user_id=author.id,
    )
    v2 = CarePlanVersion(
        client_id=client.id,
        agency_id=AGENCY_ID,
        version_no=2,
        is_active=True,
        plain_summary="current plan",
        authored_by_user_id=author.id,
    )
    session.add(v1)
    session.add(v2)
    await session.commit()

    service = CarePlanService(session)
    active = await service.get_active_for_client(client.id)
    assert active is not None
    assert active.version_no == 2
    assert active.plain_summary == "current plan"


@pytest.mark.asyncio
async def test_care_plan_service_no_active_returns_none(session: AsyncSession) -> None:
    """No active version returns None (never raises)."""
    from app.services.care_plan import CarePlanService

    client = Client(first_name="Eleanor", last_name="X", agency_id=AGENCY_ID)
    session.add(client)
    await session.commit()

    service = CarePlanService(session)
    active = await service.get_active_for_client(client.id)
    assert active is None


def test_client_care_plan_read_excludes_clinical_detail() -> None:
    """ClientCarePlanRead schema must NOT serialize clinical_detail field."""
    from app.schemas.care_plan import ClientCarePlanRead

    fields = ClientCarePlanRead.model_fields
    assert "plain_summary" in fields
    assert "care_team_blob" in fields
    assert "weekly_support_blob" in fields
    assert "allergies" in fields
    assert "emergency_contact_blob" in fields
    # The structural enforcement: clinical_detail is staff-only
    assert (
        "clinical_detail" not in fields
    ), "Client schema must not expose clinical_detail"


# --- MessageThread ---


@pytest.mark.asyncio
async def test_message_thread_get_or_create_is_idempotent(
    session: AsyncSession,
) -> None:
    """Calling get_or_create twice returns the same thread."""
    from app.services.message_thread import MessageThreadService

    client = Client(first_name="Eleanor", last_name="X", agency_id=AGENCY_ID)
    session.add(client)
    await session.commit()
    await session.refresh(client)

    service = MessageThreadService(session)
    t1 = await service.get_or_create_for_client(client.id, AGENCY_ID)
    await session.commit()
    t2 = await service.get_or_create_for_client(client.id, AGENCY_ID)
    await session.commit()
    assert t1.id == t2.id


@pytest.mark.asyncio
async def test_send_from_client_persists_message(session: AsyncSession) -> None:
    """send_from_client creates a Message row with correct sender_id."""
    from app.services.message_thread import MessageThreadService

    client = Client(first_name="Eleanor", last_name="X", agency_id=AGENCY_ID)
    user = User(
        email="eleanor@test.com",
        role=UserRole.CLIENT,
        agency_id=AGENCY_ID,
    )
    session.add(client)
    session.add(user)
    await session.commit()
    await session.refresh(client)
    await session.refresh(user)
    client.client_user_id = user.id
    session.add(client)
    await session.commit()

    service = MessageThreadService(session)
    msg = await service.send_from_client(
        client_id=client.id, sender_user_id=user.id, body="Hello", agency_id=AGENCY_ID
    )
    await session.commit()
    assert msg.id is not None
    assert msg.sender_id == user.id
    assert msg.body == "Hello"


# --- Shifts ---


@pytest.mark.asyncio
async def test_list_upcoming_for_client_filters_by_client_id(
    session: AsyncSession,
) -> None:
    """list_upcoming_for_client returns only shifts for that client."""
    from app.services.shift import ShiftService

    c1 = Client(first_name="Eleanor", last_name="One", agency_id=AGENCY_ID)
    c2 = Client(first_name="Mary", last_name="Two", agency_id=AGENCY_ID)
    session.add(c1)
    session.add(c2)
    await session.commit()
    await session.refresh(c1)
    await session.refresh(c2)

    now = datetime.now(UTC)
    s1 = Shift(
        client_id=c1.id,
        agency_id=AGENCY_ID,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=4),
    )
    s2 = Shift(
        client_id=c2.id,
        agency_id=AGENCY_ID,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=4),
    )
    session.add(s1)
    session.add(s2)
    await session.commit()

    service = ShiftService(session)
    shifts = await service.list_upcoming_for_client(c1.id, days=7)
    assert len(shifts) == 1
    assert shifts[0].client_id == c1.id


@pytest.mark.asyncio
async def test_list_upcoming_for_client_excludes_past(session: AsyncSession) -> None:
    """Past shifts are excluded from the upcoming list."""
    from app.services.shift import ShiftService

    c1 = Client(first_name="Eleanor", last_name="One", agency_id=AGENCY_ID)
    session.add(c1)
    await session.commit()
    await session.refresh(c1)

    now = datetime.now(UTC)
    past = Shift(
        client_id=c1.id,
        agency_id=AGENCY_ID,
        start_time=now - timedelta(days=2),
        end_time=now - timedelta(days=2, hours=-4),
    )
    session.add(past)
    await session.commit()

    service = ShiftService(session)
    shifts = await service.list_upcoming_for_client(c1.id, days=7)
    assert shifts == []
