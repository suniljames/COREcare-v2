"""Tests for compliance rules and BAA records."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.models import (  # noqa: F401
    Agency,
    AIConversation,
    AIFeatureFlag,
    AIMessage,
    BAARecord,
    Client,
    ComplianceRule,
    Shift,
    User,
    Visit,
)
from app.models.compliance import ComplianceRuleType
from app.schemas.compliance import BAARecordCreate, ComplianceRuleCreate
from app.services.compliance import ComplianceService

TEST_DB_URL = "sqlite+aiosqlite:///./test_compliance.db"
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


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


@pytest.mark.asyncio
async def test_create_compliance_rule(session: AsyncSession) -> None:
    """Creating a compliance rule stores state and type."""
    service = ComplianceService(session)
    rule = await service.create_rule(
        ComplianceRuleCreate(
            state_code="CA",
            rule_type=ComplianceRuleType.OVERTIME,
            name="CA Overtime",
            description="Daily overtime after 8 hours",
            rule_data={"daily_threshold": 8, "rate_multiplier": 1.5},
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert rule.state_code == "CA"
    assert rule.rule_type == ComplianceRuleType.OVERTIME
    assert rule.is_active is True


@pytest.mark.asyncio
async def test_list_rules_by_state(session: AsyncSession) -> None:
    """Filtering rules by state returns correct subset."""
    service = ComplianceService(session)
    await service.create_rule(
        ComplianceRuleCreate(
            state_code="CA",
            rule_type=ComplianceRuleType.OVERTIME,
            name="CA Rule",
        ),
        agency_id=AGENCY_ID,
    )
    await service.create_rule(
        ComplianceRuleCreate(
            state_code="NY",
            rule_type=ComplianceRuleType.MINIMUM_WAGE,
            name="NY Rule",
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    ca_rules, ca_total = await service.list_rules(state_code="CA")
    assert ca_total == 1
    assert ca_rules[0].state_code == "CA"


@pytest.mark.asyncio
async def test_create_baa(session: AsyncSession) -> None:
    """Creating a BAA record stores vendor info."""
    service = ComplianceService(session)
    baa = await service.create_baa(
        BAARecordCreate(
            vendor_name="Cloud Storage Inc.",
            vendor_contact="legal@cloud.com",
            agreement_date="2026-01-01",
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    assert baa.vendor_name == "Cloud Storage Inc."
    assert baa.is_active is True


@pytest.mark.asyncio
async def test_rule_to_response_data(session: AsyncSession) -> None:
    """rule_to_response_data parses JSON correctly."""
    service = ComplianceService(session)
    rule = await service.create_rule(
        ComplianceRuleCreate(
            state_code="TX",
            rule_type=ComplianceRuleType.REST_PERIOD,
            name="TX Rest",
            rule_data={"min_rest_hours": 8},
        ),
        agency_id=AGENCY_ID,
    )
    await session.commit()

    data = service.rule_to_response_data(rule)
    assert data["rule_data"] == {"min_rest_hours": 8}
