"""Client-persona /me/* schemas (issue #125).

Schemas for the three locked Client views: care plan, schedule, messages.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ClientShiftRead(BaseModel):
    """A single upcoming shift, as seen by the Client (their own only)."""

    id: uuid.UUID
    start_time: datetime
    end_time: datetime
    caregiver_id: uuid.UUID | None
    notes: str

    model_config = {"from_attributes": True}


class ClientMessageRead(BaseModel):
    """A single message in the Client's thread with the agency."""

    id: uuid.UUID
    sender_id: uuid.UUID
    body: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ClientMessageCreate(BaseModel):
    """Body for the Client to send a message to their agency."""

    body: str = Field(min_length=1, max_length=4000)


class ClientThreadRead(BaseModel):
    """The Client's thread + messages."""

    id: uuid.UUID
    last_message_at: datetime
    messages: list[ClientMessageRead]

    model_config = {"from_attributes": True}
