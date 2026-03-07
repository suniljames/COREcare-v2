"""User management service."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """CRUD operations for users, tenant-scoped via RLS."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_users(
        self,
        *,
        page: int = 1,
        size: int = 20,
        role: UserRole | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        """List users with optional filtering. RLS handles tenant scoping."""
        query = select(User)

        if role:
            query = query.where(User.role == role)  # type: ignore[arg-type]
        if search:
            pattern = f"%{search}%"
            query = query.where(
                User.email.like(pattern)  # type: ignore[attr-defined]
                | User.first_name.like(pattern)  # type: ignore[attr-defined]
                | User.last_name.like(pattern)  # type: ignore[attr-defined]
            )

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = (
            query.offset((page - 1) * size)
            .limit(size)
            .order_by(
                User.created_at.desc()  # type: ignore[attr-defined]
            )
        )
        result = await self.session.execute(query)
        users = list(result.scalars().all())

        return users, total

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        """Get a single user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)  # type: ignore[arg-type]
        )
        return result.scalar_one_or_none()

    async def create_user(
        self, data: UserCreate, default_agency_id: uuid.UUID | None = None
    ) -> User:
        """Create a new user."""
        user = User(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            role=data.role,
            agency_id=data.agency_id or default_agency_id,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_user(self, user_id: uuid.UUID, data: UserUpdate) -> User | None:
        """Update an existing user. Returns None if not found."""
        user = await self.get_user(user_id)
        if user is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def deactivate_user(self, user_id: uuid.UUID) -> User | None:
        """Soft-delete a user by setting is_active=False."""
        user = await self.get_user(user_id)
        if user is None:
            return None

        user.is_active = False
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
