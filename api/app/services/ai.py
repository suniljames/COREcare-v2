"""AI agent service — conversation management and message handling."""

import json
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIConversation, AIFeatureFlag, AIMessage, ConversationStatus
from app.schemas.ai import AIConversationCreate, AIMessageCreate


class AIService:
    """Conversation management for AI agent interactions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Conversations ---

    async def list_conversations(
        self,
        *,
        user_id: uuid.UUID | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[AIConversation], int]:
        query = select(AIConversation)
        if user_id:
            query = query.where(
                AIConversation.user_id == user_id  # type: ignore[arg-type]
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.offset((page - 1) * size)
            .limit(size)
            .order_by(
                AIConversation.created_at.desc()  # type: ignore[attr-defined]
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def create_conversation(
        self,
        data: AIConversationCreate,
        user_id: uuid.UUID,
        agency_id: uuid.UUID,
    ) -> AIConversation:
        conversation = AIConversation(
            user_id=user_id,
            channel=data.channel,
            external_id=data.external_id,
            agency_id=agency_id,
        )
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def get_conversation(self, conversation_id: uuid.UUID) -> AIConversation | None:
        result = await self.session.execute(
            select(AIConversation).where(
                AIConversation.id == conversation_id  # type: ignore[arg-type]
            )
        )
        return result.scalar_one_or_none()

    async def close_conversation(
        self, conversation_id: uuid.UUID, summary: str = ""
    ) -> AIConversation | None:
        conv = await self.get_conversation(conversation_id)
        if conv is None:
            return None
        conv.status = ConversationStatus.CLOSED
        conv.summary = summary
        self.session.add(conv)
        await self.session.flush()
        await self.session.refresh(conv)
        return conv

    # --- Messages ---

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        data: AIMessageCreate,
        role: str,
        agency_id: uuid.UUID,
        tokens_used: int = 0,
    ) -> AIMessage:
        message = AIMessage(
            conversation_id=conversation_id,
            role=role,
            content=data.content,
            tokens_used=tokens_used,
            agency_id=agency_id,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def list_messages(self, conversation_id: uuid.UUID) -> list[AIMessage]:
        result = await self.session.execute(
            select(AIMessage)
            .where(
                AIMessage.conversation_id == conversation_id  # type: ignore[arg-type]
            )
            .order_by(
                AIMessage.created_at.asc()  # type: ignore[attr-defined]
            )
        )
        return list(result.scalars().all())

    # --- Feature Flags ---

    async def get_feature_flag(self, feature_name: str, agency_id: uuid.UUID) -> dict[str, Any]:
        """Check if an AI feature is enabled for an agency."""
        from sqlalchemy import and_

        result = await self.session.execute(
            select(AIFeatureFlag).where(
                and_(
                    AIFeatureFlag.feature_name == feature_name,  # type: ignore[arg-type]
                    AIFeatureFlag.agency_id == agency_id,  # type: ignore[arg-type]
                )
            )
        )
        flag = result.scalar_one_or_none()
        if flag is None:
            return {"enabled": False, "config": {}}
        return {
            "enabled": flag.is_enabled,
            "config": json.loads(flag.config_json),
        }

    async def set_feature_flag(
        self,
        feature_name: str,
        agency_id: uuid.UUID,
        *,
        is_enabled: bool = True,
        config: dict[str, Any] | None = None,
    ) -> AIFeatureFlag:
        """Create or update an AI feature flag."""
        from sqlalchemy import and_

        result = await self.session.execute(
            select(AIFeatureFlag).where(
                and_(
                    AIFeatureFlag.feature_name == feature_name,  # type: ignore[arg-type]
                    AIFeatureFlag.agency_id == agency_id,  # type: ignore[arg-type]
                )
            )
        )
        flag = result.scalar_one_or_none()

        if flag is None:
            flag = AIFeatureFlag(
                feature_name=feature_name,
                is_enabled=is_enabled,
                config_json=json.dumps(config or {}),
                agency_id=agency_id,
            )
        else:
            flag.is_enabled = is_enabled
            if config is not None:
                flag.config_json = json.dumps(config)

        self.session.add(flag)
        await self.session.flush()
        await self.session.refresh(flag)
        return flag
