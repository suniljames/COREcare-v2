"""Base model with common fields for all database models."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class BaseModel(SQLModel):
    """Abstract base with UUID primary key and timestamps."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # SQLModel's stubs declare sa_type as `type[Any]`, but the runtime accepts
    # type instances and forwards them to the underlying SQLAlchemy Column.
    # Passing `DateTime(timezone=True)` is what makes Postgres emit
    # `TIMESTAMP WITH TIME ZONE`; keeping the instance is intentional.
    created_at: datetime = Field(
        default_factory=_utcnow,
        nullable=False,
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        nullable=False,
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        sa_column_kwargs={"onupdate": _utcnow},
    )


class TenantScopedModel(BaseModel):
    """Base for models that belong to a specific agency (tenant).

    All models inheriting from this will have an agency_id FK and will be
    subject to PostgreSQL Row-Level Security policies.
    """

    agency_id: uuid.UUID = Field(foreign_key="agencies.id", index=True)
