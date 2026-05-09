# AGENTS.md — entry point for AI coding assistants

You are an AI agent working on **COREcare v2**, a multi-tenant SaaS for home-care agencies. Stack: FastAPI · Next.js 15 · shadcn/ui · PostgreSQL 16 (RLS) · Clerk · Claude API · Docker Compose. This file is the canonical, tool-agnostic reference for *any* AI assistant. Tool-specific files ([`CLAUDE.md`](CLAUDE.md), [`GEMINI.md`](GEMINI.md)) carry only what is unique to those tools.

## Verify

Run `make check` before committing. It is the canonical pre-PR gate; CI runs the same target — if CI fails, `make check` reproduces it locally.

`make check` executes:

- `uv run ruff check .` — Python linting
- `uv run ruff format --check .` — Python formatting (line-length 100, **not** 88)
- `uv run mypy app/` — Python type checking
- `pytest` — API test suite
- `eslint + prettier` — web linting
- `tsc` — web type checking
- `vitest` — web unit tests
- `next build` — web production build
- Several slash-command invariant tests under `scripts/tests/`
- LFS workflow posture check

If a sub-step fails, the troubleshooting matrix in [`CONTRIBUTING.md`](CONTRIBUTING.md#troubleshooting) lists the fix command (e.g., `cd api && uv run ruff format .`). For runtime health: `make health`.

## Don't touch

Each entry is **path → consequence**. Read the linked issue or ADR before editing.

| Path | Consequence |
|---|---|
| `docs/legacy/v1-ui-catalog/` | Git LFS-backed; hand-edits break LFS invariants. See [ADR-010](docs/adr/010-v1-ui-catalog-storage.md). |
| `api/alembic/versions/` | Schema scaffolding is a known gap — do not fabricate migrations. See [#240](https://github.com/suniljames/COREcare-v2/issues/240). |
| `api/app/auth.py` | Boot-blocking invariants live here; refuses to start in non-development environments without correct configuration. See [#241](https://github.com/suniljames/COREcare-v2/issues/241). |
| `web/.env.local.example` | Holds a value required for local boot; removing or "cleaning up" entries breaks `pnpm dev`. See [`CONTRIBUTING.md`](CONTRIBUTING.md). |
| Files marked `# generated` (or similar) | Regenerate via the documented script — do not hand-edit. |
| `.pre-commit-config.yaml` v1-* hooks | Gate the v1 catalog migration; alter only with the migration owner. |

Do **not** copy seed credentials, dummy keys, internal hostnames, or environment-variable values into this file or other public docs — link to the existing location instead.

## Repo map (code directories)

Documentation directories are routed by [`docs/README.md`](docs/README.md). For code:

| Path | What lives here |
|---|---|
| [`api/app/routers/`](api/app/routers/) | FastAPI route handlers — thin; delegate to services |
| [`api/app/services/`](api/app/services/) | Business logic |
| [`api/app/models/`](api/app/models/) | SQLModel definitions |
| [`api/app/schemas/`](api/app/schemas/) | Pydantic request/response schemas |
| [`api/app/tests/`](api/app/tests/) | API tests (pytest + httpx) |
| [`api/alembic/`](api/alembic/) | Migration framework — see don't-touch above |
| [`web/src/app/`](web/src/app/) | Next.js 15 App Router pages |
| [`web/src/lib/`](web/src/lib/) | Shared utilities (no React) |
| [`web/src/__tests__/`](web/src/__tests__/) | Web unit tests (vitest) |
| [`web/e2e/`](web/e2e/) | E2E tests (Playwright) |
| [`scripts/`](scripts/) | Bash helpers, pre-commit hooks, coldreader |
| [`tools/`](tools/) | Long-running tooling (e.g., v1 screenshot catalog) |
| [`docs/`](docs/) | All documentation — start at [`docs/README.md`](docs/README.md) |

Default to **server components** in `web/src/app/`; switch to client components only for interactivity. API code is **routers → services → models** — no business logic in routers.

## Conventions

- **Branch:** `<type>/<issue>-<short-desc>` (e.g., `docs/288-agents-md`).
- **Commit:** `<type>(#<issue>): <subject>`.
- **Every change links to a GitHub issue** ([#213](https://github.com/suniljames/COREcare-v2/issues/213)).
- **Issue numbers in code, docs, and PRs are intentional anchors.** When in doubt, run `gh issue view <n>` for context — it is cheap and high-signal.
- **Branch base** must be freshly-fetched `origin/main`, never stale local `main` ([#176](https://github.com/suniljames/COREcare-v2/issues/176)).
- See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full PR workflow, test-account roster, and `make` target reference.

## Tool routing

- **Claude Code:** read [`CLAUDE.md`](CLAUDE.md) — builder-role assignment plus pipeline commands (`/define`, `/design`, `/implement`, `/review`, `/summarize`).
- **Gemini-based validators:** read [`GEMINI.md`](GEMINI.md) — validator-role assignment.
- **All other agents** (OpenAI Codex CLI, Cursor, Aider, Sourcegraph Cody, etc.): this file is your canonical reference. The pipeline slash-commands above are Claude-specific and will not work in your tool — follow the conventions in this file and operate as a regular contributor.

## Domain glossary

This is a healthcare product. Before reasoning about domain terms (*persona*, *tenant*, *agency*, *client*, *caregiver*, *family member*, *RLS*, *PHI*, *ADLs*), consult [`docs/GLOSSARY.md`](docs/GLOSSARY.md) — generic definitions don't carry over. PHI-handling rules live in [`docs/developer/SAFETY.md`](docs/developer/SAFETY.md); architecture and patterns live in [`docs/developer/ARCHITECTURE.md`](docs/developer/ARCHITECTURE.md); past decisions in [`docs/adr/`](docs/adr/).
