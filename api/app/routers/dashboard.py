"""Dashboard and portal API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.dashboard import (
    AgencyKPIs,
    CaregiverPortalSummary,
    FamilyPortalSummary,
    PlatformKPIs,
)
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/agency", response_model=AgencyKPIs)
async def agency_dashboard(
    user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AgencyKPIs:
    """Get agency dashboard KPIs. Requires care_manager+."""
    if user.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = DashboardService(session)
    return await service.get_agency_kpis(user.agency_id)


@router.get("/platform", response_model=PlatformKPIs)
async def platform_dashboard(
    _user: User = Depends(require_role(UserRole.SUPER_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PlatformKPIs:
    """Get platform-wide KPIs. Requires super_admin."""
    service = DashboardService(session)
    return await service.get_platform_kpis()


@router.get("/caregiver", response_model=CaregiverPortalSummary)
async def caregiver_portal(
    user: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CaregiverPortalSummary:
    """Get caregiver portal summary. Requires caregiver+."""
    service = DashboardService(session)
    return await service.get_caregiver_summary(user.id)


@router.get("/family", response_model=FamilyPortalSummary)
async def family_portal(
    user: User = Depends(require_role(UserRole.FAMILY)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> FamilyPortalSummary:
    """Get family portal summary. Any authenticated user."""
    service = DashboardService(session)
    return await service.get_family_summary(user.id)
