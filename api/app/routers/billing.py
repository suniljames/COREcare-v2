"""Billing and invoicing API endpoints."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.billing import InvoiceStatus
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.billing import (
    InvoiceCreate,
    InvoiceLineItemResponse,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
)
from app.services.billing import BillingService

router = APIRouter(prefix="/api/invoices", tags=["billing"])


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    page: int = 1,
    size: int = 20,
    client_id: uuid.UUID | None = None,
    invoice_status: InvoiceStatus | None = None,
    _user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> InvoiceListResponse:
    """List invoices with filtering. Requires care_manager+."""
    service = BillingService(session)
    invoices, total = await service.list_invoices(
        page=page, size=size, client_id=client_id, status=invoice_status
    )
    return InvoiceListResponse(
        items=[InvoiceResponse.model_validate(i) for i in invoices],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> InvoiceResponse:
    """Get an invoice by ID. Requires care_manager+."""
    service = BillingService(session)
    invoice = await service.get_invoice(invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceResponse.model_validate(invoice)


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> InvoiceResponse:
    """Create an invoice with line items. Requires agency_admin+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = BillingService(session)
    invoice = await service.create_invoice(data, agency_id=admin.agency_id)
    return InvoiceResponse.model_validate(invoice)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    data: InvoiceUpdate,
    _admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> InvoiceResponse:
    """Update an invoice. Requires agency_admin+."""
    service = BillingService(session)
    invoice = await service.update_invoice(invoice_id, data)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/pay", response_model=InvoiceResponse)
async def mark_invoice_paid(
    invoice_id: uuid.UUID,
    paid_date: date | None = None,
    _admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> InvoiceResponse:
    """Mark an invoice as paid. Requires agency_admin+."""
    service = BillingService(session)
    invoice = await service.mark_paid(invoice_id, paid_date=paid_date)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceResponse.model_validate(invoice)


@router.get(
    "/{invoice_id}/line-items",
    response_model=list[InvoiceLineItemResponse],
)
async def get_line_items(
    invoice_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[InvoiceLineItemResponse]:
    """Get line items for an invoice. Requires care_manager+."""
    service = BillingService(session)
    items = await service.get_line_items(invoice_id)
    return [InvoiceLineItemResponse.model_validate(i) for i in items]
