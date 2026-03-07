"""Shift scheduling service with conflict detection."""

import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift import Shift, ShiftStatus
from app.schemas.shift import ShiftCreate, ShiftUpdate


class ShiftService:
    """CRUD operations for shifts with conflict detection."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _check_conflict(
        self,
        caregiver_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        """Check if a caregiver has overlapping shifts."""
        query = (
            select(func.count())
            .select_from(Shift)
            .where(
                and_(
                    Shift.caregiver_id == caregiver_id,  # type: ignore[arg-type]
                    Shift.start_time < end_time,  # type: ignore[arg-type]
                    Shift.end_time > start_time,  # type: ignore[arg-type]
                    Shift.status != ShiftStatus.CANCELLED,  # type: ignore[arg-type]
                )
            )
        )
        if exclude_id:
            query = query.where(Shift.id != exclude_id)  # type: ignore[arg-type]
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return count > 0

    async def list_shifts(
        self,
        *,
        page: int = 1,
        size: int = 20,
        start_after: datetime | None = None,
        start_before: datetime | None = None,
        caregiver_id: uuid.UUID | None = None,
        client_id: uuid.UUID | None = None,
        status: ShiftStatus | None = None,
    ) -> tuple[list[Shift], int]:
        """List shifts with date range and filters."""
        query = select(Shift)

        if start_after:
            query = query.where(Shift.start_time >= start_after)  # type: ignore[arg-type]
        if start_before:
            query = query.where(Shift.start_time <= start_before)  # type: ignore[arg-type]
        if caregiver_id:
            query = query.where(
                Shift.caregiver_id == caregiver_id  # type: ignore[arg-type]
            )
        if client_id:
            query = query.where(Shift.client_id == client_id)  # type: ignore[arg-type]
        if status:
            query = query.where(Shift.status == status)  # type: ignore[arg-type]

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.offset((page - 1) * size)
            .limit(size)
            .order_by(
                Shift.start_time.asc()  # type: ignore[attr-defined]
            )
        )
        result = await self.session.execute(query)
        shifts = list(result.scalars().all())

        return shifts, total

    async def get_shift(self, shift_id: uuid.UUID) -> Shift | None:
        """Get a shift by ID."""
        result = await self.session.execute(
            select(Shift).where(Shift.id == shift_id)  # type: ignore[arg-type]
        )
        return result.scalar_one_or_none()

    async def create_shift(self, data: ShiftCreate, agency_id: uuid.UUID) -> Shift:
        """Create a new shift with conflict detection."""
        if data.caregiver_id:
            has_conflict = await self._check_conflict(
                data.caregiver_id, data.start_time, data.end_time
            )
            if has_conflict:
                raise HTTPException(
                    status_code=409,
                    detail="Caregiver has a conflicting shift",
                )

        shift = Shift(
            client_id=data.client_id,
            caregiver_id=data.caregiver_id,
            start_time=data.start_time,
            end_time=data.end_time,
            status=ShiftStatus.ASSIGNED if data.caregiver_id else ShiftStatus.OPEN,
            recurrence_rule=data.recurrence_rule,
            notes=data.notes,
            agency_id=agency_id,
        )
        self.session.add(shift)
        await self.session.flush()
        await self.session.refresh(shift)
        return shift

    async def update_shift(self, shift_id: uuid.UUID, data: ShiftUpdate) -> Shift | None:
        """Update a shift."""
        shift = await self.get_shift(shift_id)
        if shift is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Check conflict if caregiver or times are changing
        new_cg = update_data.get("caregiver_id", shift.caregiver_id)
        new_start = update_data.get("start_time", shift.start_time)
        new_end = update_data.get("end_time", shift.end_time)
        time_or_cg_changed = (
            "caregiver_id" in update_data
            or "start_time" in update_data
            or "end_time" in update_data
        )
        if new_cg and time_or_cg_changed:
            has_conflict = await self._check_conflict(
                new_cg, new_start, new_end, exclude_id=shift_id
            )
            if has_conflict:
                raise HTTPException(
                    status_code=409,
                    detail="Caregiver has a conflicting shift",
                )

        for field, value in update_data.items():
            setattr(shift, field, value)

        self.session.add(shift)
        await self.session.flush()
        await self.session.refresh(shift)
        return shift

    async def cancel_shift(self, shift_id: uuid.UUID) -> Shift | None:
        """Cancel a shift."""
        shift = await self.get_shift(shift_id)
        if shift is None:
            return None

        shift.status = ShiftStatus.CANCELLED
        self.session.add(shift)
        await self.session.flush()
        await self.session.refresh(shift)
        return shift
