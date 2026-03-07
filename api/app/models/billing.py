"""Billing models — invoices and line items."""

import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlmodel import Column, Field, Text

from app.models.base import TenantScopedModel


class InvoiceStatus(enum.StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(TenantScopedModel, table=True):
    """An invoice for client services."""

    __tablename__ = "invoices"

    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    invoice_number: str = Field(max_length=50, index=True)
    issue_date: date
    due_date: date
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT, index=True)
    subtotal: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    tax_rate: Decimal = Field(default=Decimal("0"), max_digits=5, decimal_places=4)
    tax_amount: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    total: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    notes: str = Field(default="", sa_column=Column(Text))
    paid_date: date | None = None


class InvoiceLineItem(TenantScopedModel, table=True):
    """A line item on an invoice."""

    __tablename__ = "invoice_line_items"

    invoice_id: uuid.UUID = Field(foreign_key="invoices.id", index=True)
    description: str = Field(max_length=500)
    quantity: Decimal = Field(default=Decimal("1"), max_digits=10, decimal_places=2)
    unit_price: Decimal = Field(default=Decimal("0"), max_digits=10, decimal_places=2)
    amount: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    shift_id: uuid.UUID | None = Field(default=None, foreign_key="shifts.id")
