"""User management API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(get_current_user),  # noqa: B008
) -> User:
    """Get the current authenticated user's profile."""
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> User:
    """Update the current user's own profile (limited fields)."""
    # Self-update: only allow name changes, not role or active status
    safe_data = UserUpdate(first_name=data.first_name, last_name=data.last_name)
    service = UserService(session)
    updated = await service.update_user(user.id, safe_data)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    size: int = 20,
    role: UserRole | None = None,
    search: str | None = None,
    _admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> UserListResponse:
    """List users (agency-scoped via RLS). Requires agency_admin+."""
    service = UserService(session)
    users, total = await service.list_users(page=page, size=size, role=role, search=search)
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    _admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> User:
    """Get a user by ID. Requires agency_admin+."""
    service = UserService(session)
    user = await service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> User:
    """Create a new user. Requires agency_admin+."""
    service = UserService(session)
    user = await service.create_user(data, default_agency_id=admin.agency_id)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    _admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> User:
    """Update a user. Requires agency_admin+."""
    service = UserService(session)
    user = await service.update_user(user_id, data)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", response_model=UserResponse)
async def deactivate_user(
    user_id: uuid.UUID,
    _admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> User:
    """Deactivate (soft-delete) a user. Requires agency_admin+."""
    service = UserService(session)
    user = await service.deactivate_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
