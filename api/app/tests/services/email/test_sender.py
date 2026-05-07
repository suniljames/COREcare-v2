"""Tests for app.services.email.sender — the single outbound-email boundary.

Issue #120 commits to:
  1. Hard-reject CRLF / NUL / over-length / empty subjects.
  2. Hard-reject malformed / empty recipients.
  3. Audit-first ordering — EmailEvent row written before transport.deliver().
  4. Idempotency — UNIQUE on idempotency_key; second send with same key returns the
     existing event without a new transport call.
  5. Tenant re-validation — sender raises if caller's agency_id mismatches the RLS
     context.
  6. PHI redaction — outbound subject is the rendered template; the audit row stores
     a redacted subject + SHA-256 hash of the rendered subject.
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

from app.models import Agency  # noqa: F401 — register for metadata
from app.models.email import EmailCategory, EmailEvent, EmailStatus
from app.services.email.sender import (
    EmailSender,
    EmailValidationError,
    IdempotencyConflictError,
    SendRequest,
)
from app.services.email.transports import EmailTransport, RecordingTransport

TEST_DB_URL = "sqlite+aiosqlite:///./test_email_sender.db"
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        agency = Agency(id=AGENCY_ID, name="Test Agency", slug="test-agency")
        other = Agency(id=OTHER_AGENCY_ID, name="Other Agency", slug="other-agency")
        s.add(agency)
        s.add(other)
        await s.commit()
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


def _make_request(
    *,
    subject: str = "Invoice ready",
    rendered_subject: str | None = None,
    recipients: list[str] | None = None,
    idempotency_key: str | None = None,
    body: str = "Body text",
    attachments: list[dict[str, Any]] | None = None,
    category: EmailCategory = EmailCategory.INVOICE,
    ref_id: uuid.UUID | None = None,
    agency_id: uuid.UUID = AGENCY_ID,
) -> SendRequest:
    return SendRequest(
        agency_id=agency_id,
        category=category,
        ref_id=ref_id or uuid.uuid4(),
        recipient=(recipients or ["family@example.com"])[0],
        subject_redacted=subject,
        subject_rendered=rendered_subject or subject,
        body=body,
        attachments=attachments or [],
        idempotency_key=idempotency_key or f"test-{uuid.uuid4()}",
    )


# --------------------------------------------------------------------------- #
# Layer 1 — subject validation: hard-reject
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_subject",
    [
        "Invoice\r\nBcc: attacker@example.com",
        "Invoice\nBcc: x",
        "Invoice\rRogue",
        "Invoice with NUL\x00byte",
        "Carriage \r return",
    ],
)
async def test_sender_rejects_crlf_and_nul_in_subject(
    session: AsyncSession, bad_subject: str
) -> None:
    """Subjects containing CR, LF, CRLF, or NUL bytes must be hard-rejected."""
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)

    with pytest.raises(EmailValidationError):
        await sender.send(_make_request(subject=bad_subject, rendered_subject=bad_subject))

    rows = (await session.execute(select(EmailEvent))).scalars().all()
    assert rows == []
    assert transport.calls == []


@pytest.mark.asyncio
async def test_sender_rejects_subject_over_200_chars(session: AsyncSession) -> None:
    """A 201-char subject must be hard-rejected."""
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)
    overflow = "x" * 201

    with pytest.raises(EmailValidationError):
        await sender.send(_make_request(subject=overflow, rendered_subject=overflow))

    assert transport.calls == []


@pytest.mark.asyncio
async def test_sender_accepts_subject_at_200_chars(session: AsyncSession) -> None:
    """The 200-char boundary is inclusive."""
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)
    boundary = "x" * 200

    event = await sender.send(_make_request(subject=boundary, rendered_subject=boundary))
    await session.commit()

    assert event.status == EmailStatus.SENT
    assert len(transport.calls) == 1


@pytest.mark.asyncio
async def test_sender_rejects_empty_subject(session: AsyncSession) -> None:
    """An empty subject must be hard-rejected (subject is required)."""
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)

    with pytest.raises(EmailValidationError):
        await sender.send(_make_request(subject="", rendered_subject=""))

    assert transport.calls == []


# --------------------------------------------------------------------------- #
# Layer 1 — recipient validation
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_recipient",
    [
        "notanemail",
        "a@",
        "@b",
        "no-at-symbol-here.example.com",
        "x" * 321 + "@example.com",  # >320 char total length
        "",
    ],
)
async def test_sender_rejects_malformed_recipient(
    session: AsyncSession, bad_recipient: str
) -> None:
    """Malformed recipients must be hard-rejected."""
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)
    req = _make_request()
    req.recipient = bad_recipient

    with pytest.raises(EmailValidationError):
        await sender.send(req)

    assert transport.calls == []


# --------------------------------------------------------------------------- #
# Layer 1 — audit-first ordering
# --------------------------------------------------------------------------- #


class _FailingTransport(EmailTransport):
    name = "failing"

    async def deliver(self, request: SendRequest) -> str:
        raise RuntimeError("transport down")


@pytest.mark.asyncio
async def test_sender_writes_failed_event_when_transport_raises(
    session: AsyncSession,
) -> None:
    """If transport.deliver() raises, an EmailEvent row exists with status=failed."""
    sender = EmailSender(session, transport=_FailingTransport())

    with pytest.raises(RuntimeError, match="transport down"):
        await sender.send(_make_request())
    await session.commit()

    rows = (await session.execute(select(EmailEvent))).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == EmailStatus.FAILED
    assert rows[0].error_message is not None
    assert "transport down" in rows[0].error_message


@pytest.mark.asyncio
async def test_sender_writes_event_before_transport_call(session: AsyncSession) -> None:
    """The audit row must be flushed before transport.deliver() is invoked."""
    saw_event_at_send_time: list[bool] = []

    class _SnoopingTransport(EmailTransport):
        name = "snoop"

        def __init__(self, sess: AsyncSession) -> None:
            self.sess = sess

        async def deliver(self, request: SendRequest) -> str:
            rows = (await self.sess.execute(select(EmailEvent))).scalars().all()
            saw_event_at_send_time.append(len(rows) >= 1)
            return "snoop-msg-id"

    sender = EmailSender(session, transport=_SnoopingTransport(session))
    await sender.send(_make_request())
    await session.commit()

    assert saw_event_at_send_time == [True]


# --------------------------------------------------------------------------- #
# Layer 1 — idempotency
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_sender_returns_existing_event_for_duplicate_key(
    session: AsyncSession,
) -> None:
    """Second send() with the same idempotency_key returns the original event,
    writes no new row, and makes no transport call."""
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)
    key = "dup-key-001"

    first = await sender.send(_make_request(idempotency_key=key))
    await session.commit()
    assert len(transport.calls) == 1

    second = await sender.send(_make_request(idempotency_key=key))
    await session.commit()

    assert second.id == first.id
    rows = (await session.execute(select(EmailEvent))).scalars().all()
    assert len(rows) == 1
    assert len(transport.calls) == 1


@pytest.mark.asyncio
async def test_sender_idempotency_conflict_on_in_flight_duplicate(
    session: AsyncSession,
) -> None:
    """If a row with the same key exists in 'pending' status, raise IdempotencyConflictError."""
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)
    key = "in-flight-key"

    # Pre-seed a pending event (simulates a concurrent in-flight send).
    pending = EmailEvent(
        agency_id=AGENCY_ID,
        category=EmailCategory.INVOICE,
        ref_id=uuid.uuid4(),
        recipient="family@example.com",
        subject_redacted="Invoice",
        subject_hash="abc",
        status=EmailStatus.PENDING,
        transport="recording",
        idempotency_key=key,
    )
    session.add(pending)
    await session.commit()

    with pytest.raises(IdempotencyConflictError):
        await sender.send(_make_request(idempotency_key=key))


@pytest.mark.asyncio
async def test_sender_rejects_retry_with_same_key_after_failed_send(
    session: AsyncSession,
) -> None:
    """A prior FAILED send is NOT silently retried under the same key. The
    caller must mint a fresh idempotency_key — protects against retry storms
    masking persistent transport failures.
    """
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)
    key = "prior-failed-key"

    failed = EmailEvent(
        agency_id=AGENCY_ID,
        category=EmailCategory.INVOICE,
        ref_id=uuid.uuid4(),
        recipient="family@example.com",
        subject_redacted="Invoice",
        subject_hash="abc",
        status=EmailStatus.FAILED,
        transport="recording",
        idempotency_key=key,
        error_code="RuntimeError",
        error_message="prior transport failure",
    )
    session.add(failed)
    await session.commit()

    with pytest.raises(IdempotencyConflictError, match="status=failed"):
        await sender.send(_make_request(idempotency_key=key))

    # No new row, no transport call.
    rows = (await session.execute(select(EmailEvent))).scalars().all()
    assert len(rows) == 1
    assert rows[0].id == failed.id
    assert transport.calls == []


# --------------------------------------------------------------------------- #
# Layer 1 — tenant re-validation
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_sender_rejects_mismatched_tenant_context(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If a tenant context is set on the session and disagrees with request.agency_id,
    sender raises EmailValidationError before writing or sending.

    SQLite has no RLS, so we patch get_tenant_context to simulate a context set
    to a different agency. On real PostgreSQL the same property holds via RLS.
    """
    from app.services.email import sender as sender_mod

    async def _fake_get_tenant_context(_sess: AsyncSession) -> uuid.UUID | None:
        return OTHER_AGENCY_ID

    monkeypatch.setattr(sender_mod, "get_tenant_context", _fake_get_tenant_context)

    transport = RecordingTransport()
    s = EmailSender(session, transport=transport)

    with pytest.raises(EmailValidationError):
        await s.send(_make_request(agency_id=AGENCY_ID))

    assert transport.calls == []


# --------------------------------------------------------------------------- #
# Layer 1 — PHI redaction
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_sender_stores_redacted_subject_and_hash(session: AsyncSession) -> None:
    """outbound transport sees the rendered subject; audit row stores
    subject_redacted (PHI-scrubbed) and subject_hash (SHA-256 of rendered subject)."""
    transport = RecordingTransport()
    sender = EmailSender(session, transport=transport)

    rendered = "Invoice for Jane Doe"
    redacted = "Invoice for <client>"
    req = _make_request(subject=redacted, rendered_subject=rendered)

    event = await sender.send(req)
    await session.commit()

    # Outbound payload sees the rendered (non-redacted) subject.
    assert transport.calls[0].subject_rendered == rendered
    # Audit row stores the redacted subject + hash of rendered.
    assert event.subject_redacted == redacted
    assert event.subject_hash == hashlib.sha256(rendered.encode()).hexdigest()
    # Raw rendered subject is NOT stored anywhere on the event.
    assert event.subject_redacted != rendered
