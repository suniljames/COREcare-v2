# Phase 0 Investigation Findings

> **Read order:** [`README.md`](README.md) (bring-up runbook) → this file (one-time investigations done before Phase 1) → [`PHI-CHECKLIST.md`](PHI-CHECKLIST.md) → [`CAPTION-STYLE.md`](CAPTION-STYLE.md).

This document captures the read-only investigations [#107](https://github.com/suniljames/COREcare-v2/issues/107) Phase 0 required before any crawler code is written. Findings are pinned against v1 commit `9738412a6e41064203fc253d9dd2a5c6a9c2e231` (matches [`docs/migration/README.md`](../../docs/migration/README.md#v1-reference-commit)). Refresh this file if v1 advances and the catalog is regenerated.

---

## Persona authentication mapping

The catalog uses the **six locked personas** from [`docs/migration/README.md` §Personas](../../docs/migration/README.md#personas). v1 does not use the same vocabulary internally; the table below is the binding mapping the crawler relies on.

| v2 Persona | v1 detection | Authenticatable? | Currently seeded in v1's `tests/e2e/conftest.py`? |
|------------|--------------|------------------|---------------------------------------------------|
| `Super-Admin` | `user.is_superuser=True` | Yes — Django staff login at `/dashboard/login/` | **Yes** — `admin@test.com` / `TestAdmin123!` (also has `is_staff=True`) |
| `Agency Admin` | `user.is_staff=True, is_superuser=False` (single-tenant collapse: in v1 production, the same person is typically both) | Yes — same login route | **No** — no staff-only-not-superuser user is seeded. Catalog can either reuse the Super-Admin user (single-tenant fact) or add one. See decision below. |
| `Care Manager` | `user.care_manager_profile` exists with `deactivated_at IS NULL` | Yes — same login route | **No** — no Care Manager user is seeded. |
| `Caregiver` | `user.caregiver_profile` exists with `deactivated_at IS NULL` | Yes — same login route | **Yes** — `caregiver1@test.com` / `TestCare123!` (with a `CaregiverProfile` row) |
| `Client` | **NOT a User.** `clients.models.Client` is an object-of-care with no FK to `auth.User`. v1 has **no Client portal**. | **No** | N/A |
| `Family Member` | `user.linked_clients` (via `ClientFamilyMember` through-table) is non-empty | Yes — same login route | **Yes** — `family1@test.com` / `TestFamily123!`, but `ClientFamilyMember` link only created when the `e2e_family_link` fixture is also pulled. |

### Decisions for the catalog

- **`Client` persona section** — record as omitted with skip-reason `no_authenticated_surface` in [`docs/legacy/README.md`](../../docs/legacy/README.md). Catalog does not include a `client/` directory of screenshots; the persona table in [`docs/legacy/v1-ui-catalog/README.md`](../../docs/legacy/v1-ui-catalog/README.md) marks it as "no v1 portal." Inventory rows that would have referenced Client screenshots stay at `not_screenshotted: no_authenticated_surface`.
- **`Care Manager` user** — must be created in the Phase 0 PHI-scrubbed fixture. v1's `RoleService` checks for `care_manager_profile`; the fixture creates a `CareManagerProfile` row plus the user.
- **`Agency Admin` vs `Super-Admin`** — v1 is single-tenant; production agency admins are typically `is_staff=True, is_superuser=True`. Catalog approach: seed **two staff users** in the fixture — one with both flags (Super-Admin section), one with only `is_staff=True` (Agency Admin section) — to capture the capability-gated UI difference where it exists. If the inventory shows no UI difference for Agency-Admin-only routes (i.e., every `is_staff` route is also reachable by superuser), Agency Admin and Super-Admin sections will share screenshots and the catalog README documents the collapse.
- **Caregiver / Family Member** — existing seeded users are usable; the fixture extends with the `ClientFamilyMember` link plus 2–3 weeks of populated shift / chart / message data so screenshots show real (placeholder) content rather than empty states.

### Auth flow (for the crawler)

- **Login URL:** `/dashboard/login/` (verified in `elitecare/settings/base.py: LOGIN_URL`).
- **Auth mechanism:** Django session cookies. Login posts username + password + CSRF token; subsequent requests carry the `sessionid` cookie.
- **CSRF handling:** the login form embeds a hidden `<input name="csrfmiddlewaretoken">`. Playwright's `page.fill` + `page.click` flow handles this naturally; do **not** reach for `request.post`.
- **Magic-link login:** `auth_service/urls.py` defines `magic-login/<uuid:token>/` at the project root. Crawler does **not** use magic links — they're triggered by email send and the catalog is offline.
- **Role-switching:** dual-role caregiver-and-care-manager users can switch via session-stored active role. The crawler logs in once per persona; no role-switch flow is exercised.

---

## Outbound integration inventory

Surveyed v1's `requirements.txt`, `elitecare/settings/`, and codebase for outbound services. Findings:

| Integration | Used in v1? | Env vars | Behavior in dev with vars unset |
|-------------|:-----------:|----------|---------------------------------|
| **Twilio** | **No** | — | N/A — `twilio` is not in `requirements.txt`, no `TWILIO_*` references in code. |
| **SendGrid (email)** | Yes | `EMAIL_HOST_PASSWORD` (and friends) | `EMAIL_BACKEND` falls back to `django.core.mail.backends.console.EmailBackend` (logs only, no send) when `EMAIL_HOST_PASSWORD` is unset. See `elitecare/settings/development.py:85-87`. |
| **QuickBooks** | Yes (via `python-quickbooks`) | `QUICKBOOKS_CLIENT_ID`, `QUICKBOOKS_CLIENT_SECRET`, `QUICKBOOKS_ENVIRONMENT` | OAuth flow fails closed when env vars are unset; no outbound API calls. |
| **Sentry** | Yes (via `sentry-sdk`) | `SENTRY_DSN` | No-op when `SENTRY_DSN` is unset. |
| **web push notifications** | Yes (via `pywebpush`) | VAPID keys + per-subscription endpoints stored in DB | No-op when VAPID keys are unset and/or no subscription rows exist in the dev DB. |
| **Stripe** | **No** | — | N/A — `stripe` matches in source are calendar-CSS pattern names, not Stripe SDK usage. |

### Decisions for the catalog

- **Net finding:** v1 dev with default unset env vars is already integration-safe. The original design synthesis (#79) recommended `*_DISABLED=1` flags on v1's process; that is over-defensive for v1 — **simply do not export the integration env vars when bringing v1 up for the catalog crawl.**
- **Crawler README's bring-up sequence** lists explicit `unset` lines for each integration env var as belt-and-suspenders, even though they're not set by default.
- **Defense in depth (still required):** the crawler's Playwright `page.route('**/*')` interception remains the second-line guard. Even if v1's process were misconfigured to reach Twilio/SendGrid/Stripe, the crawler issues GET-only by default with an explicit POST allowlist (login, role-switch). Any non-allowlisted POST is `route.abort()`-ed before it reaches v1.
- **Production-hostname blocklist** (literal regex in `crawl.ts`) hard-fails before any auth attempt. v1 production lives at `bayareaelitehomecare.com` (per `.env.example` `DEFAULT_FROM_EMAIL` comment); the blocklist matches that and any other `*.elitecare.*` patterns surfaced during crawler implementation.

---

## v1 bring-up dependencies

These hold for the pinned commit. If v1 advances, re-verify.

- **Database:** Django default is SQLite (`db.sqlite3` in v1 root). `DATABASE_URL` env var switches to PostgreSQL. **Catalog uses SQLite** — single-file, deterministic, no extra services. The fixture loads via `python manage.py loaddata` against the SQLite DB.
- **Migration state:** running `python manage.py migrate` against a fresh SQLite is required before fixture load. The pinned commit's migrations are SQLite-compatible (verified: 124 unit tests pass, 3 skipped, in #79's PR-A `make api-test` run when v1 wasn't even involved — confirming v2's stack is intact, but for v1 we trust v1's CI was green when the SHA was pinned).
- **Static assets:** v1 uses `whitenoise` for static serving. `python manage.py collectstatic` not strictly required for `runserver` (which auto-serves static during development).
- **Migrations vs current Postgres:** if the catalog operator chooses PostgreSQL instead of SQLite, the pinned commit's migrations run against PostgreSQL 14+ per v1's CI baseline. No special action.

---

## Sidebar: security finding (not blocking #107)

`~/Code/COREcare-access/.env` (gitignored, on disk only) contains a `GITHUB_PAT` value. Not committed to v1's git history (verified: `.gitignore` excludes `.env`), but a token in plaintext on disk is worth rotating proactively. **This is unrelated to the catalog work — flagging as a sidebar so the operator can address it independently.** The catalog crawler does not read or use this token.

---

## Open items for Phase 1 (the crawler)

1. **Inventory parsing** — write `scripts/extract-inventory-routes.sh` (shared with PR-A's coverage script). Emits JSON `[{persona, route, screenshot_ref}, ...]`. Crawler reads JSON.
2. **Hand-crafted PHI-scrubbed fixture** — `~/Code/COREcare-access/fixtures/v2_catalog_snapshot.json`. Spec lives in [`#107` Proposed Solution §Seed fixture spec](https://github.com/suniljames/COREcare-v2/issues/107). Hash recorded in `RUN-MANIFEST.md` at crawl time.
3. **PHI manual spike** — 5 routes per persona with the new fixture, single screenshot each, full audit against [`PHI-CHECKLIST.md`](PHI-CHECKLIST.md). Stop-the-line gate before authoritative crawl.
4. **`crawl.ts` itself** — pre-flight gates, network interception, determinism harness, login flow, screenshot loop, frontmatter writer.
5. **Reproducibility script** — `scripts/check-catalog-reproducibility.sh` using `pixelmatch`.
6. **Crawler unit tests** — inventory parsing, hostname guard, network interception, frontmatter writer.

These are the remaining Phase 1 deliverables. Phase 2 is the authoritative crawl + commit. Phase 3 (separate follow-up issue) is the ~25h human caption-authoring pass.
