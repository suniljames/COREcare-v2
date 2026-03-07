"""Tests for client management."""

import uuid
from collections.abc import AsyncGenerator
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, AuditEvent, Client, FamilyLink, User  # noqa: F401
from app.models.client import ClientStatus
from app.models.user import UserRole
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate, FamilyLinkCreate
from app.services.client import ClientService

TEST_DB_URL = "sqlite+aiosqlite:///./test_clients.db"

AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh test database session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        agency = Agency(id=AGENCY_ID, name="Test Agency", slug="test-agency")
        s.add(agency)
        await s.commit()
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


# --- Schema tests ---


@pytest.mark.asyncio
async def test_client_create_schema() -> None:
    """ClientCreate schema accepts valid data."""
    data = ClientCreate(first_name="John", last_name="Doe")
    assert data.first_name == "John"
    assert data.date_of_birth is None


@pytest.mark.asyncio
async def test_client_response_from_model() -> None:
    """ClientResponse can be created from a Client model."""
    client = Client(
        first_name="Jane",
        last_name="Doe",
        agency_id=AGENCY_ID,
    )
    resp = ClientResponse.model_validate(client)
    assert resp.first_name == "Jane"
    assert resp.status == ClientStatus.ACTIVE


# --- Service tests ---


@pytest.mark.asyncio
async def test_service_create_client(session: AsyncSession) -> None:
    """ClientService.create_client persists a new client."""
    service = ClientService(session)
    data = ClientCreate(
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1950, 1, 15),
        phone="555-0100",
    )
    client = await service.create_client(data, agency_id=AGENCY_ID)
    await session.commit()

    assert client.id is not None
    assert client.first_name == "John"
    assert client.agency_id == AGENCY_ID
    assert client.status == ClientStatus.ACTIVE


@pytest.mark.asyncio
async def test_service_list_clients(session: AsyncSession) -> None:
    """ClientService.list_clients returns paginated results."""
    service = ClientService(session)
    for i in range(5):
        await service.create_client(
            ClientCreate(first_name=f"Client{i}", last_name="Test"),
            agency_id=AGENCY_ID,
        )
    await session.commit()

    clients, total = await service.list_clients(page=1, size=3)
    assert total == 5
    assert len(clients) == 3


@pytest.mark.asyncio
async def test_service_list_clients_filter_status(session: AsyncSession) -> None:
    """ClientService.list_clients filters by status."""
    service = ClientService(session)
    await service.create_client(
        ClientCreate(first_name="Active", last_name="Client"),
        agency_id=AGENCY_ID,
    )
    c2 = await service.create_client(
        ClientCreate(first_name="Inactive", last_name="Client"),
        agency_id=AGENCY_ID,
    )
    await session.commit()
    await service.deactivate_client(c2.id)
    await session.commit()

    clients, total = await service.list_clients(status=ClientStatus.ACTIVE)
    assert total == 1
    assert clients[0].first_name == "Active"


@pytest.mark.asyncio
async def test_service_update_client(session: AsyncSession) -> None:
    """ClientService.update_client modifies fields."""
    service = ClientService(session)
    client = await service.create_client(
        ClientCreate(first_name="Old", last_name="Name"),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    updated = await service.update_client(client.id, ClientUpdate(first_name="New"))
    await session.commit()

    assert updated is not None
    assert updated.first_name == "New"
    assert updated.last_name == "Name"


@pytest.mark.asyncio
async def test_service_deactivate_client(session: AsyncSession) -> None:
    """ClientService.deactivate_client sets status=inactive."""
    service = ClientService(session)
    client = await service.create_client(
        ClientCreate(first_name="To", last_name="Deactivate"),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    deactivated = await service.deactivate_client(client.id)
    await session.commit()

    assert deactivated is not None
    assert deactivated.status == ClientStatus.INACTIVE


@pytest.mark.asyncio
async def test_service_family_link(session: AsyncSession) -> None:
    """ClientService can link a family member to a client."""
    service = ClientService(session)
    client = await service.create_client(
        ClientCreate(first_name="Patient", last_name="One"),
        agency_id=AGENCY_ID,
    )
    # Create a family user
    family_user = User(
        email="family@test.com",
        first_name="Mary",
        last_name="Family",
        role=UserRole.FAMILY,
        agency_id=AGENCY_ID,
    )
    session.add(family_user)
    await session.commit()
    await session.refresh(family_user)

    link = await service.add_family_link(
        FamilyLinkCreate(
            client_id=client.id,
            user_id=family_user.id,
            relationship_type="spouse",
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert link.client_id == client.id
    assert link.user_id == family_user.id
    assert link.relationship_type == "spouse"

    # Verify retrieval
    links = await service.get_family_links(client.id)
    assert len(links) == 1


@pytest.mark.asyncio
async def test_service_get_client_not_found(session: AsyncSession) -> None:
    """ClientService.get_client returns None for non-existent client."""
    service = ClientService(session)
    result = await service.get_client(uuid.uuid4())
    assert result is None
