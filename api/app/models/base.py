"""Base model with common fields for all database models."""

import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class BaseModel(SQLModel):
    """Abstract base with UUID primary key and timestamps."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=_utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": _utcnow},
    )


class TenantScopedModel(BaseModel):
    """Base for models that belong to a specific agency (tenant).

    All models inheriting from this will have an agency_id FK and will be
    subject to PostgreSQL Row-Level Security policies.
    """

    agency_id: uuid.UUID = Field(foreign_key="agencies.id", index=True)
