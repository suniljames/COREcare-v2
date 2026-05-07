"""Message thread model — one thread per Client per agency (issue #125).

The existing Message model (app.models.notification) carries individual
messages with `thread_id`. This MessageThread row anchors the thread metadata
and lets the agency-side inbox enumerate threads efficiently.
"""

import uuid
from datetime import UTC, datetime

from sqlmodel import Field

from app.models.base import TenantScopedModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class MessageThread(TenantScopedModel, table=True):
    """One thread per (Client, Agency) pair. Unique on (client_id, agency_id)."""

    __tablename__ = "message_threads"

    client_id: uuid.UUID = Field(foreign_key="clients.id", unique=True, index=True)
    last_message_at: datetime = Field(default_factory=_utcnow, index=True)
