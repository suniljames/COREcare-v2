"""Audit event model for HIPAA-grade logging."""

import enum
import uuid
from typing import Any

from sqlalchemy import JSON
from sqlmodel import Column, Field

from app.models.base import BaseModel


class AuditAction(enum.StrEnum):
    """Actions that can be audited."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"


class AuditEvent(BaseModel, table=True):
    """Immutable audit log entry. Append-only — never update or delete.

    Not tenant-scoped via RLS because super-admin actions span tenants.
    Filtering by agency_id is done at query time.
    """

    __tablename__ = "audit_events"

    user_id: uuid.UUID | None = Field(default=None, index=True)
    agency_id: uuid.UUID | None = Field(default=None, foreign_key="agencies.id", index=True)
    action: AuditAction = Field(index=True)
    resource_type: str = Field(index=True)
    resource_id: str = Field(default="")
    is_phi_access: bool = Field(default=False, index=True)
    ip_address: str = Field(default="")
    user_agent: str = Field(default="")
    details: str = Field(default="")
    changes: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
