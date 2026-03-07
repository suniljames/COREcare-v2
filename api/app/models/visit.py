"""Visit tracking and shift offer models."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlmodel import Field

from app.models.base import TenantScopedModel


class ShiftOfferStatus(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class ShiftOffer(TenantScopedModel, table=True):
    """An offer for a caregiver to take a shift."""

    __tablename__ = "shift_offers"

    shift_id: uuid.UUID = Field(foreign_key="shifts.id", index=True)
    caregiver_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    status: ShiftOfferStatus = Field(default=ShiftOfferStatus.PENDING, index=True)
    responded_at: datetime | None = None


class Visit(TenantScopedModel, table=True):
    """A clock-in/out record for a shift visit with GPS tracking."""

    __tablename__ = "visits"

    shift_id: uuid.UUID = Field(foreign_key="shifts.id", index=True)
    caregiver_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    clock_in: datetime | None = None
    clock_out: datetime | None = None
    clock_in_lat: Decimal | None = Field(default=None, max_digits=10, decimal_places=7)
    clock_in_lng: Decimal | None = Field(default=None, max_digits=10, decimal_places=7)
    clock_out_lat: Decimal | None = Field(default=None, max_digits=10, decimal_places=7)
    clock_out_lng: Decimal | None = Field(default=None, max_digits=10, decimal_places=7)
    geofence_valid_in: bool = Field(default=False)
    geofence_valid_out: bool = Field(default=False)
    duration_minutes: int | None = None
    notes: str = Field(default="")
