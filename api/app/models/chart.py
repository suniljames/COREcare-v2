"""Clinical charting models — templates and patient charts."""

import enum
import uuid
from datetime import datetime

from sqlmodel import Column, Field, Text

from app.models.base import TenantScopedModel


class ChartStatus(enum.StrEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SIGNED = "signed"
    AMENDED = "amended"


class ChartTemplate(TenantScopedModel, table=True):
    """A reusable template defining sections for a chart type."""

    __tablename__ = "chart_templates"

    name: str = Field(max_length=200, index=True)
    description: str = Field(default="", sa_column=Column(Text))
    version: int = Field(default=1)
    is_active: bool = Field(default=True)
    sections_json: str = Field(
        default="[]",
        sa_column=Column(Text),
    )


class Chart(TenantScopedModel, table=True):
    """A patient chart record based on a template."""

    __tablename__ = "charts"

    template_id: uuid.UUID = Field(foreign_key="chart_templates.id", index=True)
    client_id: uuid.UUID = Field(foreign_key="clients.id", index=True)
    caregiver_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    shift_id: uuid.UUID | None = Field(default=None, foreign_key="shifts.id", index=True)
    status: ChartStatus = Field(default=ChartStatus.DRAFT, index=True)
    version: int = Field(default=1)
    data_json: str = Field(
        default="{}",
        sa_column=Column(Text),
    )
    signed_at: datetime | None = None
    signed_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    notes: str = Field(default="", sa_column=Column(Text))
