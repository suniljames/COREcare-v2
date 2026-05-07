"""EmailSender — the single outbound-email boundary for v2 (ADR-011 / issue #120).

All outbound email crosses this seam:
  router  ──►  feature service  ──►  EmailSender.send  ──►  EmailTransport.deliver

Hard contracts:
  1. Subject is hard-rejected if it contains CR/LF/NUL, exceeds 200 chars, or
     is empty. No sanitize-and-continue.
  2. Recipient is hard-rejected if malformed.
  3. The EmailEvent audit row is INSERTed before transport.deliver() — a failed
     transport call still leaves a row with status=failed.
  4. idempotency_key is UNIQUE in the database. Re-sending with the same key
     returns the existing event without a transport call. A pending event with
     the same key raises IdempotencyConflictError.
  5. agency_id is required on every send and is re-validated against the
     session's tenant context (when available).

This module is intentionally the only place in the codebase that imports
transports. The architecture-fitness test enforces that.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.email import EmailCategory, EmailEvent, EmailStatus
from app.services.email.transports import EmailTransport
from app.tenant import get_tenant_context

logger = structlog.get_logger()

_MAX_SUBJECT_LEN = 200
_MAX_RECIPIENT_LEN = 320
_FORBIDDEN_SUBJECT_CHARS = ("\r", "\n", "\x00")
# Deliberately permissive but rejects obvious garbage. Real validation
# delegated to the transport / RFC 5321 at delivery time.
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class EmailValidationError(ValueError):
    """Raised when a SendRequest fails the boundary validation contract."""


class IdempotencyConflictError(RuntimeError):
    """Raised when a pending event with the same idempotency_key exists."""


@dataclass
class SendRequest:
    """One outbound email to one recipient.

    subject_rendered is what the recipient sees (may contain PHI).
    subject_redacted is what the audit row stores (PHI-scrubbed).
    Use app.services.email.redaction.render_subjects to produce both from a
    single template + parameter dict.
    """

    agency_id: uuid.UUID
    category: EmailCategory
    ref_id: uuid.UUID
    recipient: str
    subject_redacted: str
    subject_rendered: str
    body: str
    attachments: list[dict[str, Any]] = field(default_factory=list)
    idempotency_key: str = ""


@dataclass
class SendResult:
    """Outcome of a send attempt (returned to callers that prefer a value over
    raising on transport failure)."""

    event: EmailEvent
    delivered: bool
    error: Exception | None = None


class EmailSender:
    """The single outbound-email boundary."""

    def __init__(self, session: AsyncSession, *, transport: EmailTransport) -> None:
        self.session = session
        self.transport = transport

    async def send(self, request: SendRequest) -> EmailEvent:
        """Validate, audit-write, deliver, finalize. Returns the EmailEvent.

        Re-raises any exception from the transport after marking the audit row
        as failed. Returns the existing event for an idempotency-key match
        already in 'sent' status. Raises IdempotencyConflictError if a pending event
        exists for the same key.
        """
        self._validate(request)
        await self._check_tenant_context(request.agency_id)

        existing = await self._lookup_idempotent(request.idempotency_key)
        if existing is not None:
            if existing.status == EmailStatus.SENT:
                return existing
            if existing.status == EmailStatus.PENDING:
                raise IdempotencyConflictError(
                    f"send already in flight for idempotency_key={request.idempotency_key}"
                )
            # Failed prior attempts may be retried by issuing a new key —
            # we do NOT silently retry under the same key.
            raise IdempotencyConflictError(
                f"prior send for key={request.idempotency_key} ended in "
                f"status={existing.status.value}; use a fresh key to retry"
            )

        event = EmailEvent(
            agency_id=request.agency_id,
            category=request.category,
            ref_id=request.ref_id,
            recipient=request.recipient,
            subject_redacted=request.subject_redacted,
            subject_hash=hashlib.sha256(request.subject_rendered.encode()).hexdigest(),
            attachment_count=len(request.attachments),
            status=EmailStatus.PENDING,
            transport=self.transport.name,
            idempotency_key=request.idempotency_key,
        )
        # SAVEPOINT-scope the insert so a UNIQUE-constraint race rolls back ONLY
        # the failed insert — not the surrounding request transaction. Without
        # this, a concurrent send with the same idempotency_key would silently
        # discard any earlier work the request had done (e.g., a future
        # "create-invoice-and-email" flow).
        try:
            async with self.session.begin_nested():
                self.session.add(event)
                await self.session.flush()
        except IntegrityError as exc:
            raise IdempotencyConflictError(
                f"idempotency_key={request.idempotency_key} already in use"
            ) from exc

        try:
            provider_id = await self.transport.deliver(request)
        except Exception as exc:
            event.status = EmailStatus.FAILED
            event.error_message = str(exc)[:1024]
            event.error_code = type(exc).__name__[:64]
            self.session.add(event)
            await self.session.flush()
            await logger.aerror(
                "email_send_failed",
                event_id=str(event.id),
                category=request.category.value,
                ref_id=str(request.ref_id),
                agency_id=str(request.agency_id),
                transport=self.transport.name,
                error=event.error_code,
            )
            raise

        event.status = EmailStatus.SENT
        event.sent_at = datetime.now(UTC)
        event.provider_message_id = provider_id
        self.session.add(event)
        await self.session.flush()

        await logger.ainfo(
            "email_sent",
            event_id=str(event.id),
            category=request.category.value,
            ref_id=str(request.ref_id),
            agency_id=str(request.agency_id),
            transport=self.transport.name,
            provider_message_id=provider_id,
        )
        return event

    # --- internals -------------------------------------------------------- #

    def _validate(self, request: SendRequest) -> None:
        # Subject — both rendered (delivered) and redacted (stored) must be safe.
        for label, subject in (
            ("subject_rendered", request.subject_rendered),
            ("subject_redacted", request.subject_redacted),
        ):
            if not subject:
                raise EmailValidationError(f"{label} is required")
            if any(ch in subject for ch in _FORBIDDEN_SUBJECT_CHARS):
                raise EmailValidationError(
                    f"{label} contains a forbidden control character (CR/LF/NUL)"
                )
            if len(subject) > _MAX_SUBJECT_LEN:
                raise EmailValidationError(f"{label} exceeds {_MAX_SUBJECT_LEN} chars")

        # Recipient.
        recip = request.recipient
        if not recip or not _EMAIL_RE.match(recip) or len(recip) > _MAX_RECIPIENT_LEN:
            raise EmailValidationError(f"recipient is malformed: {recip!r}")

        if not request.idempotency_key:
            raise EmailValidationError("idempotency_key is required")

    async def _check_tenant_context(self, agency_id: uuid.UUID) -> None:
        ctx = await get_tenant_context(self.session)
        if ctx is not None and ctx != agency_id:
            raise EmailValidationError(
                f"send agency_id={agency_id} does not match RLS tenant context={ctx}"
            )

    async def _lookup_idempotent(self, key: str) -> EmailEvent | None:
        result = await self.session.execute(
            select(EmailEvent).where(EmailEvent.idempotency_key == key)
        )
        return result.scalar_one_or_none()
