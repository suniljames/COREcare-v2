"""Caregiver profile service."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.caregiver import CaregiverProfile
from app.schemas.caregiver import CaregiverProfileCreate, CaregiverProfileUpdate


class CaregiverService:
    """CRUD operations for caregiver profiles."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_profiles(
        self,
        *,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[CaregiverProfile], int]:
        """List caregiver profiles with pagination."""
        query = select(CaregiverProfile)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * size).limit(size)
        result = await self.session.execute(query)
        profiles = list(result.scalars().all())

        return profiles, total

    async def get_profile(self, profile_id: uuid.UUID) -> CaregiverProfile | None:
        """Get a profile by ID."""
        result = await self.session.execute(
            select(CaregiverProfile).where(
                CaregiverProfile.id == profile_id  # type: ignore[arg-type]
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> CaregiverProfile | None:
        """Get a profile by user_id."""
        result = await self.session.execute(
            select(CaregiverProfile).where(
                CaregiverProfile.user_id == user_id  # type: ignore[arg-type]
            )
        )
        return result.scalar_one_or_none()

    async def create_profile(
        self, data: CaregiverProfileCreate, agency_id: uuid.UUID
    ) -> CaregiverProfile:
        """Create a new caregiver profile."""
        profile = CaregiverProfile(
            user_id=data.user_id,
            bio=data.bio,
            years_experience=data.years_experience,
            hourly_rate=data.hourly_rate,
            overtime_rate=data.overtime_rate,
            holiday_rate=data.holiday_rate,
            skills=data.skills,
            certifications=data.certifications,
            availability=data.availability,
            agency_id=agency_id,
        )
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def update_profile(
        self, profile_id: uuid.UUID, data: CaregiverProfileUpdate
    ) -> CaregiverProfile | None:
        """Update a caregiver profile."""
        profile = await self.get_profile(profile_id)
        if profile is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile
