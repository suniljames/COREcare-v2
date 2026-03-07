"""Client management API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.client import Client, ClientStatus, FamilyLink
from app.models.user import User, UserRole
from app.rbac import require_role
from app.schemas.client import (
    ClientCreate,
    ClientListResponse,
    ClientResponse,
    ClientUpdate,
    FamilyLinkCreate,
    FamilyLinkResponse,
)
from app.services.client import ClientService

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=ClientListResponse)
async def list_clients(
    page: int = 1,
    size: int = 20,
    client_status: ClientStatus | None = None,
    search: str | None = None,
    admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ClientListResponse:
    """List clients (tenant-scoped). Requires care_manager+."""
    service = ClientService(session)
    clients, total = await service.list_clients(
        page=page, size=size, status=client_status, search=search
    )
    return ClientListResponse(
        items=[ClientResponse.model_validate(c) for c in clients],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> Client:
    """Get a client by ID. Requires caregiver+."""
    service = ClientService(session)
    client = await service.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> Client:
    """Create a new client. Requires care_manager+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    service = ClientService(session)
    return await service.create_client(data, agency_id=admin.agency_id)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> Client:
    """Update a client. Requires care_manager+."""
    service = ClientService(session)
    client = await service.update_client(client_id, data)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.delete("/{client_id}", response_model=ClientResponse)
async def deactivate_client(
    client_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> Client:
    """Deactivate a client. Requires care_manager+."""
    service = ClientService(session)
    client = await service.deactivate_client(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post(
    "/{client_id}/family",
    response_model=FamilyLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_family_link(
    client_id: uuid.UUID,
    data: FamilyLinkCreate,
    admin: User = Depends(require_role(UserRole.CARE_MANAGER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> FamilyLink:
    """Link a family member to a client. Requires care_manager+."""
    if admin.agency_id is None:
        raise HTTPException(status_code=400, detail="Super-admin must specify agency")
    data.client_id = client_id
    service = ClientService(session)
    return await service.add_family_link(data, agency_id=admin.agency_id)


@router.get("/{client_id}/family", response_model=list[FamilyLinkResponse])
async def get_family_links(
    client_id: uuid.UUID,
    admin: User = Depends(require_role(UserRole.CAREGIVER)),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[FamilyLink]:
    """Get family links for a client. Requires caregiver+."""
    service = ClientService(session)
    return await service.get_family_links(client_id)
