# COREcare v2

Multi-tenant SaaS platform for home care agencies — coordinates clients, caregivers, families, and agency staff in one place. Ground-up rebuild of the v1 product with a focus on auditability, RLS-enforced tenant isolation, and AI-assisted care planning.

**Stack:** FastAPI · Next.js 15 · shadcn/ui · PostgreSQL 16 (RLS) · Clerk · Claude API · Docker Compose.

## Get started

New contributor? **Run `scripts/setup.sh`** for a guided bootstrap (Docker stack up, test data seeded, login credentials printed). Then read [`CONTRIBUTING.md`](CONTRIBUTING.md) for the development workflow.

```bash
git clone https://github.com/suniljames/COREcare-v2.git
cd COREcare-v2
scripts/setup.sh
```

## Documentation

| Topic | File |
|-------|------|
| Contributing & dev workflow | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Architecture & patterns     | [`docs/developer/ARCHITECTURE.md`](docs/developer/ARCHITECTURE.md) |
| Testing guide               | [`docs/developer/TESTING.md`](docs/developer/TESTING.md) |
| Safety (project-specific)   | [`docs/developer/SAFETY.md`](docs/developer/SAFETY.md) |
| Architecture decisions      | [`docs/adr/`](docs/adr/) |

## Healthcare context

This product handles PHI (Protected Health Information). All contributions follow the [healthcare overlay](https://github.com/suniljames/directives/blob/main/overlays/healthcare/) of the engineering directives — see [`docs/developer/SAFETY.md`](docs/developer/SAFETY.md) before making changes that touch real data.
