"""Charting API endpoints — templates and patient charts."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.chart import ChartStatus
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.chart import (
    ChartCreate,
    ChartListResponse,
    ChartResponse,
    ChartTemplateCreate,
    ChartTemplateListResponse,
    ChartTemplateResponse,
    ChartTemplateUpdate,
    ChartUpdate,
)
from app.services.chart import ChartService

router = APIRouter(prefix="/api", tags=["charts"])


# --- Template endpoints ---


@router.get("/chart-templates", response_model=ChartTemplateListResponse)
async def list_templates(
    page: int = 1,
    size: int = 20,
    active_only: bool = True,
    _user: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ChartTemplateListResponse:
    """List chart templates. Requires caregiver+."""
    service = ChartService(session)
    templates, total = await service.list_templates(page=page, size=size, active_only=active_only)
    items = [ChartTemplateResponse(**service.template_to_response_data(t)) for t in templates]
    return ChartTemplateListResponse(items=items, total=total, page=page, size=size)


@router.get("/chart-templates/{template_id}", response_model=ChartTemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ChartTemplateResponse:
    """Get a chart template by ID. Requires caregiver+."""
    service = ChartService(session)
    template = await service.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return ChartTemplateResponse(**service.template_to_response_data(template))


@router.post(
    "/chart-templates",
    response_model=ChartTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    data: ChartTemplateCreate,
    admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ChartTemplateResponse:
    """Create a chart template. Requires care_manager+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = ChartService(session)
    template = await service.create_template(data, agency_id=admin.agency_id)
    return ChartTemplateResponse(**service.template_to_response_data(template))


@router.patch("/chart-templates/{template_id}", response_model=ChartTemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    data: ChartTemplateUpdate,
    _admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ChartTemplateResponse:
    """Update a chart template (bumps version on content changes). Requires care_manager+."""
    service = ChartService(session)
    template = await service.update_template(template_id, data)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return ChartTemplateResponse(**service.template_to_response_data(template))


# --- Chart endpoints ---


@router.get("/charts", response_model=ChartListResponse)
async def list_charts(
    page: int = 1,
    size: int = 20,
    client_id: uuid.UUID | None = None,
    caregiver_id: uuid.UUID | None = None,
    chart_status: ChartStatus | None = None,
    _user: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ChartListResponse:
    """List charts with filtering. Requires caregiver+."""
    service = ChartService(session)
    charts, total = await service.list_charts(
        page=page,
        size=size,
        client_id=client_id,
        caregiver_id=caregiver_id,
        status=chart_status,
    )
    items = [ChartResponse(**service.chart_to_response_data(c)) for c in charts]
    return ChartListResponse(items=items, total=total, page=page, size=size)


@router.get("/charts/{chart_id}", response_model=ChartResponse)
async def get_chart(
    chart_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ChartResponse:
    """Get a chart by ID. Requires caregiver+."""
    service = ChartService(session)
    chart = await service.get_chart(chart_id)
    if chart is None:
        raise HTTPException(status_code=404, detail="Chart not found")
    return ChartResponse(**service.chart_to_response_data(chart))


@router.post(
    "/charts",
    response_model=ChartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chart(
    data: ChartCreate,
    user: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ChartResponse:
    """Create a new chart. Requires caregiver+."""
    if user.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = ChartService(session)
    chart = await service.create_chart(data, caregiver_id=user.id, agency_id=user.agency_id)
    return ChartResponse(**service.chart_to_response_data(chart))


@router.patch("/charts/{chart_id}", response_model=ChartResponse)
async def update_chart(
    chart_id: uuid.UUID,
    data: ChartUpdate,
    _user: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ChartResponse:
    """Update chart data (bumps version on data changes). Requires caregiver+."""
    service = ChartService(session)
    chart = await service.update_chart(chart_id, data)
    if chart is None:
        raise HTTPException(status_code=404, detail="Chart not found")
    return ChartResponse(**service.chart_to_response_data(chart))


@router.post("/charts/{chart_id}/sign", response_model=ChartResponse)
async def sign_chart(
    chart_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ChartResponse:
    """Sign a completed chart. Requires care_manager+."""
    service = ChartService(session)
    chart = await service.sign_chart(chart_id, signer_id=user.id)
    if chart is None:
        raise HTTPException(status_code=404, detail="Chart not found")
    return ChartResponse(**service.chart_to_response_data(chart))
