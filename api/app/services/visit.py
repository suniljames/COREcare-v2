"""Visit tracking and shift offer service."""

import math
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift import Shift, ShiftStatus
from app.models.visit import ShiftOffer, ShiftOfferStatus, Visit
from app.schemas.visit import ClockInRequest, ClockOutRequest, ShiftOfferCreate

# Default geofence radius in meters
GEOFENCE_RADIUS_METERS = 200


def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two GPS points in meters."""
    r = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class VisitService:
    """Shift offers and visit clock-in/out with geofencing."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Shift Offers ---

    async def create_offer(self, data: ShiftOfferCreate, agency_id: uuid.UUID) -> ShiftOffer:
        """Create a shift offer for a caregiver."""
        offer = ShiftOffer(
            shift_id=data.shift_id,
            caregiver_id=data.caregiver_id,
            agency_id=agency_id,
        )
        self.session.add(offer)
        await self.session.flush()
        await self.session.refresh(offer)
        return offer

    async def accept_offer(self, offer_id: uuid.UUID) -> ShiftOffer:
        """Accept a shift offer — assigns caregiver to the shift."""
        result = await self.session.execute(
            select(ShiftOffer).where(
                ShiftOffer.id == offer_id  # type: ignore[arg-type]
            )
        )
        offer = result.scalar_one_or_none()
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")

        offer.status = ShiftOfferStatus.ACCEPTED
        offer.responded_at = datetime.now(UTC)

        # Assign caregiver to shift
        shift_result = await self.session.execute(
            select(Shift).where(Shift.id == offer.shift_id)  # type: ignore[arg-type]
        )
        shift = shift_result.scalar_one_or_none()
        if shift:
            shift.caregiver_id = offer.caregiver_id
            shift.status = ShiftStatus.ASSIGNED
            self.session.add(shift)

        self.session.add(offer)
        await self.session.flush()
        return offer

    async def decline_offer(self, offer_id: uuid.UUID) -> ShiftOffer:
        """Decline a shift offer."""
        result = await self.session.execute(
            select(ShiftOffer).where(
                ShiftOffer.id == offer_id  # type: ignore[arg-type]
            )
        )
        offer = result.scalar_one_or_none()
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")

        offer.status = ShiftOfferStatus.DECLINED
        offer.responded_at = datetime.now(UTC)
        self.session.add(offer)
        await self.session.flush()
        return offer

    # --- Visit Clock-in/out ---

    async def clock_in(
        self,
        data: ClockInRequest,
        caregiver_id: uuid.UUID,
        agency_id: uuid.UUID,
    ) -> Visit:
        """Clock in for a shift visit."""
        visit = Visit(
            shift_id=data.shift_id,
            caregiver_id=caregiver_id,
            clock_in=datetime.now(UTC),
            clock_in_lat=data.latitude,
            clock_in_lng=data.longitude,
            agency_id=agency_id,
        )

        # Update shift status
        shift_result = await self.session.execute(
            select(Shift).where(Shift.id == data.shift_id)  # type: ignore[arg-type]
        )
        shift = shift_result.scalar_one_or_none()
        if shift:
            shift.status = ShiftStatus.IN_PROGRESS
            self.session.add(shift)

        self.session.add(visit)
        await self.session.flush()
        await self.session.refresh(visit)
        return visit

    async def clock_out(self, visit_id: uuid.UUID, data: ClockOutRequest) -> Visit:
        """Clock out from a visit."""
        result = await self.session.execute(
            select(Visit).where(Visit.id == visit_id)  # type: ignore[arg-type]
        )
        visit = result.scalar_one_or_none()
        if visit is None:
            raise HTTPException(status_code=404, detail="Visit not found")

        visit.clock_out = datetime.now(UTC)
        visit.clock_out_lat = data.latitude
        visit.clock_out_lng = data.longitude
        visit.notes = data.notes

        # Calculate duration (normalize tz for SQLite compat)
        if visit.clock_in and visit.clock_out:
            ci = visit.clock_in.replace(tzinfo=None)
            co = visit.clock_out.replace(tzinfo=None)
            delta = co - ci
            visit.duration_minutes = int(delta.total_seconds() / 60)

        # Update shift status
        shift_result = await self.session.execute(
            select(Shift).where(
                Shift.id == visit.shift_id  # type: ignore[arg-type]
            )
        )
        shift = shift_result.scalar_one_or_none()
        if shift:
            shift.status = ShiftStatus.COMPLETED
            self.session.add(shift)

        self.session.add(visit)
        await self.session.flush()
        await self.session.refresh(visit)
        return visit

    @staticmethod
    def validate_geofence(
        visit_lat: Decimal | None,
        visit_lng: Decimal | None,
        target_lat: float,
        target_lng: float,
        radius_meters: float = GEOFENCE_RADIUS_METERS,
    ) -> bool:
        """Check if GPS coordinates are within geofence radius."""
        if visit_lat is None or visit_lng is None:
            return False
        distance = _haversine_distance(float(visit_lat), float(visit_lng), target_lat, target_lng)
        return distance <= radius_meters
