"""Client (patient) model."""

import enum
import uuid
from datetime import date
from typing import Any

from sqlalchemy import JSON
from sqlmodel import Column, Field

from app.models.base import TenantScopedModel


class ClientStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCHARGED = "discharged"


class Client(TenantScopedModel, table=True):
    """A home care client (patient). Tenant-scoped via agency_id."""

    __tablename__ = "clients"

    first_name: str = Field(index=True)
    last_name: str = Field(index=True)
    date_of_birth: date | None = None
    gender: str = Field(default="")
    phone: str = Field(default="")
    email: str = Field(default="")
    address: str = Field(default="")
    status: ClientStatus = Field(default=ClientStatus.ACTIVE, index=True)
    care_level: str = Field(default="")
    notes: str = Field(default="")
    emergency_contacts: list[dict[str, Any]] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )


class FamilyLink(TenantScopedModel, table=True):
    """Links a client to a family-role user with a relationship type."""

    __tablename__ = "family_links"

    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    relationship_type: str = Field(default="other")
