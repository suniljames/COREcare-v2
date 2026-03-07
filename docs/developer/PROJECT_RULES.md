# Project Rules

These rules are mandatory for every developer — human, AI, or otherwise.

## Data Verification

- **Never report data loss without full verification.**
- Dashboard counts != database counts (dashboards show filtered views).
- Express uncertainty first: "Let me verify further before drawing conclusions."

## Testing & Quality Gates

- **TDD:** Write failing tests first, then implement.
- `make check` must pass before any PR (runs all linters + tests + typecheck + build).
- CI runs against PostgreSQL 16.
- See [`TESTING.md`](TESTING.md) for full guide and [`TEST_BUDGET.md`](TEST_BUDGET.md) for layer decisions.

## Safety & Guardrails

- **Never** delete repos, databases, or broad paths. **Never** force-push. **Never** expose PHI.
- **Never** commit secrets. **Stop and ask** if a destructive action seems necessary.
- See [`SAFETY.md`](SAFETY.md) for the full list.

## Deployment

- **Local only.** Docker Compose on Mac Mini. No cloud hosting.
- `docker compose up --build -d && curl http://localhost:8000/healthz`
- Tailscale for network access from other devices.

## Session Isolation

- **Every code change must be associated with a GitHub issue.**
- **The main checkout must stay on `main`.** All feature work happens in isolated branches or worktrees.
