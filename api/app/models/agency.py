"""Agency (tenant) model."""

from sqlmodel import Field

from app.models.base import BaseModel


class Agency(BaseModel, table=True):
    """A home care agency — the tenant unit for multi-tenancy."""

    __tablename__ = "agencies"

    name: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    is_active: bool = Field(default=True)
    address: str | None = None
    phone: str | None = None
    email: str | None = None
