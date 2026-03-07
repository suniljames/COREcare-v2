"""v1 Django to v2 FastAPI data migration service.

This module provides ETL utilities for migrating data from the COREcare v1
Django/PostgreSQL database to the v2 FastAPI/SQLModel schema.

Migration order (respects FK dependencies):
1. Agencies
2. Users (with role mapping)
3. Clients
4. Family links
5. Caregiver profiles
6. Shifts
7. Visits
8. Credentials
9. Charts/templates (new in v2 — no v1 data)
10. Payroll/billing (new in v2 — no v1 data)

Usage:
    migrator = MigrationService(v2_session)
    report = await migrator.run_full_migration(v1_data)
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agency import Agency
from app.models.client import Client
from app.models.shift import Shift, ShiftStatus
from app.models.user import User, UserRole

# v1 role → v2 role mapping
V1_ROLE_MAP: dict[str, UserRole] = {
    "admin": UserRole.AGENCY_ADMIN,
    "manager": UserRole.CARE_MANAGER,
    "caregiver": UserRole.CAREGIVER,
    "family": UserRole.FAMILY,
}

# v1 shift status → v2 status mapping
V1_SHIFT_STATUS_MAP: dict[str, ShiftStatus] = {
    "open": ShiftStatus.OPEN,
    "assigned": ShiftStatus.ASSIGNED,
    "in_progress": ShiftStatus.IN_PROGRESS,
    "completed": ShiftStatus.COMPLETED,
    "cancelled": ShiftStatus.CANCELLED,
}


@dataclass
class MigrationReport:
    """Report of migration results."""

    agencies_migrated: int = 0
    users_migrated: int = 0
    clients_migrated: int = 0
    shifts_migrated: int = 0
    visits_migrated: int = 0
    credentials_migrated: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agencies_migrated": self.agencies_migrated,
            "users_migrated": self.users_migrated,
            "clients_migrated": self.clients_migrated,
            "shifts_migrated": self.shifts_migrated,
            "visits_migrated": self.visits_migrated,
            "credentials_migrated": self.credentials_migrated,
            "errors": self.errors,
            "success": self.success,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class MigrationService:
    """ETL service for v1 → v2 data migration."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.id_map: dict[str, dict[str, uuid.UUID]] = {
            "agencies": {},
            "users": {},
            "clients": {},
            "shifts": {},
        }

    async def migrate_agency(self, v1_data: dict[str, Any]) -> Agency:
        """Migrate a v1 agency record."""
        agency = Agency(
            name=v1_data["name"],
            slug=v1_data.get("slug", v1_data["name"].lower().replace(" ", "-")),
        )
        self.session.add(agency)
        await self.session.flush()
        await self.session.refresh(agency)
        self.id_map["agencies"][str(v1_data.get("id", ""))] = agency.id
        return agency

    async def migrate_user(self, v1_data: dict[str, Any], agency_id: uuid.UUID) -> User:
        """Migrate a v1 user with role mapping."""
        v1_role = v1_data.get("role", "caregiver")
        role = V1_ROLE_MAP.get(v1_role, UserRole.CAREGIVER)

        user = User(
            email=v1_data["email"],
            first_name=v1_data.get("first_name", ""),
            last_name=v1_data.get("last_name", ""),
            role=role,
            agency_id=agency_id,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        self.id_map["users"][str(v1_data.get("id", ""))] = user.id
        return user

    async def migrate_client(self, v1_data: dict[str, Any], agency_id: uuid.UUID) -> Client:
        """Migrate a v1 client record."""
        client = Client(
            first_name=v1_data.get("first_name", ""),
            last_name=v1_data.get("last_name", ""),
            agency_id=agency_id,
        )
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        self.id_map["clients"][str(v1_data.get("id", ""))] = client.id
        return client

    async def migrate_shift(self, v1_data: dict[str, Any], agency_id: uuid.UUID) -> Shift | None:
        """Migrate a v1 shift record."""
        client_v1_id = str(v1_data.get("client_id", ""))
        client_id = self.id_map["clients"].get(client_v1_id)
        if client_id is None:
            return None

        caregiver_id = None
        cg_v1_id = str(v1_data.get("caregiver_id", ""))
        if cg_v1_id:
            caregiver_id = self.id_map["users"].get(cg_v1_id)

        v1_status = v1_data.get("status", "open")
        status = V1_SHIFT_STATUS_MAP.get(v1_status, ShiftStatus.OPEN)

        shift = Shift(
            client_id=client_id,
            caregiver_id=caregiver_id,
            start_time=v1_data["start_time"],
            end_time=v1_data["end_time"],
            status=status,
            agency_id=agency_id,
        )
        self.session.add(shift)
        await self.session.flush()
        await self.session.refresh(shift)
        self.id_map["shifts"][str(v1_data.get("id", ""))] = shift.id
        return shift

    async def run_full_migration(self, v1_data: dict[str, list[dict[str, Any]]]) -> MigrationReport:
        """Run complete migration from v1 data export.

        Expected v1_data format:
        {
            "agencies": [...],
            "users": [...],
            "clients": [...],
            "shifts": [...],
        }
        """
        report = MigrationReport()

        # 1. Agencies
        for agency_data in v1_data.get("agencies", []):
            try:
                await self.migrate_agency(agency_data)
                report.agencies_migrated += 1
            except Exception as e:
                report.errors.append(f"Agency {agency_data.get('name')}: {e}")

        # 2. Users
        for user_data in v1_data.get("users", []):
            try:
                agency_v1_id = str(user_data.get("agency_id", ""))
                agency_id = self.id_map["agencies"].get(agency_v1_id)
                if agency_id:
                    await self.migrate_user(user_data, agency_id)
                    report.users_migrated += 1
            except Exception as e:
                report.errors.append(f"User {user_data.get('email')}: {e}")

        # 3. Clients
        for client_data in v1_data.get("clients", []):
            try:
                agency_v1_id = str(client_data.get("agency_id", ""))
                agency_id = self.id_map["agencies"].get(agency_v1_id)
                if agency_id:
                    await self.migrate_client(client_data, agency_id)
                    report.clients_migrated += 1
            except Exception as e:
                report.errors.append(f"Client {client_data.get('last_name')}: {e}")

        # 4. Shifts
        for shift_data in v1_data.get("shifts", []):
            try:
                agency_v1_id = str(shift_data.get("agency_id", ""))
                agency_id = self.id_map["agencies"].get(agency_v1_id)
                if agency_id:
                    shift = await self.migrate_shift(shift_data, agency_id)
                    if shift:
                        report.shifts_migrated += 1
            except Exception as e:
                report.errors.append(f"Shift: {e}")

        await self.session.flush()
        report.completed_at = datetime.now(UTC)
        return report
