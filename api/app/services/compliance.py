"""Compliance rule and BAA management service."""

import json
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import BAARecord, ComplianceRule, ComplianceRuleType
from app.schemas.compliance import BAARecordCreate, ComplianceRuleCreate


class ComplianceService:
    """CRUD for compliance rules and BAA records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Compliance Rules ---

    async def list_rules(
        self,
        *,
        page: int = 1,
        size: int = 20,
        state_code: str | None = None,
        rule_type: ComplianceRuleType | None = None,
    ) -> tuple[list[ComplianceRule], int]:
        query = select(ComplianceRule).where(
            ComplianceRule.is_active == True  # type: ignore[arg-type]  # noqa: E712
        )
        if state_code:
            query = query.where(
                ComplianceRule.state_code == state_code  # type: ignore[arg-type]
            )
        if rule_type:
            query = query.where(
                ComplianceRule.rule_type == rule_type  # type: ignore[arg-type]
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * size).limit(size)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def create_rule(self, data: ComplianceRuleCreate, agency_id: uuid.UUID) -> ComplianceRule:
        rule = ComplianceRule(
            state_code=data.state_code,
            rule_type=data.rule_type,
            name=data.name,
            description=data.description,
            rule_json=json.dumps(data.rule_data),
            agency_id=agency_id,
        )
        self.session.add(rule)
        await self.session.flush()
        await self.session.refresh(rule)
        return rule

    @staticmethod
    def rule_to_response_data(rule: ComplianceRule) -> dict[str, Any]:
        """Convert rule model to response dict with parsed JSON."""
        return {
            "id": rule.id,
            "state_code": rule.state_code,
            "rule_type": rule.rule_type,
            "name": rule.name,
            "description": rule.description,
            "rule_data": json.loads(rule.rule_json),
            "is_active": rule.is_active,
            "agency_id": rule.agency_id,
            "created_at": rule.created_at,
        }

    # --- BAA Records ---

    async def list_baas(self, *, page: int = 1, size: int = 20) -> tuple[list[BAARecord], int]:
        query = select(BAARecord).where(
            BAARecord.is_active == True  # type: ignore[arg-type]  # noqa: E712
        )
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * size).limit(size)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def create_baa(self, data: BAARecordCreate, agency_id: uuid.UUID) -> BAARecord:
        baa = BAARecord(
            vendor_name=data.vendor_name,
            vendor_contact=data.vendor_contact,
            agreement_date=data.agreement_date,
            expiration_date=data.expiration_date,
            document_url=data.document_url,
            notes=data.notes,
            agency_id=agency_id,
        )
        self.session.add(baa)
        await self.session.flush()
        await self.session.refresh(baa)
        return baa
