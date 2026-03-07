"""Tests for user management CRUD."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, AuditEvent, User  # noqa: F401 — register models
from app.models.user import UserRole
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.user import UserService

TEST_DB_URL = "sqlite+aiosqlite:///./test_users.db"

AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh test database session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        # Create a test agency
        agency = Agency(id=AGENCY_ID, name="Test Agency", slug="test-agency")
        s.add(agency)
        await s.commit()
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


# --- Schema tests ---


@pytest.mark.asyncio
async def test_user_create_schema_valid() -> None:
    """UserCreate schema accepts valid data."""
    data = UserCreate(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        role=UserRole.CAREGIVER,
    )
    assert data.email == "test@example.com"
    assert data.role == UserRole.CAREGIVER


@pytest.mark.asyncio
async def test_user_create_schema_invalid_email() -> None:
    """UserCreate schema rejects invalid email."""
    with pytest.raises(ValueError):
        UserCreate(email="not-an-email", first_name="Test", last_name="User")


@pytest.mark.asyncio
async def test_user_update_schema_partial() -> None:
    """UserUpdate schema allows partial updates."""
    data = UserUpdate(first_name="NewName")
    assert data.first_name == "NewName"
    assert data.last_name is None
    assert data.role is None


@pytest.mark.asyncio
async def test_user_response_from_attributes() -> None:
    """UserResponse can be created from a User model."""
    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        role=UserRole.CAREGIVER,
        agency_id=AGENCY_ID,
    )
    resp = UserResponse.model_validate(user)
    assert resp.email == "test@example.com"


@pytest.mark.asyncio
async def test_user_list_response_structure() -> None:
    """UserListResponse has correct structure."""
    resp = UserListResponse(items=[], total=0, page=1, size=20)
    assert resp.total == 0
    assert resp.page == 1


# --- Service tests ---


@pytest.mark.asyncio
async def test_service_create_user(session: AsyncSession) -> None:
    """UserService.create_user persists a new user."""
    service = UserService(session)
    data = UserCreate(
        email="new@example.com",
        first_name="New",
        last_name="User",
        role=UserRole.CAREGIVER,
    )
    user = await service.create_user(data, default_agency_id=AGENCY_ID)
    await session.commit()

    assert user.id is not None
    assert user.email == "new@example.com"
    assert user.agency_id == AGENCY_ID


@pytest.mark.asyncio
async def test_service_list_users(session: AsyncSession) -> None:
    """UserService.list_users returns paginated results."""
    service = UserService(session)
    for i in range(5):
        await service.create_user(
            UserCreate(
                email=f"user{i}@example.com",
                first_name=f"User{i}",
                last_name="Test",
            ),
            default_agency_id=AGENCY_ID,
        )
    await session.commit()

    users, total = await service.list_users(page=1, size=3)
    assert total == 5
    assert len(users) == 3


@pytest.mark.asyncio
async def test_service_list_users_filter_role(session: AsyncSession) -> None:
    """UserService.list_users filters by role."""
    service = UserService(session)
    await service.create_user(
        UserCreate(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            role=UserRole.AGENCY_ADMIN,
        ),
        default_agency_id=AGENCY_ID,
    )
    await service.create_user(
        UserCreate(
            email="cg@example.com",
            first_name="CG",
            last_name="User",
            role=UserRole.CAREGIVER,
        ),
        default_agency_id=AGENCY_ID,
    )
    await session.commit()

    users, total = await service.list_users(role=UserRole.AGENCY_ADMIN)
    assert total == 1
    assert users[0].role == UserRole.AGENCY_ADMIN


@pytest.mark.asyncio
async def test_service_update_user(session: AsyncSession) -> None:
    """UserService.update_user modifies fields."""
    service = UserService(session)
    user = await service.create_user(
        UserCreate(email="update@example.com", first_name="Old", last_name="Name"),
        default_agency_id=AGENCY_ID,
    )
    await session.commit()

    updated = await service.update_user(user.id, UserUpdate(first_name="New"))
    await session.commit()

    assert updated is not None
    assert updated.first_name == "New"
    assert updated.last_name == "Name"


@pytest.mark.asyncio
async def test_service_deactivate_user(session: AsyncSession) -> None:
    """UserService.deactivate_user sets is_active=False."""
    service = UserService(session)
    user = await service.create_user(
        UserCreate(email="deactivate@example.com", first_name="To", last_name="Deactivate"),
        default_agency_id=AGENCY_ID,
    )
    await session.commit()

    deactivated = await service.deactivate_user(user.id)
    await session.commit()

    assert deactivated is not None
    assert deactivated.is_active is False


@pytest.mark.asyncio
async def test_service_get_user(session: AsyncSession) -> None:
    """UserService.get_user returns a user by ID."""
    service = UserService(session)
    user = await service.create_user(
        UserCreate(email="get@example.com", first_name="Get", last_name="User"),
        default_agency_id=AGENCY_ID,
    )
    await session.commit()

    found = await service.get_user(user.id)
    assert found is not None
    assert found.email == "get@example.com"


@pytest.mark.asyncio
async def test_service_get_user_not_found(session: AsyncSession) -> None:
    """UserService.get_user returns None for non-existent user."""
    service = UserService(session)
    result = await service.get_user(uuid.uuid4())
    assert result is None
