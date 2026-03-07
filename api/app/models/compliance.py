"""Multi-state compliance and HIPAA infrastructure models."""

import enum

from sqlmodel import Column, Field, Text

from app.models.base import TenantScopedModel


class ComplianceRuleType(enum.StrEnum):
    OVERTIME = "overtime"
    MINIMUM_WAGE = "minimum_wage"
    REST_PERIOD = "rest_period"
    TRAINING_REQUIREMENT = "training_requirement"
    BACKGROUND_CHECK = "background_check"
    LICENSURE = "licensure"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class ComplianceRule(TenantScopedModel, table=True):
    """A state-specific compliance rule for an agency."""

    __tablename__ = "compliance_rules"

    state_code: str = Field(max_length=2, index=True)
    rule_type: ComplianceRuleType = Field(index=True)
    name: str = Field(max_length=200)
    description: str = Field(default="", sa_column=Column(Text))
    rule_json: str = Field(default="{}", sa_column=Column(Text))
    is_active: bool = Field(default=True)


class BAARecord(TenantScopedModel, table=True):
    """Business Associate Agreement tracking for HIPAA compliance."""

    __tablename__ = "baa_records"

    vendor_name: str = Field(max_length=200)
    vendor_contact: str = Field(default="", max_length=200)
    agreement_date: str = Field(default="", max_length=10)
    expiration_date: str = Field(default="", max_length=10)
    document_url: str = Field(default="", max_length=500)
    is_active: bool = Field(default=True)
    notes: str = Field(default="", sa_column=Column(Text))
