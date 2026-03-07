"""AI agent API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.ai import (
    AIConversationCreate,
    AIConversationListResponse,
    AIConversationResponse,
    AIMessageCreate,
    AIMessageResponse,
)
from app.services.ai import AIService

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/conversations", response_model=AIConversationListResponse)
async def list_conversations(
    page: int = 1,
    size: int = 20,
    user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AIConversationListResponse:
    """List AI conversations for current user. Any authenticated user."""
    service = AIService(session)
    conversations, total = await service.list_conversations(user_id=user.id, page=page, size=size)
    return AIConversationListResponse(
        items=[AIConversationResponse.model_validate(c) for c in conversations],
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "/conversations",
    response_model=AIConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    data: AIConversationCreate,
    user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AIConversationResponse:
    """Start a new AI conversation. Any authenticated user."""
    if user.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = AIService(session)
    conversation = await service.create_conversation(
        data, user_id=user.id, agency_id=user.agency_id
    )
    return AIConversationResponse.model_validate(conversation)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[AIMessageResponse],
)
async def list_messages(
    conversation_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[AIMessageResponse]:
    """Get messages in a conversation. Any authenticated user."""
    service = AIService(session)
    messages = await service.list_messages(conversation_id)
    return [AIMessageResponse.model_validate(m) for m in messages]


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AIMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: uuid.UUID,
    data: AIMessageCreate,
    user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AIMessageResponse:
    """Send a message in a conversation. Any authenticated user."""
    if user.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = AIService(session)
    # Store user message
    message = await service.add_message(
        conversation_id, data, role="user", agency_id=user.agency_id
    )
    return AIMessageResponse.model_validate(message)


@router.post(
    "/conversations/{conversation_id}/close",
    response_model=AIConversationResponse,
)
async def close_conversation(
    conversation_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AIConversationResponse:
    """Close a conversation. Any authenticated user."""
    service = AIService(session)
    conversation = await service.close_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return AIConversationResponse.model_validate(conversation)


@router.get("/features/{feature_name}")
async def get_feature_flag(
    feature_name: str,
    user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict[str, object]:
    """Check if an AI feature is enabled. Requires care_manager+."""
    if user.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = AIService(session)
    return await service.get_feature_flag(feature_name, user.agency_id)
