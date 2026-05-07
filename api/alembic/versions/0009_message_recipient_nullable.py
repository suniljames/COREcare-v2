"""Make messages.recipient_id nullable for thread-routed messages.

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-07

Client-persona thread messages (issue #125) route by thread_id, not by
specific staff recipient. The agency-side inbox enumerates threads, not
per-staff recipients. Make the column nullable; family-messaging still
populates it for per-recipient messages.
"""

import sqlalchemy as sa

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("messages", "recipient_id", existing_type=sa.Uuid, nullable=True)


def downgrade() -> None:
    # Note: requires that no NULL recipient_id rows exist before downgrading.
    op.alter_column("messages", "recipient_id", existing_type=sa.Uuid, nullable=False)
