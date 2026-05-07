"""Role-Based Access Control: role hierarchy and permission dependencies.

The `Client` role is a *sibling axis*, not a privilege level. ROLE_HIERARCHY
intentionally excludes CLIENT — staff routes use require_role(); the Client
persona uses require_client_self() (issue #125).
"""

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models.client import Client
from app.models.user import User, UserRole
from app.tenant import set_client_context, set_tenant_context

# Role hierarchy — higher index = more privilege.
# CLIENT is intentionally absent: it is a sibling axis (own-row access),
# not a privilege subset of FAMILY. See app.rbac.require_client_self().
ROLE_HIERARCHY: list[UserRole] = [
    UserRole.FAMILY,
    UserRole.CAREGIVER,
    UserRole.CARE_MANAGER,
    UserRole.AGENCY_ADMIN,
    UserRole.SUPER_ADMIN,
]


def role_level(role: UserRole) -> int:
    """Get the privilege level of a role (0 = lowest).

    Returns -1 for roles outside the staff hierarchy (e.g., CLIENT) so that
    has_min_role(client, *) returns False without raising.
    """
    try:
        return ROLE_HIERARCHY.index(role)
    except ValueError:
        return -1


def has_min_role(user_role: UserRole, min_role: UserRole) -> bool:
    """Check if a user's role meets the minimum required staff role.

    Returns False for any role outside ROLE_HIERARCHY (notably CLIENT).
    Client routes must use require_client_self() instead.
    """
    actual = role_level(user_role)
    if actual < 0:
        return False
    return actual >= role_level(min_role)


def require_role(
    min_role: UserRole,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """FastAPI dependency factory: require a minimum staff role level.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.AGENCY_ADMIN))])
        async def admin_only(): ...
    """

    async def _check_role(
        request: Request,  # noqa: ARG001
        user: User = Depends(get_current_user),  # noqa: B008
    ) -> User:
        if not has_min_role(user.role, min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {min_role.value} role or higher",
            )
        return user

    return _check_role


def require_client_self() -> Callable[..., Coroutine[Any, Any, Client]]:
    """FastAPI dependency factory: require the caller is a Client persona.

    Returns the linked Client row and (re-)sets the dual-axis RLS context.
    Raises 403 for non-Client roles or orphaned Client accounts (no
    `clients.client_user_id` linkage).

    The dependency re-applies set_client_context inside the route's session
    transaction so that even if the auth dependency ran on a different
    transaction, the route's queries see Client-scoped RLS.
    """

    async def _resolve(
        user: User = Depends(get_current_user),  # noqa: B008
        session: AsyncSession = Depends(get_session),  # noqa: B008
    ) -> Client:
        if user.role != UserRole.CLIENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint is only available to Client-role accounts.",
            )
        result = await session.execute(
            select(Client).where(Client.client_user_id == user.id)  # type: ignore[arg-type]
        )
        client = result.scalar_one_or_none()
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not linked to a client record.",
            )
        # Re-apply dual-axis RLS context for the route's queries.
        if user.agency_id:
            await set_tenant_context(session, user.agency_id)
        await set_client_context(session, client.id)
        return client

    return _resolve
