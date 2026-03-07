"""Notification, push subscription, and messaging schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.notification import NotificationChannel, NotificationType


class NotificationCreate(BaseModel):
    user_id: uuid.UUID
    notification_type: NotificationType
    channel: NotificationChannel = NotificationChannel.IN_APP
    title: str
    body: str = ""
    resource_type: str = ""
    resource_id: str = ""


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: NotificationType
    channel: NotificationChannel
    title: str
    body: str
    is_read: bool
    read_at: datetime | None
    resource_type: str
    resource_id: str
    agency_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    size: int


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh_key: str = ""
    auth_key: str = ""


class PushSubscriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    endpoint: str
    is_active: bool
    agency_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    recipient_id: uuid.UUID
    body: str
    thread_id: uuid.UUID | None = None


class MessageResponse(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    recipient_id: uuid.UUID
    thread_id: uuid.UUID
    body: str
    is_read: bool
    read_at: datetime | None
    agency_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
    page: int
    size: int
