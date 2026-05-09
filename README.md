# COREcare v2

Multi-tenant SaaS platform for home care agencies — coordinates clients, caregivers, families, and agency staff in one place. Ground-up rebuild of the v1 product with a focus on auditability, RLS-enforced tenant isolation, and AI-assisted care planning.

**Stack:** FastAPI · Next.js 15 · shadcn/ui · PostgreSQL 16 (RLS) · Clerk · Claude API · Docker Compose.

## Get started

New contributor? **Run `make setup`** for a guided bootstrap — checks tool versions, seeds `.env` files from examples, brings up the Docker stack, and waits for `/healthz`. Then apply migrations, seed test data, and verify the stack:

```bash
git clone https://github.com/suniljames/COREcare-v2.git
cd COREcare-v2
make setup        # bootstrap (or: bash scripts/setup.sh)
make api-migrate  # alembic upgrade head — creates the schema
make api-seed     # demo agency + 7 test users
make health       # API / Web / DB / Redis check
```

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full development workflow, the test-account roster, and `make check` (the pre-PR quality gate).

## Documentation

**Start here:** [`docs/README.md`](docs/README.md) routes you by role (backend, frontend, reviewer, on-call, PM) and explains the rest of the docs tree.

**Domain glossary:** [`docs/GLOSSARY.md`](docs/GLOSSARY.md) — persona, tenant, RLS, PHI, ADLs, and the rest of the home-care vocabulary in one place.

| Direct link | When to use it |
|---|---|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | First-day setup + branch / commit / PR conventions |
| [`AGENTS.md`](AGENTS.md) | Canonical entry point for AI coding assistants (verify command, repo map, don't-touch list) |
| [`docs/developer/`](docs/developer/) | Architecture, testing, safety, code review |
| [`docs/design-system/`](docs/design-system/) | Frontend tokens, components, accessibility |
| [`docs/adr/`](docs/adr/) | 11 numbered Architecture Decision Records |

## Healthcare context

This product handles PHI (Protected Health Information). All contributions follow the [healthcare overlay](https://github.com/suniljames/directives/blob/main/overlays/healthcare/) of the engineering directives — see [`docs/developer/SAFETY.md`](docs/developer/SAFETY.md) before making changes that touch real data.
