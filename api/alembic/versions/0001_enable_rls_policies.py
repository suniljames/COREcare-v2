"""Enable Row-Level Security policies for multi-tenancy.

Revision ID: 0001
Revises:
Create Date: 2026-03-07
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Tables that are tenant-scoped and need RLS.
# Add new tenant-scoped tables here as they are created.
TENANT_SCOPED_TABLES = ["users"]


def upgrade() -> None:
    for table in TENANT_SCOPED_TABLES:
        # Enable RLS on the table
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        # Force RLS even for table owner (the app's DB user)
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        # Create the tenant isolation policy
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
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
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
