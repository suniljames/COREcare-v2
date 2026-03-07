"""Credential management service with expiration tracking."""

import uuid
from datetime import date, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credential import Credential, CredentialStatus, CredentialType
from app.schemas.credential import CredentialCreate, CredentialUpdate, ExpiringCredentialAlert


class CredentialService:
    """CRUD for caregiver credentials with expiration alerts."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_credentials(
        self,
        *,
        page: int = 1,
        size: int = 20,
        caregiver_id: uuid.UUID | None = None,
        credential_type: CredentialType | None = None,
        status: CredentialStatus | None = None,
    ) -> tuple[list[Credential], int]:
        query = select(Credential)

        if caregiver_id:
            query = query.where(
                Credential.caregiver_id == caregiver_id  # type: ignore[arg-type]
            )
        if credential_type:
            query = query.where(
                Credential.credential_type == credential_type  # type: ignore[arg-type]
            )
        if status:
            query = query.where(
                Credential.status == status  # type: ignore[arg-type]
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = (
            query.offset((page - 1) * size)
            .limit(size)
            .order_by(
                Credential.expiration_date.asc()  # type: ignore[union-attr]
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_credential(self, credential_id: uuid.UUID) -> Credential | None:
        result = await self.session.execute(
            select(Credential).where(
                Credential.id == credential_id  # type: ignore[arg-type]
            )
        )
        return result.scalar_one_or_none()

    async def create_credential(self, data: CredentialCreate, agency_id: uuid.UUID) -> Credential:
        credential = Credential(
            caregiver_id=data.caregiver_id,
            credential_type=data.credential_type,
            name=data.name,
            issuing_authority=data.issuing_authority,
            credential_number=data.credential_number,
            issued_date=data.issued_date,
            expiration_date=data.expiration_date,
            document_url=data.document_url,
            notes=data.notes,
            agency_id=agency_id,
        )
        self.session.add(credential)
        await self.session.flush()
        await self.session.refresh(credential)
        return credential

    async def update_credential(
        self, credential_id: uuid.UUID, data: CredentialUpdate
    ) -> Credential | None:
        credential = await self.get_credential(credential_id)
        if credential is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(credential, field, value)

        self.session.add(credential)
        await self.session.flush()
        await self.session.refresh(credential)
        return credential

    async def delete_credential(self, credential_id: uuid.UUID) -> bool:
        credential = await self.get_credential(credential_id)
        if credential is None:
            return False
        await self.session.delete(credential)
        await self.session.flush()
        return True

    async def check_expiring(
        self,
        *,
        reference_date: date | None = None,
    ) -> list[ExpiringCredentialAlert]:
        """Find credentials expiring within 90 days and return alerts."""
        today = reference_date or date.today()
        threshold = today + timedelta(days=90)

        result = await self.session.execute(
            select(Credential).where(
                and_(
                    Credential.expiration_date != None,  # type: ignore[arg-type]  # noqa: E711
                    Credential.expiration_date <= threshold,  # type: ignore[arg-type, operator]
                    Credential.expiration_date >= today,  # type: ignore[arg-type, operator]
                    Credential.status != CredentialStatus.EXPIRED,  # type: ignore[arg-type]
                )
            )
        )
        credentials = result.scalars().all()

        alerts: list[ExpiringCredentialAlert] = []
        for cred in credentials:
            if cred.expiration_date is None:
                continue
            days_left = (cred.expiration_date - today).days
            alerts.append(
                ExpiringCredentialAlert(
                    credential_id=cred.id,
                    caregiver_id=cred.caregiver_id,
                    name=cred.name,
                    credential_type=cred.credential_type,
                    expiration_date=cred.expiration_date,
                    days_until_expiry=days_left,
                )
            )

        return alerts

    async def update_expiration_statuses(
        self,
        *,
        reference_date: date | None = None,
    ) -> int:
        """Scan all credentials and update status based on expiration date.

        Returns the number of credentials updated.
        """
        today = reference_date or date.today()
        updated = 0

        result = await self.session.execute(
            select(Credential).where(
                Credential.expiration_date != None  # type: ignore[arg-type]  # noqa: E711
            )
        )
        credentials = result.scalars().all()

        for cred in credentials:
            if cred.expiration_date is None:
                continue

            days_left = (cred.expiration_date - today).days
            new_status = cred.status

            if days_left < 0:
                new_status = CredentialStatus.EXPIRED
            elif days_left <= 90:
                new_status = CredentialStatus.EXPIRING_SOON
            else:
                new_status = CredentialStatus.ACTIVE

            if new_status != cred.status:
                cred.status = new_status
                self.session.add(cred)
                updated += 1

        if updated:
            await self.session.flush()

        return updated
