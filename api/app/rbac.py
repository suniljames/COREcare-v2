"""Role-Based Access Control: role hierarchy and permission dependencies."""

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from app.auth import get_current_user
from app.models.user import User, UserRole

# Role hierarchy — higher index = more privilege
ROLE_HIERARCHY: list[UserRole] = [
    UserRole.FAMILY,
    UserRole.CAREGIVER,
    UserRole.CARE_MANAGER,
    UserRole.AGENCY_ADMIN,
    UserRole.SUPER_ADMIN,
]


def role_level(role: UserRole) -> int:
    """Get the privilege level of a role (0 = lowest)."""
    return ROLE_HIERARCHY.index(role)


def has_min_role(user_role: UserRole, min_role: UserRole) -> bool:
    """Check if a user's role meets the minimum required role."""
    return role_level(user_role) >= role_level(min_role)


def require_role(
    min_role: UserRole,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """FastAPI dependency factory: require a minimum role level.

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
