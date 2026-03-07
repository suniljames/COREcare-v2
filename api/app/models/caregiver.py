"""Caregiver profile model."""

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON
from sqlmodel import Column, Field

from app.models.base import TenantScopedModel


class CaregiverProfile(TenantScopedModel, table=True):
    """Extended profile for caregiver users. One-to-one with User."""

    __tablename__ = "caregiver_profiles"

    user_id: uuid.UUID = Field(foreign_key="users.id", unique=True, index=True)
    bio: str = Field(default="")
    years_experience: int = Field(default=0)
    hourly_rate: Decimal = Field(default=Decimal("0.00"), max_digits=8, decimal_places=2)
    overtime_rate: Decimal = Field(default=Decimal("0.00"), max_digits=8, decimal_places=2)
    holiday_rate: Decimal = Field(default=Decimal("0.00"), max_digits=8, decimal_places=2)
    skills: list[str] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    certifications: list[dict[str, Any]] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    availability: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
