"""Client-persona invite endpoints (issue #125).

Two surfaces:
- POST /api/clients/{client_id}/invite — staff issuance (care_manager+)
- POST /api/client-invites/redeem — public redemption (no auth)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.client_invite import (
    ClientInviteIssue,
    ClientInviteIssueResponse,
    ClientInviteRedeem,
)
from app.services.client_invite import ClientInviteService

issue_router = APIRouter(prefix="/api/clients", tags=["client-invites"])
redeem_router = APIRouter(prefix="/api/client-invites", tags=["client-invites"])


@issue_router.post(
    "/{client_id}/invite",
    response_model=ClientInviteIssueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def issue_client_invite(
    client_id: uuid.UUID,
    body: ClientInviteIssue,
    admin: User = Depends(require_role(UserRole.CARE_MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> ClientInviteIssueResponse:
    """Issue a Client-persona invite. Requires care_manager+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = ClientInviteService(session)
    invite = await service.issue_invite(
        client_id=client_id,
        email=str(body.email),
        actor_user_id=admin.id,
        agency_id=admin.agency_id,
    )
    return ClientInviteIssueResponse.model_validate(invite)


@redeem_router.post("/redeem", status_code=status.HTTP_200_OK)
async def redeem_client_invite(
    body: ClientInviteRedeem,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Redeem a Client-persona invite. Public endpoint (Clerk redemption flow)."""
    service = ClientInviteService(session)
    user, client = await service.redeem_invite(
        token=body.token,
        clerk_user_id=body.clerk_user_id,
        clerk_email=str(body.clerk_email),
    )
    return {
        "user_id": str(user.id),
        "client_id": str(client.id),
        "agency_id": str(client.agency_id),
    }
