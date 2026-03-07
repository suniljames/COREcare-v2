"""Dashboard service — aggregation queries for KPIs and portal summaries."""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Invoice, InvoiceStatus
from app.models.client import Client, ClientStatus
from app.models.credential import Credential, CredentialStatus
from app.models.notification import Message, Notification
from app.models.payroll import PayrollPeriod, PayrollPeriodStatus
from app.models.shift import Shift, ShiftStatus
from app.models.user import User, UserRole
from app.models.visit import ShiftOffer, ShiftOfferStatus, Visit
from app.schemas.dashboard import (
    AgencyKPIs,
    CaregiverPortalSummary,
    FamilyPortalSummary,
    PlatformKPIs,
)


class DashboardService:
    """Aggregation queries for dashboards and portals."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_agency_kpis(self, agency_id: uuid.UUID) -> AgencyKPIs:
        """Get KPIs for an agency admin dashboard."""
        today = date.today()
        today_start = datetime(today.year, today.month, today.day, tzinfo=UTC)
        today_end = today_start + timedelta(days=1)
        week_start = today_start - timedelta(days=today.weekday())

        # Total clients
        total_clients_r = await self.session.execute(
            select(func.count()).select_from(Client).where(Client.agency_id == agency_id)  # type: ignore[arg-type]
        )
        total_clients = total_clients_r.scalar() or 0

        # Active clients
        active_clients_r = await self.session.execute(
            select(func.count())
            .select_from(Client)
            .where(
                and_(
                    Client.agency_id == agency_id,  # type: ignore[arg-type]
                    Client.status == ClientStatus.ACTIVE,  # type: ignore[arg-type]
                )
            )
        )
        active_clients = active_clients_r.scalar() or 0

        # Total caregivers
        total_cg_r = await self.session.execute(
            select(func.count())
            .select_from(User)
            .where(
                and_(
                    User.agency_id == agency_id,  # type: ignore[arg-type]
                    User.role == UserRole.CAREGIVER,  # type: ignore[arg-type]
                )
            )
        )
        total_caregivers = total_cg_r.scalar() or 0

        # Active shifts today
        active_today_r = await self.session.execute(
            select(func.count())
            .select_from(Shift)
            .where(
                and_(
                    Shift.agency_id == agency_id,  # type: ignore[arg-type]
                    Shift.start_time < today_end,  # type: ignore[arg-type]
                    Shift.end_time > today_start,  # type: ignore[arg-type]
                    Shift.status != ShiftStatus.CANCELLED,  # type: ignore[arg-type]
                )
            )
        )
        active_shifts_today = active_today_r.scalar() or 0

        # Open shifts
        open_shifts_r = await self.session.execute(
            select(func.count())
            .select_from(Shift)
            .where(
                and_(
                    Shift.agency_id == agency_id,  # type: ignore[arg-type]
                    Shift.status == ShiftStatus.OPEN,  # type: ignore[arg-type]
                )
            )
        )
        open_shifts = open_shifts_r.scalar() or 0

        # Completed visits this week
        visits_week_r = await self.session.execute(
            select(func.count())
            .select_from(Visit)
            .where(
                and_(
                    Visit.agency_id == agency_id,  # type: ignore[arg-type]
                    Visit.clock_out != None,  # type: ignore[arg-type]  # noqa: E711
                    Visit.created_at >= week_start,  # type: ignore[arg-type]
                )
            )
        )
        completed_visits = visits_week_r.scalar() or 0

        # Pending payroll
        pending_payroll_r = await self.session.execute(
            select(func.coalesce(func.sum(PayrollPeriod.total_amount), 0))
            .select_from(PayrollPeriod)
            .where(
                and_(
                    PayrollPeriod.agency_id == agency_id,  # type: ignore[arg-type]
                    PayrollPeriod.status == PayrollPeriodStatus.PENDING_APPROVAL,  # type: ignore[arg-type]
                )
            )
        )
        pending_payroll = pending_payroll_r.scalar() or Decimal("0")

        # Outstanding invoices
        outstanding_r = await self.session.execute(
            select(func.count(), func.coalesce(func.sum(Invoice.total), 0))
            .select_from(Invoice)
            .where(
                and_(
                    Invoice.agency_id == agency_id,  # type: ignore[arg-type]
                    Invoice.status.in_(  # type: ignore[attr-defined]
                        [InvoiceStatus.SENT, InvoiceStatus.OVERDUE]
                    ),
                )
            )
        )
        outstanding_row = outstanding_r.one()
        outstanding_count = outstanding_row[0] or 0
        outstanding_amount = outstanding_row[1] or Decimal("0")

        # Expiring credentials
        expiring_r = await self.session.execute(
            select(func.count())
            .select_from(Credential)
            .where(
                and_(
                    Credential.agency_id == agency_id,  # type: ignore[arg-type]
                    Credential.status == CredentialStatus.EXPIRING_SOON,  # type: ignore[arg-type]
                )
            )
        )
        expiring_creds = expiring_r.scalar() or 0

        return AgencyKPIs(
            total_clients=total_clients,
            active_clients=active_clients,
            total_caregivers=total_caregivers,
            active_shifts_today=active_shifts_today,
            open_shifts=open_shifts,
            completed_visits_this_week=completed_visits,
            pending_payroll_amount=Decimal(str(pending_payroll)),
            outstanding_invoices=outstanding_count,
            outstanding_invoice_amount=Decimal(str(outstanding_amount)),
            expiring_credentials_count=expiring_creds,
        )

    async def get_platform_kpis(self) -> PlatformKPIs:
        """Get platform-wide KPIs for super-admin."""
        from app.models.agency import Agency

        today = date.today()
        month_start = datetime(today.year, today.month, 1, tzinfo=UTC)

        agencies_r = await self.session.execute(select(func.count()).select_from(Agency))
        users_r = await self.session.execute(select(func.count()).select_from(User))
        clients_r = await self.session.execute(select(func.count()).select_from(Client))
        shifts_month_r = await self.session.execute(
            select(func.count())
            .select_from(Shift)
            .where(
                Shift.start_time >= month_start  # type: ignore[arg-type]
            )
        )
        revenue_r = await self.session.execute(
            select(func.coalesce(func.sum(Invoice.total), 0))
            .select_from(Invoice)
            .where(
                and_(
                    Invoice.status == InvoiceStatus.PAID,  # type: ignore[arg-type]
                    Invoice.created_at >= month_start,  # type: ignore[arg-type]
                )
            )
        )

        return PlatformKPIs(
            total_agencies=agencies_r.scalar() or 0,
            total_users=users_r.scalar() or 0,
            total_clients=clients_r.scalar() or 0,
            total_shifts_this_month=shifts_month_r.scalar() or 0,
            total_revenue_this_month=Decimal(str(revenue_r.scalar() or 0)),
        )

    async def get_caregiver_summary(self, user_id: uuid.UUID) -> CaregiverPortalSummary:
        """Get summary for caregiver portal."""
        now = datetime.now(UTC)

        # Upcoming shifts
        upcoming_r = await self.session.execute(
            select(func.count())
            .select_from(Shift)
            .where(
                and_(
                    Shift.caregiver_id == user_id,  # type: ignore[arg-type]
                    Shift.start_time > now,  # type: ignore[arg-type]
                    Shift.status != ShiftStatus.CANCELLED,  # type: ignore[arg-type]
                )
            )
        )

        # Completed visits this week
        week_start = now - timedelta(days=now.weekday())
        visits_r = await self.session.execute(
            select(func.count())
            .select_from(Visit)
            .where(
                and_(
                    Visit.caregiver_id == user_id,  # type: ignore[arg-type]
                    Visit.clock_out != None,  # type: ignore[arg-type]  # noqa: E711
                    Visit.created_at >= week_start,  # type: ignore[arg-type]
                )
            )
        )

        # Pending offers
        offers_r = await self.session.execute(
            select(func.count())
            .select_from(ShiftOffer)
            .where(
                and_(
                    ShiftOffer.caregiver_id == user_id,  # type: ignore[arg-type]
                    ShiftOffer.status == ShiftOfferStatus.PENDING,  # type: ignore[arg-type]
                )
            )
        )

        # Expiring credentials
        expiring_r = await self.session.execute(
            select(func.count())
            .select_from(Credential)
            .where(
                and_(
                    Credential.caregiver_id == user_id,  # type: ignore[arg-type]
                    Credential.status == CredentialStatus.EXPIRING_SOON,  # type: ignore[arg-type]
                )
            )
        )

        # Unread notifications
        notif_r = await self.session.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,  # type: ignore[arg-type]
                    Notification.is_read == False,  # type: ignore[arg-type]  # noqa: E712
                )
            )
        )

        # Unread messages
        msg_r = await self.session.execute(
            select(func.count())
            .select_from(Message)
            .where(
                and_(
                    Message.recipient_id == user_id,  # type: ignore[arg-type]
                    Message.is_read == False,  # type: ignore[arg-type]  # noqa: E712
                )
            )
        )

        return CaregiverPortalSummary(
            upcoming_shifts=upcoming_r.scalar() or 0,
            completed_visits_this_week=visits_r.scalar() or 0,
            pending_offers=offers_r.scalar() or 0,
            expiring_credentials=expiring_r.scalar() or 0,
            unread_notifications=notif_r.scalar() or 0,
            unread_messages=msg_r.scalar() or 0,
        )

    async def get_family_summary(self, user_id: uuid.UUID) -> FamilyPortalSummary:
        """Get summary for family portal."""
        from app.models.client import FamilyLink

        now = datetime.now(UTC)
        week_ago = now - timedelta(days=7)

        # Linked clients
        linked_r = await self.session.execute(
            select(func.count())
            .select_from(FamilyLink)
            .where(
                FamilyLink.user_id == user_id  # type: ignore[arg-type]
            )
        )

        # Upcoming shifts for linked clients
        linked_client_ids = await self.session.execute(
            select(FamilyLink.client_id).where(  # type: ignore[call-overload]
                FamilyLink.user_id == user_id
            )
        )
        client_ids = [row[0] for row in linked_client_ids.all()]

        upcoming_shifts = 0
        recent_visits = 0
        if client_ids:
            upcoming_r = await self.session.execute(
                select(func.count())
                .select_from(Shift)
                .where(
                    and_(
                        Shift.client_id.in_(client_ids),  # type: ignore[attr-defined]
                        Shift.start_time > now,  # type: ignore[arg-type]
                        Shift.status != ShiftStatus.CANCELLED,  # type: ignore[arg-type]
                    )
                )
            )
            upcoming_shifts = upcoming_r.scalar() or 0

            visits_r = await self.session.execute(
                select(func.count())
                .select_from(Visit)
                .where(
                    and_(
                        Visit.shift_id.in_(  # type: ignore[attr-defined]
                            select(Shift.id).where(  # type: ignore[call-overload]
                                Shift.client_id.in_(client_ids)  # type: ignore[attr-defined]
                            )
                        ),
                        Visit.created_at >= week_ago,  # type: ignore[arg-type]
                    )
                )
            )
            recent_visits = visits_r.scalar() or 0

        # Unread messages
        msg_r = await self.session.execute(
            select(func.count())
            .select_from(Message)
            .where(
                and_(
                    Message.recipient_id == user_id,  # type: ignore[arg-type]
                    Message.is_read == False,  # type: ignore[arg-type]  # noqa: E712
                )
            )
        )

        # Unread notifications
        notif_r = await self.session.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,  # type: ignore[arg-type]
                    Notification.is_read == False,  # type: ignore[arg-type]  # noqa: E712
                )
            )
        )

        return FamilyPortalSummary(
            linked_clients=linked_r.scalar() or 0,
            upcoming_shifts=upcoming_shifts,
            recent_visits=recent_visits,
            unread_messages=msg_r.scalar() or 0,
            unread_notifications=notif_r.scalar() or 0,
        )
