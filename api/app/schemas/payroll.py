"""Payroll request/response schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.payroll import PayrollPeriodStatus


class PayrollPeriodCreate(BaseModel):
    start_date: date
    end_date: date
    notes: str = ""


class PayrollPeriodUpdate(BaseModel):
    notes: str | None = None
    status: PayrollPeriodStatus | None = None


class PayrollEntryCreate(BaseModel):
    caregiver_id: uuid.UUID
    regular_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    hourly_rate: Decimal = Decimal("0")
    overtime_rate: Decimal = Decimal("0")
    notes: str = ""


class PayrollEntryResponse(BaseModel):
    id: uuid.UUID
    period_id: uuid.UUID
    caregiver_id: uuid.UUID
    regular_hours: Decimal
    overtime_hours: Decimal
    hourly_rate: Decimal
    overtime_rate: Decimal
    total_amount: Decimal
    notes: str
    agency_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class PayrollPeriodResponse(BaseModel):
    id: uuid.UUID
    start_date: date
    end_date: date
    status: PayrollPeriodStatus
    total_hours: Decimal
    total_amount: Decimal
    approved_by_id: uuid.UUID | None
    notes: str
    agency_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PayrollPeriodListResponse(BaseModel):
    items: list[PayrollPeriodResponse]
    total: int
    page: int
    size: int
