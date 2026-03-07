"""Dashboard KPI and portal schemas."""

from decimal import Decimal

from pydantic import BaseModel


class AgencyKPIs(BaseModel):
    """Key performance indicators for an agency dashboard."""

    total_clients: int = 0
    active_clients: int = 0
    total_caregivers: int = 0
    active_shifts_today: int = 0
    open_shifts: int = 0
    completed_visits_this_week: int = 0
    pending_payroll_amount: Decimal = Decimal("0")
    outstanding_invoices: int = 0
    outstanding_invoice_amount: Decimal = Decimal("0")
    expiring_credentials_count: int = 0
    unread_notifications: int = 0


class PlatformKPIs(BaseModel):
    """Platform-wide KPIs for super-admin dashboard."""

    total_agencies: int = 0
    total_users: int = 0
    total_clients: int = 0
    total_shifts_this_month: int = 0
    total_revenue_this_month: Decimal = Decimal("0")


class CaregiverPortalSummary(BaseModel):
    """Summary data for caregiver portal."""

    upcoming_shifts: int = 0
    completed_visits_this_week: int = 0
    pending_offers: int = 0
    expiring_credentials: int = 0
    unread_notifications: int = 0
    unread_messages: int = 0


class FamilyPortalSummary(BaseModel):
    """Summary data for family portal."""

    linked_clients: int = 0
    upcoming_shifts: int = 0
    recent_visits: int = 0
    unread_messages: int = 0
    unread_notifications: int = 0
