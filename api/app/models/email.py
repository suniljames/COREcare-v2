"""Email-event audit model — single audit table for all outbound email.

Issue #120 / ADR-011 commits to one EmailEvent table covering every outbound
email category (invoices, credential alerts, shift offers, weekly health, …).
v1's BillingEmailLog + InvoiceEmailLog split is explicitly not carried forward.

PHI handling:
  - subject_redacted: PII-scrubbed subject (queryable, no PHI).
  - subject_hash: SHA-256 of the rendered (non-redacted) subject — useful for
    dedup and diagnostics without storing PHI.
  - Body content lives in object storage; this row only references it via
    body_storage_uri.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlmodel import Field, UniqueConstraint

from app.models.base import TenantScopedModel


class EmailCategory(enum.StrEnum):
    """High-level category for an outbound email.

    Operators querying "did the family receive the invoice?" filter on
    (category, ref_id). Add categories here as new email features land.
    """

    INVOICE = "invoice"
    CREDENTIAL_ALERT = "credential_alert"
    SHIFT_OFFER = "shift_offer"
    WEEKLY_HEALTH = "weekly_health"
    SYSTEM = "system"


class EmailStatus(enum.StrEnum):
    """Lifecycle status of an outbound email.

    pending  — row written, transport not yet called.
    sent     — transport accepted the message.
    failed   — transport rejected or raised; error_message populated.
    bounced  — provider webhook reported a bounce (post-send).
    delivered/opened/clicked — provider webhook engagement updates.
    """

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"


class EmailEvent(TenantScopedModel, table=True):
    """One row per recipient per send attempt.

    Audit-first: this row is INSERTed before transport.deliver() is invoked, so
    a failed transport call still leaves a row with status=failed. The unique
    index on idempotency_key prevents accidental double-sends.
    """

    __tablename__ = "email_events"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_email_events_idempotency_key"),)

    category: EmailCategory = Field(index=True)
    ref_id: uuid.UUID = Field(index=True)
    recipient: str = Field(max_length=320)
    subject_redacted: str = Field(max_length=200)
    subject_hash: str = Field(max_length=64)
    body_storage_uri: str | None = Field(default=None, max_length=1024)
    attachment_count: int = Field(default=0)
    status: EmailStatus = Field(default=EmailStatus.PENDING, index=True)
    transport: str = Field(max_length=64)
    provider_message_id: str | None = Field(default=None, max_length=256)
    error_code: str | None = Field(default=None, max_length=64)
    error_message: str | None = Field(default=None, max_length=1024)
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    bounced_at: datetime | None = None
    idempotency_key: str = Field(max_length=256)
