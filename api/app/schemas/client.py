"""Client request/response schemas."""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.models.client import ClientStatus


class ClientCreate(BaseModel):
    """Schema for creating a new client."""

    first_name: str
    last_name: str
    date_of_birth: date | None = None
    gender: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    care_level: str = ""
    notes: str = ""
    emergency_contacts: list[dict[str, Any]] | None = None


class ClientUpdate(BaseModel):
    """Schema for updating a client. All fields optional."""

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    status: ClientStatus | None = None
    care_level: str | None = None
    notes: str | None = None
    emergency_contacts: list[dict[str, Any]] | None = None


class ClientResponse(BaseModel):
    """Schema for client API responses."""

    id: uuid.UUID
    first_name: str
    last_name: str
    date_of_birth: date | None
    gender: str
    phone: str
    email: str
    address: str
    status: ClientStatus
    care_level: str
    notes: str
    emergency_contacts: list[dict[str, Any]] | None
    agency_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientListResponse(BaseModel):
    """Paginated list of clients."""

    items: list[ClientResponse]
    total: int
    page: int
    size: int


class FamilyLinkCreate(BaseModel):
    """Schema for linking a family member to a client."""

    client_id: uuid.UUID
    user_id: uuid.UUID
    relationship_type: str = "other"


class FamilyLinkResponse(BaseModel):
    """Schema for family link API responses."""

    id: uuid.UUID
    client_id: uuid.UUID
    user_id: uuid.UUID
    relationship_type: str
    agency_id: uuid.UUID

    model_config = {"from_attributes": True}
