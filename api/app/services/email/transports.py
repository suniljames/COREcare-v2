"""Email transports — pluggable backends behind the EmailSender boundary.

A transport's only job is to deliver a SendRequest's payload over the wire and
return a provider message ID. All validation, audit logging, and idempotency
live in EmailSender; transports stay dumb.

Selected at startup via settings.email_transport. The architecture-fitness
test (test_email_boundary.py) bans imports of this module from anywhere
outside app.services.email.* — feature code uses EmailSender exclusively.
"""

from __future__ import annotations

import abc
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.email.sender import SendRequest


class EmailTransport(abc.ABC):
    """Backend that physically delivers an email."""

    name: str = "abstract"

    @abc.abstractmethod
    async def deliver(self, request: SendRequest) -> str:
        """Send the message and return a provider message ID.

        Raise to signal a transport failure; EmailSender will mark the audit
        row as failed and re-raise.
        """


@dataclass
class RecordingTransport(EmailTransport):
    """In-memory transport for tests. Captures each call without delivering."""

    name: str = "recording"
    calls: list[SendRequest] = field(default_factory=list)

    async def deliver(self, request: SendRequest) -> str:
        self.calls.append(request)
        return f"recording-{uuid.uuid4()}"


@dataclass
class ConsoleTransport(EmailTransport):
    """Default dev/test transport — prints rather than delivering."""

    name: str = "console"

    async def deliver(self, request: SendRequest) -> str:
        # Intentionally print(): visible in dev, structlog in prod is on the
        # sender's audit row, not here.
        print(  # noqa: T201
            f"[email/console] to={request.recipient} "
            f"category={request.category.value} "
            f"subject={request.subject_rendered!r}"
        )
        return f"console-{uuid.uuid4()}"


class SendGridTransport(EmailTransport):
    """Production transport. Importing the SendGrid SDK is intentionally lazy —
    keeps tests / dev environments without the package installable."""

    name: str = "sendgrid"

    def __init__(self, api_key: str, from_address: str) -> None:
        if not api_key:
            raise ValueError("SENDGRID_API_KEY is required for SendGridTransport")
        self._api_key = api_key
        self._from = from_address

    async def deliver(self, request: SendRequest) -> str:  # pragma: no cover
        # Real implementation lives in a follow-up issue once SendGrid is
        # provisioned for v2. Until then, this transport is unselectable in
        # settings; tests use RecordingTransport.
        raise NotImplementedError(
            "SendGridTransport.deliver pending v2 SendGrid provisioning "
            "(see CUTOVER_PLAN.md)."
        )
