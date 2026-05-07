"""Tests for the Client-persona invite issuance + redemption flow (issue #125).

Per Security review §2-3: invite-only account creation, email-match required,
72h TTL, single-use. Audit log entries written on every outcome.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, AuditEvent, Client, User  # noqa: F401
from app.models.user import UserRole

TEST_DB_URL = "sqlite+aiosqlite:///./test_client_invite.db"
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-00000000b001")


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
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


# --- Model ---


def test_client_invite_model_exists() -> None:
    """ClientInvite model importable from app.models."""
    from app.models import ClientInvite  # noqa: F401

    assert ClientInvite is not None


# --- Issuance ---


@pytest.mark.asyncio
async def test_issue_invite_creates_row(session: AsyncSession) -> None:
    """issue_invite persists a token row with TTL and email."""
    from app.services.client_invite import ClientInviteService

    client = Client(first_name="Eleanor", last_name="X", agency_id=AGENCY_ID)
    session.add(client)
    await session.commit()
    await session.refresh(client)

    actor = User(email="cm@test.com", role=UserRole.CARE_MANAGER, agency_id=AGENCY_ID)
    session.add(actor)
    await session.commit()
    await session.refresh(actor)

    service = ClientInviteService(session)
    invite = await service.issue_invite(
        client_id=client.id,
        email="eleanor@example.com",
        actor_user_id=actor.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert invite.id is not None
    assert invite.client_id == client.id
    assert invite.email == "eleanor@example.com"
    assert invite.token  # non-empty
    assert invite.redeemed_at is None
    # Default TTL: 72h
    expires = invite.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    assert expires > datetime.now(UTC) + timedelta(hours=71)


@pytest.mark.asyncio
async def test_issue_invite_writes_audit(session: AsyncSession) -> None:
    """Issuance writes a 'client_invite_issued' audit event."""
    from app.services.client_invite import ClientInviteService

    client = Client(first_name="Eleanor", last_name="X", agency_id=AGENCY_ID)
    actor = User(email="cm@test.com", role=UserRole.CARE_MANAGER, agency_id=AGENCY_ID)
    session.add(client)
    session.add(actor)
    await session.commit()
    await session.refresh(client)
    await session.refresh(actor)

    service = ClientInviteService(session)
    await service.issue_invite(
        client_id=client.id,
        email="eleanor@example.com",
        actor_user_id=actor.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    result = await session.execute(
        select(AuditEvent).where(AuditEvent.resource_type == "client_invite")  # type: ignore[arg-type]
    )
    events = list(result.scalars().all())
    assert len(events) == 1
    assert events[0].details == "client_invite_issued"


# --- Redemption ---


@pytest.mark.asyncio
async def test_redeem_invite_matching_email_succeeds(session: AsyncSession) -> None:
    """Redemption with matching email links the User and Client."""
    from app.services.client_invite import ClientInviteService

    client = Client(first_name="Eleanor", last_name="X", agency_id=AGENCY_ID)
    actor = User(email="cm@test.com", role=UserRole.CARE_MANAGER, agency_id=AGENCY_ID)
    session.add(client)
    session.add(actor)
    await session.commit()
    await session.refresh(client)
    await session.refresh(actor)

    service = ClientInviteService(session)
    invite = await service.issue_invite(
        client_id=client.id,
        email="eleanor@example.com",
        actor_user_id=actor.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    user, redeemed_client = await service.redeem_invite(
        token=invite.token,
        clerk_user_id="clerk_user_eleanor",
        clerk_email="eleanor@example.com",
    )
    await session.commit()

    assert user.role == UserRole.CLIENT
    assert user.clerk_id == "clerk_user_eleanor"
    assert user.email == "eleanor@example.com"
    assert user.agency_id == AGENCY_ID
    assert redeemed_client.id == client.id
    assert redeemed_client.client_user_id == user.id


@pytest.mark.asyncio
async def test_redeem_invite_email_mismatch_fails(session: AsyncSession) -> None:
    """Redemption with a different email raises and writes audit."""
    from fastapi import HTTPException

    from app.services.client_invite import ClientInviteService

    client = Client(first_name="Eleanor", last_name="X", agency_id=AGENCY_ID)
    actor = User(email="cm@test.com", role=UserRole.CARE_MANAGER, agency_id=AGENCY_ID)
    session.add(client)
    session.add(actor)
    await session.commit()
    await session.refresh(client)
    await session.refresh(actor)

    service = ClientInviteService(session)
    invite = await service.issue_invite(
        client_id=client.id,
        email="eleanor@example.com",
        actor_user_id=actor.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await service.redeem_invite(
            token=invite.token,
            clerk_user_id="attacker_clerk",
            clerk_email="attacker@example.com",
        )
    assert exc_info.value.status_code == 403

    # Audit written
    result = await session.execute(
        select(AuditEvent).where(
            AuditEvent.details == "client_invite_failed_email_mismatch"  # type: ignore[arg-type]
        )
    )
    events = list(result.scalars().all())
    assert len(events) == 1


@pytest.mark.asyncio
async def test_redeem_invite_expired_fails(session: AsyncSession) -> None:
    """Redemption past TTL raises 410 Gone."""
    from fastapi import HTTPException

    from app.models import ClientInvite
    from app.services.client_invite import ClientInviteService

    client = Client(first_name="Eleanor", last_name="X", agency_id=AGENCY_ID)
    actor = User(email="cm@test.com", role=UserRole.CARE_MANAGER, agency_id=AGENCY_ID)
    session.add(client)
    session.add(actor)
    await session.commit()
    await session.refresh(client)
    await session.refresh(actor)

    expired = ClientInvite(
        client_id=client.id,
        agency_id=AGENCY_ID,
        email="eleanor@example.com",
        token="expired_token_value",
        expires_at=datetime.now(UTC) - timedelta(hours=1),
        issued_by_user_id=actor.id,
    )
    session.add(expired)
    await session.commit()

    service = ClientInviteService(session)
    with pytest.raises(HTTPException) as exc_info:
        await service.redeem_invite(
            token="expired_token_value",
            clerk_user_id="clerk_x",
            clerk_email="eleanor@example.com",
        )
    assert exc_info.value.status_code == 410


@pytest.mark.asyncio
async def test_redeem_invite_single_use(session: AsyncSession) -> None:
    """Re-redeeming an already-redeemed invite raises 410 Gone."""
    from fastapi import HTTPException

    from app.services.client_invite import ClientInviteService

    client = Client(first_name="Eleanor", last_name="X", agency_id=AGENCY_ID)
    actor = User(email="cm@test.com", role=UserRole.CARE_MANAGER, agency_id=AGENCY_ID)
    session.add(client)
    session.add(actor)
    await session.commit()
    await session.refresh(client)
    await session.refresh(actor)

    service = ClientInviteService(session)
    invite = await service.issue_invite(
        client_id=client.id,
        email="eleanor@example.com",
        actor_user_id=actor.id,
        agency_id=AGENCY_ID,
    )
    await session.commit()

    # First redemption succeeds
    await service.redeem_invite(
        token=invite.token,
        clerk_user_id="clerk_first",
        clerk_email="eleanor@example.com",
    )
    await session.commit()

    # Second attempt fails
    with pytest.raises(HTTPException) as exc_info:
        await service.redeem_invite(
            token=invite.token,
            clerk_user_id="clerk_second",
            clerk_email="eleanor@example.com",
        )
    assert exc_info.value.status_code == 410
