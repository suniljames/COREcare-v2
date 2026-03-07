"""Notification, push subscription, and messaging API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.notification import (
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    NotificationCreate,
    NotificationListResponse,
    NotificationResponse,
    PushSubscriptionCreate,
    PushSubscriptionResponse,
)
from app.services.notification import NotificationService

router = APIRouter(prefix="/api", tags=["notifications"])


# --- Notifications ---


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    page: int = 1,
    size: int = 20,
    unread_only: bool = False,
    user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> NotificationListResponse:
    """List current user's notifications. Any authenticated user."""
    service = NotificationService(session)
    notifications, total = await service.list_notifications(
        user_id=user.id, page=page, size=size, unread_only=unread_only
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        size=size,
    )


@router.get("/notifications/unread-count")
async def unread_count(
    user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict[str, int]:
    """Get unread notification count. Any authenticated user."""
    service = NotificationService(session)
    count = await service.get_unread_count(user.id)
    return {"count": count}


@router.post(
    "/notifications",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    data: NotificationCreate,
    admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> NotificationResponse:
    """Create a notification. Requires care_manager+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = NotificationService(session)
    notification = await service.create_notification(data, agency_id=admin.agency_id)
    return NotificationResponse.model_validate(notification)


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> NotificationResponse:
    """Mark a notification as read. Any authenticated user."""
    service = NotificationService(session)
    notification = await service.mark_read(notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse.model_validate(notification)


@router.post("/notifications/read-all")
async def mark_all_read(
    user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict[str, int]:
    """Mark all notifications as read. Any authenticated user."""
    service = NotificationService(session)
    count = await service.mark_all_read(user.id)
    return {"marked_read": count}


# --- Push Subscriptions ---


@router.post(
    "/push-subscriptions",
    response_model=PushSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe_push(
    data: PushSubscriptionCreate,
    user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PushSubscriptionResponse:
    """Subscribe to push notifications. Any authenticated user."""
    if user.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = NotificationService(session)
    sub = await service.subscribe_push(data, user_id=user.id, agency_id=user.agency_id)
    return PushSubscriptionResponse.model_validate(sub)


@router.delete("/push-subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_push(
    subscription_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> None:
    """Unsubscribe from push notifications. Any authenticated user."""
    service = NotificationService(session)
    unsubscribed = await service.unsubscribe_push(subscription_id)
    if not unsubscribed:
        raise HTTPException(status_code=404, detail="Subscription not found")


# --- Messages ---


@router.post(
    "/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    data: MessageCreate,
    user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> MessageResponse:
    """Send a message. Any authenticated user."""
    if user.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = NotificationService(session)
    message = await service.send_message(data, sender_id=user.id, agency_id=user.agency_id)
    return MessageResponse.model_validate(message)


@router.get("/messages/threads", response_model=list[uuid.UUID])
async def list_threads(
    user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[uuid.UUID]:
    """List message thread IDs for current user. Any authenticated user."""
    service = NotificationService(session)
    return await service.list_user_threads(user.id)


@router.get("/messages/threads/{thread_id}", response_model=MessageListResponse)
async def get_thread(
    thread_id: uuid.UUID,
    page: int = 1,
    size: int = 50,
    _user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> MessageListResponse:
    """Get messages in a thread. Any authenticated user."""
    service = NotificationService(session)
    messages, total = await service.list_thread(thread_id, page=page, size=size)
    return MessageListResponse(
        items=[MessageResponse.model_validate(m) for m in messages],
        total=total,
        page=page,
        size=size,
    )


@router.post("/messages/{message_id}/read", response_model=MessageResponse)
async def mark_message_read(
    message_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> MessageResponse:
    """Mark a message as read. Any authenticated user."""
    service = NotificationService(session)
    message = await service.mark_message_read(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageResponse.model_validate(message)
