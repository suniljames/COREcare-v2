"""Caregiver credential management models."""

import enum
import uuid
from datetime import date

from sqlmodel import Column, Field, Text

from app.models.base import TenantScopedModel


class CredentialStatus(enum.StrEnum):
    ACTIVE = "active"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    PENDING_REVIEW = "pending_review"


class CredentialType(enum.StrEnum):
    LICENSE = "license"
    CERTIFICATION = "certification"
    TRAINING = "training"
    BACKGROUND_CHECK = "background_check"
    HEALTH_SCREENING = "health_screening"
    OTHER = "other"


class Credential(TenantScopedModel, table=True):
    """A caregiver's credential (license, certification, etc.)."""

    __tablename__ = "credentials"

    caregiver_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    credential_type: CredentialType = Field(index=True)
    name: str = Field(max_length=200)
    issuing_authority: str = Field(default="", max_length=200)
    credential_number: str = Field(default="", max_length=100)
    issued_date: date | None = None
    expiration_date: date | None = None
    status: CredentialStatus = Field(default=CredentialStatus.ACTIVE, index=True)
    document_url: str = Field(default="", max_length=500)
    notes: str = Field(default="", sa_column=Column(Text))
    alert_sent_90: bool = Field(default=False)
    alert_sent_60: bool = Field(default=False)
    alert_sent_30: bool = Field(default=False)
    alert_sent_7: bool = Field(default=False)
