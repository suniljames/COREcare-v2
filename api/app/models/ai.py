"""AI agent and conversation models."""

import enum
import uuid

from sqlmodel import Column, Field, Text

from app.models.base import TenantScopedModel


class ConversationChannel(enum.StrEnum):
    WEB = "web"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class ConversationStatus(enum.StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    ESCALATED = "escalated"


class AIConversation(TenantScopedModel, table=True):
    """An AI agent conversation with a user."""

    __tablename__ = "ai_conversations"

    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    channel: ConversationChannel = Field(default=ConversationChannel.WEB, index=True)
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE, index=True)
    external_id: str = Field(default="", max_length=200)
    summary: str = Field(default="", sa_column=Column(Text))


class AIMessage(TenantScopedModel, table=True):
    """A message in an AI conversation."""

    __tablename__ = "ai_messages"

    conversation_id: uuid.UUID = Field(foreign_key="ai_conversations.id", index=True)
    role: str = Field(max_length=20)  # "user", "assistant", "system"
    content: str = Field(sa_column=Column(Text))
    tokens_used: int = Field(default=0)


class AIFeatureFlag(TenantScopedModel, table=True):
    """Feature flags for AI capabilities per agency."""

    __tablename__ = "ai_feature_flags"

    feature_name: str = Field(max_length=100, index=True)
    is_enabled: bool = Field(default=False)
    config_json: str = Field(default="{}", sa_column=Column(Text))
