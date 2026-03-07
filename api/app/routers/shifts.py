"""Shift scheduling API endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.shift import Shift, ShiftStatus
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.shift import (
    ShiftCreate,
    ShiftListResponse,
    ShiftResponse,
    ShiftUpdate,
)
from app.services.shift import ShiftService

router = APIRouter(prefix="/api/shifts", tags=["shifts"])


@router.get("", response_model=ShiftListResponse)
async def list_shifts(
    page: int = 1,
    size: int = 20,
    start_after: datetime | None = None,
    start_before: datetime | None = None,
    caregiver_id: uuid.UUID | None = None,
    client_id: uuid.UUID | None = None,
    shift_status: ShiftStatus | None = None,
    _user: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ShiftListResponse:
    """List shifts with filtering. Requires caregiver+."""
    service = ShiftService(session)
    shifts, total = await service.list_shifts(
        page=page,
        size=size,
        start_after=start_after,
        start_before=start_before,
        caregiver_id=caregiver_id,
        client_id=client_id,
        status=shift_status,
    )
    return ShiftListResponse(
        items=[ShiftResponse.model_validate(s) for s in shifts],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{shift_id}", response_model=ShiftResponse)
async def get_shift(
    shift_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> Shift:
    """Get a shift by ID. Requires caregiver+."""
    service = ShiftService(session)
    shift = await service.get_shift(shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    return shift


@router.post("", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
    data: ShiftCreate,
    admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> Shift:
    """Create a new shift. Requires care_manager+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = ShiftService(session)
    return await service.create_shift(data, agency_id=admin.agency_id)


@router.patch("/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: uuid.UUID,
    data: ShiftUpdate,
    _admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> Shift:
    """Update a shift. Requires care_manager+."""
    service = ShiftService(session)
    shift = await service.update_shift(shift_id, data)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    return shift


@router.delete("/{shift_id}", response_model=ShiftResponse)
async def cancel_shift(
    shift_id: uuid.UUID,
    _admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> Shift:
    """Cancel a shift. Requires care_manager+."""
    service = ShiftService(session)
    shift = await service.cancel_shift(shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    return shift
