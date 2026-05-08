# PHI Audit — Pre-Crawl (Partial: caregiver re-crawl)

**Date:** 2026-05-08
**Scope:** Partial re-crawl of caregiver persona only (13 routes × 2 viewports = 26 WebPs)
**Tracking:** PR 4 of [#184](https://github.com/suniljames/COREcare-v2/issues/184)
**Auditor:** automated agent + fixture-level verification
**Fixture sha256:** `03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92` (UNCHANGED from original Phase 2D crawl)
**v1 commit:** `9738412a6e41064203fc253d9dd2a5c6a9c2e231` (UNCHANGED)

---

## Why this audit exists

The original Phase 2D crawl (2026-05-07) performed a fixture-level PHI audit covering all personas, including caregiver. That audit stands.

**This partial re-crawl re-captures the caregiver persona against the same fixture sha and same v1 commit.** The data substance is identical. What changed at crawl time: the fixture's `CaregiverProfile.onboarding_completed_at` and `profile_completed_at` were stamped before the re-crawl so the fixture caregiver could traverse routes beyond `/caregiver/onboarding/` (the original crawl captured 13 redirect targets because the fixture user's onboarding gate was unsatisfied, leaving most caregiver routes documented as the onboarding wizard rather than the real screens).

The PHI exposure surface is therefore the same as the original audit's caregiver coverage — but the captured pages are now the real persona-context UI (dashboard, schedule, profile, expenses, earnings, reports) rather than the redirect target. This audit re-affirms the caregiver surface against the actual rendered content.

The two download routes (`/caregiver/weekly/csv/`, `/caregiver/weekly/pdf/`) are not re-crawled — Playwright treats them as downloads and the original capture (a redirect target) is preserved. The corresponding caption files note this explicitly.

## Methodology

Inherits the methodology of [`PHI-AUDIT-PRECRAWL-2026-05-07.md`](PHI-AUDIT-PRECRAWL-2026-05-07.md): fixture-level guarantees in lieu of a full 25-image manual spike.

**Additional verification for this re-crawl:**

1. **Fixture sha256 verified before re-crawl** — operator confirmed `shasum -a 256 fixtures/v2_catalog_snapshot.json` matches `RUN-MANIFEST.md`'s recorded value. No fixture drift.
2. **CaregiverProfile state mutation scope** — only `onboarding_completed_at` and `profile_completed_at` were stamped; no PHI fields were added or modified. The mutation was applied to the fixture's caregiver row in the running SQLite DB and was NOT committed back to the source fixture (the snapshot file remains untouched).
3. **Outbound integrations explicitly disabled** during the re-crawl run — `.env` set `TWILIO_DISABLED=1`, `SENDGRID_DISABLED=1`, `STRIPE_DISABLED=1`, `QUICKBOOKS_DISABLED=1`. v1 process started with `unset SENDGRID_API_KEY EMAIL_HOST_PASSWORD QUICKBOOKS_CLIENT_ID QUICKBOOKS_CLIENT_SECRET SENTRY_DSN` per the bring-up runbook.
4. **Crawler `intercepted-non-GET` discipline** — same crawler binary as Phase 2D; no destructive interactions exercised.

## Verification — programmatic

### Fixture content (re-confirmed)

The fixture has not been modified on disk. The original audit's fixture-content scan stands.

### Page-render content (sample-level)

The 26 re-crawled WebPs were spot-checked by direct visual inspection against the 11 PHI categories from `PHI-CHECKLIST.md`:
- Dashboard / schedule / shift-offers / clock — show `[CLIENT_NAME]_001` and `[REDACTED]` placeholders for client name and address; `[ADDRESS]` placeholder visible. No real-name patterns observed.
- Profile — shows `[CAREGIVER_NAME]_001` first name + `[REDACTED]` last name; placeholder vocabulary intact.
- Client profile (`/caregiver/clients/<int>/`) — shows `[CLIENT_NAME]_001`'s home, address `[ADDRESS], [REDACTED], CA [REDACTED]`, no care plan, no emergency contact (empty states).
- Expense submit / list — empty fixture state ("No expenses found", "Submit your first expense").
- Earnings / weekly summary — empty fixture state ("No shifts" / "No visits recorded").
- Reports list / new — empty fixture state ("No reports yet"); report builder form has no PHI surfaces.

**No real-name patterns observed.** No PHI placeholder values appear in any caption body (verified by `bash scripts/check-v1-caption-phi.sh`).

## Risk-acknowledged carryover

The risk noted in `PHI-AUDIT-PRECRAWL-2026-05-07.md` carries forward: a future PR introducing real fixture data or a v1 template change leaking outside fixture bounds would not be caught by fixture-level guarantees alone. Operator follow-up to run a full manual 11-category spike still applies before the next non-partial catalog refresh.

## Result

**PASS.** No PHI exposure surfaces detected in the re-crawled caregiver captures. Fixture-level guarantees + sample-level visual inspection both clean. Audit re-affirms the caregiver persona's PHI hygiene against the real persona-context UI.
