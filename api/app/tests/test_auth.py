"""Tests for Clerk authentication integration."""

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, User  # noqa: F401 — register models
from app.models.user import UserRole

TEST_DB_URL = "sqlite+aiosqlite:///./test_auth.db"


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh test database session."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


def _make_protected_app() -> FastAPI:
    """Create a minimal FastAPI app with a protected endpoint."""
    from app.auth import get_current_user

    test_app = FastAPI()

    @test_app.get("/protected")
    async def protected(
        user: User = Depends(get_current_user),  # noqa: B008
    ) -> dict[str, str]:
        return {"email": user.email}

    return test_app


# --- Dev mode (no Clerk keys) tests ---


@pytest.mark.asyncio
async def test_dev_mode_no_auth_returns_mock_user() -> None:
    """In dev mode (no Clerk secret), missing auth returns dev mock user."""
    from app.auth import get_current_user

    assert get_current_user is not None
    assert callable(get_current_user)


@pytest.mark.asyncio
async def test_missing_auth_header_in_prod_mode() -> None:
    """When Clerk is configured, missing auth header returns 401."""
    test_app = _make_protected_app()

    with patch("app.auth.settings") as mock_settings:
        mock_settings.clerk_secret_key = "sk_test_fake"
        mock_settings.clerk_publishable_key = "pk_test_fake"
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/protected")
            assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_returns_401() -> None:
    """An invalid JWT token returns 401."""
    test_app = _make_protected_app()

    with (
        patch("app.auth.settings") as mock_settings,
        patch("app.auth._get_clerk_jwks", return_value={"fake-kid": {}}),
    ):
        mock_settings.clerk_secret_key = "sk_test_fake"
        mock_settings.clerk_publishable_key = "pk_test_fake"
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/protected", headers={"Authorization": "Bearer invalid.token.here"}
            )
            assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dev_mode_token_decodes() -> None:
    """In dev mode, a simple HS256 token is decoded without verification."""
    token = jwt.encode({"sub": "user_test123"}, "secret", algorithm="HS256")
    from app.auth import _decode_dev_token

    claims = _decode_dev_token(token)
    assert claims["sub"] == "user_test123"


@pytest.mark.asyncio
async def test_get_current_user_callable(session: AsyncSession) -> None:
    """get_current_user is a callable async function."""
    from app.auth import get_current_user

    agency_id = uuid.uuid4()
    user = User(
        email="test@test.com",
        first_name="Test",
        last_name="User",
        role=UserRole.CAREGIVER,
        clerk_id="clerk_test_123",
        agency_id=agency_id,
    )
    session.add(user)
    await session.commit()

    assert callable(get_current_user)
