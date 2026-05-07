"""Create message_threads table.

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-07

One thread per (Client, Agency) pair. Enables agency-side inbox enumeration
and is the join target for Client-persona message RLS.
"""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "message_threads",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("agency_id", sa.Uuid, sa.ForeignKey("agencies.id"), nullable=False),
        sa.Column(
            "client_id",
            sa.Uuid,
            sa.ForeignKey("clients.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_message_threads_agency_id", "message_threads", ["agency_id"])
    op.create_index("ix_message_threads_client_id", "message_threads", ["client_id"])
    op.create_index(
        "ix_message_threads_last_message_at",
        "message_threads",
        ["last_message_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_message_threads_last_message_at", table_name="message_threads")
    op.drop_index("ix_message_threads_client_id", table_name="message_threads")
    op.drop_index("ix_message_threads_agency_id", table_name="message_threads")
    op.drop_table("message_threads")
