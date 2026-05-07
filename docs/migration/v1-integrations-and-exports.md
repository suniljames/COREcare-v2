# V1 Integrations and Exports

> **Read [`README.md`](README.md) first.** It locks every convention used here.

This document inventories everything v1 talks to outside its own database: external integrations (third-party SaaS), the internal notification and email backend (because it's a customer-visible side channel that can silently break on rebuild), and customer-facing exports (CSV, PDF, accounting hand-offs). Anything that fires when an end-user takes an action in v1 is in scope.

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

Three architectural buckets to keep in mind while reading:

1. **External vendor integrations** rebuild as a v2 third-party-clients service layer (`api/app/services/integrations/`). v1 was single-tenant; v2 must agency-scope every credential.
2. **Internal email + push pipeline** is built atop one shared substrate (SendGrid SMTP via `core.email.backends.SendGridSMTPBackend`) plus a sender helper (`core.email.service.send_email_safely`) plus an audit-log model (`core.models.EmailEvent`). Per-application pipelines below all fan out through this substrate.
3. **Customer-facing exports** are file-generation endpoints that must preserve v1's HIPAA-access-log behaviour where present (e.g., schedule PDF).

View-As impersonation is documented under the inventory's [top-level admin routes](v1-pages-inventory.md#top-level-elitecareurlspy) — it controls staff session context, it does not export PHI to integrations.

---

## Schema

| Field | Description |
|-------|-------------|
| `name` | Integration or export name |
| `vendor_or_internal` | Stripe, Twilio, SendGrid, QuickBooks, internal, etc. |
| `trigger` | What action or schedule fires it (user click, cron job, webhook, etc.); cron expressions verbatim |
| `direction_and_sync` | `inbound` / `outbound` / `bidirectional`; `sync` / `async` |
| `surfaces_at_routes` | Anchor links into pages-inventory rows where users encounter the integration in the UI; literal `_no UI surface — operator-only_` for orphans |
| `customer_visibility` | What end-users see (a banner, an email, a downloaded file, nothing); prefixed `🔒 PHI · ` when PHI-bearing |
| `v2_status` | `implemented` / `scaffolded` / `missing` |
| `severity` | `H` / `M` / `L` / `D` (only when `v2_status=missing`) |

---

## External integrations

Third-party SaaS v1 integrates with. Sub-grouped by vendor.

### Billing and payments

v1 does not ship a payments processor. Client invoices are generated in v1, optionally pushed to QuickBooks Online (under [Accounting](#accounting)) for AR reconciliation, and emailed as PDFs to family members (under [Internal notification and email backend](#internal-notification-and-email-backend)). Stripe, Square, and Plaid are absent at the pinned commit.

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| _v1 ships no third-party billing/payments processor_ | n/a | n/a | outbound; sync | _no UI surface — operator-only_ | Sees: nothing — billing settled outside v1, in QuickBooks Online or by check. | missing | D |

### Payroll

v1 does not push timecards to a third-party payroll vendor. Payroll is computed in-app and exported as files (CSV / Excel / PDF) for off-platform reconciliation; see [Customer-facing exports](#customer-facing-exports). Gusto, ADP, and Paychex are absent.

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| _v1 ships no third-party payroll integration_ | n/a | n/a | outbound; sync | _no UI surface — operator-only_ | Sees: timecard exports under [the dashboard app group](v1-pages-inventory.md#dashboard) flow into off-platform payroll workflows. | missing | D |

### Accounting

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| QuickBooks Online | Intuit | Agency Admin clicks Connect (OAuth start); the send-invoice POST sends a client's weekly invoice; the live customer-search backs the client-link modal | bidirectional; sync | [`/quickbooks/connect/`, `/quickbooks/send-invoice/<int:client_id>/`, `/quickbooks/customers/search/`, `/quickbooks/clients/<int:client_id>/link/`](v1-pages-inventory.md#quickbooks_integration) | 🔒 PHI · Sees: connection status banner on admin index, invoice line items appear in the agency's QuickBooks customer record. Channel: QuickBooks customer record. v1 stores per-agency OAuth tokens in `QuickBooksConnection`; every send is logged to `QuickBooksInvoiceLog` with a billing snapshot for audit. | missing | H |

### Messaging and notifications (third-party)

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| SendGrid | Twilio SendGrid (SMTP) | Every transactional email v1 sends fans out through `core.email.backends.SendGridSMTPBackend`; SendGrid posts delivery-status events back via the inbound webhook receiver | bidirectional; async | _no UI surface — operator-only (substrate; per-app email rows below cite their UI surfaces individually)_ | Sees: every transactional email arrives in customer inboxes via SendGrid; subjects/footers carry `COMPANY_NAME` branding (Issue #631); confidentiality notice appended to PHI-bearing mail. Configured via env vars `EMAIL_HOST_PASSWORD` (API key), `DEFAULT_FROM_EMAIL`, `SENDGRID_WEBHOOK_SECRET`. | missing | H |
| `Web Push` | browser-supplied (FCM / APNs / Mozilla autopush) | `pywebpush.webpush()` invoked from `caregiver_dashboard.services.notification_service` on caregiver/admin notification fanout | outbound; async | [`/admin/todays-shifts/`, `/admin/open-shifts/`](v1-pages-inventory.md#top-level-elitecareurlspy) and caregiver-portal routes (Caregiver section pending) | Sees: OS push toast on caregiver/admin device. Channel: registered browser/device endpoint. Graceful skip when `WEBPUSH_VAPID_PRIVATE_KEY` / `WEBPUSH_VAPID_PUBLIC_KEY` env vars are unset — caregiver still receives the in-app inbox entry and email; only push-to-device is dropped. Subscription endpoints stored per-user in `caregiver_dashboard.models.PushSubscription`. | missing | M |

### Identity, auth, and SSO (third-party)

v1 ships first-party password and magic-link auth (`auth_service` app); rate-limits at the view layer. No third-party identity provider integration at the pinned commit. Social login, Okta, Azure AD, and Auth0 are absent.

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| _v1 ships no third-party identity provider_ | n/a | n/a | inbound; sync | _no UI surface — operator-only_ | Sees: nothing — auth flows live entirely under [the auth_service app group](v1-pages-inventory.md#auth_service). | missing | D |

### Other

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| Sentry | Sentry | Any uncaught exception in elitecare; initialized when `SENTRY_DSN` env var is set | outbound; async | _no UI surface — operator-only_ | Sees: nothing — operator-only error tracking. v1 settings import `sentry_sdk` with graceful fallback when DSN unset. v2 must verify `before_send` PHI scrubbing is configured before enabling. | missing | L |

---

## Internal notification and email backend

v1's own notification system and email-sending pipeline. Customer-visible side channels that aren't third-party but can silently break on rebuild if undocumented.

### Email pipeline

Every entry below ultimately fans out through SendGrid SMTP (see the [Messaging and notifications](#messaging-and-notifications-third-party) substrate row). Each row names its `core.email.log_email_event` category, which lands in `core.models.EmailEvent` for delivery-status reconciliation against SendGrid webhooks. Subject lines truncate to 200 chars in the audit log; `EmailEvent.subject` may carry PHI for billing- and clinical-content sends — v2 must decide store-as-is, redact-at-write, or split-into-non-PHI-category-code on rebuild.

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| Password-reset email | internal | User submits password-reset form (rate-limited 3/hour/IP, timing-safe per `auth_service/services.py`) | outbound; sync | [`/password-reset/<uuid:token>/`](v1-pages-inventory.md#auth_service) | Sees: email containing a single-use UUID token (5/min/IP rate limit on consume); subject is role-aware (Issue #622). EmailEvent category: `auth_password_reset`. | missing | D |
| Magic-link login email | internal | User submits email on the magic-link form (`is_staff`/`is_superuser` users blocked at the view layer); 30-minute single-use UUID token | outbound; sync | [`/magic-login/<uuid:token>/`](v1-pages-inventory.md#auth_service) | Sees: email with subject `Sign-in link from [AGENCY_NAME]`. EmailEvent category: `auth_magic_link`. | missing | D |
| Admin password-change notification | internal | Admin password change in `auth_service/services.py:send_admin_password_change_notification` — fan-out to all other admins | outbound; sync | _no UI surface — operator notification (audit signal)_ | Sees: subject `Admin password change detected`; first-name greeting, no email leak (Issue #624). EmailEvent category: `auth_admin_password`. | missing | H |
| Caregiver invitation email | internal | Agency Admin invites a caregiver via the v1 invitation flow (`employees/utils.py`); UUID invitation token | outbound; sync | [`/employees/invitation/<uuid:token>/`](v1-pages-inventory.md#employees) | Sees: email with invitation acceptance link; recipient sets password and completes profile in one combined form. EmailEvent category: `invitation`. | missing | H |
| Shift assignment email | internal | Caregiver newly assigned to a shift (`shifts/signals.py:_send_shift_notification`, `notification_type="new_assignment"`) | outbound; sync | [`/admin/todays-shifts/`, `/admin/open-shifts/`](v1-pages-inventory.md#top-level-elitecareurlspy) (Agency Admin assigns; caregiver receives) | 🔒 PHI · Sees: client name, shift date/time, location in caregiver's inbox. Template `emails/shift_new_assignment`. EmailEvent category: `shift_assignment`. | missing | H |
| Shift rate-change email | internal | Shift `bill_rate` or `pay_rate` changes (`shifts/signals.py`, `notification_type="rate_changed"`) | outbound; sync | [`/admin/todays-shifts/`](v1-pages-inventory.md#top-level-elitecareurlspy) | 🔒 PHI · Sees: shift summary with old vs new rate. Template `emails/shift_rate_changed`. EmailEvent category: `shift_rate_change`. | missing | M |
| Pre-shift reminder email | internal | `send_shift_reminders` Render cron runs `*/15 * * * *`; `shifts/services/shift_reminder_service.py` scans for shifts starting within 15 hours (`SCAN_WINDOW_HOURS = 15`), targets ~8 hours before shift start, respects 9pm–7am Pacific quiet hours (Issue #642) | outbound; sync | _no UI surface — Caregiver section pending_ | 🔒 PHI · Sees: informational shift summary with client first name, city, start/end time. Template `emails/pre_shift_reminder`. EmailEvent category: `pre_shift_reminder`. Idempotent via `Shift.pre_shift_reminder_sent_at` stamp. | missing | H |
| Shift-canceled email | internal | Admin cancels a shift via the explicit cancel flow (`shifts/signals.py`, `shift_canceled` Signal); not fired on programmatic delete | outbound; sync | [`/admin/todays-shifts/`](v1-pages-inventory.md#top-level-elitecareurlspy) | 🔒 PHI · Sees: shift cancellation notice. Template `emails/shift_canceled`. EmailEvent category: `shift_canceled`. | missing | H |
| Credential-expiry email | internal | `check_expiring_credentials` management command (`credentials/notifications.py`); operator schedules via cron or manual run | outbound; sync | [`/employees/complete-profile/`](v1-pages-inventory.md#employees) | Sees: email listing credentials expiring within configured threshold. EmailEvent category: `credential_expiry`. | missing | M |
| Rate-change notification email | internal | Caregiver pay-rate change applied (`employees/services/rate_change_service.py`, `apply_scheduled_rate_changes` cron-eligible command) | outbound; sync | _no UI surface — operator-managed cadence_ | Sees: rate change details with effective date. EmailEvent category: `rate_change_notification`. | missing | M |
| Rate-change request — new | internal | Caregiver submits rate-change request (`employees/services/rate_change_request_service.py`) | outbound; sync | _no UI surface — Care Manager / Agency Admin sections pending_ | Sees: request notification routed to approvers. EmailEvent category: `rate_change_request_new`. | missing | M |
| Rate-change request — approved | internal | Approver approves a pending rate-change request | outbound; sync | _no UI surface — Care Manager / Agency Admin sections pending_ | Sees: approval confirmation with new rate and effective date. EmailEvent category: `rate_change_request_approved`. | missing | M |
| Rate-change request — rejected | internal | Approver rejects a pending rate-change request | outbound; sync | _no UI surface — Care Manager / Agency Admin sections pending_ | Sees: rejection reason from approver. EmailEvent category: `rate_change_request_rejected`. | missing | M |
| Overpayment consent request | internal | Overpayment recovery initiated (`employees/services/overpayment_recovery_service.py`); legal-grade consent flow | outbound; sync | _no UI surface — Care Manager / Agency Admin sections pending_ | Sees: consent form link with recovery details. EmailEvent category: `overpayment_consent_request`. | missing | H |
| Overpayment consent declined | internal | Caregiver declines overpayment recovery consent | outbound; sync | _no UI surface — Care Manager / Agency Admin sections pending_ | Sees: agency-side notification of decline. EmailEvent category: `overpayment_consent_declined`. | missing | H |
| Care request notification | internal | Family submits a care request (`clients/services/care_request_service.py`) | outbound; sync | [`/family-signup/`](v1-pages-inventory.md#shared-routes) | 🔒 PHI · Sees: admin gets new-inquiry notification with intake fields. | missing | H |
| Anomaly alert | internal | `core/services/anomaly_detection.py` flags an operational anomaly (e.g., timecard data drift) | outbound; sync | _no UI surface — operator alerting_ | Sees: nothing — operator alerting only. EmailEvent category: `anomaly_alert`. | missing | M |
| Client billing PDF email | internal | Agency Admin emails the client billing PDF to family members (`dashboard/views.py:admin_email_billing_pdf`); per-send row in `BillingEmailLog` (Issue #631; legacy logs migrated via `migrate_legacy_email_logs`) | outbound; sync | [`/dashboard/admin/invoices/<int:client_id>/email/`](v1-pages-inventory.md#dashboard) | 🔒 PHI · Sees: PDF attachment with client billing summary in family member's inbox. Channel: inbox. v1 audit row: `BillingEmailLog`. | missing | H |
| Invoice email service | internal | Same surface as client billing PDF email — separate sender helper in `billing/services/invoice_email_service.py` validates subject for header injection (Issue rejecting subject > 200 chars or containing `\r\n`) | outbound; sync | [`/dashboard/admin/invoices/<int:client_id>/email/`](v1-pages-inventory.md#dashboard) | 🔒 PHI · Sees: PDF attachment with invoice. Channel: inbox. v1 audit row: `InvoiceEmailLog`. EmailEvent category: `invoice`. | missing | H |
| Health-report email (operator-triggered) | internal | Agency Admin emails a generated health-report PDF (`charting/services/health_report_email_service.py`); cover message optional | outbound; sync | [`/charting/reports/email/`](v1-pages-inventory.md#charting) | 🔒 PHI · Sees: clinical or family report PDF in recipient's inbox. EmailEvent category: `health_report`. | missing | H |
| Weekly admin data-health email | internal | `weekly-health-email` Render cron runs `0 14 * * 1` (Mon 14:00 UTC = Mon 06:00 Pacific); `core/management/commands/send_weekly_health_email.py` (Issue #299); recipients from `ADMIN_HEALTH_REPORT_RECIPIENTS` env var (CSV) | outbound; sync | _no UI surface — operator monitoring_ | Sees: agency admin gets weekly data-health summary in inbox; recipients comma-separated env var. EmailEvent category: `health_report`. | missing | M |
| SendGrid delivery webhook receiver | internal | SendGrid posts delivery-status events to `core/email/webhook_views.py`; HMAC-validated against `SENDGRID_WEBHOOK_SECRET` (Issue #631); updates `EmailEvent.status` and `sendgrid_message_id` | inbound; sync | _no UI surface — operator-only_ | Sees: nothing — internal status reconciliation; if webhook fails, send-vs-delivered ratio in operator dashboard goes stale. v2 cannot drop signature validation. | missing | H |
| Email delivery canary | internal | `core/management/commands/email_delivery_canary.py` (Issue #631); operator schedules via cron; sends to `CANARY_EMAIL_ADDRESS` env var | outbound; sync | _no UI surface — operator monitoring_ | Sees: nothing — synthetic deliverability probe. EmailEvent category: `test`. | missing | M |

### In-app notifications

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| Caregiver notification inbox | internal | Domain events fan out to `caregiver_dashboard.services.notification_service.create_notification` (Issue #855 Phase 7); read/unread per recipient | outbound; sync | _no UI surface — Caregiver section pending; reachable via the caregiver dashboard once authored_ | Sees: caregiver/admin in-app inbox with unread count and per-row read state. v1 audit row: `caregiver_dashboard.models.CaregiverNotification`. v2 has the model + router scaffolded under `api/app/routers/notifications.py`. | scaffolded |  |
| `Web Push` delivery | internal | `notification_service` invokes `pywebpush.webpush()` for users with registered `PushSubscription` rows; expired-410-Gone subscriptions are deleted from the registry | outbound; async | _no UI surface — Caregiver section pending_ | Sees: OS push toast on registered devices; gracefully skipped if VAPID keys unset. v1 audit row: `caregiver_dashboard.models.PushSubscription`. See also the `Web Push` row under [External integrations § Messaging](#messaging-and-notifications-third-party) for the per-user vendor surface. | missing | M |

### Operational scheduled jobs

Render cron entries from v1's `render.yaml`. Customer-impacting crons are documented above as their email rows; the four operator-only crons below have no UI surface but exist in v1's runtime substrate. A v2 rebuild that drops one silently breaks production (e.g., the disk-utilization check is the only signal that media uploads are filling the persistent disk).

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| Verification log cleanup cron | internal | `cleanup-verification-logs` Render cron runs `0 3 * * *` (daily 03:00 UTC); `core/management/commands/cleanup_verification_logs.py`; retention 90 days normal / 365 days anomalies (Issue #300) | outbound; sync | _no UI surface — operator-only_ | Sees: nothing — data hygiene only. Configurable via `AUDIT_LOG_RETENTION_DAYS` and `AUDIT_LOG_ANOMALY_RETENTION_DAYS` env vars. | missing | M |
| Charting metrics snapshot cron | internal | `snapshot-charting-metrics` Render cron runs `0 4 * * *` (daily 04:00 UTC); `charting/management/commands/snapshot_charting_metrics.py` (Issue #792 Phase 2.5); writes daily charting metrics rows | outbound; sync | _no UI surface — operator-only (feeds admin dashboards once consumed)_ | Sees: nothing directly; downstream admin metrics dashboards depend on the daily snapshot. | missing | M |
| Disk-utilization check cron | internal | `check-disk-utilization` Render cron runs `0 5 * * *` (daily 05:00 UTC); curl POSTs `/ops/disk-check/` with `Authorization: Bearer $DISK_CHECK_TOKEN` because Render crons spin up fresh containers without the persistent `/var/data/` disk; the endpoint runs `DiskUtilizationService` in-process inside the web service (Issue #1333 Plan #24) | outbound; sync | _no UI surface — operator-only_ | Sees: nothing — operator alerting on media-disk pressure. `DISK_CHECK_TOKEN` env var must match between cron caller and web receiver. | missing | M |
| Database migrations safety-net cron | internal | `corecare-database-migrations` Render cron runs `0 2 * * *` (daily 02:00 UTC); `python manage.py migrate --noinput`; catches migrations added between deploys or during deploy pauses (Issue #618) | outbound; sync | _no UI surface — operator-only_ | Sees: nothing — operator-only deploy safety net. | missing | L |

---

## Customer-facing exports

User-triggered or scheduled exports that produce a file or feed visible to a customer. See also [`v1-functionality-delta.md`](v1-functionality-delta.md) for severity rationale on missing export gaps.

### CSV exports

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| All-staff timecard CSV | internal | Agency Admin triggers the CSV export from the timecards summary page; `dashboard/views.py` writes via `csv.writer` | outbound; sync | [`/dashboard/admin/timecards/export/csv/`](v1-pages-inventory.md#dashboard) | 🔒 PHI · Sees: CSV with caregivers, hours, pay for the selected period. Channel: browser download. Feeds off-platform payroll workflows. | missing | M |

### PDF exports

PDF generation throughout v1 uses ReportLab; filenames are timestamped on disk-attachment outputs.

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| Single-caregiver timecard PDF | internal | Agency Admin clicks PDF on a caregiver's timecard detail | outbound; sync | [`/dashboard/admin/timecards/<int:caregiver_id>/pdf/`](v1-pages-inventory.md#dashboard) | 🔒 PHI · Sees: PDF with caregiver's period timecard. Channel: browser download. | missing | M |
| All-staff timecard PDF | internal | Agency Admin triggers the PDF export from the timecards summary page | outbound; sync | [`/dashboard/admin/timecards/export/pdf/`](v1-pages-inventory.md#dashboard) | 🔒 PHI · Sees: PDF with all caregivers' timecard summary. Channel: browser download. | missing | M |
| Client billing PDF | internal | Agency Admin generates a per-client billing PDF for the selected period | outbound; sync | [`/dashboard/admin/invoices/<int:client_id>/billing-pdf/`](v1-pages-inventory.md#dashboard) | 🔒 PHI · Sees: PDF with client billing summary and line items. Channel: browser download or attached to the [client billing PDF email](#email-pipeline). | missing | H |
| Client schedule PDF | internal | Agency Admin generates a monthly schedule PDF for a client (calendar-grid or agenda) | outbound; sync | [`/clients/<int:client_id>/schedule/pdf/`](v1-pages-inventory.md#clients) | 🔒 PHI · Sees: PDF with client name, caregiver names, shift times, optional weekend column. HIPAA-access-logged in v1 — v2 must preserve the access-log behavior. Channel: browser download. | missing | L |
| Health-report PDF (clinical, direct) | internal | Authorized user POSTs to the direct-clinical endpoint with a `?days=` window | outbound; sync | [`/charting/reports/<int:client_id>/clinical/`](v1-pages-inventory.md#charting) | 🔒 PHI · Sees: clinical health-report PDF with PHI sections. Channel: browser download. | missing | H |
| Health-report PDF (generated on demand) | internal | Authorized user submits the generate form with type, day window, sections, and formatting options | outbound; sync | [`/charting/reports/generate/`](v1-pages-inventory.md#charting) | 🔒 PHI · Sees: clinical or family health-report PDF. Channel: browser download. | missing | H |

### Other formats

| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |
|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|
| All-staff timecard Excel | internal | Agency Admin triggers the Excel export from the timecards summary page; `openpyxl.Workbook` with formatting (Font, Border, PatternFill); fallback to CSV if openpyxl absent | outbound; sync | [`/dashboard/admin/timecards/export/excel/`](v1-pages-inventory.md#dashboard) | 🔒 PHI · Sees: XLSX with caregivers, hours, pay; openable in Excel. Channel: browser download. | missing | L |
| Health-report batch zip | internal | Agency Admin selects multiple clients and submits a batch run; partial-success warning on errors | outbound; sync | [`/charting/reports/batch/`](v1-pages-inventory.md#charting) | 🔒 PHI · Sees: zip of health-report PDFs for the selected clients. Channel: browser download. | missing | H |
| QuickBooks invoice push | internal | Agency Admin triggers the QuickBooks invoice send for a client's weekly invoice; logged to `QuickBooksInvoiceLog` with billing snapshot | outbound; sync | [`/quickbooks/send-invoice/<int:client_id>/`](v1-pages-inventory.md#quickbooks_integration) | 🔒 PHI · Sees: invoice line items appear on the agency's QuickBooks customer record. Channel: QuickBooks customer record. See also the QuickBooks Online row under [External integrations § Accounting](#accounting). | missing | H |

---

## Cross-references

Orphan integrations — entries above that have no UI surface in `v1-pages-inventory.md`:

- **SendGrid (substrate)** — operator-only configuration; per-app email rows cite their UI surfaces.
- **Sentry** — operator-only error tracking.
- **Admin password-change notification email** — operator notification fan-out, no end-user surface.
- **Rate-change notification / request / approval / rejection emails (4 entries)** — Care Manager / Agency Admin UI surfaces pending in inventory.
- **Overpayment consent request / declined emails (2 entries)** — Care Manager / Agency Admin UI surfaces pending in inventory.
- **Anomaly alert email** — operator alerting only.
- **Weekly admin data-health email** — operator monitoring (delivered to inbox, but no end-user UI surface).
- **SendGrid delivery webhook receiver** — operator-only inbound webhook.
- **Email delivery canary** — operator monitoring.
- **Caregiver notification inbox + `Web Push` delivery (in-app notifications)** — Caregiver-section UI surfaces pending in inventory.
- **Verification log cleanup cron, charting metrics snapshot cron, disk-utilization check cron, database migrations safety-net cron** — operator-only Render cron jobs.

Customer-impacting Render crons (`weekly-health-email`, `send-shift-reminders`) surface as their respective email rows under [Email pipeline](#email-pipeline) above; the cron expressions live in those rows' `trigger` cells per the locked convention.
