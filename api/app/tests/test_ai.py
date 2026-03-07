"""Tests for AI conversation management and feature flags."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import (  # noqa: F401
    Agency,
    AIConversation,
    AIFeatureFlag,
    AIMessage,
    BAARecord,
    Client,
    ComplianceRule,
    Shift,
    User,
    Visit,
)
from app.models.ai import ConversationChannel, ConversationStatus
from app.models.user import UserRole
from app.schemas.ai import AIConversationCreate, AIMessageCreate
from app.services.ai import AIService

TEST_DB_URL = "sqlite+aiosqlite:///./test_ai.db"
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


async def _create_user(session: AsyncSession) -> User:
    user = User(
        email="user@test.com",
        first_name="Test",
        last_name="User",
        role=UserRole.CAREGIVER,
        agency_id=AGENCY_ID,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_conversation(session: AsyncSession) -> None:
    """Creating a conversation sets active status."""
    user = await _create_user(session)
    service = AIService(session)

    conv = await service.create_conversation(
        AIConversationCreate(channel=ConversationChannel.WEB),
        user_id=user.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert conv.status == ConversationStatus.ACTIVE
    assert conv.user_id == user.id


@pytest.mark.asyncio
async def test_add_and_list_messages(session: AsyncSession) -> None:
    """Messages are added and listed in order."""
    user = await _create_user(session)
    service = AIService(session)

    conv = await service.create_conversation(
        AIConversationCreate(),
        user_id=user.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    await service.add_message(
        conv.id,
        AIMessageCreate(content="Hello"),
        role="user",
        agency_id=AGENCY_ID,
    )
    await service.add_message(
        conv.id,
        AIMessageCreate(content="Hi! How can I help?"),
        role="assistant",
        agency_id=AGENCY_ID,
        tokens_used=15,
    )
    await session.commit()

    messages = await service.list_messages(conv.id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert messages[1].tokens_used == 15


@pytest.mark.asyncio
async def test_close_conversation(session: AsyncSession) -> None:
    """Closing a conversation updates status and summary."""
    user = await _create_user(session)
    service = AIService(session)

    conv = await service.create_conversation(
        AIConversationCreate(),
        user_id=user.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    closed = await service.close_conversation(conv.id, summary="Resolved scheduling question")
    await session.commit()

    assert closed is not None
    assert closed.status == ConversationStatus.CLOSED
    assert closed.summary == "Resolved scheduling question"


@pytest.mark.asyncio
async def test_feature_flag(session: AsyncSession) -> None:
    """Feature flags can be set and retrieved."""
    service = AIService(session)

    # Default: not enabled
    flag = await service.get_feature_flag("smart_scheduling", AGENCY_ID)
    assert flag["enabled"] is False

    # Enable it
    await service.set_feature_flag(
        "smart_scheduling",
        AGENCY_ID,
        is_enabled=True,
        config={"max_suggestions": 5},
    )
    await session.commit()

    flag = await service.get_feature_flag("smart_scheduling", AGENCY_ID)
    assert flag["enabled"] is True
    assert flag["config"]["max_suggestions"] == 5


@pytest.mark.asyncio
async def test_list_conversations_by_user(session: AsyncSession) -> None:
    """Listing conversations filters by user."""
    user = await _create_user(session)
    service = AIService(session)

    await service.create_conversation(
        AIConversationCreate(),
        user_id=user.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    convs, total = await service.list_conversations(user_id=user.id)
    assert total == 1

    other_convs, other_total = await service.list_conversations(user_id=uuid.uuid4())
    assert other_total == 0
