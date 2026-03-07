"""Visit and shift offer schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.visit import ShiftOfferStatus


class ShiftOfferCreate(BaseModel):
    shift_id: uuid.UUID
    caregiver_id: uuid.UUID


class ShiftOfferResponse(BaseModel):
    id: uuid.UUID
    shift_id: uuid.UUID
    caregiver_id: uuid.UUID
    status: ShiftOfferStatus
    responded_at: datetime | None
    agency_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ClockInRequest(BaseModel):
    shift_id: uuid.UUID
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class ClockOutRequest(BaseModel):
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    notes: str = ""


class VisitResponse(BaseModel):
    id: uuid.UUID
    shift_id: uuid.UUID
    caregiver_id: uuid.UUID
    clock_in: datetime | None
    clock_out: datetime | None
    clock_in_lat: Decimal | None
    clock_in_lng: Decimal | None
    clock_out_lat: Decimal | None
    clock_out_lng: Decimal | None
    geofence_valid_in: bool
    geofence_valid_out: bool
    duration_minutes: int | None
    notes: str
    agency_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
