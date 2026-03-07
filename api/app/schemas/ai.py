"""AI conversation and feature schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.ai import ConversationChannel, ConversationStatus


class AIConversationCreate(BaseModel):
    channel: ConversationChannel = ConversationChannel.WEB
    external_id: str = ""


class AIMessageCreate(BaseModel):
    content: str


class AIMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    tokens_used: int
    agency_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class AIConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    channel: ConversationChannel
    status: ConversationStatus
    external_id: str
    summary: str
    agency_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class AIConversationListResponse(BaseModel):
    items: list[AIConversationResponse]
    total: int
    page: int
    size: int
