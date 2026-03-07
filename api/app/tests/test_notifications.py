"""Tests for notifications, push subscriptions, and messaging."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import (  # noqa: F401
    Agency,
    Client,
    Message,
    Notification,
    PushSubscription,
    Shift,
    User,
    Visit,
)
from app.models.notification import NotificationType
from app.models.user import UserRole
from app.schemas.notification import MessageCreate, NotificationCreate, PushSubscriptionCreate
from app.services.notification import NotificationService

TEST_DB_URL = "sqlite+aiosqlite:///./test_notifications.db"
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        agency = Agency(id=AGENCY_ID, name="Test Agency", slug="test-agency")
        s.add(agency)
        await s.commit()
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


async def _create_user(session: AsyncSession, email: str = "user@test.com") -> User:
    user = User(
        email=email,
        first_name="Test",
        last_name="User",
        role=UserRole.CAREGIVER,
        agency_id=AGENCY_ID,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


# --- Notification tests ---


@pytest.mark.asyncio
async def test_create_notification(session: AsyncSession) -> None:
    """Creating a notification stores it as unread."""
    user = await _create_user(session)
    service = NotificationService(session)

    notif = await service.create_notification(
        NotificationCreate(
            user_id=user.id,
            notification_type=NotificationType.SHIFT_ASSIGNED,
            title="New shift assigned",
            body="You have been assigned to a new shift.",
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert notif.is_read is False
    assert notif.title == "New shift assigned"


@pytest.mark.asyncio
async def test_mark_read(session: AsyncSession) -> None:
    """Marking a notification as read sets is_read and read_at."""
    user = await _create_user(session)
    service = NotificationService(session)

    notif = await service.create_notification(
        NotificationCreate(
            user_id=user.id,
            notification_type=NotificationType.SYSTEM,
            title="Test",
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    read = await service.mark_read(notif.id)
    await session.commit()

    assert read is not None
    assert read.is_read is True
    assert read.read_at is not None


@pytest.mark.asyncio
async def test_mark_all_read(session: AsyncSession) -> None:
    """mark_all_read marks all unread notifications."""
    user = await _create_user(session)
    service = NotificationService(session)

    for i in range(3):
        await service.create_notification(
            NotificationCreate(
                user_id=user.id,
                notification_type=NotificationType.SYSTEM,
                title=f"Notif {i}",
            ),
            agency_id=AGENCY_ID,
        )
    await session.commit()

    count = await service.mark_all_read(user.id)
    await session.commit()

    assert count == 3
    unread = await service.get_unread_count(user.id)
    assert unread == 0


@pytest.mark.asyncio
async def test_unread_count(session: AsyncSession) -> None:
    """get_unread_count returns correct count."""
    user = await _create_user(session)
    service = NotificationService(session)

    await service.create_notification(
        NotificationCreate(
            user_id=user.id,
            notification_type=NotificationType.SYSTEM,
            title="Test",
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert await service.get_unread_count(user.id) == 1


@pytest.mark.asyncio
async def test_list_unread_only(session: AsyncSession) -> None:
    """Filtering by unread_only excludes read notifications."""
    user = await _create_user(session)
    service = NotificationService(session)

    await service.create_notification(
        NotificationCreate(
            user_id=user.id,
            notification_type=NotificationType.SYSTEM,
            title="Unread",
        ),
        agency_id=AGENCY_ID,
    )
    n2 = await service.create_notification(
        NotificationCreate(
            user_id=user.id,
            notification_type=NotificationType.SYSTEM,
            title="Will be read",
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    await service.mark_read(n2.id)
    await session.commit()

    items, total = await service.list_notifications(user_id=user.id, unread_only=True)
    assert total == 1
    assert items[0].title == "Unread"


# --- Push Subscription tests ---


@pytest.mark.asyncio
async def test_subscribe_and_unsubscribe(session: AsyncSession) -> None:
    """Push subscribe creates, unsubscribe deactivates."""
    user = await _create_user(session)
    service = NotificationService(session)

    sub = await service.subscribe_push(
        PushSubscriptionCreate(
            endpoint="https://push.example.com/sub1",
            p256dh_key="key1",
            auth_key="auth1",
        ),
        user_id=user.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert sub.is_active is True

    subs = await service.get_user_subscriptions(user.id)
    assert len(subs) == 1

    await service.unsubscribe_push(sub.id)
    await session.commit()

    subs_after = await service.get_user_subscriptions(user.id)
    assert len(subs_after) == 0


# --- Message tests ---


@pytest.mark.asyncio
async def test_send_and_list_messages(session: AsyncSession) -> None:
    """Sending messages creates a thread and messages are retrievable."""
    sender = await _create_user(session, email="sender@test.com")
    recipient = await _create_user(session, email="recipient@test.com")
    service = NotificationService(session)

    thread_id = uuid.uuid4()
    await service.send_message(
        MessageCreate(
            recipient_id=recipient.id,
            body="Hello!",
            thread_id=thread_id,
        ),
        sender_id=sender.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    await service.send_message(
        MessageCreate(
            recipient_id=sender.id,
            body="Hi back!",
            thread_id=thread_id,
        ),
        sender_id=recipient.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    messages, total = await service.list_thread(thread_id)
    assert total == 2

    threads = await service.list_user_threads(sender.id)
    assert thread_id in threads


@pytest.mark.asyncio
async def test_mark_message_read(session: AsyncSession) -> None:
    """Marking a message as read sets timestamp."""
    sender = await _create_user(session, email="s@test.com")
    recipient = await _create_user(session, email="r@test.com")
    service = NotificationService(session)

    msg = await service.send_message(
        MessageCreate(recipient_id=recipient.id, body="Test"),
        sender_id=sender.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    read_msg = await service.mark_message_read(msg.id)
    await session.commit()

    assert read_msg is not None
    assert read_msg.is_read is True
    assert read_msg.read_at is not None
