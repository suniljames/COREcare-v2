"""Shift scheduling model."""

import enum
import uuid
from datetime import datetime

from sqlmodel import Field

from app.models.base import TenantScopedModel


class ShiftStatus(enum.StrEnum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Shift(TenantScopedModel, table=True):
    """A scheduled care shift. Tenant-scoped via agency_id."""

    __tablename__ = "shifts"

    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    caregiver_id: uuid.UUID | None = Field(default=None, foreign_key="users.id", index=True)
    start_time: datetime = Field(index=True)
    end_time: datetime
    status: ShiftStatus = Field(default=ShiftStatus.OPEN, index=True)
    recurrence_rule: str = Field(default="")
    notes: str = Field(default="")
