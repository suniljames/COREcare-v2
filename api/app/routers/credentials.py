"""Credential management API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.credential import CredentialStatus, CredentialType
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.credential import (
    CredentialCreate,
    CredentialListResponse,
    CredentialResponse,
    CredentialUpdate,
    ExpiringCredentialAlert,
)
from app.services.credential import CredentialService

router = APIRouter(prefix="/api/credentials", tags=["credentials"])


@router.get("", response_model=CredentialListResponse)
async def list_credentials(
    page: int = 1,
    size: int = 20,
    caregiver_id: uuid.UUID | None = None,
    credential_type: CredentialType | None = None,
    credential_status: CredentialStatus | None = None,
    _user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CredentialListResponse:
    """List credentials with filtering. Requires care_manager+."""
    service = CredentialService(session)
    credentials, total = await service.list_credentials(
        page=page,
        size=size,
        caregiver_id=caregiver_id,
        credential_type=credential_type,
        status=credential_status,
    )
    return CredentialListResponse(
        items=[CredentialResponse.model_validate(c) for c in credentials],
        total=total,
        page=page,
        size=size,
    )


@router.get("/expiring", response_model=list[ExpiringCredentialAlert])
async def get_expiring_credentials(
    _user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[ExpiringCredentialAlert]:
    """Get credentials expiring within 90 days. Requires care_manager+."""
    service = CredentialService(session)
    return await service.check_expiring()


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: uuid.UUID,
    _user: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CredentialResponse:
    """Get a credential by ID. Requires care_manager+."""
    service = CredentialService(session)
    credential = await service.get_credential(credential_id)
    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")
    return CredentialResponse.model_validate(credential)


@router.post("", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    data: CredentialCreate,
    admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CredentialResponse:
    """Create a credential record. Requires care_manager+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = CredentialService(session)
    credential = await service.create_credential(data, agency_id=admin.agency_id)
    return CredentialResponse.model_validate(credential)


@router.patch("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: uuid.UUID,
    data: CredentialUpdate,
    _admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CredentialResponse:
    """Update a credential. Requires care_manager+."""
    service = CredentialService(session)
    credential = await service.update_credential(credential_id, data)
    if credential is None:
        raise HTTPException(status_code=404, detail="Credential not found")
    return CredentialResponse.model_validate(credential)


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: uuid.UUID,
    _admin: User = Depends(require_role(UserRole.AGENCY_ADMIN)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> None:
    """Delete a credential. Requires agency_admin+."""
    service = CredentialService(session)
    deleted = await service.delete_credential(credential_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Credential not found")


@router.post("/update-statuses")
async def update_credential_statuses(
    _admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict[str, int]:
    """Scan and update credential statuses based on expiration dates. Requires care_manager+."""
    service = CredentialService(session)
    updated = await service.update_expiration_statuses()
    return {"updated_count": updated}
