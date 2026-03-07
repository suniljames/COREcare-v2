"""Tests for credential management with expiration tracking."""

import uuid
from collections.abc import AsyncGenerator
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import Agency, Client, Credential, Shift, User, Visit  # noqa: F401
from app.models.credential import CredentialStatus, CredentialType
from app.models.user import UserRole
from app.schemas.credential import CredentialCreate, CredentialUpdate
from app.services.credential import CredentialService

TEST_DB_URL = "sqlite+aiosqlite:///./test_credentials.db"
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TODAY = date.today()


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
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


async def _create_caregiver(session: AsyncSession) -> User:
    cg = User(
        email="cg@test.com",
        first_name="CG",
        last_name="Test",
        role=UserRole.CAREGIVER,
        agency_id=AGENCY_ID,
    )
    session.add(cg)
    await session.commit()
    await session.refresh(cg)
    return cg


@pytest.mark.asyncio
async def test_create_credential(session: AsyncSession) -> None:
    """Creating a credential stores all fields."""
    cg = await _create_caregiver(session)
    service = CredentialService(session)

    cred = await service.create_credential(
        CredentialCreate(
            caregiver_id=cg.id,
            credential_type=CredentialType.LICENSE,
            name="RN License",
            issuing_authority="State Board of Nursing",
            credential_number="RN-12345",
            issued_date=TODAY - timedelta(days=365),
            expiration_date=TODAY + timedelta(days=180),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert cred.name == "RN License"
    assert cred.credential_type == CredentialType.LICENSE
    assert cred.status == CredentialStatus.ACTIVE


@pytest.mark.asyncio
async def test_update_credential(session: AsyncSession) -> None:
    """Updating a credential changes the specified fields."""
    cg = await _create_caregiver(session)
    service = CredentialService(session)

    cred = await service.create_credential(
        CredentialCreate(
            caregiver_id=cg.id,
            credential_type=CredentialType.CERTIFICATION,
            name="CPR Cert",
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    updated = await service.update_credential(
        cred.id,
        CredentialUpdate(name="CPR/AED Certification", issuing_authority="AHA"),
    )
    await session.commit()

    assert updated is not None
    assert updated.name == "CPR/AED Certification"
    assert updated.issuing_authority == "AHA"


@pytest.mark.asyncio
async def test_delete_credential(session: AsyncSession) -> None:
    """Deleting a credential removes it from the database."""
    cg = await _create_caregiver(session)
    service = CredentialService(session)

    cred = await service.create_credential(
        CredentialCreate(
            caregiver_id=cg.id,
            credential_type=CredentialType.TRAINING,
            name="HIPAA Training",
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    deleted = await service.delete_credential(cred.id)
    await session.commit()
    assert deleted is True

    # Verify it's gone
    result = await service.get_credential(cred.id)
    assert result is None


@pytest.mark.asyncio
async def test_check_expiring_finds_credentials(session: AsyncSession) -> None:
    """check_expiring returns credentials expiring within 90 days."""
    cg = await _create_caregiver(session)
    service = CredentialService(session)

    # Expiring in 30 days - should appear
    await service.create_credential(
        CredentialCreate(
            caregiver_id=cg.id,
            credential_type=CredentialType.LICENSE,
            name="Expiring License",
            expiration_date=TODAY + timedelta(days=30),
        ),
        agency_id=AGENCY_ID,
    )
    # Expiring in 180 days - should NOT appear
    await service.create_credential(
        CredentialCreate(
            caregiver_id=cg.id,
            credential_type=CredentialType.CERTIFICATION,
            name="Far Out Cert",
            expiration_date=TODAY + timedelta(days=180),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    alerts = await service.check_expiring(reference_date=TODAY)
    assert len(alerts) == 1
    assert alerts[0].name == "Expiring License"
    assert alerts[0].days_until_expiry == 30


@pytest.mark.asyncio
async def test_check_expiring_excludes_past(session: AsyncSession) -> None:
    """check_expiring excludes already-expired credentials."""
    cg = await _create_caregiver(session)
    service = CredentialService(session)

    await service.create_credential(
        CredentialCreate(
            caregiver_id=cg.id,
            credential_type=CredentialType.LICENSE,
            name="Already Expired",
            expiration_date=TODAY - timedelta(days=10),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    alerts = await service.check_expiring(reference_date=TODAY)
    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_update_expiration_statuses(session: AsyncSession) -> None:
    """update_expiration_statuses transitions credentials to correct status."""
    cg = await _create_caregiver(session)
    service = CredentialService(session)

    # Create credentials at different stages
    expired_cred = await service.create_credential(
        CredentialCreate(
            caregiver_id=cg.id,
            credential_type=CredentialType.LICENSE,
            name="Expired",
            expiration_date=TODAY - timedelta(days=5),
        ),
        agency_id=AGENCY_ID,
    )
    expiring_cred = await service.create_credential(
        CredentialCreate(
            caregiver_id=cg.id,
            credential_type=CredentialType.CERTIFICATION,
            name="Expiring Soon",
            expiration_date=TODAY + timedelta(days=45),
        ),
        agency_id=AGENCY_ID,
    )
    active_cred = await service.create_credential(
        CredentialCreate(
            caregiver_id=cg.id,
            credential_type=CredentialType.TRAINING,
            name="Still Active",
            expiration_date=TODAY + timedelta(days=200),
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    updated_count = await service.update_expiration_statuses(reference_date=TODAY)
    await session.commit()

    # Refresh to get updated statuses
    expired_refreshed = await service.get_credential(expired_cred.id)
    expiring_refreshed = await service.get_credential(expiring_cred.id)
    active_refreshed = await service.get_credential(active_cred.id)

    assert expired_refreshed is not None
    assert expired_refreshed.status == CredentialStatus.EXPIRED
    assert expiring_refreshed is not None
    assert expiring_refreshed.status == CredentialStatus.EXPIRING_SOON
    assert active_refreshed is not None
    assert active_refreshed.status == CredentialStatus.ACTIVE
    assert updated_count == 2  # expired + expiring_soon changed


@pytest.mark.asyncio
async def test_list_credentials_filter_by_type(session: AsyncSession) -> None:
    """Filtering credentials by type returns correct subset."""
    cg = await _create_caregiver(session)
    service = CredentialService(session)

    await service.create_credential(
        CredentialCreate(
            caregiver_id=cg.id,
            credential_type=CredentialType.LICENSE,
            name="License",
        ),
        agency_id=AGENCY_ID,
    )
    await service.create_credential(
        CredentialCreate(
            caregiver_id=cg.id,
            credential_type=CredentialType.TRAINING,
            name="Training",
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    creds, total = await service.list_credentials(credential_type=CredentialType.LICENSE)
    assert total == 1
    assert creds[0].name == "License"
