"""Care plan service — version selection + Client/staff field separation (issue #125)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.care_plan import CarePlanVersion


class CarePlanService:
    """Read access to care plan versions.

    The Client-facing endpoint always returns the *active* version; staff
    endpoints can list history. Authoring + version creation lives in the
    staff service surface (out of scope for #125's Client-as-user PR).
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_for_client(
        self, client_id: uuid.UUID
    ) -> CarePlanVersion | None:
        """Return the unique is_active=True version for a Client, if any."""
        result = await self.session.execute(
            select(CarePlanVersion).where(
                CarePlanVersion.client_id == client_id,  # type: ignore[arg-type]
                CarePlanVersion.is_active == True,  # type: ignore[arg-type]  # noqa: E712
            )
        )
        return result.scalar_one_or_none()
