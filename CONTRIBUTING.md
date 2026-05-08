# COREcare v2 — Developer Guide

Multi-tenant SaaS platform for home care coordination. Ground-up rebuild with FastAPI + Next.js 15 + shadcn/ui + PostgreSQL RLS + Clerk + Claude API.

This project follows the [engineering directives](https://github.com/suniljames/directives) (includes [healthcare overlay](https://github.com/suniljames/directives/blob/main/overlays/healthcare/)).

<!-- team: engineering -->
<!-- pipeline-mode: autonomous -->

## Get running in 10 minutes

**Prerequisite:** [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running. Everything else (Python, Node, pnpm, uv, git-lfs) is recommended but optional — Docker handles the runtime.

```bash
git clone https://github.com/suniljames/COREcare-v2.git
cd COREcare-v2
make setup        # or: bash scripts/setup.sh
```

`make setup` is idempotent: it checks tool versions, seeds `api/.env` and `web/.env.local` from the example files (without overwriting existing files), starts the Docker stack, and waits for the API to be healthy. On success it prints next-step commands.

> **Note — schema init is currently broken** ([#240](https://github.com/suniljames/COREcare-v2/issues/240)). `make api-migrate` and `make api-seed` are *not* run by `make setup` because no migration creates the initial tables. The Docker stack still comes up and `/healthz` works; persona-driven UI flows and DB-backed endpoints will fail until #240 is resolved.

Verify everything is green:

```bash
make health       # API / Web / DB / Redis health
make check        # Lint + typecheck + test + build (must pass before PRs)
```

If `make setup` warns about missing tools (Node, Python, pnpm, uv), those are only needed for non-Docker workflows — the Docker stack will still come up. See [Troubleshooting](#troubleshooting) below if anything fails.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12, uv) |
| Frontend | Next.js 15 App Router (pnpm) |
| UI Library | shadcn/ui + Tailwind CSS |
| Database | PostgreSQL 16 + SQLModel + Alembic |
| Multi-tenancy | PostgreSQL Row-Level Security (RLS) |
| Auth | Clerk (JWT backend + React components) |
| AI | Claude API (Anthropic SDK) |
| Deployment | Docker Compose (local Mac Mini only) |
| CI | GitHub Actions |

## Dev/Test Environment

After cloning, install Git LFS once so the [v1 UI catalog](docs/legacy/v1-ui-catalog/) WebP binaries (per [ADR-010](docs/adr/010-v1-ui-catalog-storage.md)) are fetched correctly:

```bash
git lfs install
```

Local Docker Compose: `docker compose up` starts API (8000), Web (3000), PostgreSQL, Redis.

Test accounts (seeded by `make api-seed`):

| Role | Email | Password |
|------|-------|----------|
| Super-Admin | superadmin@test.com | `TestSuper123!` |
| Agency Admin | admin@test.com | `TestAdmin123!` |
| Care Manager | manager1@test.com | `TestManager123!` |
| Caregiver 1 | caregiver1@test.com | `TestCare123!` |
| Caregiver 2 | caregiver2@test.com | `TestCare123!` |
| Family 1 | family1@test.com | `TestFamily123!` |
| Family 2 | family2@test.com | `TestFamily123!` |

```bash
make check                # Lint + typecheck + test + build (must pass before PRs)
make test                 # All tests
make api-test             # API tests only
make web-test             # Web tests only
make test-e2e             # E2E tests (requires Docker stack)
make coldreader-test      # V1 inventory cold-reader rotation script self-test (see scripts/coldreader/README.md)
make coldreader-local-dry # Dry-run the rotation parser + fixtures against the live inventory
```

Tailscale for network access from other devices.

## Local authentication

The API ships with a **dev fallback** in [`api/app/auth.py`](api/app/auth.py): when `CLERK_SECRET_KEY` is empty *and* the request has no `Authorization` header, every endpoint resolves to a mock `super_admin` user. This lets you exercise API endpoints (via `curl`, the Swagger UI at `/docs`, or unit tests) with no Clerk account.

The web app boots with a publicly-known dummy Clerk publishable key (the same one CI uses) so `pnpm dev` and `pnpm build` succeed locally. You **cannot sign in through the web UI with the dummy key** — Clerk's hosted sign-in flow needs a real `pk_test_...` and matching `sk_test_...`.

When to set real Clerk keys:

| Goal | Need real Clerk? |
|------|------------------|
| Run API tests / hit `/docs` / drive endpoints with `curl` | No |
| Run web in dev with the layout rendering | No (dummy key boots it) |
| Sign in via the web UI as a seeded user | Yes — both `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` |
| Run E2E tests against the full stack | Yes |

Get keys from [Clerk's dashboard](https://dashboard.clerk.com/) and put them in `web/.env.local` and `api/.env`.

## Branches and commits

Branch names: `<type>/<issue>-<short-desc>` (e.g. `feat/235-onboarding-cleanup`, `docs/106-readme-rewrite`).

Commit messages: `<type>(#<issue>): <subject>` (e.g. `feat(#235): add scripts/setup.sh`). See `git log` for the project's prevailing style. Every change must be associated with a GitHub issue — see [`#213`](https://github.com/suniljames/COREcare-v2/issues/213).

PRs run `make check` in CI; they're blocked until that passes. Use [`.github/pull_request_template.md`](.github/pull_request_template.md) — the template prompts for the linked issue, summary, and test plan.

## Troubleshooting

**`make setup` fails at "Docker is installed but not running"**
Open Docker Desktop and wait for it to finish starting, then re-run `make setup`.

**API never comes up after `make setup`**
Inspect logs: `docker compose logs api`. The most common cause is a port conflict — check that nothing is already bound to `:8000`, `:3000`, `:5432`, or `:6379`.

**Web app shows "Invalid publishable key"**
`web/.env.local` is missing or has an unset `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`. Run `make setup` again, or `cp web/.env.local.example web/.env.local`.

**API tests pass locally but fail in CI**
The local pytest suite uses SQLite (via `aiosqlite`); CI uses real PostgreSQL. If your test depends on Postgres-specific behavior (RLS, JSONB ops, advisory locks), it must run against the Docker stack. See [`docs/developer/TESTING.md`](docs/developer/TESTING.md).

**`make check` fails on `ruff format --check`**
The editor post-tool hook formats with `black` (line length 88), but the project uses `ruff format` (line length 100). Run `cd api && uv run ruff format .` before committing.

**`make api-seed` fails with "relation does not exist"**
Tracked in [#240](https://github.com/suniljames/COREcare-v2/issues/240) — no migration runs `CREATE TABLE`, so `ALTER TABLE users` in `0001_enable_rls_policies.py` fails first. Until that's fixed, schema is only created in test fixtures via `SQLModel.metadata.create_all`.

## Slash-command Invariants

Slash commands that cut branches must do so from an explicit, freshly-fetched
named remote ref (e.g., `origin/main`) — never from an implicit local branch.
See [`#176`](https://github.com/suniljames/COREcare-v2/issues/176) and the
regression test at `scripts/tests/test_implement_branch_cut.sh`.

Pipeline commands (`/define`, `/design`, `/implement`, `/review`) abort on
closed issues by default. Pass `--force-on-closed` to override on a single
run. See [`#213`](https://github.com/suniljames/COREcare-v2/issues/213).

## Domain context (home-care SaaS)

If you're unfamiliar with home-care coordination, read [`docs/GLOSSARY.md`](docs/GLOSSARY.md) once — it defines *persona*, *tenant*, *agency*, *client*, *caregiver*, *family member*, *RLS*, *PHI*, and the other vocabulary that shows up across the codebase. HIPAA-specific rules live in [`docs/developer/SAFETY.md`](docs/developer/SAFETY.md).

## Project Docs

For a role-based map of the full docs tree, start at [`docs/README.md`](docs/README.md).

Direct links to the docs you'll touch most often:

| Topic | File |
|-------|------|
| Architecture & patterns | [`docs/developer/ARCHITECTURE.md`](docs/developer/ARCHITECTURE.md) |
| Testing guide | [`docs/developer/TESTING.md`](docs/developer/TESTING.md) |
| Safety (project-specific) | [`docs/developer/SAFETY.md`](docs/developer/SAFETY.md) |
| Code review lenses | [`docs/developer/code-review-lenses.md`](docs/developer/code-review-lenses.md) |
| Project context | [`docs/developer/project-context.md`](docs/developer/project-context.md) |
| Design system | [`docs/design-system/`](docs/design-system/) |
| ADRs | [`docs/adr/`](docs/adr/) |
| Glossary | [`docs/GLOSSARY.md`](docs/GLOSSARY.md) |
