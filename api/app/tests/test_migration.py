"""Tests for v1 → v2 data migration."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import (  # noqa: F401
    Agency,
    AIConversation,
    AIFeatureFlag,
    AIMessage,
    BAARecord,
    Client,
    ComplianceRule,
    Shift,
    User,
    Visit,
)
from app.models.user import UserRole
from app.services.migration import V1_ROLE_MAP, MigrationService

TEST_DB_URL = "sqlite+aiosqlite:///./test_migration.db"
NOW = datetime.now(UTC).replace(microsecond=0)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


V1_EXPORT: dict[str, list[dict[str, Any]]] = {
    "agencies": [
        {"id": "1", "name": "Test Home Care", "slug": "test-home-care"},
    ],
    "users": [
        {
            "id": "10",
            "email": "admin@test.com",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "agency_id": "1",
        },
        {
            "id": "20",
            "email": "cg@test.com",
            "first_name": "Care",
            "last_name": "Giver",
            "role": "caregiver",
            "agency_id": "1",
        },
    ],
    "clients": [
        {
            "id": "100",
            "first_name": "Test",
            "last_name": "Client",
            "agency_id": "1",
        },
    ],
    "shifts": [
        {
            "id": "1000",
            "client_id": "100",
            "caregiver_id": "20",
            "start_time": NOW,
            "end_time": NOW + timedelta(hours=4),
            "status": "assigned",
            "agency_id": "1",
        },
    ],
}


@pytest.mark.asyncio
async def test_full_migration(session: AsyncSession) -> None:
    """Full migration creates agencies, users, clients, shifts."""
    migrator = MigrationService(session)
    report = await migrator.run_full_migration(V1_EXPORT)
    await session.commit()

    assert report.success
    assert report.agencies_migrated == 1
    assert report.users_migrated == 2
    assert report.clients_migrated == 1
    assert report.shifts_migrated == 1
    assert report.completed_at is not None


@pytest.mark.asyncio
async def test_role_mapping(session: AsyncSession) -> None:
    """v1 roles map to v2 roles correctly."""
    assert V1_ROLE_MAP["admin"] == UserRole.AGENCY_ADMIN
    assert V1_ROLE_MAP["caregiver"] == UserRole.CAREGIVER
    assert V1_ROLE_MAP["family"] == UserRole.FAMILY
    assert V1_ROLE_MAP["manager"] == UserRole.CARE_MANAGER


@pytest.mark.asyncio
async def test_migration_report_to_dict(session: AsyncSession) -> None:
    """MigrationReport.to_dict produces serializable output."""
    migrator = MigrationService(session)
    report = await migrator.run_full_migration(V1_EXPORT)
    await session.commit()

    report_dict = report.to_dict()
    assert isinstance(report_dict, dict)
    assert report_dict["success"] is True
    assert report_dict["agencies_migrated"] == 1


@pytest.mark.asyncio
async def test_migration_with_missing_agency(session: AsyncSession) -> None:
    """Users referencing unknown agency are skipped."""
    data: dict[str, list[dict[str, Any]]] = {
        "agencies": [],
        "users": [
            {
                "id": "10",
                "email": "orphan@test.com",
                "role": "caregiver",
                "agency_id": "999",
            },
        ],
    }
    migrator = MigrationService(session)
    report = await migrator.run_full_migration(data)
    await session.commit()

    assert report.users_migrated == 0


@pytest.mark.asyncio
async def test_id_mapping_across_entities(session: AsyncSession) -> None:
    """ID mapping resolves v1 IDs to v2 UUIDs for FK references."""
    migrator = MigrationService(session)
    await migrator.run_full_migration(V1_EXPORT)
    await session.commit()

    assert "1" in migrator.id_map["agencies"]
    assert "10" in migrator.id_map["users"]
    assert "20" in migrator.id_map["users"]
    assert "100" in migrator.id_map["clients"]
    assert "1000" in migrator.id_map["shifts"]

    # All values should be UUIDs
    for entity_map in migrator.id_map.values():
        for v2_id in entity_map.values():
            assert isinstance(v2_id, uuid.UUID)
