"""Outbound email — single boundary for all email leaving v2.

ADR-011 commits to a single sender (EmailSender) and a single audit table
(EmailEvent). No router, feature service, or background job calls a transport
SDK directly. The architecture-fitness test in
api/app/tests/architecture/test_email_boundary.py enforces this at CI time.

Public API (importable by feature code):
    EmailSender, EmailValidationError, IdempotencyConflict,
    SendRequest, SendResult, make_email_sender, render_subjects
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.email.redaction import render_subjects
from app.services.email.sender import (
    EmailSender,
    EmailValidationError,
    IdempotencyConflict,
    SendRequest,
    SendResult,
)
from app.services.email.transports import (
    ConsoleTransport,
    EmailTransport,
    SendGridTransport,
)


def make_email_sender(session: AsyncSession) -> EmailSender:
    """Construct an EmailSender using the configured transport.

    Selected at startup via settings.email_transport. Routers depend on this
    factory rather than instantiating transports directly — that keeps the
    architecture-fitness rule clean (only this package imports transports).
    """
    transport: EmailTransport
    name = settings.email_transport.lower()
    if name == "sendgrid":
        transport = SendGridTransport(
            api_key=settings.sendgrid_api_key,
            from_address=settings.email_from_address,
        )
    else:
        transport = ConsoleTransport()
    return EmailSender(session, transport=transport)


__all__ = [
    "EmailSender",
    "EmailValidationError",
    "IdempotencyConflict",
    "SendRequest",
    "SendResult",
    "make_email_sender",
    "render_subjects",
]
