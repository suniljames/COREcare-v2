"""Notification, push subscription, and messaging service."""

import uuid
from datetime import UTC, datetime

from typing import Any

from sqlalchemy import and_, distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Message, Notification, PushSubscription
from app.schemas.notification import MessageCreate, NotificationCreate, PushSubscriptionCreate


class NotificationService:
    """CRUD for notifications, push subscriptions, and messages."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Notifications ---

    async def list_notifications(
        self,
        *,
        user_id: uuid.UUID,
        page: int = 1,
        size: int = 20,
        unread_only: bool = False,
    ) -> tuple[list[Notification], int]:
        query = select(Notification).where(
            Notification.user_id == user_id  # type: ignore[arg-type]
        )
        if unread_only:
            query = query.where(
                Notification.is_read == False  # type: ignore[arg-type]  # noqa: E712
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.offset((page - 1) * size)
            .limit(size)
            .order_by(
                Notification.created_at.desc()  # type: ignore[attr-defined]
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def create_notification(
        self, data: NotificationCreate, agency_id: uuid.UUID
    ) -> Notification:
        notification = Notification(
            user_id=data.user_id,
            notification_type=data.notification_type,
            channel=data.channel,
            title=data.title,
            body=data.body,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            agency_id=agency_id,
        )
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def mark_read(self, notification_id: uuid.UUID) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.id == notification_id  # type: ignore[arg-type]
            )
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            return None

        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread notifications as read. Returns count updated."""
        result = await self.session.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == user_id,  # type: ignore[arg-type]
                    Notification.is_read == False,  # type: ignore[arg-type]  # noqa: E712
                )
            )
        )
        notifications = result.scalars().all()
        now = datetime.now(UTC)
        count = 0
        for n in notifications:
            n.is_read = True
            n.read_at = now
            self.session.add(n)
            count += 1
        if count:
            await self.session.flush()
        return count

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,  # type: ignore[arg-type]
                    Notification.is_read == False,  # type: ignore[arg-type]  # noqa: E712
                )
            )
        )
        return result.scalar() or 0

    # --- Push Subscriptions ---

    async def subscribe_push(
        self,
        data: PushSubscriptionCreate,
        user_id: uuid.UUID,
        agency_id: uuid.UUID,
    ) -> PushSubscription:
        sub = PushSubscription(
            user_id=user_id,
            endpoint=data.endpoint,
            p256dh_key=data.p256dh_key,
            auth_key=data.auth_key,
            agency_id=agency_id,
        )
        self.session.add(sub)
        await self.session.flush()
        await self.session.refresh(sub)
        return sub

    async def unsubscribe_push(self, subscription_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(PushSubscription).where(
                PushSubscription.id == subscription_id  # type: ignore[arg-type]
            )
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return False
        sub.is_active = False
        self.session.add(sub)
        await self.session.flush()
        return True

    async def get_user_subscriptions(self, user_id: uuid.UUID) -> list[PushSubscription]:
        result = await self.session.execute(
            select(PushSubscription).where(
                and_(
                    PushSubscription.user_id == user_id,  # type: ignore[arg-type]
                    PushSubscription.is_active == True,  # type: ignore[arg-type]  # noqa: E712
                )
            )
        )
        return list(result.scalars().all())

    # --- Messages ---

    async def send_message(
        self,
        data: MessageCreate,
        sender_id: uuid.UUID,
        agency_id: uuid.UUID,
    ) -> Message:
        thread_id = data.thread_id or uuid.uuid4()
        message = Message(
            sender_id=sender_id,
            recipient_id=data.recipient_id,
            thread_id=thread_id,
            body=data.body,
            agency_id=agency_id,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def list_thread(
        self,
        thread_id: uuid.UUID,
        *,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[Message], int]:
        query = select(Message).where(
            Message.thread_id == thread_id  # type: ignore[arg-type]
        )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.offset((page - 1) * size)
            .limit(size)
            .order_by(
                Message.created_at.asc()  # type: ignore[attr-defined]
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def list_user_threads(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        """Get unique thread IDs for a user (sender or recipient)."""
        rows: Any = await self.session.execute(
            select(
                distinct(Message.thread_id)  # type: ignore[arg-type]
            ).where(
                or_(
                    Message.sender_id == user_id,  # type: ignore[arg-type]
                    Message.recipient_id == user_id,  # type: ignore[arg-type]
                )
            )
        )
        return [row[0] for row in rows.all()]

    async def mark_message_read(self, message_id: uuid.UUID) -> Message | None:
        result = await self.session.execute(
            select(Message).where(
                Message.id == message_id  # type: ignore[arg-type]
            )
        )
        message = result.scalar_one_or_none()
        if message is None:
            return None

        message.is_read = True
        message.read_at = datetime.now(UTC)
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message
