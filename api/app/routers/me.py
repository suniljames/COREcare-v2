"""Client persona /api/v1/me/* router (issue #125).

All routes require require_client_self() — staff roles get 403 here. The
Client's own client_id is resolved server-side from the authenticated user;
no path parameters expose another Client's ID.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models.audit import AuditAction, AuditEvent
from app.models.client import Client
from app.models.user import User
from app.rbac import require_client_self
from app.schemas.care_plan import ClientCarePlanRead
from app.schemas.client_me import (
    ClientMessageCreate,
    ClientMessageRead,
    ClientShiftRead,
    ClientThreadRead,
)
from app.services.care_plan import CarePlanService
from app.services.message_thread import MessageThreadService
from app.services.shift import ShiftService

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/me", tags=["me"])


async def _audit(
    session: AsyncSession,
    *,
    user: User,
    client: Client,
    action_detail: str,
) -> None:
    event = AuditEvent(
        user_id=user.id,
        agency_id=client.agency_id,
        action=AuditAction.READ,
        resource_type="client_self",
        resource_id=str(client.id),
        is_phi_access=True,
        details=action_detail,
    )
    session.add(event)
    await session.flush()


@router.get("/care-plan", response_model=ClientCarePlanRead | None)
async def read_my_care_plan(
    request: Request,  # noqa: ARG001
    user: User = Depends(get_current_user),
    client: Client = Depends(require_client_self()),
    session: AsyncSession = Depends(get_session),
) -> ClientCarePlanRead | None:
    """Read the active care plan version for the authenticated Client."""
    service = CarePlanService(session)
    active = await service.get_active_for_client(client.id)
    await _audit(
        session, user=user, client=client, action_detail="client_read_own_care_plan"
    )
    if active is None:
        return None
    return ClientCarePlanRead.model_validate(active)


@router.get("/schedule", response_model=list[ClientShiftRead])
async def read_my_schedule(
    request: Request,  # noqa: ARG001
    user: User = Depends(get_current_user),
    client: Client = Depends(require_client_self()),
    session: AsyncSession = Depends(get_session),
) -> list[ClientShiftRead]:
    """Read the next 7 days of shifts for the authenticated Client."""
    service = ShiftService(session)
    shifts = await service.list_upcoming_for_client(client.id, days=7)
    await _audit(
        session, user=user, client=client, action_detail="client_read_own_schedule"
    )
    return [ClientShiftRead.model_validate(s) for s in shifts]


@router.get("/messages", response_model=ClientThreadRead)
async def read_my_messages(
    request: Request,  # noqa: ARG001
    user: User = Depends(get_current_user),
    client: Client = Depends(require_client_self()),
    session: AsyncSession = Depends(get_session),
) -> ClientThreadRead:
    """Read the Client's message thread with their agency."""
    service = MessageThreadService(session)
    thread = await service.get_or_create_for_client(client.id, client.agency_id)
    messages = await service.list_messages(thread.id)
    await _audit(
        session, user=user, client=client, action_detail="client_read_own_messages"
    )
    return ClientThreadRead(
        id=thread.id,
        last_message_at=thread.last_message_at,
        messages=[ClientMessageRead.model_validate(m) for m in messages],
    )


@router.post(
    "/messages",
    status_code=status.HTTP_201_CREATED,
    response_model=ClientMessageRead,
)
async def send_my_message(
    body: ClientMessageCreate,
    user: User = Depends(get_current_user),
    client: Client = Depends(require_client_self()),
    session: AsyncSession = Depends(get_session),
) -> ClientMessageRead:
    """Send a message from the Client into their thread."""
    if not body.body.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message body cannot be empty.",
        )
    service = MessageThreadService(session)
    msg = await service.send_from_client(
        client_id=client.id,
        sender_user_id=user.id,
        body=body.body,
        agency_id=client.agency_id,
    )
    event = AuditEvent(
        user_id=user.id,
        agency_id=client.agency_id,
        action=AuditAction.CREATE,
        resource_type="client_self_message",
        resource_id=str(msg.id),
        is_phi_access=True,
        details="client_sent_message_to_agency",
    )
    session.add(event)
    await session.flush()
    return ClientMessageRead.model_validate(msg)
