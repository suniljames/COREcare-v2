"""Payroll API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.payroll import PayrollPeriodStatus
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.payroll import (
    PayrollEntryCreate,
    PayrollEntryResponse,
    PayrollPeriodCreate,
    PayrollPeriodListResponse,
    PayrollPeriodResponse,
    PayrollPeriodUpdate,
)
from app.services.payroll import PayrollService

router = APIRouter(prefix="/api/payroll", tags=["payroll"])


@router.get("/periods", response_model=PayrollPeriodListResponse)
async def list_periods(
    page: int = 1,
    size: int = 20,
    period_status: PayrollPeriodStatus | None = None,
    _user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PayrollPeriodListResponse:
    """List payroll periods. Requires care_manager+."""
    service = PayrollService(session)
    periods, total = await service.list_periods(page=page, size=size, status=period_status)
    return PayrollPeriodListResponse(
        items=[PayrollPeriodResponse.model_validate(p) for p in periods],
        total=total,
        page=page,
        size=size,
    )


@router.get("/periods/{period_id}", response_model=PayrollPeriodResponse)
async def get_period(
    period_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PayrollPeriodResponse:
    """Get a payroll period by ID. Requires care_manager+."""
    service = PayrollService(session)
    period = await service.get_period(period_id)
    if period is None:
        raise HTTPException(status_code=404, detail="Payroll period not found")
    return PayrollPeriodResponse.model_validate(period)


@router.post(
    "/periods",
    response_model=PayrollPeriodResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_period(
    data: PayrollPeriodCreate,
    admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PayrollPeriodResponse:
    """Create a payroll period. Requires agency_admin+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = PayrollService(session)
    period = await service.create_period(data, agency_id=admin.agency_id)
    return PayrollPeriodResponse.model_validate(period)


@router.patch("/periods/{period_id}", response_model=PayrollPeriodResponse)
async def update_period(
    period_id: uuid.UUID,
    data: PayrollPeriodUpdate,
    _admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PayrollPeriodResponse:
    """Update a payroll period. Requires agency_admin+."""
    service = PayrollService(session)
    period = await service.update_period(period_id, data)
    if period is None:
        raise HTTPException(status_code=404, detail="Payroll period not found")
    return PayrollPeriodResponse.model_validate(period)


@router.post("/periods/{period_id}/submit", response_model=PayrollPeriodResponse)
async def submit_period(
    period_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PayrollPeriodResponse:
    """Submit a payroll period for approval. Requires care_manager+."""
    service = PayrollService(session)
    period = await service.submit_for_approval(period_id)
    if period is None:
        raise HTTPException(status_code=404, detail="Payroll period not found")
    return PayrollPeriodResponse.model_validate(period)


@router.post("/periods/{period_id}/approve", response_model=PayrollPeriodResponse)
async def approve_period(
    period_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PayrollPeriodResponse:
    """Approve a payroll period. Requires agency_admin+."""
    service = PayrollService(session)
    period = await service.approve_period(period_id, approver_id=user.id)
    if period is None:
        raise HTTPException(status_code=404, detail="Payroll period not found")
    return PayrollPeriodResponse.model_validate(period)


@router.post("/periods/{period_id}/reject", response_model=PayrollPeriodResponse)
async def reject_period(
    period_id: uuid.UUID,
    _admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PayrollPeriodResponse:
    """Reject a payroll period. Requires agency_admin+."""
    service = PayrollService(session)
    period = await service.reject_period(period_id)
    if period is None:
        raise HTTPException(status_code=404, detail="Payroll period not found")
    return PayrollPeriodResponse.model_validate(period)


# --- Entries ---


@router.get(
    "/periods/{period_id}/entries",
    response_model=list[PayrollEntryResponse],
)
async def list_entries(
    period_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[PayrollEntryResponse]:
    """List payroll entries for a period. Requires care_manager+."""
    service = PayrollService(session)
    entries = await service.list_entries(period_id)
    return [PayrollEntryResponse.model_validate(e) for e in entries]


@router.post(
    "/periods/{period_id}/entries",
    response_model=PayrollEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_entry(
    period_id: uuid.UUID,
    data: PayrollEntryCreate,
    admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PayrollEntryResponse:
    """Add a payroll entry to a period. Requires care_manager+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = PayrollService(session)
    entry = await service.add_entry(period_id, data, agency_id=admin.agency_id)
    return PayrollEntryResponse.model_validate(entry)
