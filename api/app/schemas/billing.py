"""Billing and invoicing request/response schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.billing import InvoiceStatus


class InvoiceLineItemCreate(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")
    shift_id: uuid.UUID | None = None


class InvoiceLineItemResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    shift_id: uuid.UUID | None
    agency_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceCreate(BaseModel):
    client_id: uuid.UUID
    issue_date: date
    due_date: date
    tax_rate: Decimal = Decimal("0")
    notes: str = ""
    line_items: list[InvoiceLineItemCreate] = []


class InvoiceUpdate(BaseModel):
    status: InvoiceStatus | None = None
    due_date: date | None = None
    notes: str | None = None
    paid_date: date | None = None


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    invoice_number: str
    issue_date: date
    due_date: date
    status: InvoiceStatus
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    notes: str
    paid_date: date | None
    agency_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    total: int
    page: int
    size: int


class InvoiceEmailRequest(BaseModel):
    """Request body for POST /api/invoices/{invoice_id}/email."""

    recipients: list[str]


class InvoiceEmailEvent(BaseModel):
    """Per-recipient send result returned by the email endpoint."""

    id: uuid.UUID
    recipient: str
    status: str
    sent_at: datetime | None
    provider_message_id: str | None

    model_config = {"from_attributes": True}


class InvoiceEmailResponse(BaseModel):
    invoice_id: uuid.UUID
    events: list[InvoiceEmailEvent]
