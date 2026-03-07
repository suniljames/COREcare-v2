"""Compliance and BAA API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.compliance import ComplianceRuleType
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.compliance import (
    BAARecordCreate,
    BAARecordResponse,
    ComplianceRuleCreate,
    ComplianceRuleListResponse,
    ComplianceRuleResponse,
)
from app.services.compliance import ComplianceService

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


@router.get("/rules", response_model=ComplianceRuleListResponse)
async def list_rules(
    page: int = 1,
    size: int = 20,
    state_code: str | None = None,
    rule_type: ComplianceRuleType | None = None,
    _user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ComplianceRuleListResponse:
    """List compliance rules. Requires care_manager+."""
    service = ComplianceService(session)
    rules, total = await service.list_rules(
        page=page, size=size, state_code=state_code, rule_type=rule_type
    )
    items = [ComplianceRuleResponse(**service.rule_to_response_data(r)) for r in rules]
    return ComplianceRuleListResponse(items=items, total=total, page=page, size=size)


@router.post(
    "/rules",
    response_model=ComplianceRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rule(
    data: ComplianceRuleCreate,
    admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ComplianceRuleResponse:
    """Create a compliance rule. Requires agency_admin+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = ComplianceService(session)
    rule = await service.create_rule(data, agency_id=admin.agency_id)
    return ComplianceRuleResponse(**service.rule_to_response_data(rule))


@router.get("/baas", response_model=list[BAARecordResponse])
async def list_baas(
    page: int = 1,
    size: int = 20,
    _user: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[BAARecordResponse]:
    """List BAA records. Requires agency_admin+."""
    service = ComplianceService(session)
    baas, _ = await service.list_baas(page=page, size=size)
    return [BAARecordResponse.model_validate(b) for b in baas]


@router.post(
    "/baas",
    response_model=BAARecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_baa(
    data: BAARecordCreate,
    admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> BAARecordResponse:
    """Create a BAA record. Requires agency_admin+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = ComplianceService(session)
    baa = await service.create_baa(data, agency_id=admin.agency_id)
    return BAARecordResponse.model_validate(baa)
