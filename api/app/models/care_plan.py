"""Care plan versioning model (issue #125).

Append-only versioned care plan with separated Client-facing (`plain_summary`,
`care_team_blob`, `weekly_support_blob`, `allergies`, `emergency_contact_blob`)
and staff-only (`clinical_detail`) fields. The Client API schema
(`ClientCarePlanRead`) excludes the staff field structurally; RLS enforces
which row, the schema enforces which fields.

A partial unique index (`is_active=true`) enforces "exactly one active
version per Client" at the database level.
"""

import uuid
from typing import Any

from sqlalchemy import JSON, Text
from sqlmodel import Column, Field

from app.models.base import TenantScopedModel


class CarePlanVersion(TenantScopedModel, table=True):
    """A single version of a Client's care plan. Append-only — never updated.

    Activating a new version is a transaction: deactivate-then-insert.
    The partial unique index on (client_id) WHERE is_active = true makes
    the race condition impossible at the DB layer.
    """

    __tablename__ = "care_plan_versions"

    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    version_no: int = Field(index=True)
    is_active: bool = Field(default=False, index=True)
    plain_summary: str = Field(default="", sa_column=Column(Text))
    care_team_blob: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    weekly_support_blob: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    allergies: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    emergency_contact_blob: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    clinical_detail: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    authored_by_user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    supersedes_version_id: uuid.UUID | None = Field(
        default=None, foreign_key="care_plan_versions.id"
    )
