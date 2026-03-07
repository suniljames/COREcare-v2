"""Tests for billing — invoices and line items."""

import uuid
from collections.abc import AsyncGenerator
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, Client, Invoice, InvoiceLineItem, Shift, User, Visit  # noqa: F401
from app.models.billing import InvoiceStatus
from app.schemas.billing import InvoiceCreate, InvoiceLineItemCreate, InvoiceUpdate
from app.services.billing import BillingService

TEST_DB_URL = "sqlite+aiosqlite:///./test_billing.db"
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TODAY = date.today()


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        agency = Agency(id=AGENCY_ID, name="Test Agency", slug="test-agency")
        s.add(agency)
        await s.commit()
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


async def _create_client(session: AsyncSession) -> Client:
    client = Client(
        first_name="Test",
        last_name="Client",
        agency_id=AGENCY_ID,
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client


@pytest.mark.asyncio
async def test_create_invoice_with_line_items(session: AsyncSession) -> None:
    """Creating an invoice calculates subtotal, tax, and total."""
    client = await _create_client(session)
    service = BillingService(session)

    invoice = await service.create_invoice(
        InvoiceCreate(
            client_id=client.id,
            issue_date=TODAY,
            due_date=TODAY + timedelta(days=30),
            tax_rate=Decimal("0.08"),
            line_items=[
                InvoiceLineItemCreate(
                    description="Home care - 4 hours",
                    quantity=Decimal("4"),
                    unit_price=Decimal("50.00"),
                ),
                InvoiceLineItemCreate(
                    description="Transportation",
                    quantity=Decimal("1"),
                    unit_price=Decimal("25.00"),
                ),
            ],
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    # 4*50 + 1*25 = 225, tax = 225*0.08 = 18, total = 243
    assert invoice.subtotal == Decimal("225.00")
    assert invoice.tax_amount == Decimal("18.0000")
    assert invoice.total == Decimal("243.0000")
    assert invoice.status == InvoiceStatus.DRAFT
    assert invoice.invoice_number == "INV-000001"


@pytest.mark.asyncio
async def test_sequential_invoice_numbers(session: AsyncSession) -> None:
    """Invoice numbers increment sequentially."""
    client = await _create_client(session)
    service = BillingService(session)

    inv1 = await service.create_invoice(
        InvoiceCreate(
            client_id=client.id,
            issue_date=TODAY,
            due_date=TODAY + timedelta(days=30),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    inv2 = await service.create_invoice(
        InvoiceCreate(
            client_id=client.id,
            issue_date=TODAY,
            due_date=TODAY + timedelta(days=30),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert inv1.invoice_number == "INV-000001"
    assert inv2.invoice_number == "INV-000002"


@pytest.mark.asyncio
async def test_mark_paid(session: AsyncSession) -> None:
    """Marking an invoice as paid sets status and date."""
    client = await _create_client(session)
    service = BillingService(session)

    invoice = await service.create_invoice(
        InvoiceCreate(
            client_id=client.id,
            issue_date=TODAY,
            due_date=TODAY + timedelta(days=30),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    paid = await service.mark_paid(invoice.id, paid_date=TODAY)
    await session.commit()

    assert paid is not None
    assert paid.status == InvoiceStatus.PAID
    assert paid.paid_date == TODAY


@pytest.mark.asyncio
async def test_get_line_items(session: AsyncSession) -> None:
    """Line items are retrievable after invoice creation."""
    client = await _create_client(session)
    service = BillingService(session)

    invoice = await service.create_invoice(
        InvoiceCreate(
            client_id=client.id,
            issue_date=TODAY,
            due_date=TODAY + timedelta(days=30),
            line_items=[
                InvoiceLineItemCreate(
                    description="Service A",
                    quantity=Decimal("2"),
                    unit_price=Decimal("100"),
                ),
            ],
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    items = await service.get_line_items(invoice.id)
    assert len(items) == 1
    assert items[0].description == "Service A"
    assert items[0].amount == Decimal("200")


@pytest.mark.asyncio
async def test_update_invoice_status(session: AsyncSession) -> None:
    """Updating invoice status works correctly."""
    client = await _create_client(session)
    service = BillingService(session)

    invoice = await service.create_invoice(
        InvoiceCreate(
            client_id=client.id,
            issue_date=TODAY,
            due_date=TODAY + timedelta(days=30),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    updated = await service.update_invoice(invoice.id, InvoiceUpdate(status=InvoiceStatus.SENT))
    await session.commit()

    assert updated is not None
    assert updated.status == InvoiceStatus.SENT


@pytest.mark.asyncio
async def test_list_invoices_filter_by_client(session: AsyncSession) -> None:
    """Filtering invoices by client_id returns correct subset."""
    client = await _create_client(session)
    service = BillingService(session)

    await service.create_invoice(
        InvoiceCreate(
            client_id=client.id,
            issue_date=TODAY,
            due_date=TODAY + timedelta(days=30),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    invoices, total = await service.list_invoices(client_id=client.id)
    assert total == 1

    other_invoices, other_total = await service.list_invoices(client_id=uuid.uuid4())
    assert other_total == 0
