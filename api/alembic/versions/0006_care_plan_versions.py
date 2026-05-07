"""Create care_plan_versions table.

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-07

Append-only versioned care plans. Partial unique index enforces
"exactly one active version per Client" at the DB layer.
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "care_plan_versions",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("agency_id", sa.Uuid, sa.ForeignKey("agencies.id"), nullable=False),
        sa.Column("client_id", sa.Uuid, sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("version_no", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("plain_summary", sa.Text, nullable=False, server_default=""),
        sa.Column("care_team_blob", sa.JSON, nullable=False),
        sa.Column("weekly_support_blob", sa.JSON, nullable=False),
        sa.Column("allergies", sa.JSON, nullable=False),
        sa.Column("emergency_contact_blob", sa.JSON, nullable=False),
        sa.Column("clinical_detail", sa.JSON, nullable=False),
        sa.Column(
            "authored_by_user_id",
            sa.Uuid,
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "supersedes_version_id",
            sa.Uuid,
            sa.ForeignKey("care_plan_versions.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_care_plan_versions_client_id", "care_plan_versions", ["client_id"]
    )
    op.create_index(
        "ix_care_plan_versions_agency_id", "care_plan_versions", ["agency_id"]
    )
    op.create_index(
        "ix_care_plan_versions_version_no", "care_plan_versions", ["version_no"]
    )
    op.create_index(
        "ix_care_plan_versions_is_active", "care_plan_versions", ["is_active"]
    )
    op.create_index(
        "ix_care_plan_versions_authored_by_user_id",
        "care_plan_versions",
        ["authored_by_user_id"],
    )
    # Partial unique index: exactly one active version per Client.
    op.execute(
        "CREATE UNIQUE INDEX uq_care_plan_active_per_client "
        "ON care_plan_versions (client_id) WHERE is_active = true"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_care_plan_active_per_client")
    op.drop_index(
        "ix_care_plan_versions_authored_by_user_id", table_name="care_plan_versions"
    )
    op.drop_index("ix_care_plan_versions_is_active", table_name="care_plan_versions")
    op.drop_index("ix_care_plan_versions_version_no", table_name="care_plan_versions")
    op.drop_index("ix_care_plan_versions_agency_id", table_name="care_plan_versions")
    op.drop_index("ix_care_plan_versions_client_id", table_name="care_plan_versions")
    op.drop_table("care_plan_versions")
