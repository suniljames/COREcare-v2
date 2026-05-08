# Migrations Runbook

Schema state in COREcare v2 is owned by Alembic. This runbook covers the
common flows: bootstrap, reset, add a migration, recover from a wedged
local DB, and diagnose CI failures. See
[`ARCHITECTURE.md`](ARCHITECTURE.md#database-schema) for the
migrations-as-source-of-truth invariant.

## Bootstrap from empty

After cloning the repo or rebuilding the dev stack:

```bash
docker compose up -d db
make api-migrate
make api-seed
```

`make api-migrate` runs `alembic upgrade head`. `make api-seed` inserts the
demo agency and seven test users (see `api/app/seed.py`). Both are
idempotent — re-running them is safe.

## Reset existing local schema

If your local Postgres is in a broken or unknown state — for instance,
tables created by `SQLModel.metadata.create_all` from a stray test run
without an `alembic_version` row — drop everything and start over:

```bash
make db-reset
```

`db-reset` drops the database, recreates it, runs migrations, and seeds.
One command, full recovery. You don't need to reason about the prior
state.

## Add a new migration

After changing models in `api/app/models/`:

```bash
docker compose up -d db
make -C api migration MSG="describe-the-change-in-kebab-case"
```

This calls `alembic revision --autogenerate` against the running dev DB.
**Inspect the generated file under `api/alembic/versions/` before
committing.** Autogenerate misses several things you must port by hand:

- **Partial indexes** (`postgresql_where=...`). Add a
  `sqlite_where` mirror if the column is exercised by SQLite test
  fixtures.
- **Postgres-specific column types** like `JSONB` vs `JSON`. Default to
  `sa.dialects.postgresql.JSONB()` for any column you'd ever filter on.
- **RLS policies** for new `TenantScopedModel` subclasses (see "Adding
  RLS to a new table" below).
- **Enum value casing.** SQLAlchemy's default uses `enum.name`
  (UPPERCASE). Confirm the application's INSERT path matches.

After hand-editing, verify on a fresh DB:

```bash
make db-reset
uv run --project api pytest -m integration   # drift test must stay green
```

## Adding RLS to a new tenant-scoped table

Every `TenantScopedModel` subclass needs a Row-Level Security policy.
Follow the pattern in `api/alembic/versions/0001_initial_schema.py`:

- **Single-axis** (`tenant_isolation`) — for tables only staff query.
  Mirror the `users`/`email_events` policies.
- **Dual-axis** (`tenant_and_client_isolation`) — for tables a Client
  persona queries directly. Mirror the `clients`/`shifts`/etc.
  policies.

Always include `FORCE ROW LEVEL SECURITY` so policies apply to the
table owner (the app's DB user). Update the
`SINGLE_AXIS_TABLES`/`DUAL_AXIS_TABLES` sets at the top of
`api/app/tests/test_migrations_e2e.py` so the policy-parity test
includes the new table.

## Recovery: "I broke my local schema"

```bash
make db-reset
```

If `db-reset` itself fails (e.g., docker compose isn't running):

```bash
docker compose up -d db
make db-reset
```

If the long-lived dev container is in a wedged state, drop it and let
docker compose recreate:

```bash
docker compose down -v   # WARNING: -v drops the volume too. Local data lost.
docker compose up -d db
make db-reset
```

## Recovery: "Migration fails in CI"

The most common failure is **schema drift** — the migration head and
`SQLModel.metadata` disagree. The drift test (`alembic check`) flags it.
Workflow:

1. Pull the failing test output from CI.
2. Run locally:

   ```bash
   make db-reset
   DATABASE_URL=postgresql+asyncpg://corecare:corecare@localhost:5432/corecare \
     uv run --project api alembic check
   ```

3. If `alembic check` reports operations, regenerate:

   ```bash
   make -C api migration MSG="reconcile-drift"
   ```

4. Inspect the new migration. If it's a single-line column change,
   commit. If it's many ops, review carefully — you may have
   accidentally introduced model changes that should have been
   intentional migrations.

## Recovery: "alembic upgrade head fails on a fresh DB"

This was issue #240. Steps to triage if it ever recurs:

1. `docker exec <db-container> psql -U corecare -d corecare -c "\dt"` —
   any tables present? Should be none on a true fresh DB.
2. `docker exec <db-container> psql -U corecare -d corecare -c "SELECT * FROM alembic_version"` —
   any rows? Should be none on a true fresh DB.
3. Run the migration with `--sql` to see the generated DDL without
   applying:

   ```bash
   uv run --project api alembic upgrade head --sql
   ```

4. If a CREATE TABLE references another table not in the same file,
   the migration ordering is wrong — reorder operations or split into
   two migrations.

## Reference

- Migration files: `api/alembic/versions/`
- Alembic config: `api/alembic.ini`, `api/alembic/env.py`
- Drift guard: `api/app/tests/test_migrations_e2e.py`
- Seed data: `api/app/seed.py`
- Reset target: `Makefile` → `db-reset`
