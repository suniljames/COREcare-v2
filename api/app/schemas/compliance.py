"""Compliance rule and BAA schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.compliance import ComplianceRuleType


class ComplianceRuleCreate(BaseModel):
    state_code: str
    rule_type: ComplianceRuleType
    name: str
    description: str = ""
    rule_data: dict[str, Any] = {}


class ComplianceRuleResponse(BaseModel):
    id: uuid.UUID
    state_code: str
    rule_type: ComplianceRuleType
    name: str
    description: str
    rule_data: dict[str, Any]
    is_active: bool
    agency_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ComplianceRuleListResponse(BaseModel):
    items: list[ComplianceRuleResponse]
    total: int
    page: int
    size: int


class BAARecordCreate(BaseModel):
    vendor_name: str
    vendor_contact: str = ""
    agreement_date: str = ""
    expiration_date: str = ""
    document_url: str = ""
    notes: str = ""


class BAARecordResponse(BaseModel):
    id: uuid.UUID
    vendor_name: str
    vendor_contact: str
    agreement_date: str
    expiration_date: str
    document_url: str
    is_active: bool
    notes: str
    agency_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
