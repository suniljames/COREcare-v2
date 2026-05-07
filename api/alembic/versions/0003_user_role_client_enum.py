"""Add 'client' value to userrole enum.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-07

PG enum-add restriction: standalone migration, no other DDL referencing the
new value in the same transaction.
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'client'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly. The
    # approach is type-rename + recreate + cast back. Skipping for v2-MVP
    # because rolling back this migration without dropping dependent rows
    # is unsafe; a true rollback creates a new migration that drops Client
    # users first.
    pass
