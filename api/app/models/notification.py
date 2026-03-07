"""Notification and messaging models."""

import enum
import uuid
from datetime import datetime

from sqlmodel import Column, Field, Text

from app.models.base import TenantScopedModel


class NotificationType(enum.StrEnum):
    SHIFT_ASSIGNED = "shift_assigned"
    SHIFT_CANCELLED = "shift_cancelled"
    SHIFT_REMINDER = "shift_reminder"
    CREDENTIAL_EXPIRING = "credential_expiring"
    PAYROLL_APPROVED = "payroll_approved"
    INVOICE_SENT = "invoice_sent"
    CHART_SIGNED = "chart_signed"
    MESSAGE_RECEIVED = "message_received"
    SYSTEM = "system"


class NotificationChannel(enum.StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"


class Notification(TenantScopedModel, table=True):
    """An in-app notification for a user."""

    __tablename__ = "notifications"

    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    notification_type: NotificationType = Field(index=True)
    channel: NotificationChannel = Field(default=NotificationChannel.IN_APP)
    title: str = Field(max_length=200)
    body: str = Field(default="", sa_column=Column(Text))
    is_read: bool = Field(default=False, index=True)
    read_at: datetime | None = None
    resource_type: str = Field(default="", max_length=50)
    resource_id: str = Field(default="", max_length=100)


class PushSubscription(TenantScopedModel, table=True):
    """A Web Push subscription for a user's device."""

    __tablename__ = "push_subscriptions"

    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    endpoint: str = Field(sa_column=Column(Text))
    p256dh_key: str = Field(default="", max_length=500)
    auth_key: str = Field(default="", max_length=500)
    is_active: bool = Field(default=True)


class Message(TenantScopedModel, table=True):
    """A HIPAA-safe message between users (family messaging)."""

    __tablename__ = "messages"

    sender_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    recipient_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    thread_id: uuid.UUID = Field(index=True)
    body: str = Field(sa_column=Column(Text))
    is_read: bool = Field(default=False)
    read_at: datetime | None = None
