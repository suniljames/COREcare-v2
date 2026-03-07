# COREcare v2 Project Guidelines

Multi-tenant SaaS platform for home care coordination. Ground-up rebuild with FastAPI + Next.js 15 + shadcn/ui + PostgreSQL RLS + Clerk + Claude API.

> **For all AI agents.** Sections under "Project Rules" apply to every agent working in this repo (Claude Code, Gemini, or any future agent). Sections under "Claude Code Agent Config" are Claude-specific — Gemini should read them for context but follow its own `GEMINI.md` for agent-specific behavior.

## Documentation Index

| Topic | File | Description |
|-------|------|-------------|
| Agent Split | See `docs/adr/009-multi-agent-engineering-split.md` | Role assignments, rationale, coordination protocol |
| Engineering Committee | See `docs/developer/ENGINEERING_COMMITTEE.md` | Committee review process, personas, test spec format |
| Testing | See `docs/developer/TESTING.md` | pytest/vitest/Playwright guides |
| Test Budget | See `docs/developer/TEST_BUDGET.md` | Layer decision checklist |
| Design System | See `docs/design-system/` | Brand, tokens, components, responsive, a11y |
| Safety & Guardrails | See `.claude/docs/SAFETY.md` | Destructive action prohibitions (shared rules, Claude path) |
| Personas | See `.claude/docs/PERSONAS.md` | Hazel interaction guide (Claude-specific) |
| Workflow | See `.claude/docs/WORKFLOW.md` | Issue lifecycle details (Claude-specific) |

---

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

---

## Dev/Test Environment

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

---

# Project Rules (All Agents)

These rules apply to every AI agent working in this repo.

### GitHub Identity
- **All GitHub operations must be performed as `suniljames`.**
- Before any `gh` CLI command, run `gh auth switch --user suniljames`.
- Git commits use `suniljames <suniljames@users.noreply.github.com>`.

### Multi-Agent Architecture
- **Two AI agents:** Claude Code (builder/executor, 7 roles) and Google Gemini (validator/risk manager, 4 roles).
- **Claude Code owns:** Engineering Manager, Software Engineer, System Architect, Data Engineer, AI/ML Engineer, UX Designer, SRE.
- **Gemini owns:** Security Engineer, QA Engineer, PM, Tech Writer.
- **Flow:** Gemini PM defines requirements → Claude Code builds → Gemini QA/Security validates → Claude Code addresses feedback.
- The builder and validator should be different models to maximize independent verification.
- See `docs/adr/009-multi-agent-engineering-split.md` for full rationale and coordination protocol.

### Autonomous Workflow (Abstract Pipeline)

No human review gates. The pipeline runs end-to-end without stopping. Each stage produces artifacts the next stage consumes.

| Stage | Purpose | Produces | Label |
|-------|---------|----------|-------|
| **1. Product Review** | Evaluate the issue, write a PRD with acceptance criteria | PRD comment on the GitHub issue | `pm-reviewed` |
| **2. Design Review** | Engineering committee reviews feasibility, architecture, UX, security | Design decision + test specification comments | `design-complete` |
| **3. Implementation** | TDD: scaffold failing tests → implement → green → refactor | Code in a feature branch, all tests passing | `implementing` |
| **4. Code Review & Merge** | CI gate → autonomous eng-committee code review (up to 3 rounds) → squash merge | Merged PR | `merged` |
| **5. Deploy & Verify** | Docker rebuild, health check, close issue | Running deployment | Issue closed |
| **6. Summarize** (optional) | Plain-language stakeholder summary | Summary comment | `summarized` |

Each agent implements this pipeline using its own tooling. Claude Code uses `/pm`, `/design`, `/implement`, `/ramd`, `/summarize` slash commands. Gemini uses its equivalent commands. The labels and artifacts are the shared contract — tooling is agent-specific.

### Cross-Agent Handoff Protocol
- **The repo is the source of truth.** All handoffs happen through files, PR comments, and issue comments — never through inter-agent messages.
- **Structured artifacts:** PRDs, test reports, security findings, and review comments follow defined formats (see `docs/developer/ENGINEERING_COMMITTEE.md` for test spec format).
- **Label-driven coordination:** Agents check GitHub issue labels to determine which pipeline stage is complete before proceeding.
- **PR labels:** All autonomously created PRs are labeled `ai:autonomous`.
- **Review findings:** Posted as PR comments with severity levels: `MUST-FIX`, `SHOULD-FIX`, `NIT`.

### Data Verification
- **Never report data loss without full verification.**
- Dashboard counts != database counts (dashboards show filtered views).
- Express uncertainty first: "Let me verify further before drawing conclusions."

### Multi-Tenancy
- All data queries must be tenant-scoped via RLS policies.
- Super-admin bypasses RLS to see all agencies.
- Never expose cross-tenant data in API responses.
- Test multi-tenant isolation in service tests for every data-access endpoint.

### Development Patterns
- **API:** Service layer pattern — routers call services, services call models. No business logic in routers.
- **Web:** Server Components by default. Client Components only for interactivity. Use shadcn/ui components.
- **Shared component reuse:** Search for existing components before creating new ones.
- Follow design system tokens — no hardcoded colors, spacing, or fonts.

### Testing & Quality Gates
- TDD: Write failing tests first, then implement.
- `make check` must pass before any PR (runs all linters + tests + typecheck + build).
- CI runs against PostgreSQL 16.
- See `docs/developer/TESTING.md` for backend/frontend test guides.

### Safety & Guardrails
- See `.claude/docs/SAFETY.md` for the full list. Key rules:
- **Never** delete repos, databases, or broad paths. **Never** force-push. **Never** expose PHI.
- **Never** commit secrets. **Stop and ask** if a destructive action seems necessary.

### Deployment
- **Local only.** Docker Compose on Mac Mini. No cloud hosting.
- `docker compose up --build -d && curl http://localhost:8000/healthz`
- Tailscale for network access from other devices.

### Session Isolation
- **Every code change must be associated with a GitHub issue.**
- **The main checkout must stay on `main`.** All feature work happens in isolated branches or worktrees.

---

# Claude Code Agent Config

These sections are specific to Claude Code. Other agents: read for context, follow your own config.

### Worktree & Session Management
- Use `claude -w` or `EnterWorktree` for branch isolation.
- Resume with `claude --from-pr <url>`.
- Progress tracked at `.claude/memory/progress/<issue-number>-progress.md`.

### Pipeline Commands
- `/pm` — Product review (PRD generation)
- `/design` — Engineering committee design review
- `/implement` — TDD implementation in a worktree
- `/ramd` — Review gates, approve, merge, deploy
- `/summarize` — Stakeholder summary

### For Hazel
- Always ask "Who is this?" at the start of a conversation.
- If Hazel, follow guidance in `.claude/docs/PERSONAS.md`.
