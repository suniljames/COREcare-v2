"""Tests for BillingService.email_invoice — feature-layer integration.

Confirms that:
  - A successful send writes exactly one EmailEvent row with category=INVOICE,
    ref_id=invoice.id, agency_id matching the invoice's tenant, status=SENT.
  - Idempotency at the feature layer: re-emailing the same invoice to the same
    recipient is a no-op (no second row).
  - Multi-recipient: one row per recipient, each with its own idempotency_key.
  - Cross-tenant isolation: an agency-B request for an agency-A invoice gets a
    404 with no row written and no transport call.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

from app.models import Agency, Client, Invoice, InvoiceLineItem  # noqa: F401
from app.models.email import EmailCategory, EmailEvent, EmailStatus
from app.schemas.billing import InvoiceCreate, InvoiceLineItemCreate
from app.services.billing import BillingService
from app.services.email.sender import EmailSender
from app.services.email.transports import RecordingTransport

TEST_DB_URL = "sqlite+aiosqlite:///./test_billing_email.db"
AGENCY_A = uuid.UUID("00000000-0000-0000-0000-00000000000a")
AGENCY_B = uuid.UUID("00000000-0000-0000-0000-00000000000b")
TODAY = date.today()


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        s.add(Agency(id=AGENCY_A, name="Agency A", slug="a"))
        s.add(Agency(id=AGENCY_B, name="Agency B", slug="b"))
        await s.commit()
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


async def _make_invoice(session: AsyncSession, agency_id: uuid.UUID) -> Invoice:
    client = Client(first_name="Test", last_name="Client", agency_id=agency_id)
    session.add(client)
    await session.commit()
    await session.refresh(client)

    service = BillingService(session)
    invoice = await service.create_invoice(
        InvoiceCreate(
            client_id=client.id,
            issue_date=TODAY,
            due_date=TODAY + timedelta(days=30),
            line_items=[
                InvoiceLineItemCreate(
                    description="Care",
                    quantity=Decimal("4"),
                    unit_price=Decimal("50"),
                ),
            ],
        ),
        agency_id=agency_id,
    )
    await session.commit()
    return invoice


@pytest.mark.asyncio
async def test_email_invoice_writes_one_event_per_recipient(
    session: AsyncSession,
) -> None:
    invoice = await _make_invoice(session, AGENCY_A)
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)
    service = BillingService(session, sender=sender)

    events = await service.email_invoice(
        invoice.id,
        agency_id=AGENCY_A,
        recipients=["family@example.com"],
    )
    await session.commit()

    assert len(events) == 1
    e = events[0]
    assert e.category == EmailCategory.INVOICE
    assert e.ref_id == invoice.id
    assert e.agency_id == AGENCY_A
    assert e.status == EmailStatus.SENT
    assert e.recipient == "family@example.com"
    assert len(transport.calls) == 1


@pytest.mark.asyncio
async def test_email_invoice_idempotent_for_same_recipient(
    session: AsyncSession,
) -> None:
    invoice = await _make_invoice(session, AGENCY_A)
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)
    service = BillingService(session, sender=sender)

    first = await service.email_invoice(
        invoice.id, agency_id=AGENCY_A, recipients=["family@example.com"]
    )
    await session.commit()
    second = await service.email_invoice(
        invoice.id, agency_id=AGENCY_A, recipients=["family@example.com"]
    )
    await session.commit()

    assert first[0].id == second[0].id
    rows = (
        (await session.execute(select(EmailEvent).where(EmailEvent.ref_id == invoice.id)))
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert len(transport.calls) == 1


@pytest.mark.asyncio
async def test_email_invoice_multi_recipient_writes_one_row_each(
    session: AsyncSession,
) -> None:
    invoice = await _make_invoice(session, AGENCY_A)
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)
    service = BillingService(session, sender=sender)

    recipients = [
        "family1@example.com",
        "family2@example.com",
        "family3@example.com",
    ]
    events = await service.email_invoice(invoice.id, agency_id=AGENCY_A, recipients=recipients)
    await session.commit()

    assert len(events) == 3
    assert {e.recipient for e in events} == set(recipients)
    keys = {e.idempotency_key for e in events}
    assert len(keys) == 3, "each recipient gets a distinct idempotency key"
    assert len(transport.calls) == 3


@pytest.mark.asyncio
async def test_email_invoice_cross_tenant_returns_none_and_writes_nothing(
    session: AsyncSession,
) -> None:
    """Agency B requesting Agency A's invoice gets None back, no row, no send.

    On real PostgreSQL with RLS, the cross-tenant lookup returns no row. On
    SQLite (this test) we simulate by passing the requesting agency_id and
    asserting the service refuses to email an invoice it cannot see.
    """
    invoice = await _make_invoice(session, AGENCY_A)
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)
    service = BillingService(session, sender=sender)

    result = await service.email_invoice(
        invoice.id, agency_id=AGENCY_B, recipients=["family@example.com"]
    )

    assert result == []
    rows = (await session.execute(select(EmailEvent))).scalars().all()
    assert rows == []
    assert transport.calls == []
