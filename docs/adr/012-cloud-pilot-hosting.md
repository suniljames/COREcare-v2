# ADR-012: Cloud Pilot Hosting (Render + Vercel + R2)

**Status:** Proposed
**Date:** 2026-05-09
**Related:** [ADR-005](005-docker-compose-local-deployment.md) (deployment portion superseded for the pilot environment), [ADR-002](002-postgresql-rls-multi-tenancy.md), [ADR-003](003-clerk-authentication.md), [ADR-007](007-event-sourced-audit-logging.md), [ADR-011](011-email-outbound-boundary.md)
**Issues:** [#294](https://github.com/suniljames/COREcare-v2/issues/294), [#295](https://github.com/suniljames/COREcare-v2/issues/295)

## Context

[ADR-005](005-docker-compose-local-deployment.md) committed v2 to local Docker Compose on a Mac Mini, accessed via Tailscale, with two driving rationales: zero hosting cost and HIPAA data-locality ("data never leaves the premises"). At the time the user base was a single agency transitioning from v1, the cutover hadn't begun, and there was no second contributor.

Three things have changed since:

1. **An external contributor is joining.** A two-person team needs a shared remote environment to point at — the "all dev is local" model breaks the moment two people want to demo the same change to a third party, point a webhook at a stable URL, or coordinate a deploy.
2. **CI/deploy discipline matters before real users, not after.** Pre-cutover is the cheapest time to learn how to operate the deploy pipeline, exercise the rollback path, and run a restore drill. A team that ships its first deploy on the day real PHI lands has skipped the only safe time to make mistakes.
3. **The cutover plan ([CUTOVER_PLAN.md](../migration/CUTOVER_PLAN.md)) implies a v2 environment that can run in parallel with v1's Render production for shadow-traffic / canary work.** A Mac Mini reachable only via Tailscale doesn't satisfy that.

The audit of v1's Render production (sole web service + managed Postgres + Render disk + Render cron, no Redis, no scripted rollback, persistent-disk media pattern) and a parallel audit of `Project-Leila/Core` (Vercel + Supabase + Resend + git-crypted secrets + 24 GitHub Actions workflows, gated `workflow_run` deploys) gave us two reference points for the operational shape. Neither transplants directly — v1 is a Django monolith, Project-Leila is a fully-Supabase-resident BaaS architecture, v2 is FastAPI + Next.js with custom AI orchestration — but the patterns combine into a cleaner third option.

## Decision

Stand up a single non-local environment named **`staging`** on cloud infrastructure, comprising:

- **FastAPI** on **Render** (web service + native cron + managed Postgres + managed Redis), region `oregon`.
- **Next.js** on **Vercel** (per-PR preview deploys, custom domain `staging.<host>`).
- **Object storage** on **Cloudflare R2** (per-env bucket, signed URLs, encryption-at-rest). Explicitly NOT Render persistent disk.
- **Email** via **Resend** (HIPAA-eligible BAA when needed; Message-ID stamping for webhook correlation, modeled on v1's `core.email.backends.SendGridSMTPBackend` pattern).
- **Errors** via **Sentry**, with `before_send` PHI scrubber implemented day-1 (closing the gap v1's `docs/HIPAA_COMPLIANCE.md` spec'd but never shipped).
- **Auth** via real Clerk dev instance for staging (the dummy publishable + secret keys baked into `docker-compose.yml` are local-dev-only).
- **Health** via `/healthz` (DB-touching) and `/livez` (process-only), modeled on v1's status-page short-circuit pattern.
- **Migrations** via Render `preDeployCommand: cd api && uv run alembic upgrade head`, plus a 2 AM safety-net cron (mirrors v1's belt-and-suspenders pattern).

The deploy pipeline (CI gating, change-classifier, queued non-cancelling deploys, git-crypted secrets, optional self-hosted Mac Mini runner) is decided in the companion work tracked in [#295](https://github.com/suniljames/COREcare-v2/issues/295) and adopts the relevant patterns from `Project-Leila/Core`. This ADR locks the platform; #295 locks the pipeline shape.

### Naming: `staging`, not `production`

Even though it's the only non-local environment for now, this is `staging`. Reasons:

- "Promote to prod" stays a meaningful step when real users join. If the pilot env is named `production`, the muscle memory becomes "every merge ships to prod" — exactly what we want to avoid when real PHI lands.
- The real-prod slot remains reserved (likely `app.<host>`); when it's stood up later, it's an additive change, not a rename.
- v1 stays the canonical "production" until cutover.

### HIPAA / data-locality posture

ADR-005's "data never leaves the premises" is **relaxed for the pilot environment only**, on these conditions:

- **No real PHI.** The pilot runs against synthetic / seeded data only. The `make api-seed` 7-user fixture is the upper bound on data sensitivity. No live agency data is loaded into the pilot at any point.
- **No BAAs signed yet.** Render, Vercel, R2, Resend, Sentry, Clerk are all chosen with BAA-eligibility in mind, but no contracts are executed during the pilot. We pay the BAA-and-contract overhead only when the pilot is being promoted to a real-user environment.
- **Architecture is HIPAA-shaped from day-1**, even without the contracts: PHI scrubber in Sentry, encryption-at-rest in R2, RLS-enforced tenant isolation unchanged from [ADR-002](002-postgresql-rls-multi-tenancy.md), fail-closed auth unchanged from [ADR-003](003-clerk-authentication.md) and `api/app/auth.py`'s `is_dev_mode` gate.
- **Mac Mini option preserved.** The `render.yaml` and the deploy pipeline are designed so the same image can run on the Mac Mini if cost, HIPAA, or operational reasons force a fallback. The optional self-hosted Mac Mini GitHub Actions runner (#295 P2a) is the bridge between cloud-pilot and Mac-Mini-prod if we need it.

When the pilot graduates to handling real PHI, that promotion gets its own ADR — covering BAAs, the production environment shape (which may differ — could stay on Render Pro, could move to Mac Mini, could go AWS HIPAA-eligible), and the explicit data-locality decision for v2 production. **This ADR does not pre-commit to where v2 production runs.** It only commits to where the pilot runs.

## Alternatives considered

1. **Hold the line on ADR-005 — Mac Mini only, no cloud.** Rejected. Doesn't solve the second-contributor problem, doesn't give us a stable URL for webhooks or for shadow-traffic against v1, and forces the team to learn the deploy pipeline simultaneously with onboarding real users — the worst possible time.

2. **Vercel for both frontend and backend (serverless functions).** Rejected. v2's FastAPI service has long-running AI orchestration paths (Claude API calls), background work, and intentional state in Postgres + Redis. Vercel's serverless model would force a rewrite of those into Edge Functions or external workers. Vercel for the Next.js side only, paired with Render for FastAPI, is the right split.

3. **Supabase BaaS, à la Project-Leila.** Rejected. Project-Leila chose Supabase Edge Functions + PostgREST + GoTrue + Realtime as a unified backend. v2 has explicitly chosen FastAPI for type-safe Python with custom AI orchestration ([ADR-001](001-fastapi-nextjs-architecture.md)) and Clerk for auth ([ADR-003](003-clerk-authentication.md)). Switching to Supabase is a from-scratch backend rewrite, not a hosting choice.

4. **Fly.io.** Reasonable alternative; rejected for now because v1 already runs on Render and the team has operational familiarity with Render's failure modes, dashboard, and pricing. Reduces the surface area of "new things to learn at the same time." Revisit if Render-specific limits (build minutes, regional availability, plan ceilings) bite during the pilot.

5. **AWS (ECS + RDS + ElastiCache + S3) or GCP (Cloud Run + Cloud SQL + Memorystore + GCS).** Rejected for the pilot. The operational complexity dwarfs the pilot's scope. If v2 production needs HIPAA-eligible managed services with a BAA at scale, AWS HealthLake-adjacent or a partner like Datica is the more honest path — but that's a real-prod decision, not a pilot-env decision.

6. **Cloudflare Pages instead of Vercel for Next.js.** Reasonable; rejected because Vercel's per-PR preview-deploys + Next.js-native runtime are tighter integrations than Cloudflare Pages' Next.js support today. Revisit if Vercel pricing becomes an issue.

7. **Render persistent disk instead of R2 for media.** Rejected — v1 explicitly suffered from this pattern (cron containers can't see the disk, requiring the bearer-token-protected `/ops/disk-check/` curl-shim). Object storage is the correct primitive for stateless container deployments and gives us cross-region replication for free if R2 plans permit.

## Consequences

### Positive

- A two-person team gets a shared environment immediately. Webhooks have a stable URL.
- The pilot exercises the same code path (FastAPI + Postgres + Redis, RLS-enforced) that v2 production will use, just on cloud infra.
- Resend + Sentry-with-PHI-scrubber + R2 all close known gaps from v1 (no SendGrid lock-in, no "implement the scrubber later," no persistent-disk pattern).
- The deploy pipeline (#295) gets a real target to deploy to, not just a Mac Mini that's offline when the deployer is on a plane.
- Adopting Project-Leila's git-crypt secrets pattern means adding a collaborator's secret access is a GPG-key exchange, not console permission management.
- v1's Mac-Mini Tailscale pattern is preserved for the developer's own workstation but is no longer the deployment target.

### Negative

- Real cost. Render `starter` web + `Basic 1GB` Postgres + `starter` Redis + Vercel Pro (eventually) + R2 storage + Resend + Sentry — initial pilot is ~$50-100/month, scaling with usage and HIPAA tiers. ADR-005's "zero hosting cost" no longer holds.
- More moving parts than a single-machine Docker Compose. Render outage, Vercel outage, R2 outage, Resend outage, Clerk outage are now distinct failure modes the team has to reason about. Mitigated by all five being market-standard providers with public status pages.
- Provider lock-in surface area widens. R2's S3-compatible API minimizes object-storage lock-in; Resend / Sentry / Clerk are direct vendor relationships. We accept this for the pilot — the abstractions to swap providers can be added later if a real switch becomes likely.
- The team has to operate cloud infrastructure for the first time. This is the *intended* outcome — exercising the muscle pre-PHI — but it does mean things will break in ways the Mac-Mini-only world wouldn't have.

### Risks

- **Real PHI accidentally lands in the pilot.** Mitigation: the pilot env's seed flow is explicitly the only data-loading path; CONTRIBUTING.md makes "do not point the pilot at v1 backups or real customer data" a hard rule; Sentry PHI scrubber is implemented before the pilot serves any traffic so even an accidental data leak doesn't escape into error tracking.
- **Cost creep.** Render and Vercel both have free tiers that lapse. Mitigation: monthly cost review; the fallback to Mac Mini self-hosting remains documented in case the pilot's economics shift.
- **A pilot-only behavior gets baked into "production" assumptions.** Example: relying on Vercel preview-deploy URLs as a stable surface, or hard-coding `staging.<host>` in seeded data. Mitigation: env-var-driven URLs everywhere, and a cutover checklist when graduating staging to a real-prod environment.
- **Render-specific dependencies.** v1 already uses Render-specific patterns (`fromDatabase`, `preDeployCommand`, native cron); reusing them in v2 deepens the lock-in. Mitigation: keep `render.yaml` thin and document any Render-specific behavior in a `deployment/` README so a future Fly/AWS migration has a clear surface to translate.
- **Self-hosted Mac Mini runner becomes a single point of failure.** If we adopt the optional Mac Mini GitHub Actions runner from #295 P2a for sensitive deploys, the Mac being offline blocks deploys. Mitigation: deploys must work from GitHub-hosted runners by default; the Mac Mini is opt-in for `workflow_dispatch` only.

## What this ADR does NOT decide

- **Where v2 production (the real-user environment) runs.** That's a separate decision when the pilot is being promoted. The pilot infrastructure is intentionally chosen to make multiple production paths still viable — staying on Render at higher tiers, moving to Mac Mini for HIPAA-on-premises, or moving to AWS HIPAA-eligible managed services.
- **BAA execution.** No BAAs are signed for the pilot. When real PHI is imminent, the BAA work gets its own issue and is gated before the first PHI write.
- **Status page / out-of-band dashboard.** v1 hosts a static status dashboard on GitHub Pages; Project-Leila has none. v2 pilot will not have one. Revisit when there are real users who need reassurance during outages.
- **On-call / pager wiring.** v1's `EMERGENCY_PROCEDURES.md` has `[TBD]` placeholders. v2 pilot inherits the same gap intentionally — paging matters when there are users to page on behalf of.
- **Cron job inventory.** v1 has six cron jobs (weekly health email, 15-min shift reminders, daily verification-log cleanup, daily metrics snapshot, daily disk-utilization probe, 2 AM migrate). v2 pilot starts with only the migrate safety-net; product crons are added per-feature as those features land.
- **Custom domain.** `staging.<host>` is the placeholder; the actual domain is a #294 sub-decision.

## Reversal cost / when to revisit

This ADR is **moderately expensive to reverse**. The platform-level commitment (Render + Vercel + R2 + Resend + Sentry) is large enough that switching mid-pilot would mean rebuilding the deploy pipeline, re-issuing secrets, and re-pointing DNS — perhaps a week of work. The application-level patterns (env-var-driven URLs, S3-compatible object client, Clerk-mediated auth) are designed to keep that switching cost down.

Revisit this ADR when:

- The pilot is being promoted to handle real PHI (mandatory new ADR for the production environment).
- Costs exceed ~$300/month with no usage that justifies it.
- Render, Vercel, or any other listed provider undergoes a material change that affects HIPAA-eligibility, pricing tier structure, or regional availability.
- The cutover plan from v1 changes shape in a way that requires v2 production to live somewhere specific (e.g., on the same network as v1 for shadow-traffic).
- A second contributor's productivity is being harmed by Render / Vercel limitations (free-tier ceilings, build minutes, regional latency).
