# PHI Audit — Pre-Crawl (Partial: family-member re-crawl)

**Date:** 2026-05-08
**Scope:** Partial re-crawl of family-member persona only (4 routes × 2 viewports = 8 WebPs)
**Tracking:** [#204](https://github.com/suniljames/COREcare-v2/issues/204), amends PR 3 of [#184](https://github.com/suniljames/COREcare-v2/issues/184)
**Auditor:** automated agent + fixture-level verification
**Fixture sha256:** `03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92` (UNCHANGED from original Phase 2D crawl)
**v1 commit:** `9738412a6e41064203fc253d9dd2a5c6a9c2e231` (UNCHANGED)

---

## Why this audit exists

The original Phase 2D crawl (2026-05-07) performed a fixture-level PHI audit covering all personas, including family-member. That audit stands.

**This partial re-crawl re-captures the same family-member routes against the same fixture sha and same v1 commit.** The data substance is identical. What changed: the inventory's documented routes (`/family/...` → `/dashboard/family/...`), which the crawler now hits correctly. The PHI exposure surface is therefore the same as the original audit's family-member coverage — but the captured pages are the real UI rather than 404s, so this audit re-affirms the family-member surface against the actual rendered content.

## Methodology

Inherits the methodology of [`PHI-AUDIT-PRECRAWL-2026-05-07.md`](PHI-AUDIT-PRECRAWL-2026-05-07.md): fixture-level guarantees in lieu of a 25-image manual spike.

**Additional verification for this re-crawl:**

1. **Fixture sha256 verified before re-crawl** — operator confirmed `shasum -a 256 fixtures/v2_catalog_snapshot.json` matches `RUN-MANIFEST.md`'s recorded value. No fixture drift.
2. **Outbound integrations explicitly disabled** during the re-crawl run — `.env` set `TWILIO_DISABLED=1`, `SENDGRID_DISABLED=1`, `STRIPE_DISABLED=1`, `QUICKBOOKS_DISABLED=1`. v1 process was started with `unset SENDGRID_API_KEY EMAIL_HOST_PASSWORD QUICKBOOKS_CLIENT_ID QUICKBOOKS_CLIENT_SECRET SENTRY_DSN` per the bring-up runbook.
3. **Crawler `intercepted-non-GET` discipline** — same crawler binary as Phase 2D; no destructive interactions exercised.

## Verification — programmatic

### Fixture content (re-confirmed)

The fixture has not been modified. The original audit's fixture-content scan stands.

### Page-render content (sample-level)

The 4 re-crawled WebPs were spot-checked by direct visual inspection:
- `family-member/001-dashboard.{desktop,mobile}.webp` — shows `[CLIENT_NAME]_001 [REDACTED]` linked-client card; PHI placeholder vocabulary intact.
- `family-member/002-client.{desktop,mobile}.webp` — shows `[CLIENT_NAME]_001`, `[CAREGIVER_NAME]_001`, `[REDACTED]`, `[NOTE_TEXT]` across calendar, messages, care team. PHI placeholder vocabulary intact across all surfaces.
- `family-member/003-billing-pdf.{desktop,mobile}.webp` — plain-text "No billing data available for this period." (no PHI surface).
- `family-member/004-health-report.{desktop,mobile}.webp` — plain-text "There isn't enough recent health data..." (no PHI surface).

**No real-name patterns observed.** No PHI placeholder values appear in any caption body (verified by `bash scripts/check-v1-caption-phi.sh`).

## Risk-acknowledged carryover

The risk noted in `PHI-AUDIT-PRECRAWL-2026-05-07.md` carries forward: a future PR introducing real fixture data or a v1 template change leaking outside fixture bounds would not be caught by fixture-level guarantees alone. Operator follow-up to run a full manual 11-category spike still applies before the next non-partial catalog refresh.

## Result

**PASS.** No PHI exposure surfaces detected in the re-crawled family-member captures. Fixture-level guarantees + sample-level visual inspection both clean. Audit re-affirms the family-member persona's PHI hygiene against the corrected inventory paths.
