"""Payroll service — period management, entry calculations, approval."""

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import PayrollEntry, PayrollPeriod, PayrollPeriodStatus
from app.schemas.payroll import PayrollEntryCreate, PayrollPeriodCreate, PayrollPeriodUpdate


class PayrollService:
    """CRUD for payroll periods and entries with approval workflow."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Periods ---

    async def list_periods(
        self,
        *,
        page: int = 1,
        size: int = 20,
        status: PayrollPeriodStatus | None = None,
    ) -> tuple[list[PayrollPeriod], int]:
        query = select(PayrollPeriod)
        if status:
            query = query.where(
                PayrollPeriod.status == status  # type: ignore[arg-type]
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.offset((page - 1) * size)
            .limit(size)
            .order_by(
                PayrollPeriod.start_date.desc()  # type: ignore[attr-defined]
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_period(self, period_id: uuid.UUID) -> PayrollPeriod | None:
        result = await self.session.execute(
            select(PayrollPeriod).where(
                PayrollPeriod.id == period_id  # type: ignore[arg-type]
            )
        )
        return result.scalar_one_or_none()

    async def create_period(self, data: PayrollPeriodCreate, agency_id: uuid.UUID) -> PayrollPeriod:
        period = PayrollPeriod(
            start_date=data.start_date,
            end_date=data.end_date,
            notes=data.notes,
            agency_id=agency_id,
        )
        self.session.add(period)
        await self.session.flush()
        await self.session.refresh(period)
        return period

    async def update_period(
        self, period_id: uuid.UUID, data: PayrollPeriodUpdate
    ) -> PayrollPeriod | None:
        period = await self.get_period(period_id)
        if period is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(period, field, value)

        self.session.add(period)
        await self.session.flush()
        await self.session.refresh(period)
        return period

    async def submit_for_approval(self, period_id: uuid.UUID) -> PayrollPeriod | None:
        period = await self.get_period(period_id)
        if period is None:
            return None

        period.status = PayrollPeriodStatus.PENDING_APPROVAL
        self.session.add(period)
        await self.session.flush()
        await self.session.refresh(period)
        return period

    async def approve_period(
        self, period_id: uuid.UUID, approver_id: uuid.UUID
    ) -> PayrollPeriod | None:
        period = await self.get_period(period_id)
        if period is None:
            return None

        period.status = PayrollPeriodStatus.APPROVED
        period.approved_by_id = approver_id
        self.session.add(period)
        await self.session.flush()
        await self.session.refresh(period)
        return period

    async def reject_period(self, period_id: uuid.UUID) -> PayrollPeriod | None:
        period = await self.get_period(period_id)
        if period is None:
            return None

        period.status = PayrollPeriodStatus.REJECTED
        self.session.add(period)
        await self.session.flush()
        await self.session.refresh(period)
        return period

    # --- Entries ---

    async def list_entries(self, period_id: uuid.UUID) -> list[PayrollEntry]:
        result = await self.session.execute(
            select(PayrollEntry).where(
                PayrollEntry.period_id == period_id  # type: ignore[arg-type]
            )
        )
        return list(result.scalars().all())

    async def add_entry(
        self,
        period_id: uuid.UUID,
        data: PayrollEntryCreate,
        agency_id: uuid.UUID,
    ) -> PayrollEntry:
        total = (data.regular_hours * data.hourly_rate) + (data.overtime_hours * data.overtime_rate)

        entry = PayrollEntry(
            period_id=period_id,
            caregiver_id=data.caregiver_id,
            regular_hours=data.regular_hours,
            overtime_hours=data.overtime_hours,
            hourly_rate=data.hourly_rate,
            overtime_rate=data.overtime_rate,
            total_amount=total,
            notes=data.notes,
            agency_id=agency_id,
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)

        # Update period totals
        await self._recalculate_period_totals(period_id)
        return entry

    async def _recalculate_period_totals(self, period_id: uuid.UUID) -> None:
        """Recalculate total hours and amount for a payroll period."""
        entries = await self.list_entries(period_id)

        total_hours = Decimal("0")
        total_amount = Decimal("0")
        for e in entries:
            total_hours += e.regular_hours + e.overtime_hours
            total_amount += e.total_amount

        period = await self.get_period(period_id)
        if period:
            period.total_hours = total_hours
            period.total_amount = total_amount
            self.session.add(period)
            await self.session.flush()
