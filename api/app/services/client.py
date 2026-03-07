"""Client management service."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client, ClientStatus, FamilyLink
from app.schemas.client import ClientCreate, ClientUpdate, FamilyLinkCreate


class ClientService:
    """CRUD operations for clients, tenant-scoped via RLS."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_clients(
        self,
        *,
        page: int = 1,
        size: int = 20,
        status: ClientStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[Client], int]:
        """List clients with optional filtering."""
        query = select(Client)

        if status:
            query = query.where(Client.status == status)  # type: ignore[arg-type]
        if search:
            pattern = f"%{search}%"
            query = query.where(
                Client.first_name.like(pattern)  # type: ignore[attr-defined]
                | Client.last_name.like(pattern)  # type: ignore[attr-defined]
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.offset((page - 1) * size)
            .limit(size)
            .order_by(
                Client.last_name.asc()  # type: ignore[attr-defined]
            )
        )
        result = await self.session.execute(query)
        clients = list(result.scalars().all())

        return clients, total

    async def get_client(self, client_id: uuid.UUID) -> Client | None:
        """Get a single client by ID."""
        result = await self.session.execute(
            select(Client).where(Client.id == client_id)  # type: ignore[arg-type]
        )
        return result.scalar_one_or_none()

    async def create_client(self, data: ClientCreate, agency_id: uuid.UUID) -> Client:
        """Create a new client within an agency."""
        client = Client(
            first_name=data.first_name,
            last_name=data.last_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            phone=data.phone,
            email=data.email,
            address=data.address,
            care_level=data.care_level,
            notes=data.notes,
            emergency_contacts=data.emergency_contacts,
            agency_id=agency_id,
        )
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client

    async def update_client(self, client_id: uuid.UUID, data: ClientUpdate) -> Client | None:
        """Update a client. Returns None if not found."""
        client = await self.get_client(client_id)
        if client is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)

        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client

    async def deactivate_client(self, client_id: uuid.UUID) -> Client | None:
        """Set client status to inactive."""
        client = await self.get_client(client_id)
        if client is None:
            return None

        client.status = ClientStatus.INACTIVE
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client

    async def add_family_link(self, data: FamilyLinkCreate, agency_id: uuid.UUID) -> FamilyLink:
        """Link a family member to a client."""
        link = FamilyLink(
            client_id=data.client_id,
            user_id=data.user_id,
            relationship_type=data.relationship_type,
            agency_id=agency_id,
        )
        self.session.add(link)
        await self.session.flush()
        await self.session.refresh(link)
        return link

    async def get_family_links(self, client_id: uuid.UUID) -> list[FamilyLink]:
        """Get all family links for a client."""
        result = await self.session.execute(
            select(FamilyLink).where(
                FamilyLink.client_id == client_id  # type: ignore[arg-type]
            )
        )
        return list(result.scalars().all())
