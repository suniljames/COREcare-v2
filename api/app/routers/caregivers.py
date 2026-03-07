"""Caregiver profile API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.caregiver import CaregiverProfile
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.caregiver import (
    CaregiverProfileCreate,
    CaregiverProfileListResponse,
    CaregiverProfileResponse,
    CaregiverProfileUpdate,
)
from app.services.caregiver import CaregiverService

router = APIRouter(prefix="/api/caregivers", tags=["caregivers"])


@router.get("", response_model=CaregiverProfileListResponse)
async def list_profiles(
    page: int = 1,
    size: int = 20,
    _admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CaregiverProfileListResponse:
    """List caregiver profiles. Requires care_manager+."""
    service = CaregiverService(session)
    profiles, total = await service.list_profiles(page=page, size=size)
    return CaregiverProfileListResponse(
        items=[CaregiverProfileResponse.model_validate(p) for p in profiles],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{profile_id}", response_model=CaregiverProfileResponse)
async def get_profile(
    profile_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CaregiverProfile:
    """Get a caregiver profile. Requires caregiver+."""
    service = CaregiverService(session)
    profile = await service.get_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post(
    "",
    response_model=CaregiverProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    data: CaregiverProfileCreate,
    admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CaregiverProfile:
    """Create a caregiver profile. Requires agency_admin+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = CaregiverService(session)
    return await service.create_profile(data, agency_id=admin.agency_id)


@router.patch("/{profile_id}", response_model=CaregiverProfileResponse)
async def update_profile(
    profile_id: uuid.UUID,
    data: CaregiverProfileUpdate,
    _admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CaregiverProfile:
    """Update a caregiver profile. Requires care_manager+."""
    service = CaregiverService(session)
    profile = await service.update_profile(profile_id, data)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
