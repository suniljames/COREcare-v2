"""Tests for HIPAA-grade audit logging."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, User  # noqa: F401 — register models for metadata
from app.models.audit import AuditAction, AuditEvent
from app.services.audit import AuditService

TEST_DB_URL = "sqlite+aiosqlite:///./test_audit.db"


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh test database session (SQLite)."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


# --- Model structure tests ---


@pytest.mark.asyncio
async def test_audit_event_has_required_fields() -> None:
    """AuditEvent model declares all required audit fields."""
    fields = AuditEvent.model_fields
    assert "user_id" in fields
    assert "agency_id" in fields
    assert "action" in fields
    assert "resource_type" in fields
    assert "resource_id" in fields
    assert "is_phi_access" in fields
    assert "ip_address" in fields
    assert "changes" in fields


@pytest.mark.asyncio
async def test_audit_action_enum_values() -> None:
    """AuditAction enum has all expected action types."""
    actions = {a.value for a in AuditAction}
    assert actions == {"create", "read", "update", "delete", "login", "logout", "export"}


@pytest.mark.asyncio
async def test_audit_event_agency_id_nullable() -> None:
    """AuditEvent.agency_id is optional (for super-admin platform-level actions)."""
    event = AuditEvent(action=AuditAction.LOGIN, resource_type="session", agency_id=None)
    assert event.agency_id is None


# --- Service tests ---


@pytest.mark.asyncio
async def test_audit_service_creates_event(session: AsyncSession) -> None:
    """AuditService.log() creates an audit event in the database."""
    service = AuditService(session)
    agency_id = uuid.uuid4()
    user_id = uuid.uuid4()

    event = await service.log(
        action=AuditAction.CREATE,
        resource_type="user",
        resource_id="user-123",
        user_id=user_id,
        agency_id=agency_id,
        details="Created new user",
    )
    await session.commit()

    assert event.id is not None
    assert event.action == AuditAction.CREATE
    assert event.resource_type == "user"
    assert event.resource_id == "user-123"
    assert event.user_id == user_id
    assert event.agency_id == agency_id
    assert event.details == "Created new user"
    assert event.created_at is not None


@pytest.mark.asyncio
async def test_audit_service_phi_flag(session: AsyncSession) -> None:
    """AuditService.log() correctly sets the is_phi_access flag."""
    service = AuditService(session)

    event = await service.log(
        action=AuditAction.READ,
        resource_type="client_chart",
        resource_id="chart-456",
        is_phi_access=True,
    )
    await session.commit()

    assert event.is_phi_access is True


@pytest.mark.asyncio
async def test_audit_service_stores_changes(session: AsyncSession) -> None:
    """AuditService.log() stores before/after change details as JSON."""
    service = AuditService(session)

    changes = {"before": {"status": "active"}, "after": {"status": "inactive"}}
    event = await service.log(
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id="user-789",
        changes=changes,
    )
    await session.commit()
    await session.refresh(event)

    assert event.changes == changes


@pytest.mark.asyncio
async def test_audit_events_queryable(session: AsyncSession) -> None:
    """Multiple audit events can be queried from the database."""
    service = AuditService(session)

    for i in range(3):
        await service.log(
            action=AuditAction.READ,
            resource_type="client",
            resource_id=f"client-{i}",
        )
    await session.commit()

    result = await session.execute(text("SELECT COUNT(*) FROM audit_events"))
    count = result.scalar()
    assert count == 3
