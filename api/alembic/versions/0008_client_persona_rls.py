"""Dual-axis RLS policies for the Client persona.

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-07

Adds the Client-row-isolation axis on top of the existing tenant axis. A
Client (with `app.current_client_id` set) can only read their own row; staff
(no client context) read tenant-scoped as before; super-admin (no contexts)
sees all.

Drops the old single-axis tenant_isolation policies on `clients` and creates
a dual-axis tenant_and_client_isolation policy. Same pattern applied to
`shifts`, `messages`, `care_plan_versions`, and `message_threads`.

`WITH CHECK` mirrors `USING` to gate writes (Data Engineer §1).
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


# Tables and the row-key column that must equal current_client_id when
# the Client context is set.
DUAL_AXIS_TABLES = {
    # table_name: (own-row column name in the table)
    "clients": "id",
    "shifts": "client_id",
    "care_plan_versions": "client_id",
    "message_threads": "client_id",
}


def _create_dual_axis_policy(table: str, own_column: str) -> str:
    return f"""
        CREATE POLICY tenant_and_client_isolation ON {table}
          USING (
            (current_setting('app.current_client_id', true) = ''
              AND (agency_id::text = current_setting('app.current_tenant_id', true)
                   OR current_setting('app.current_tenant_id', true) = ''))
            OR
            (current_setting('app.current_client_id', true) <> ''
              AND {own_column}::text = current_setting('app.current_client_id', true)
              AND agency_id::text = current_setting('app.current_tenant_id', true))
          )
          WITH CHECK (
            (current_setting('app.current_client_id', true) = ''
              AND (agency_id::text = current_setting('app.current_tenant_id', true)
                   OR current_setting('app.current_tenant_id', true) = ''))
            OR
            (current_setting('app.current_client_id', true) <> ''
              AND {own_column}::text = current_setting('app.current_client_id', true)
              AND agency_id::text = current_setting('app.current_tenant_id', true))
          )
    """


def _create_messages_policy() -> str:
    """Messages: visible if the thread belongs to the current Client."""
    return """
        CREATE POLICY tenant_and_client_isolation ON messages
          USING (
            (current_setting('app.current_client_id', true) = ''
              AND (agency_id::text = current_setting('app.current_tenant_id', true)
                   OR current_setting('app.current_tenant_id', true) = ''))
            OR
            (current_setting('app.current_client_id', true) <> ''
              AND thread_id IN (
                SELECT id FROM message_threads
                WHERE client_id::text = current_setting('app.current_client_id', true)
              )
              AND agency_id::text = current_setting('app.current_tenant_id', true))
          )
          WITH CHECK (
            (current_setting('app.current_client_id', true) = ''
              AND (agency_id::text = current_setting('app.current_tenant_id', true)
                   OR current_setting('app.current_tenant_id', true) = ''))
            OR
            (current_setting('app.current_client_id', true) <> ''
              AND thread_id IN (
                SELECT id FROM message_threads
                WHERE client_id::text = current_setting('app.current_client_id', true)
              )
              AND agency_id::text = current_setting('app.current_tenant_id', true))
          )
    """


def upgrade() -> None:
    for table, own_column in DUAL_AXIS_TABLES.items():
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(_create_dual_axis_policy(table, own_column))

    # Messages: thread-based join policy
    op.execute("ALTER TABLE messages ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE messages FORCE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON messages")
    op.execute(_create_messages_policy())


def downgrade() -> None:
    for table in [*DUAL_AXIS_TABLES.keys(), "messages"]:
        op.execute(f"DROP POLICY IF EXISTS tenant_and_client_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
