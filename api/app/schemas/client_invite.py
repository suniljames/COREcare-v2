"""Client-persona invite schemas (issue #125)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class ClientInviteIssue(BaseModel):
    """Body for staff to issue an invite to a Client."""

    email: EmailStr


class ClientInviteIssueResponse(BaseModel):
    """Response after issuing an invite. Token is returned for delivery."""

    id: uuid.UUID
    client_id: uuid.UUID
    email: str
    token: str
    expires_at: datetime

    model_config = {"from_attributes": True}


class ClientInviteRedeem(BaseModel):
    """Body submitted by the Clerk-redeemed user during invite redemption."""

    token: str
    clerk_user_id: str
    clerk_email: EmailStr
