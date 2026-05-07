# Phase 2 Runbook

> **Read order:** [`README.md`](README.md) (bring-up) → [`INVESTIGATIONS.md`](INVESTIGATIONS.md) → [`PHI-CHECKLIST.md`](PHI-CHECKLIST.md) → this file → [`CAPTION-STYLE.md`](CAPTION-STYLE.md).

This runbook is the operator's single-page document for Phase 2 of [#107](https://github.com/suniljames/COREcare-v2/issues/107). Each step has a verification step ("how do I know it worked") and a remediation step ("what if it didn't"). Phase 2A — bug closure — is **already merged**; this runbook drives Phase 2B onwards.

If a step fails: STOP. Do not skip. Fix the failing step or push back on the design — operating on bad inputs is worse than not operating at all.

---

## Summary

Estimated wall-clock: **~4 days** (most of it is the user-owned fixture authoring in 2B).

| Sub-phase | What | Wall-clock | Owner |
|-----------|------|-----------:|-------|
| 2B | Author PHI-scrubbed Django fixture | ~1 day | user |
| 2C | Manual PHI spike (stop-the-line gate) | ~2 hours | user |
| 2D | Authoritative crawl | ~30 min | user (passive) |
| 2E | Reproducibility + audits | ~2 hours | user |
| 2F | Index population + cold smoke | ~1 hour | user + 1 reviewer |
| 2G | Commit + PR | ~30 min | user |

---

## Phase 2B — Fixture authoring (~1 day)

Author `~/Code/COREcare-access/fixtures/v2_catalog_snapshot.json` per the spec table in [#107 Proposed Solution §Seed fixture spec](https://github.com/suniljames/COREcare-v2/issues/107).

### Steps

1. `cd ~/Code/COREcare-access && git fetch && git checkout 9738412a6e41064203fc253d9dd2a5c6a9c2e231`
2. `python manage.py migrate` against a fresh SQLite DB (`unset DATABASE_URL` first; SQLite is the default per [INVESTIGATIONS.md](INVESTIGATIONS.md)).
3. Author `fixtures/v2_catalog_snapshot.json` in Django `loaddata` JSON format. Required entities (per #107 spec):
   - `User` × 2 staff (Super-Admin with `is_superuser=True`, Agency Admin with `is_staff=True` only)
   - `User` + `CareManagerProfile` × 1
   - `User` + `CaregiverProfile` × 3 (active+valid / expiring-soon / expired)
   - `User` + `ClientFamilyMember` × 1
   - `Agency` × 2
   - `Client` × 6 (3 per agency) — names from `[CLIENT_NAME]_001` etc.
   - Past shifts: 14 days × ~3 per caregiver
   - Future shifts: 14 days × ~3 per caregiver
   - Chart notes × ~10 (PHI placeholder vocabulary, no Faker)
   - Care plans: 1 per client
   - Expense submissions × ~5
4. Validate: `python manage.py loaddata fixtures/v2_catalog_snapshot.json` exits 0.
5. Hash: `shasum -a 256 fixtures/v2_catalog_snapshot.json | tee fixtures/v2_catalog_snapshot.sha256`.
6. Record path + hash in `tools/v1-screenshot-catalog/INVESTIGATIONS.md` under a new "Fixture snapshot" section.

### Verification

- `python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.count())"` → 8 users (2 staff + 1 care manager + 3 caregivers + 1 family + maybe a default admin).
- `python manage.py shell -c "from clients.models import Client; print(Client.objects.count())"` → 6.
- Open `http://localhost:8000/dashboard/login/` → log in as each persona. Each should land on a populated dashboard, not an empty state.

### Remediation

- If migrations fail against pinned commit, check Python version + Django version in `requirements.txt`; the pinned commit's CI baseline holds.
- If fixture loading fails on FK constraints, ensure entities are listed in dependency order in the JSON (User before CaregiverProfile, etc.).
- **Faker output is unacceptable.** All field values come from the locked PHI placeholder set in `docs/migration/README.md`.

---

## Phase 2C — Manual PHI spike (~2 hours, stop-the-line gate)

5 routes per persona × 5 personas = 25 manual single-image samples, audited against [`PHI-CHECKLIST.md`](PHI-CHECKLIST.md) (11 categories, yes/no/N/A).

### Steps

1. v1 running with the fixture loaded (see Phase 2D step 1 below for the bring-up sequence).
2. For each persona, log in via browser at `http://localhost:8000/dashboard/login/`.
3. Pick 5 routes per persona — **must include** any client-detail, chart-note, or billing/financial view (per Data Engineer Phase 2 minimum-coverage rule).
4. Take a single browser screenshot of each route.
5. For each image: walk the 11 categories in `PHI-CHECKLIST.md`; record yes/no/N/A + free-text note.
6. Record results in `tools/v1-screenshot-catalog/PHI-AUDIT-PRECRAWL-<YYYY-MM-DD>.md`. Format: 25-row × 11-column table.

### Stop-the-line gate

If **any** category is `no` (PHI present that shouldn't be):

1. STOP.
2. Identify which fixture field produced the leak.
3. Fix `fixtures/v2_catalog_snapshot.json`. Re-load. Re-hash.
4. Re-spike from step 2.

Do not proceed to Phase 2D until **every** category is yes/N/A.

---

## Phase 2D — Authoritative crawl (~30 min)

### Steps

1. **Bring up v1** (in a dedicated terminal):
   ```bash
   cd ~/Code/COREcare-access
   git checkout 9738412a6e41064203fc253d9dd2a5c6a9c2e231
   unset DATABASE_URL
   # Outbound integrations are off by default per INVESTIGATIONS.md;
   # we still set explicit unsets as belt-and-suspenders.
   unset SENDGRID_API_KEY EMAIL_HOST_PASSWORD QUICKBOOKS_CLIENT_ID QUICKBOOKS_CLIENT_SECRET SENTRY_DSN
   python manage.py loaddata fixtures/v2_catalog_snapshot.json  # idempotent on a fresh DB
   python manage.py runserver 0.0.0.0:8000
   ```

2. **In the v2 worktree**, fill in `tools/v1-screenshot-catalog/.env` (gitignored):
   ```bash
   cd tools/v1-screenshot-catalog
   cp .env.example .env
   # Edit .env:
   #   V1_BASE_URL=http://localhost:8000
   #   V1_FIXTURE_SHA256=<contents of ~/Code/COREcare-access/fixtures/v2_catalog_snapshot.sha256>
   #   V1_SUPER_ADMIN_USERNAME=superadmin@catalog.local  (etc.)
   ```

3. **Run pre-flight + crawl**:
   ```bash
   pnpm install   # if not already
   pnpm exec playwright install chromium  # if not already
   pnpm crawl --output-dir ../../docs/legacy/v1-ui-catalog/
   ```

   Expected output:
   - 5 pre-flight gates pass within ~5 seconds
   - Per-persona login + per-route capture log lines stream to stdout AND `<output-dir>/crawl.log`
   - Final `run.complete` event with `routes_visited` ≈ 134, `routes_errored: 0`
   - `RUN-MANIFEST.md`, `crawl.log`, `intercepted-non-GET.log` written to `<output-dir>`

### Verification

- `cat ../../docs/legacy/v1-ui-catalog/RUN-MANIFEST.md` shows the v1 commit, fixture sha256, operator, host, playwright_version, and counts.
- `tail ../../docs/legacy/v1-ui-catalog/crawl.log` ends with a `run.complete` event.
- `wc -l ../../docs/legacy/v1-ui-catalog/intercepted-non-GET.log` reports a small number (typically <50: Sentry beacons, web-push posts).
- **Inspect intercepted-non-GET.log:** every entry must have `origin: page-script`. **If any has `origin: navigation`** (would mean the crawler clicked a destructive button), STOP and fix the crawler before merging.

### Remediation

- If a single persona's login fails, the run continues for other personas (logged as `persona.login` event with `status: failed`). Investigate fixture user credentials match `.env` exactly.
- If the crawl aborts mid-persona, use `pnpm crawl --output-dir ... --resume-from <persona-slug>` to skip already-completed personas.
- If Gate 4 fails (output dir not writable), `mkdir -p` the dir first.

---

## Phase 2E — Reproducibility + audits (~2 hours)

### Steps

1. **Reproducibility two-run**:
   ```bash
   mkdir -p /tmp/catalog-rerun
   pnpm crawl --output-dir /tmp/catalog-rerun
   # then from repo root:
   bash scripts/check-catalog-reproducibility.sh \
     docs/legacy/v1-ui-catalog/ \
     /tmp/catalog-rerun/ \
     --output-dir docs/legacy/v1-ui-catalog/reproducibility-report
   ```
   Expected: every (route, viewport) pair within 0.5% pixel diff. Fixture-hash gate passes.

   **STOP-and-root-cause** if any image exceeds threshold OR fixture hashes diverge between the two runs. Common causes: stale Playwright Chromium build, fixture edited between runs (re-hash and re-load), forgotten determinism harness override.

2. **Coverage check**:
   ```bash
   bash scripts/check-v1-catalog-coverage.sh
   ```
   Expected: ≥95% coverage. **Update** `docs/migration/v1-pages-inventory.md` rows: replace `not_screenshotted: pending #79` with the canonical_id (e.g., `agency-admin/001-dashboard`) for every captured row, or with a locked skip-reason value (e.g., `no_authenticated_surface`, `auth_redirect`) for genuinely-skipped rows. Re-run the coverage script until OK.

3. **Post-crawl PHI 10% sample audit**:
   ```bash
   # Use Python's random.seed(42) to pick the sample; cap 100 images.
   ```
   Audit each against `PHI-CHECKLIST.md`. Commit `tools/v1-screenshot-catalog/PHI-AUDIT-POSTCRAWL-<YYYY-MM-DD>.md` (table format).

4. **Secret scan** over the diff:
   ```bash
   gitleaks detect --source . --redact --no-git --log-opts="$(git merge-base HEAD origin/main)..HEAD"
   # Plus a manual grep over caption files:
   grep -rE '(@|Bearer|password|token|secret)' docs/legacy/v1-ui-catalog/ --include='*.md'
   ```
   Both must report zero hits.

5. **Optional empty-state variants** (≤15 routes): identify routes where the empty state is meaningful UX, drop a temporary fixture tweak, re-run with `pnpm crawl --output-dir .../empty-variants --only-routes <id1>,<id2>`. Caption with `seed_state: empty`. Move WebPs into the main catalog dir alongside the populated variants (`<NNN>-<route>.empty.{desktop,mobile}.webp`).

### Verification

- `cat docs/legacy/v1-ui-catalog/reproducibility-report/report.md` summary line shows `Exceeded / failed: 0`.
- `bash scripts/check-v1-catalog-coverage.sh` exits 0; "OK: catalog coverage holds" printed.
- `tools/v1-screenshot-catalog/PHI-AUDIT-POSTCRAWL-*.md` shows zero `no` verdicts.
- gitleaks + manual grep both empty.

### Remediation

- Reproducibility outliers: re-run `pnpm crawl` once more — sometimes a transient v1 server hiccup creates a one-off diff. If diffs persist, examine `reproducibility-report/<canonical_id>.<viewport>.diff.png` to identify the changed region; root-cause via the determinism harness.
- Coverage gaps: every `not_screenshotted: pending #79` row must be updated. Use a locked skip-reason value or a canonical_id; the soft-warn surfaces drift.
- PHI hits: STOP. Fix the fixture, re-spike (Phase 2C), re-crawl (Phase 2D).

---

## Phase 2F — Index population + cold smoke (~1 hour)

### Steps

1. **Update `docs/legacy/v1-ui-catalog/README.md`**:
   - Persona-section table: route counts per persona, lead viewports (Caregiver + Family Member: mobile-first listing).
   - Generation-provenance section: paragraph (not key-value) referencing v1 commit, fixture hash, RUN-MANIFEST.md, RUN date, crawler git ref.
   - Mirror the boundary statement from `tools/v1-screenshot-catalog/README.md` opening line.
2. **Update `docs/legacy/README.md`**:
   - Pinned references section: v1 SHA, fixture hash, generation date.
   - Skip-reason taxonomy already includes `no_authenticated_surface` (Phase 2A.5; no edit needed).
3. **Run T7 cold smoke** with one v2 contributor (or self-with-disclosure):
   - Open `docs/legacy/v1-ui-catalog/README.md` from a fresh shell. No prior v1 access required.
   - Find within 60 seconds each:
     (a) the Agency Admin shift detail page,
     (b) the Caregiver clock-in flow,
     (c) the Family Member visit-notes view.
   - Record times in PR description.
4. For any case >30 seconds: edit the index README to add the prose that was missing.

### Verification

- `docs/legacy/v1-ui-catalog/README.md` no longer says "pending #107" anywhere.
- T7 results recorded in PR description.

---

## Phase 2G — Commit + PR (~30 min)

### Steps

1. **LFS size-check**:
   ```bash
   git lfs ls-files | wc -l   # expected 200–800 files
   du -sh docs/legacy/v1-ui-catalog/  # expected 80–300 MB
   ```
   If size >500 MB, investigate (q=80 sharp config not honored, or some pages absurdly large). If file count <100 or >1000, investigate.

2. **File the Phase 3 caption-authoring issue** using the locked draft in [#107 Appendix A](https://github.com/suniljames/COREcare-v2/issues/107).

3. **File the LFS-bandwidth-monitoring follow-up issue** (1-month-after-merge SRE task). Reference ADR-010 Alternative B as the escape hatch.

4. **Commit** using the locked format in [#107 Appendix B](https://github.com/suniljames/COREcare-v2/issues/107). Single atomic commit; inventory + catalog ship together.

5. **Push** to `feat/107-phase-2-*` branch:
   ```bash
   git push -u origin feat/107-phase-2-authoritative-crawl
   ```

6. **Open the PR** using the locked 13-line gate-list checklist in [#107 Appendix C](https://github.com/suniljames/COREcare-v2/issues/107). Reviewer signs off line-by-line; no checkmark = no merge.

### Verification

- `git lfs ls-files` count matches RUN-MANIFEST.md count.
- PR description contains every gate from Appendix C, with evidence per line.
- Phase 3 issue exists, linked from the catalog README, linked from caption TODO markers.

### Remediation

- If LFS push hits bandwidth limits mid-push: don't `git lfs prune`; check GitHub Settings → Billing → Git LFS for the v2 repo. May need to wait for the next billing cycle or upgrade.
- If the PHI-audit-artifacts CI gate fails: confirm both `PHI-AUDIT-PRECRAWL-*.md` and `PHI-AUDIT-POSTCRAWL-*.md` were committed in the same PR.
