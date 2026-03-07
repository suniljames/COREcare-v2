"""Payroll models — periods, entries, and approval workflow."""

import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlmodel import Column, Field, Text

from app.models.base import TenantScopedModel


class PayrollPeriodStatus(enum.StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PROCESSED = "processed"
    REJECTED = "rejected"


class PayrollPeriod(TenantScopedModel, table=True):
    """A payroll period (e.g. bi-weekly) for an agency."""

    __tablename__ = "payroll_periods"

    start_date: date
    end_date: date
    status: PayrollPeriodStatus = Field(default=PayrollPeriodStatus.DRAFT, index=True)
    total_hours: Decimal = Field(default=Decimal("0"), max_digits=10, decimal_places=2)
    total_amount: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    approved_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    notes: str = Field(default="", sa_column=Column(Text))


class PayrollEntry(TenantScopedModel, table=True):
    """A single caregiver's payroll line within a period."""

    __tablename__ = "payroll_entries"

    period_id: uuid.UUID = Field(foreign_key="payroll_periods.id", index=True)
    caregiver_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    regular_hours: Decimal = Field(default=Decimal("0"), max_digits=8, decimal_places=2)
    overtime_hours: Decimal = Field(default=Decimal("0"), max_digits=8, decimal_places=2)
    hourly_rate: Decimal = Field(default=Decimal("0"), max_digits=8, decimal_places=2)
    overtime_rate: Decimal = Field(default=Decimal("0"), max_digits=8, decimal_places=2)
    total_amount: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    notes: str = Field(default="", sa_column=Column(Text))
