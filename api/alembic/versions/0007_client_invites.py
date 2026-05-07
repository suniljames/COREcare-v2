"""Create client_invites table.

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-07

Single-use, time-boxed invites for Client-persona account creation. Email
match is enforced at redemption time; expiry is enforced via expires_at.
"""

import sqlalchemy as sa

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_invites",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("agency_id", sa.Uuid, sa.ForeignKey("agencies.id"), nullable=False),
        sa.Column("client_id", sa.Uuid, sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("token", sa.String, nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "issued_by_user_id",
            sa.Uuid,
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
    )
    op.create_index("ix_client_invites_client_id", "client_invites", ["client_id"])
    op.create_index("ix_client_invites_agency_id", "client_invites", ["agency_id"])
    op.create_index("ix_client_invites_email", "client_invites", ["email"])
    op.create_index("ix_client_invites_token", "client_invites", ["token"], unique=True)
    op.create_index("ix_client_invites_redeemed_at", "client_invites", ["redeemed_at"])
    op.create_index(
        "ix_client_invites_issued_by_user_id",
        "client_invites",
        ["issued_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_client_invites_issued_by_user_id", table_name="client_invites")
    op.drop_index("ix_client_invites_redeemed_at", table_name="client_invites")
    op.drop_index("ix_client_invites_token", table_name="client_invites")
    op.drop_index("ix_client_invites_email", table_name="client_invites")
    op.drop_index("ix_client_invites_agency_id", table_name="client_invites")
    op.drop_index("ix_client_invites_client_id", table_name="client_invites")
    op.drop_table("client_invites")
