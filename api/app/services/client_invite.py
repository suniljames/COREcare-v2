"""Client-persona invite service: issuance + redemption (issue #125).

Per Security review §2: invite-only, single-use, 72h TTL, email-match
required at redemption. Audit log entries written on every outcome
(issued, redeemed, failed_email_mismatch).
"""

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditEvent
from app.models.client import Client
from app.models.client_invite import ClientInvite
from app.models.user import User, UserRole

DEFAULT_TTL_HOURS = 72
TOKEN_BYTES = 32  # 256-bit token

# Generic detail string for all pre-redemption failures — never leak whether
# the token was found, expired, or had a mismatched email. Specific failure
# reasons are captured in the audit log only (Writer §1).
INVITE_INVALID_DETAIL = "Invite is invalid or expired."


def _normalize_email(email: str) -> str:
    """Unicode-safe email comparison (Security §2): strip + casefold."""
    return email.strip().casefold()


def _ensure_aware(dt: datetime) -> datetime:
    """SQLite returns naive datetimes; treat them as UTC for comparison."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class ClientInviteService:
    """Issue and redeem invites for the Client persona."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def issue_invite(
        self,
        *,
        client_id: uuid.UUID,
        email: str,
        actor_user_id: uuid.UUID,
        agency_id: uuid.UUID,
        ttl_hours: int = DEFAULT_TTL_HOURS,
    ) -> ClientInvite:
        """Issue a single-use invite for a Client + email."""
        invite = ClientInvite(
            client_id=client_id,
            agency_id=agency_id,
            email=email,
            token=secrets.token_urlsafe(TOKEN_BYTES),
            expires_at=datetime.now(UTC) + timedelta(hours=ttl_hours),
            issued_by_user_id=actor_user_id,
        )
        self.session.add(invite)
        await self.session.flush()
        await self.session.refresh(invite)

        self.session.add(
            AuditEvent(
                user_id=actor_user_id,
                agency_id=agency_id,
                action=AuditAction.CREATE,
                resource_type="client_invite",
                resource_id=str(invite.id),
                is_phi_access=False,
                details="client_invite_issued",
            )
        )
        await self.session.flush()
        return invite

    async def redeem_invite(
        self,
        *,
        token: str,
        clerk_user_id: str,
        clerk_email: str,
    ) -> tuple[User, Client]:
        """Redeem an invite. Returns (user, client) on success.

        Pre-redemption failures all return the same generic detail
        ("Invite is invalid or expired.") so the response does not leak
        whether the token was unknown, already-used, expired, or email-
        mismatched. Specific reasons are written to the audit log.

        Raises:
            403: token unknown OR clerk_email does not match invite.email
              OR existing User holds a staff role (collision)
              OR Client is already linked to a different User
            410 Gone: invite expired OR already redeemed
        """
        result = await self.session.execute(
            select(ClientInvite).where(ClientInvite.token == token)  # type: ignore[arg-type]
        )
        invite = result.scalar_one_or_none()
        if invite is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=INVITE_INVALID_DETAIL,
            )

        # Expiry / single-use checks first.
        if invite.redeemed_at is not None:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=INVITE_INVALID_DETAIL,
            )
        if _ensure_aware(invite.expires_at) <= datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=INVITE_INVALID_DETAIL,
            )

        # Unicode-safe email-match check. Failure is the canonical signal for
        # an impersonation attempt — audit it.
        if _normalize_email(invite.email) != _normalize_email(clerk_email):
            self.session.add(
                AuditEvent(
                    user_id=None,
                    agency_id=invite.agency_id,
                    action=AuditAction.LOGIN,
                    resource_type="client_invite",
                    resource_id=str(invite.id),
                    is_phi_access=False,
                    details="client_invite_failed_email_mismatch",
                )
            )
            await self.session.flush()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=INVITE_INVALID_DETAIL,
            )

        # Resolve the User row by clerk_id, if one exists.
        user_result = await self.session.execute(
            select(User).where(User.clerk_id == clerk_user_id)  # type: ignore[arg-type]
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            user = User(
                email=clerk_email,
                role=UserRole.CLIENT,
                clerk_id=clerk_user_id,
                agency_id=invite.agency_id,
            )
            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)
        else:
            # If the existing User holds any non-Client role, refuse —
            # redeeming an invite must not silently demote a staff or family
            # account to Client and reassign their agency (SWE §5).
            if user.role != UserRole.CLIENT:
                self.session.add(
                    AuditEvent(
                        user_id=user.id,
                        agency_id=invite.agency_id,
                        action=AuditAction.LOGIN,
                        resource_type="client_invite",
                        resource_id=str(invite.id),
                        is_phi_access=False,
                        details="client_invite_failed_role_collision",
                    )
                )
                await self.session.flush()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=INVITE_INVALID_DETAIL,
                )
            user.role = UserRole.CLIENT
            user.email = clerk_email
            user.agency_id = invite.agency_id
            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)

        # Link the Client row to the User. If a different User is already
        # linked (e.g., reissued invite redeemed by attacker), refuse.
        client_result = await self.session.execute(
            select(Client).where(Client.id == invite.client_id)  # type: ignore[arg-type]
        )
        client = client_result.scalar_one()
        if client.client_user_id is not None and client.client_user_id != user.id:
            self.session.add(
                AuditEvent(
                    user_id=user.id,
                    agency_id=invite.agency_id,
                    action=AuditAction.LOGIN,
                    resource_type="client_invite",
                    resource_id=str(invite.id),
                    is_phi_access=False,
                    details="client_invite_failed_already_linked",
                )
            )
            await self.session.flush()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=INVITE_INVALID_DETAIL,
            )
        client.client_user_id = user.id
        self.session.add(client)

        invite.redeemed_at = datetime.now(UTC)
        self.session.add(invite)

        self.session.add(
            AuditEvent(
                user_id=user.id,
                agency_id=invite.agency_id,
                action=AuditAction.LOGIN,
                resource_type="client_invite",
                resource_id=str(invite.id),
                is_phi_access=False,
                details="client_invite_redeemed",
            )
        )
        await self.session.flush()
        await self.session.refresh(client)
        return user, client
