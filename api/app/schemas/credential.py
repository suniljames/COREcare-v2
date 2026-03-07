"""Credential request/response schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.credential import CredentialStatus, CredentialType


class CredentialCreate(BaseModel):
    caregiver_id: uuid.UUID
    credential_type: CredentialType
    name: str
    issuing_authority: str = ""
    credential_number: str = ""
    issued_date: date | None = None
    expiration_date: date | None = None
    document_url: str = ""
    notes: str = ""


class CredentialUpdate(BaseModel):
    name: str | None = None
    issuing_authority: str | None = None
    credential_number: str | None = None
    issued_date: date | None = None
    expiration_date: date | None = None
    status: CredentialStatus | None = None
    document_url: str | None = None
    notes: str | None = None


class CredentialResponse(BaseModel):
    id: uuid.UUID
    caregiver_id: uuid.UUID
    credential_type: CredentialType
    name: str
    issuing_authority: str
    credential_number: str
    issued_date: date | None
    expiration_date: date | None
    status: CredentialStatus
    document_url: str
    notes: str
    alert_sent_90: bool
    alert_sent_60: bool
    alert_sent_30: bool
    alert_sent_7: bool
    agency_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CredentialListResponse(BaseModel):
    items: list[CredentialResponse]
    total: int
    page: int
    size: int


class ExpiringCredentialAlert(BaseModel):
    credential_id: uuid.UUID
    caregiver_id: uuid.UUID
    name: str
    credential_type: CredentialType
    expiration_date: date
    days_until_expiry: int
