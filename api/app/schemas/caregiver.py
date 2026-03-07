"""Caregiver profile request/response schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class CaregiverProfileCreate(BaseModel):
    """Schema for creating a caregiver profile."""

    user_id: uuid.UUID
    bio: str = ""
    years_experience: int = 0
    hourly_rate: Decimal = Decimal("0.00")
    overtime_rate: Decimal = Decimal("0.00")
    holiday_rate: Decimal = Decimal("0.00")
    skills: list[str] | None = None
    certifications: list[dict[str, Any]] | None = None
    availability: dict[str, Any] | None = None


class CaregiverProfileUpdate(BaseModel):
    """Schema for updating a caregiver profile."""

    bio: str | None = None
    years_experience: int | None = None
    hourly_rate: Decimal | None = None
    overtime_rate: Decimal | None = None
    holiday_rate: Decimal | None = None
    skills: list[str] | None = None
    certifications: list[dict[str, Any]] | None = None
    availability: dict[str, Any] | None = None


class CaregiverProfileResponse(BaseModel):
    """Schema for caregiver profile API responses."""

    id: uuid.UUID
    user_id: uuid.UUID
    bio: str
    years_experience: int
    hourly_rate: Decimal
    overtime_rate: Decimal
    holiday_rate: Decimal
    skills: list[str] | None
    certifications: list[dict[str, Any]] | None
    availability: dict[str, Any] | None
    agency_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaregiverProfileListResponse(BaseModel):
    """Paginated list of caregiver profiles."""

    items: list[CaregiverProfileResponse]
    total: int
    page: int
    size: int
