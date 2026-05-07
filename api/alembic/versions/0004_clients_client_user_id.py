"""Add clients.client_user_id FK column.

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-07

Nullable FK from clients.client_user_id -> users.id, unique. ON DELETE SET
NULL: the clinical record outlives the login.
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("client_user_id", sa.Uuid, nullable=True),
    )
    op.create_unique_constraint("uq_clients_client_user_id", "clients", ["client_user_id"])
    op.create_index("ix_clients_client_user_id", "clients", ["client_user_id"])
    op.create_foreign_key(
        "fk_clients_client_user_id_users",
        "clients",
        "users",
        ["client_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_clients_client_user_id_users", "clients", type_="foreignkey")
    op.drop_index("ix_clients_client_user_id", table_name="clients")
    op.drop_constraint("uq_clients_client_user_id", "clients", type_="unique")
    op.drop_column("clients", "client_user_id")
