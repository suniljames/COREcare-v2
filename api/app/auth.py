"""Authentication: Clerk JWT validation and user resolution."""

import uuid

import httpx
import structlog
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.models.user import User
from app.tenant import clear_tenant_context, set_tenant_context

logger = structlog.get_logger()

# Clerk JWKS cache (populated on first request)
_jwks: dict[str, dict[str, str]] = {}


async def _get_clerk_jwks() -> dict[str, dict[str, str]]:
    """Fetch Clerk's JWKS (JSON Web Key Set) for JWT verification."""
    global _jwks  # noqa: PLW0603
    if _jwks:
        return _jwks

    # Clerk exposes JWKS at a well-known endpoint
    jwks_url = f"https://{settings.clerk_publishable_key.split('_')[1]}.clerk.accounts.dev/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_url)
        resp.raise_for_status()
        data = resp.json()
        for key in data.get("keys", []):
            _jwks[key["kid"]] = key
    return _jwks


def _decode_dev_token(token: str) -> dict[str, str]:
    """In dev mode (no Clerk keys), decode without verification."""
    result: dict[str, str] = jwt.decode(
        token, "", algorithms=["HS256"], options={"verify_signature": False}
    )
    return result


async def _get_clerk_user_id(request: Request) -> str:
    """Extract and validate the Clerk user ID from the request."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header[7:]

    # Dev mode: skip verification when no Clerk secret configured
    if not settings.clerk_secret_key:
        try:
            claims = jwt.decode(
                token, "", algorithms=["HS256", "RS256"], options={"verify_signature": False}
            )
            sub: str = claims.get("sub", "")
            return sub
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
            ) from e

    # Production: verify against Clerk JWKS
    try:
        jwks = await _get_clerk_jwks()
        header = jwt.get_unverified_header(token)
        kid: str = header.get("kid", "")
        if kid not in jwks:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unknown signing key",
            )
        claims = jwt.decode(
            token,
            jwks[kid],
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        sub = claims.get("sub", "")
        return str(sub)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        ) from e


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> User:
    """FastAPI dependency: resolve authenticated user and set tenant context.

    In dev mode with no Clerk configured and no Authorization header,
    returns a mock admin user for testing convenience.
    """
    auth_header = request.headers.get("Authorization", "")

    # Dev fallback: no Clerk configured and no auth header → mock user
    if not settings.clerk_secret_key and not auth_header:
        await clear_tenant_context(session)
        return User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000099"),
            email="dev@localhost",
            first_name="Dev",
            last_name="User",
            role="super_admin",
            agency_id=None,
        )

    clerk_user_id = await _get_clerk_user_id(request)

    # Look up local user by clerk_id
    result = await session.execute(
        select(User).where(User.clerk_id == clerk_user_id)  # type: ignore[arg-type]
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Account may not be synced.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Set tenant context for RLS
    if user.agency_id:
        await set_tenant_context(session, user.agency_id)
    else:
        await clear_tenant_context(session)

    return user
