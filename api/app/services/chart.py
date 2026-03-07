"""Charting service — templates and patient charts with versioning."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chart import Chart, ChartStatus, ChartTemplate
from app.schemas.chart import ChartCreate, ChartTemplateCreate, ChartTemplateUpdate, ChartUpdate


class ChartService:
    """CRUD for chart templates and patient charts."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Templates ---

    async def list_templates(
        self,
        *,
        page: int = 1,
        size: int = 20,
        active_only: bool = True,
    ) -> tuple[list[ChartTemplate], int]:
        query = select(ChartTemplate)
        if active_only:
            query = query.where(
                ChartTemplate.is_active == True  # type: ignore[arg-type]  # noqa: E712
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.offset((page - 1) * size).limit(size).order_by(ChartTemplate.name.asc())  # type: ignore[attr-defined]
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_template(self, template_id: uuid.UUID) -> ChartTemplate | None:
        result = await self.session.execute(
            select(ChartTemplate).where(
                ChartTemplate.id == template_id  # type: ignore[arg-type]
            )
        )
        return result.scalar_one_or_none()

    async def create_template(
        self, data: ChartTemplateCreate, agency_id: uuid.UUID
    ) -> ChartTemplate:
        template = ChartTemplate(
            name=data.name,
            description=data.description,
            sections_json=json.dumps(data.sections),
            agency_id=agency_id,
        )
        self.session.add(template)
        await self.session.flush()
        await self.session.refresh(template)
        return template

    async def update_template(
        self, template_id: uuid.UUID, data: ChartTemplateUpdate
    ) -> ChartTemplate | None:
        template = await self.get_template(template_id)
        if template is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Bump version on content changes
        content_changed = False
        if "sections" in update_data:
            template.sections_json = json.dumps(update_data.pop("sections"))
            content_changed = True
        if "name" in update_data:
            content_changed = True

        for field, value in update_data.items():
            setattr(template, field, value)

        if content_changed:
            template.version += 1

        self.session.add(template)
        await self.session.flush()
        await self.session.refresh(template)
        return template

    # --- Charts ---

    async def list_charts(
        self,
        *,
        page: int = 1,
        size: int = 20,
        client_id: uuid.UUID | None = None,
        caregiver_id: uuid.UUID | None = None,
        status: ChartStatus | None = None,
    ) -> tuple[list[Chart], int]:
        query = select(Chart)

        if client_id:
            query = query.where(Chart.client_id == client_id)  # type: ignore[arg-type]
        if caregiver_id:
            query = query.where(
                Chart.caregiver_id == caregiver_id  # type: ignore[arg-type]
            )
        if status:
            query = query.where(Chart.status == status)  # type: ignore[arg-type]

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.offset((page - 1) * size).limit(size).order_by(Chart.created_at.desc())  # type: ignore[attr-defined]
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_chart(self, chart_id: uuid.UUID) -> Chart | None:
        result = await self.session.execute(
            select(Chart).where(Chart.id == chart_id)  # type: ignore[arg-type]
        )
        return result.scalar_one_or_none()

    async def create_chart(
        self, data: ChartCreate, caregiver_id: uuid.UUID, agency_id: uuid.UUID
    ) -> Chart:
        chart = Chart(
            template_id=data.template_id,
            client_id=data.client_id,
            caregiver_id=caregiver_id,
            shift_id=data.shift_id,
            data_json=json.dumps(data.data),
            notes=data.notes,
            agency_id=agency_id,
        )
        self.session.add(chart)
        await self.session.flush()
        await self.session.refresh(chart)
        return chart

    async def update_chart(self, chart_id: uuid.UUID, data: ChartUpdate) -> Chart | None:
        chart = await self.get_chart(chart_id)
        if chart is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        if "data" in update_data:
            chart.data_json = json.dumps(update_data.pop("data"))
            chart.version += 1

        for field, value in update_data.items():
            setattr(chart, field, value)

        self.session.add(chart)
        await self.session.flush()
        await self.session.refresh(chart)
        return chart

    async def sign_chart(self, chart_id: uuid.UUID, signer_id: uuid.UUID) -> Chart | None:
        chart = await self.get_chart(chart_id)
        if chart is None:
            return None

        chart.status = ChartStatus.SIGNED
        chart.signed_at = datetime.now(UTC)
        chart.signed_by_id = signer_id
        self.session.add(chart)
        await self.session.flush()
        await self.session.refresh(chart)
        return chart

    @staticmethod
    def template_to_response_data(template: ChartTemplate) -> dict[str, Any]:
        """Convert template model to response-friendly dict with parsed sections."""
        data = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "version": template.version,
            "is_active": template.is_active,
            "sections": json.loads(template.sections_json),
            "agency_id": template.agency_id,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
        }
        return data

    @staticmethod
    def chart_to_response_data(chart: Chart) -> dict[str, Any]:
        """Convert chart model to response-friendly dict with parsed data."""
        data = {
            "id": chart.id,
            "template_id": chart.template_id,
            "client_id": chart.client_id,
            "caregiver_id": chart.caregiver_id,
            "shift_id": chart.shift_id,
            "status": chart.status,
            "version": chart.version,
            "data": json.loads(chart.data_json),
            "signed_at": chart.signed_at,
            "signed_by_id": chart.signed_by_id,
            "notes": chart.notes,
            "agency_id": chart.agency_id,
            "created_at": chart.created_at,
            "updated_at": chart.updated_at,
        }
        return data
