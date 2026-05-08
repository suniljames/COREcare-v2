# PHI Audit — Pre-Crawl (Phase 2H: Care Manager fixture extension + full re-crawl)

**Date:** 2026-05-08
**Scope:** Full re-crawl of all 5 personas (172 WebPs) against an extended fixture (#237).
**Tracking:** [#237](https://github.com/suniljames/COREcare-v2/issues/237)
**Auditor:** automated agent + fixture-level verification
**Fixture sha256:** `2a23bc538b58780cfe1657cc4d9e227f8eab81b32983bd6fc91e9dd9199e5720` (NEW — extends the prior `03b4148...` snapshot)
**v1 commit:** `9738412a6e41064203fc253d9dd2a5c6a9c2e231` (UNCHANGED)

---

## Why this audit exists

Phase 2H extends the fixture with three new entities to render the Care Manager routes that Phase 2D could not capture: a `CareManagerClientAssignment` row linking the test CM to client pk 1, an `Expense` row (REJECTED status, $9.99, submitted by the CM), and an `ExpenseReceipt` row pointing at a synthetic placeholder PNG. The Client row is also enriched with `dnr=true` and `diagnosis="[DIAGNOSIS]"` so the rich `cm_client_focus` UI surfaces. Finally, `CaregiverProfile.profile_completed_at` and `onboarding_completed_at` are stamped in the fixture itself, replacing the runtime workaround that Phase 2D used.

These are **net-new fixture rows** — not just a re-render of existing data. The fixture sha256 has changed. This audit therefore covers more than fixture re-confirmation: it confirms that every new field uses the locked PHI placeholder vocabulary and that no plausibly-real values were introduced.

The receipt route (`/care-manager/expenses/<int:expense_id>/receipt/<int:receipt_id>/`) is reclassified to `not_screenshotted: non_html_response` (it returns `Content-Disposition: attachment` per `care_manager/views.py:741`); the route is no longer captured.

## Methodology

Inherits the methodology of [`PHI-AUDIT-PRECRAWL-2026-05-07.md`](PHI-AUDIT-PRECRAWL-2026-05-07.md). The fixture-level scan is augmented with explicit checks on every new entity field.

### Verification — fixture content

| Entity | PHI-bearing field | Value | Verdict |
|--------|-------------------|-------|---------|
| `clients.caremanagerclientassignment` (pk=1) | none — relational only | `care_manager=3, client=1, assigned_at="2026-05-08T12:00:00Z"` | clean (no text fields) |
| `clients.client` (pk=1, enriched) | `diagnosis` | `"[DIAGNOSIS]"` | placeholder |
| `clients.client` (pk=1, enriched) | `dnr` | `true` | non-PHI flag |
| `expenses.expense` (pk=1) | `description` | `"[NOTE_TEXT]"` | placeholder |
| `expenses.expense` (pk=1) | `notes` | `""` (empty) | clean |
| `expenses.expense` (pk=1) | `rejection_reason` | `"[NOTE_TEXT]"` | placeholder |
| `expenses.expense` (pk=1) | `amount` | `"9.99"` | deliberately non-realistic — see INVESTIGATIONS.md amount-value convention |
| `expenses.expensereceipt` (pk=1) | `original_filename` | `"[REDACTED].png"` | placeholder |
| `expenses.expensereceipt` (pk=1) | `file` | `"expenses/3/1/receipt-redacted.png"` | clean (path-only; placeholder filename) |
| `employees.caregiverprofile` (pk=1, enriched) | `profile_completed_at`, `onboarding_completed_at` | `"2026-04-01T12:00:00Z"` | non-PHI timestamps |

### Verification — placeholder blob

| Path | Bytes | sha256 | PHI surfaces |
|------|------:|--------|--------------|
| `<v1 MEDIA_ROOT>/expenses/3/1/receipt-redacted.png` | 258 | `6b8b8de2d293229ad1b435f52476c4904a5d21130d6052407ace775a5d520535` | none — flat-grey 200×100 PNG, no identifying marks, no embedded EXIF, no rendered text |

### Outbound integrations during the crawl

- `.env`: `TWILIO_DISABLED=1`, `SENDGRID_DISABLED=1`, `STRIPE_DISABLED=1`, `QUICKBOOKS_DISABLED=1`.
- v1 process: `unset DATABASE_URL SENDGRID_API_KEY EMAIL_HOST_PASSWORD QUICKBOOKS_CLIENT_ID QUICKBOOKS_CLIENT_SECRET SENTRY_DSN` per the bring-up runbook.
- Loaddata triggers `shifts.signals.send_new_assignment_email`. With `EMAIL_HOST_PASSWORD` unset, Django dev defaults to `console.EmailBackend` and the email contents print to stdout — never reach a real SMTP. Confirmed during pre-crawl smoke test (the email-shaped log was emitted to console).

### Crawler discipline

- Same crawler binary as Phase 2D. No destructive interactions exercised. `intercepted-non-GET.log` is empty for the full crawl.

## Result

**PASS.** Fixture content uses placeholder values exclusively. Placeholder PNG blob is content-clean. Outbound integrations disabled. The full re-crawl proceeded with no PHI risk surfaces in the input fixture or environment configuration. Post-crawl content scan continues at [`PHI-AUDIT-POSTCRAWL-2026-05-08-cm-recrawl.md`](PHI-AUDIT-POSTCRAWL-2026-05-08-cm-recrawl.md).
