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
3. Pick 5 routes per persona — **must include** any client-detail, chart-note, or billing/financial view (per the data-engineer review's minimum-coverage rule on #107).
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

   **STOP-and-root-cause** if any image exceeds threshold OR fixture hashes diverge between the two runs. Common causes: stale Playwright/Chromium build, fixture edited between runs (re-hash and re-load), forgotten determinism harness override.

2. **Coverage check**:
   ```bash
   bash scripts/check-v1-catalog-coverage.sh
   ```
   Expected: ≥95% coverage. **Update** `docs/migration/v1-pages-inventory.md` rows: replace `not_screenshotted: pending #79` with the canonical_id (e.g., `agency-admin/001-dashboard`) for every captured row, or with a locked skip-reason value (e.g., `no_authenticated_surface`, `auth_redirect`) for genuinely-skipped rows. Re-run the coverage script until OK.

3. **Post-crawl PHI 10% sample audit**:
   ```bash
   # Sample via python's random.seed(42); cap at 100 images.
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

## Phase 2H — Care Manager fixture extension + targeted re-crawl (#237, ~2 hours)

Closes the Care Manager catalog gap: 3 inventory rows whose `screenshot_ref` was `not_screenshotted: no_seed_data` because the test Care Manager account had no assigned `Client` and no submitted `Expense`. Phase 2D's fixture optimised cross-persona coverage of read-heavy surfaces and under-seeded CM-specific relational state.

### Pre-flight (v1 side)

1. `cd ~/Code/COREcare-access && git status` — clean tree, on commit `9738412a6e41064203fc253d9dd2a5c6a9c2e231`.
2. Read `care_manager/services.py` for `CareManagerService.get_assigned_client_ids` and `care_manager/models.py` (or wherever `CareManagerProfile` is defined) to confirm the `CareManagerProfile`↔`Client` linkage model. Common shapes: an M2M field on `CareManagerProfile`, an explicit through-table (`CareManagerAssignment`), or a FK on `Client`. The fixture row format follows the linkage model exactly — wrong model = `Http404` persists.
3. Inspect `expenses/models.py` `Expense` and `ExpenseReceipt` for `full_clean()` validation rules, max_length on text fields, custom `save()` hooks, and `post_save` signals. Loaddata fires signals unless they short-circuit on `kwargs.get("raw")` — confirm no signal will hit network during loaddata.
4. Confirm env-var hygiene per Phase 2E (line 144): `unset DATABASE_URL SENDGRID_API_KEY EMAIL_HOST_PASSWORD QUICKBOOKS_CLIENT_ID QUICKBOOKS_CLIENT_SECRET SENTRY_DSN`. Critical: `EMAIL_HOST_PASSWORD` must be unset so `loaddata`'s shift-assignment signal hits `console.EmailBackend`, not real SMTP.

### Steps

5. Edit `~/Code/COREcare-access/fixtures/v2_catalog_snapshot.json`:
   - **Link** the existing `CareManagerProfile` (test CM) to the existing `Client` (PK 1) via the confirmed mechanism. **Do not** add the Client to any caregiver/shift/chart relationships — minimise cross-persona blast radius.
   - **Enrich** the `Client` row to render rich `cm_client_focus` UI: DNR flag, ≥1 alert flag, `diagnosis = "[DIAGNOSIS]"`, `address = "[ADDRESS]"`, `phone = "[PHONE]"`. Reuse the existing `ClientFamilyMember` link.
   - **Add** 1 `Expense` row: `pk = 1`, `submitter = <test_cm_user_pk>`, `client = 1`, `status = "REJECTED"`, `description = "[NOTE_TEXT]"`, `amount = 9.99` (deliberately non-realistic — document the convention in `INVESTIGATIONS.md`).
   - **Add** 1 `ExpenseReceipt` row: `pk = 1`, `expense = 1`, `original_filename = "[REDACTED].png"`, `image = "<MEDIA-relative-path-to-placeholder.png>"`.
6. Place a synthetic placeholder PNG at `<MEDIA_ROOT>/<image-path>`: ≤2 KB, flat-grey or "RECEIPT [REDACTED]" synthetic, no identifying marks.
7. Re-validate fixture loads cleanly:
   ```bash
   cd ~/Code/COREcare-access
   rm -f db.sqlite3
   DJANGO_SETTINGS_MODULE=elitecare.settings.development ./venv/bin/python manage.py migrate
   DJANGO_SETTINGS_MODULE=elitecare.settings.development ./venv/bin/python manage.py loaddata fixtures/v2_catalog_snapshot.json
   ```
   Exit code 0; reported object count matches the new total in `INVESTIGATIONS.md` Records line.
8. Re-hash fixture: `shasum -a 256 fixtures/v2_catalog_snapshot.json`.
9. Update `tools/v1-screenshot-catalog/INVESTIGATIONS.md` "Fixture snapshot" table:
   - `sha256` row → new hash.
   - `Records` line → updated total (was 20; new total = 20 + linkage + Expense + ExpenseReceipt = 23 if linkage is a single row).
   - Add a `placeholder_blobs` row listing the placeholder PNG path + sha256.
   - Add a paragraph in the table caption describing the linkage model and the `9.99` amount-value convention.
10. Update `tools/v1-screenshot-catalog/.env` (gitignored, operator-side): `V1_FIXTURE_SHA256=<new-hash>`.
11. Smoke-test the 3 routes manually via `runserver`:
    ```bash
    DJANGO_SETTINGS_MODULE=elitecare.settings.development ./venv/bin/python manage.py runserver 0.0.0.0:8000
    # In another shell, log in as test CM in a browser, then:
    curl -I -b cookies.txt http://localhost:8000/care-manager/expenses/1/receipt/1/
    ```
    Expect: `/care-manager/` populated; `/care-manager/client/1/` HTTP 200 (no 404); `/care-manager/expenses/1/edit/` HTTP 200 with REJECTED status visible; receipt route HTTP 200 with `Content-Disposition: attachment`.

### Re-crawl

12. Full re-crawl all 5 personas (single canonical fixture; replace existing CM captures + capture 2 new ones). The receipt route is now skipped via inventory `non_html_response`.
    ```bash
    cd tools/v1-screenshot-catalog
    pnpm crawl --output-dir ../../docs/legacy/v1-ui-catalog/
    ```
13. Verify CM directory contents: `001-care-manager.{desktop,mobile}.webp` (re-captured, populated), `002-client.{desktop,mobile}.webp` (new), `003-expenses.{desktop,mobile}.webp` (re-captured, populated), `004-submit.{desktop,mobile}.webp` (re-captured), `005-edit.{desktop,mobile}.webp` (new). Receipt route produces no files.

### Reproducibility + PHI gates

14. Second crawl to a temp dir, then reproducibility check:
    ```bash
    pnpm crawl --output-dir /tmp/catalog-rerun/
    bash ../../scripts/check-catalog-reproducibility.sh \
      ../../docs/legacy/v1-ui-catalog/ /tmp/catalog-rerun/ \
      --output-dir ../../docs/legacy/v1-ui-catalog/reproducibility-report
    ```
    Pixel diff ≤ 0.5%.
15. Pixel-diff existing AA / CG / FM `.webp` files pre/post (operator: `git diff --stat docs/legacy/v1-ui-catalog/`). Any non-empty image diff → re-PHI-audit those captures.
16. PHI audit on changed CM `.webp` files + new captions per `PHI-CHECKLIST.md`. Author at `tools/v1-screenshot-catalog/PHI-AUDIT-POSTCRAWL-<date>-cm-recrawl.md`. Zero `no` verdicts.

### Captions, inventory, READMEs

17. Rewrite `docs/legacy/v1-ui-catalog/care-manager/001-care-manager.md` body (now populated state — drop the "with assigned clients (not visible at this seed_state)" hedging block).
18. Author `docs/legacy/v1-ui-catalog/care-manager/002-client.md` per `CAPTION-STYLE.md` (cite `cm_client_focus`).
19. Rewrite `docs/legacy/v1-ui-catalog/care-manager/003-expenses.md` body (now lists the new REJECTED expense).
20. Spot-check `004-submit.md`; rewrite only if rendered content actually changed.
21. Author `docs/legacy/v1-ui-catalog/care-manager/005-edit.md` per `CAPTION-STYLE.md` (cite `ExpenseService.resubmit_expense` for REJECTED + `ExpenseService.edit_expense` otherwise).
22. **Do not** author a `006-receipt.md` — receipt route's inventory row is the canonical documentation; no caption file for skipped routes.
23. Update `docs/migration/v1-pages-inventory.md`:
    - Row 380 (`/care-manager/client/<int:pk>/`): `screenshot_ref` → `care-manager/002-client`.
    - Row 383 (`/care-manager/expenses/<int:expense_id>/edit/`): `screenshot_ref` → `care-manager/005-edit`.
    - Row 384 (`/care-manager/expenses/<int:expense_id>/receipt/<int:receipt_id>/`): `screenshot_ref` → `not_screenshotted: non_html_response`.
24. Update `docs/legacy/v1-ui-catalog/README.md`:
    - Persona table Care Manager count `3` → `5`.
    - Per-route index Care Manager subsection: add `care-manager/002-client` and `care-manager/005-edit` bullets in canonical_id-ascending order.
25. Update `docs/legacy/v1-ui-catalog/RUN-MANIFEST.md`: new fixture sha256, generated date, route counts (`captured`, `skipped`, `errored`).

### Verification (release gates)

26. `make scan-v1-docs` passes (hygiene + structure + coverage).
27. `cd tools/v1-screenshot-catalog && pnpm test` — 91 tests pass (existing 79 + 12 added by #237 prep).
28. Reproducibility check ≤ 0.5% pixel diff (step 14).
29. PHI audit zero `no` verdicts (step 16).
30. Sunil PHI sign-off on the new captures.

### Remediation

- If `cm_client_focus` still raises `Http404` after fixture extension: the `CareManagerProfile`↔`Client` linkage model was wrong (step 2). Re-read v1 source; rebuild fixture row.
- If `cm_edit_expense` renders the *edit* form (not *resubmit*): `Expense.status` enum value is wrong. v1's enum is case-sensitive; confirm the literal value (likely `"REJECTED"` but verify).
- If receipt route returns a non-attachment response (e.g., HTTP 200 with `Content-Type: image/png` and inline disposition): the `non_html_response` reclassification may not apply. Inspect v1's `cm_serve_receipt` view for the actual response shape and re-evaluate; possibly the route IS screenshottable as an inline image.
- If pixel-diff against AA / CG / FM captures is non-empty: the new fixture row leaked into other personas' views. Narrow the linkage scope (no caregiver assignment, no shifts on the new client) and re-crawl.
