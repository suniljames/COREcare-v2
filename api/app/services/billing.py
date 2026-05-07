"""Billing service — invoice management with line items."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Invoice, InvoiceLineItem, InvoiceStatus
from app.models.email import EmailCategory, EmailEvent
from app.schemas.billing import InvoiceCreate, InvoiceUpdate
from app.services.email import (
    EmailSender,
    IdempotencyConflictError,
    SendRequest,
    render_subjects,
)


class BillingService:
    """CRUD for invoices and line items, plus invoice email."""

    def __init__(self, session: AsyncSession, *, sender: EmailSender | None = None) -> None:
        self.session = session
        self.sender = sender

    async def list_invoices(
        self,
        *,
        page: int = 1,
        size: int = 20,
        client_id: uuid.UUID | None = None,
        status: InvoiceStatus | None = None,
    ) -> tuple[list[Invoice], int]:
        query = select(Invoice)
        if client_id:
            query = query.where(
                Invoice.client_id == client_id  # type: ignore[arg-type]
            )
        if status:
            query = query.where(Invoice.status == status)  # type: ignore[arg-type]

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.offset((page - 1) * size).limit(size).order_by(Invoice.issue_date.desc())  # type: ignore[attr-defined]
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_invoice(self, invoice_id: uuid.UUID) -> Invoice | None:
        result = await self.session.execute(
            select(Invoice).where(Invoice.id == invoice_id)  # type: ignore[arg-type]
        )
        return result.scalar_one_or_none()

    async def _generate_invoice_number(self, agency_id: uuid.UUID) -> str:
        """Generate sequential invoice number per agency."""
        count_result = await self.session.execute(
            select(func.count()).select_from(Invoice).where(Invoice.agency_id == agency_id)  # type: ignore[arg-type]
        )
        count = (count_result.scalar() or 0) + 1
        return f"INV-{count:06d}"

    async def create_invoice(self, data: InvoiceCreate, agency_id: uuid.UUID) -> Invoice:
        invoice_number = await self._generate_invoice_number(agency_id)

        # Calculate line item amounts
        subtotal = Decimal("0")
        line_items: list[InvoiceLineItem] = []
        for item_data in data.line_items:
            amount = item_data.quantity * item_data.unit_price
            line_item = InvoiceLineItem(
                description=item_data.description,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                amount=amount,
                shift_id=item_data.shift_id,
                agency_id=agency_id,
            )
            subtotal += amount
            line_items.append(line_item)

        tax_amount = subtotal * data.tax_rate
        total = subtotal + tax_amount

        invoice = Invoice(
            client_id=data.client_id,
            invoice_number=invoice_number,
            issue_date=data.issue_date,
            due_date=data.due_date,
            status=InvoiceStatus.DRAFT,
            subtotal=subtotal,
            tax_rate=data.tax_rate,
            tax_amount=tax_amount,
            total=total,
            notes=data.notes,
            agency_id=agency_id,
        )
        self.session.add(invoice)
        await self.session.flush()
        await self.session.refresh(invoice)

        # Attach line items to invoice
        for li in line_items:
            li.invoice_id = invoice.id
            self.session.add(li)
        await self.session.flush()

        return invoice

    async def update_invoice(self, invoice_id: uuid.UUID, data: InvoiceUpdate) -> Invoice | None:
        invoice = await self.get_invoice(invoice_id)
        if invoice is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(invoice, field, value)

        self.session.add(invoice)
        await self.session.flush()
        await self.session.refresh(invoice)
        return invoice

    async def mark_paid(
        self, invoice_id: uuid.UUID, paid_date: date | None = None
    ) -> Invoice | None:
        invoice = await self.get_invoice(invoice_id)
        if invoice is None:
            return None

        invoice.status = InvoiceStatus.PAID
        invoice.paid_date = paid_date or date.today()
        self.session.add(invoice)
        await self.session.flush()
        await self.session.refresh(invoice)
        return invoice

    async def get_line_items(self, invoice_id: uuid.UUID) -> list[InvoiceLineItem]:
        result = await self.session.execute(
            select(InvoiceLineItem).where(
                InvoiceLineItem.invoice_id == invoice_id  # type: ignore[arg-type]
            )
        )
        return list(result.scalars().all())

    async def email_invoice(
        self,
        invoice_id: uuid.UUID,
        *,
        agency_id: uuid.UUID,
        recipients: list[str],
    ) -> list[EmailEvent]:
        """Email an invoice's PDF to one or more recipients (issue #120 / ADR-011).

        Returns one EmailEvent per recipient. Idempotent on
        (invoice_id, recipient): a second call with the same recipient returns
        the original event without a re-send.

        Cross-tenant requests get an empty list (the agency_id passed by the
        caller does not match the invoice's tenant); on PostgreSQL the same
        property holds via RLS and the invoice lookup returns None.
        """
        if self.sender is None:
            raise RuntimeError(
                "BillingService was constructed without an EmailSender; "
                "wire one via BillingService(session, sender=...)"
            )

        invoice = await self.get_invoice(invoice_id)
        if invoice is None or invoice.agency_id != agency_id:
            return []

        events: list[EmailEvent] = []
        for recipient in recipients:
            template = "Invoice {invoice_number} from your care agency"
            params = {"invoice_number": invoice.invoice_number}
            rendered, redacted = render_subjects(template, params)
            req = SendRequest(
                agency_id=agency_id,
                category=EmailCategory.INVOICE,
                ref_id=invoice.id,
                recipient=recipient,
                subject_redacted=redacted,
                subject_rendered=rendered,
                body=(
                    f"Your invoice {invoice.invoice_number} is attached. "
                    f"Total due: {invoice.total}."
                ),
                attachments=[
                    {
                        "filename": f"invoice-{invoice.invoice_number}.pdf",
                        "content_type": "application/pdf",
                    }
                ],
                idempotency_key=f"invoice:{invoice.id}:{recipient}",
            )
            try:
                event = await self.sender.send(req)
            except IdempotencyConflictError:
                continue
            events.append(event)
        return events
