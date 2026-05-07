"""Database models."""

from app.models.agency import Agency
from app.models.ai import AIConversation, AIFeatureFlag, AIMessage
from app.models.audit import AuditAction, AuditEvent
from app.models.base import BaseModel, TenantScopedModel
from app.models.billing import Invoice, InvoiceLineItem, InvoiceStatus
from app.models.care_plan import CarePlanVersion
from app.models.caregiver import CaregiverProfile
from app.models.chart import Chart, ChartStatus, ChartTemplate
from app.models.client import Client, ClientStatus, FamilyLink
from app.models.client_invite import ClientInvite
from app.models.compliance import BAARecord, ComplianceRule
from app.models.credential import Credential, CredentialStatus, CredentialType
from app.models.email import EmailCategory, EmailEvent, EmailStatus
from app.models.message_thread import MessageThread
from app.models.notification import (
    Message,
    Notification,
    NotificationType,
    PushSubscription,
)
from app.models.payroll import PayrollEntry, PayrollPeriod, PayrollPeriodStatus
from app.models.shift import Shift, ShiftStatus
from app.models.user import User, UserRole
from app.models.visit import ShiftOffer, ShiftOfferStatus, Visit

__all__ = [
    "Agency",
    "AIConversation",
    "AIFeatureFlag",
    "AIMessage",
    "AuditAction",
    "AuditEvent",
    "BAARecord",
    "BaseModel",
    "CarePlanVersion",
    "CaregiverProfile",
    "ComplianceRule",
    "Chart",
    "ChartStatus",
    "ChartTemplate",
    "Client",
    "ClientInvite",
    "ClientStatus",
    "Credential",
    "CredentialStatus",
    "CredentialType",
    "EmailCategory",
    "EmailEvent",
    "EmailStatus",
    "FamilyLink",
    "Invoice",
    "InvoiceLineItem",
    "InvoiceStatus",
    "Message",
    "MessageThread",
    "Notification",
    "NotificationType",
    "PayrollEntry",
    "PayrollPeriod",
    "PayrollPeriodStatus",
    "PushSubscription",
    "Shift",
    "ShiftOffer",
    "ShiftOfferStatus",
    "ShiftStatus",
    "TenantScopedModel",
    "User",
    "UserRole",
    "Visit",
]
