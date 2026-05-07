"""Client-persona invite token model (issue #125).

Single-use, time-boxed invite issued by Care Manager / Agency Admin to a
specific Client + email. Redemption matches the email and links the User to
the Client via `clients.client_user_id`.
"""

import uuid
from datetime import datetime

from sqlmodel import Field

from app.models.base import TenantScopedModel


class ClientInvite(TenantScopedModel, table=True):
    """An outstanding invite for a Client to set up their own account."""

    __tablename__ = "client_invites"

    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    email: str = Field(index=True)
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    redeemed_at: datetime | None = Field(default=None, index=True)
    issued_by_user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
