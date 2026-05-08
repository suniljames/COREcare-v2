"""Tests for Clerk authentication integration."""

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import structlog
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.config import settings
from app.db import get_session
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


# ---------------------------------------------------------------------------
# Issue #241 — env-gated dev fallback + startup guard
# ---------------------------------------------------------------------------


def _attach_session_override(test_app: FastAPI, session: AsyncSession) -> None:
    """Wire the test's SQLite session into the app's get_session dependency."""

    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield session

    test_app.dependency_overrides[get_session] = _override


# Group 1 — runtime gate on get_current_user mock fallback (auth.py:114)


@pytest.mark.asyncio
async def test_dev_env_no_secret_no_header_returns_mock_user(
    session: AsyncSession,
) -> None:
    """environment=development + no secret + no header → 200 with mock super_admin."""
    test_app = _make_protected_app()
    _attach_session_override(test_app, session)
    with (
        patch.object(settings, "environment", "development"),
        patch.object(settings, "clerk_secret_key", ""),
    ):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/protected")
            assert resp.status_code == 200
            assert resp.json()["email"] == "dev@localhost"


@pytest.mark.asyncio
async def test_prod_env_no_secret_no_header_returns_401(
    session: AsyncSession,
) -> None:
    """environment=production + no secret + no header → 401 (the bug being fixed)."""
    test_app = _make_protected_app()
    _attach_session_override(test_app, session)
    with (
        patch.object(settings, "environment", "production"),
        patch.object(settings, "clerk_secret_key", ""),
    ):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/protected")
            assert resp.status_code == 401


@pytest.mark.asyncio
async def test_staging_env_no_secret_no_header_returns_401(
    session: AsyncSession,
) -> None:
    """environment=staging + no secret + no header → 401 (any non-development fails closed)."""
    test_app = _make_protected_app()
    _attach_session_override(test_app, session)
    with (
        patch.object(settings, "environment", "staging"),
        patch.object(settings, "clerk_secret_key", ""),
    ):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/protected")
            assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dev_env_with_secret_no_header_returns_401(
    session: AsyncSession,
) -> None:
    """environment=development + secret set + no header → 401.

    Real Clerk in dev still demands a token; the env gate alone does not
    re-enable the mock-user fallback when CLERK_SECRET_KEY is configured.
    """
    test_app = _make_protected_app()
    _attach_session_override(test_app, session)
    with (
        patch.object(settings, "environment", "development"),
        patch.object(settings, "clerk_secret_key", "sk_test_real"),
    ):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/protected")
            assert resp.status_code == 401


# Group 2 — runtime gate on _get_clerk_user_id verification-skip (auth.py:61)


@pytest.mark.asyncio
async def test_prod_env_no_secret_forged_token_returns_401(
    session: AsyncSession,
) -> None:
    """environment=production + no secret + forged Bearer for an EXISTING user → 401.

    Seeds a real user matching the forged ``sub`` claim; in unfixed code the
    dev-decode branch would resolve the forged token to that user and return 200.
    The env gate must block the dev-decode path so the request falls through to
    real JWKS verification (which 401s the unsigned-by-Clerk token).
    """
    agency_id = uuid.uuid4()
    target_user = User(
        email="target@victim.local",
        first_name="Target",
        last_name="Victim",
        role=UserRole.AGENCY_ADMIN,
        clerk_id="user_241_forged_target",
        agency_id=agency_id,
    )
    session.add(target_user)
    await session.commit()

    test_app = _make_protected_app()
    _attach_session_override(test_app, session)
    forged = jwt.encode({"sub": "user_241_forged_target"}, "fake-secret", algorithm="HS256")
    with (
        patch.object(settings, "environment", "production"),
        patch.object(settings, "clerk_secret_key", ""),
        patch("app.auth._get_clerk_jwks", return_value={}),
    ):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/protected", headers={"Authorization": f"Bearer {forged}"})
            assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dev_env_no_secret_token_resolves_seeded_user(
    session: AsyncSession,
) -> None:
    """environment=development + no secret + dev-decoded token with valid sub → 200, that user."""
    agency_id = uuid.uuid4()
    user = User(
        email="seeded@dev.local",
        first_name="Seeded",
        last_name="DevUser",
        role=UserRole.CAREGIVER,
        clerk_id="user_241_seeded",
        agency_id=agency_id,
    )
    session.add(user)
    await session.commit()

    test_app = _make_protected_app()
    _attach_session_override(test_app, session)
    token = jwt.encode({"sub": "user_241_seeded"}, "dummy", algorithm="HS256")
    with (
        patch.object(settings, "environment", "development"),
        patch.object(settings, "clerk_secret_key", ""),
    ):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/protected", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200
            assert resp.json()["email"] == "seeded@dev.local"


# Group 3 — startup guard


def test_startup_guard_raises_in_production_without_secret() -> None:
    """environment=production + no secret → _validate_startup_config raises RuntimeError."""
    from app.main import _validate_startup_config

    with (
        patch.object(settings, "environment", "production"),
        patch.object(settings, "clerk_secret_key", ""),
        pytest.raises(RuntimeError, match="CLERK_SECRET_KEY must be set"),
    ):
        _validate_startup_config()


def test_startup_guard_raises_in_staging_without_secret() -> None:
    """environment=staging + no secret → _validate_startup_config raises RuntimeError."""
    from app.main import _validate_startup_config

    with (
        patch.object(settings, "environment", "staging"),
        patch.object(settings, "clerk_secret_key", ""),
        pytest.raises(RuntimeError, match="CLERK_SECRET_KEY must be set"),
    ):
        _validate_startup_config()


def test_startup_guard_passes_in_development_without_secret() -> None:
    """environment=development + no secret → _validate_startup_config returns cleanly."""
    from app.main import _validate_startup_config

    with (
        patch.object(settings, "environment", "development"),
        patch.object(settings, "clerk_secret_key", ""),
    ):
        _validate_startup_config()  # should not raise


def test_startup_guard_passes_in_production_with_secret() -> None:
    """environment=production + secret set → _validate_startup_config returns cleanly."""
    from app.main import _validate_startup_config

    with (
        patch.object(settings, "environment", "production"),
        patch.object(settings, "clerk_secret_key", "sk_live_real"),
    ):
        _validate_startup_config()  # should not raise


# Group 4 — telemetry


@pytest.mark.asyncio
async def test_dev_fallback_emits_telemetry_event(session: AsyncSession) -> None:
    """When the dev fallback fires, log event auth.dev_fallback_used is emitted exactly once."""
    test_app = _make_protected_app()
    _attach_session_override(test_app, session)
    with (
        patch.object(settings, "environment", "development"),
        patch.object(settings, "clerk_secret_key", ""),
        structlog.testing.capture_logs() as captured,
    ):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/protected")
            assert resp.status_code == 200

    fallback_events = [e for e in captured if e.get("event") == "auth.dev_fallback_used"]
    assert len(fallback_events) == 1
    assert fallback_events[0].get("environment") == "development"
    assert fallback_events[0].get("path") == "/protected"
