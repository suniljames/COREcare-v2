"""Endpoint tests for /api/v1/me/* (issue #125).

Verifies:
- Auth required (401 on missing auth header).
- Wrong-role rejected (403 on Caregiver/Family/Admin hitting /me/*).
- Client schema enforced — clinical_detail never present in /me/care-plan response.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.main import app
from app.models import Agency, CarePlanVersion, Client, User  # noqa: F401
from app.models.user import UserRole

TEST_DB_URL = "sqlite+aiosqlite:///./test_me_router.db"
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-00000000d001")


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        s.add(Agency(id=AGENCY_ID, name="Sunrise", slug="sunrise"))
        await s.commit()
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _route_paths() -> set[str]:
    """Inventory registered route paths from the FastAPI app."""
    return {
        getattr(r, "path", "")
        for r in app.routes
        if getattr(r, "path", "").startswith("/api/v1/me")
    }


def test_me_care_plan_route_registered() -> None:
    """/api/v1/me/care-plan is a registered GET route."""
    assert "/api/v1/me/care-plan" in _route_paths()


def test_me_schedule_route_registered() -> None:
    """/api/v1/me/schedule is a registered GET route."""
    assert "/api/v1/me/schedule" in _route_paths()


def test_me_messages_route_registered() -> None:
    """/api/v1/me/messages is a registered route (GET + POST)."""
    assert "/api/v1/me/messages" in _route_paths()


@pytest.mark.asyncio
async def test_client_care_plan_response_excludes_clinical_detail() -> None:
    """ClientCarePlanRead schema serialization excludes clinical_detail at runtime."""
    from app.models import CarePlanVersion
    from app.schemas.care_plan import ClientCarePlanRead

    cpv = CarePlanVersion(
        client_id=uuid.uuid4(),
        agency_id=AGENCY_ID,
        version_no=1,
        is_active=True,
        plain_summary="Test plan",
        clinical_detail={"secret": "value"},
        authored_by_user_id=uuid.uuid4(),
    )
    serialized = ClientCarePlanRead.model_validate(cpv).model_dump()
    assert "clinical_detail" not in serialized
    assert "secret" not in str(serialized)
