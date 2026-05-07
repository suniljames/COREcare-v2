"""User model."""

import enum
import uuid

from sqlmodel import Field

from app.models.base import BaseModel


class UserRole(enum.StrEnum):
    """Role hierarchy: super_admin > agency_admin > care_manager > caregiver > family.

    `client` is a sibling axis, not a privilege level — Clients authenticate
    against their own row only and never traverse the staff role ladder.
    See `app.rbac.ROLE_HIERARCHY` (which intentionally excludes CLIENT).
    """

    SUPER_ADMIN = "super_admin"
    AGENCY_ADMIN = "agency_admin"
    CARE_MANAGER = "care_manager"
    CAREGIVER = "caregiver"
    FAMILY = "family"
    CLIENT = "client"


class User(BaseModel, table=True):
    """Platform user. Synced from Clerk. Agency-scoped (except super_admin)."""

    __tablename__ = "users"

    email: str = Field(unique=True, index=True)
    first_name: str = Field(default="")
    last_name: str = Field(default="")
    role: UserRole = Field(default=UserRole.CAREGIVER)
    is_active: bool = Field(default=True)
    clerk_id: str | None = Field(default=None, unique=True, index=True)
    agency_id: uuid.UUID | None = Field(
        default=None, foreign_key="agencies.id", index=True
    )
