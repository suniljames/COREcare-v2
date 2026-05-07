"""Email events — single audit table for all outbound email (issue #120).

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-07

Creates the email_events table, its enums, supporting indexes, and the RLS
policy that mirrors other tenant-scoped tables. v1's BillingEmailLog and
InvoiceEmailLog do NOT backfill — see CUTOVER_PLAN.md.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


EMAIL_CATEGORY_VALUES = (
    "invoice",
    "credential_alert",
    "shift_offer",
    "weekly_health",
    "system",
)
EMAIL_STATUS_VALUES = (
    "pending",
    "sent",
    "failed",
    "bounced",
    "delivered",
    "opened",
    "clicked",
)


def upgrade() -> None:
    email_category = sa.Enum(*EMAIL_CATEGORY_VALUES, name="email_category")
    email_status = sa.Enum(*EMAIL_STATUS_VALUES, name="email_status")
    email_category.create(op.get_bind(), checkfirst=True)
    email_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "email_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "agency_id",
            sa.UUID(),
            sa.ForeignKey("agencies.id"),
            nullable=False,
        ),
        sa.Column("category", email_category, nullable=False),
        sa.Column("ref_id", sa.UUID(), nullable=False),
        sa.Column("recipient", sa.String(length=320), nullable=False),
        sa.Column("subject_redacted", sa.String(length=200), nullable=False),
        sa.Column("subject_hash", sa.String(length=64), nullable=False),
        sa.Column("body_storage_uri", sa.String(length=1024), nullable=True),
        sa.Column("attachment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", email_status, nullable=False, server_default="pending"),
        sa.Column("transport", sa.String(length=64), nullable=False),
        sa.Column("provider_message_id", sa.String(length=256), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bounced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=256), nullable=False),
    )

    op.create_index("ix_email_events_agency_id", "email_events", ["agency_id"])
    op.create_index("ix_email_events_category", "email_events", ["category"])
    op.create_index("ix_email_events_ref_id", "email_events", ["ref_id"])
    op.create_index("ix_email_events_status", "email_events", ["status"])
    op.create_index(
        "ix_email_events_lookup",
        "email_events",
        ["agency_id", "category", "ref_id"],
    )
    op.create_index(
        "ix_email_events_failures",
        "email_events",
        ["agency_id", "status", "created_at"],
    )
    op.create_unique_constraint(
        "uq_email_events_idempotency_key",
        "email_events",
        ["idempotency_key"],
    )
    op.create_index(
        "ix_email_events_provider_message_id",
        "email_events",
        ["provider_message_id"],
        unique=True,
        postgresql_where=sa.text("provider_message_id IS NOT NULL"),
    )

    # RLS — mirrors 0001_enable_rls_policies.py.
    op.execute("ALTER TABLE email_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE email_events FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation ON email_events
        USING (
            agency_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.current_tenant_id', true) = ''
        )
        WITH CHECK (
            agency_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.current_tenant_id', true) = ''
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON email_events")
    op.execute("ALTER TABLE email_events DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_email_events_provider_message_id", table_name="email_events")
    op.drop_constraint("uq_email_events_idempotency_key", "email_events", type_="unique")
    op.drop_index("ix_email_events_failures", table_name="email_events")
    op.drop_index("ix_email_events_lookup", table_name="email_events")
    op.drop_index("ix_email_events_status", table_name="email_events")
    op.drop_index("ix_email_events_ref_id", table_name="email_events")
    op.drop_index("ix_email_events_category", table_name="email_events")
    op.drop_index("ix_email_events_agency_id", table_name="email_events")
    op.drop_table("email_events")
    sa.Enum(name="email_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="email_category").drop(op.get_bind(), checkfirst=True)
