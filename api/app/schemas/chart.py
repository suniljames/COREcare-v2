"""Chart template and chart request/response schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.chart import ChartStatus


class ChartTemplateCreate(BaseModel):
    name: str
    description: str = ""
    sections: list[dict[str, Any]] = []


class ChartTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sections: list[dict[str, Any]] | None = None
    is_active: bool | None = None


class ChartTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    version: int
    is_active: bool
    sections: list[dict[str, Any]]
    agency_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChartTemplateListResponse(BaseModel):
    items: list[ChartTemplateResponse]
    total: int
    page: int
    size: int


class ChartCreate(BaseModel):
    template_id: uuid.UUID
    client_id: uuid.UUID
    shift_id: uuid.UUID | None = None
    data: dict[str, Any] = {}
    notes: str = ""


class ChartUpdate(BaseModel):
    data: dict[str, Any] | None = None
    notes: str | None = None
    status: ChartStatus | None = None


class ChartResponse(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    client_id: uuid.UUID
    caregiver_id: uuid.UUID
    shift_id: uuid.UUID | None
    status: ChartStatus
    version: int
    data: dict[str, Any]
    signed_at: datetime | None
    signed_by_id: uuid.UUID | None
    notes: str
    agency_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChartListResponse(BaseModel):
    items: list[ChartResponse]
    total: int
    page: int
    size: int
