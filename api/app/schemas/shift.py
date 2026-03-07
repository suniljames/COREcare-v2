"""Shift request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.shift import ShiftStatus


class ShiftCreate(BaseModel):
    """Schema for creating a new shift."""

    client_id: uuid.UUID
    caregiver_id: uuid.UUID | None = None
    start_time: datetime
    end_time: datetime
    recurrence_rule: str = ""
    notes: str = ""


class ShiftUpdate(BaseModel):
    """Schema for updating a shift."""

    caregiver_id: uuid.UUID | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: ShiftStatus | None = None
    notes: str | None = None


class ShiftResponse(BaseModel):
    """Schema for shift API responses."""

    id: uuid.UUID
    client_id: uuid.UUID
    caregiver_id: uuid.UUID | None
    start_time: datetime
    end_time: datetime
    status: ShiftStatus
    recurrence_rule: str
    notes: str
    agency_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShiftListResponse(BaseModel):
    """Paginated list of shifts."""

    items: list[ShiftResponse]
    total: int
    page: int
    size: int
