# v1 UI Catalog — Index

> **This catalog operates against v1 (`hcunanan79/COREcare-access`).** v2 contributors browse the screenshots + captions here without ever needing v1 access. The crawler that produced these binaries lives at [`tools/v1-screenshot-catalog/`](../../../tools/v1-screenshot-catalog/) — read its [`README.md`](../../../tools/v1-screenshot-catalog/README.md) first if you want to understand how the catalog is generated or refresh it.

**Status:** AUTHORITATIVE. Phase 2D crawl ran on 2026-05-07 against v1 commit [`9738412a`](https://github.com/hcunanan79/COREcare-access/commit/9738412a6e41064203fc253d9dd2a5c6a9c2e231). Caption frontmatter is complete; caption bodies (CTAs visible + interaction notes) are tracked separately in the Phase 3 follow-up issue (linked below).

> **Read [`../README.md`](../README.md) first.** It locks sensitivity classification, persona vocabulary, pinned references, and the skip-reason taxonomy used here.

---

## How to read this catalog

Every captured (route, persona) pair has three files in the persona's directory:

| File | Purpose |
|------|---------|
| `<NNN>-<route>.desktop.webp` | Full-page screenshot at 1440×900 |
| `<NNN>-<route>.mobile.webp` | Full-page screenshot at 390×844 |
| `<NNN>-<route>.md` | Caption — frontmatter + (Phase 3) observed CTAs + interaction notes |

Numbering is 3-digit zero-padded, sequential within the persona section. The caption's `lead_viewport` field encodes which viewport is canonical for the persona: Caregiver and Family Member lead with **mobile** (per [`docs/design-system/RESPONSIVE.md`](../../design-system/RESPONSIVE.md) — they operate from phones in the field); other personas lead with desktop. Both viewports are always captured.

The caption is the cross-reference handle. Its frontmatter `canonical_id` field (e.g., `agency-admin/001-todays-shifts`) is what the [pages inventory](../../migration/v1-pages-inventory.md) `screenshot_ref` column points at.

## Caption schema

```yaml
---
canonical_id: <persona-slug>/<NNN>-<route-slug>
route: <v1 URL pattern, with <int:id> placeholders>
persona: <canonical persona name from ../migration/README.md>
lead_viewport: desktop | mobile
seed_state: populated | empty
v1_commit: <SHA the catalog was generated against>
generated: <YYYY-MM-DD>
---
**CTAs visible:** <comma-separated list of buttons/links observable in the screenshot>

**Interaction notes** (1–4 bullets, observed behavior only):
- <element> → <result>
- ⚠ destructive: <element> → <result>. Skipped by crawler.
```

Interaction-note rules (from [#79](https://github.com/suniljames/COREcare-v2/issues/79) Writer review): observed behavior only, no speculation, format `<element> → <result>`. Destructive interactions get a `⚠ destructive:` prefix and **must not** be triggered by the crawler.

## Persona index

Persona section order matches [`../../migration/README.md` §Personas](../../migration/README.md#personas). Within-persona routes are ordered by `canonical_id` ascending (sequence number preserves "what comes next" navigation).

| Persona | Directory | Captures | Lead viewport |
|---------|-----------|---------:|---------------|
| Super-Admin | [`super-admin/`](super-admin/) | 1 | desktop |
| Agency Admin | [`agency-admin/`](agency-admin/) | 61 | desktop |
| Care Manager | [`care-manager/`](care-manager/) | 5 | desktop |
| Caregiver | [`caregiver/`](caregiver/) | 15 | **mobile** |
| Client | [`client/`](client/) | 0 (no v1 portal) | n/a |
| Family Member | [`family-member/`](family-member/) | 4 | **mobile** |

**Total:** 86 captured (route, persona) pairs × 2 viewports = 172 WebP files via Git LFS. 48 inventory rows are recorded as `not_screenshotted: <reason>` in [`docs/migration/v1-pages-inventory.md`](../../migration/v1-pages-inventory.md) per the [skip-reason taxonomy](../README.md#skip-reason-taxonomy).

The Client persona has no captures because v1 has no Client login portal — Client is an object-of-care, not a User. See [`tools/v1-screenshot-catalog/INVESTIGATIONS.md`](../../../tools/v1-screenshot-catalog/INVESTIGATIONS.md#persona-authentication-mapping) for the persona-mapping decisions.

## Per-route index

Quick scan of every captured route by persona, with the inventory's one-line purpose. Click a canonical_id to open its caption file. Routes not captured (intentionally or pending fixture expansion) are listed under [Skipped routes](#skipped-routes) below.

### Super-Admin

- [`super-admin/001-kill-all`](super-admin/001-kill-all.md) — `/admin/view-as/kill-all/` — Emergency kill switch for all active View As sessions; audit-logged in v1.

### Agency Admin

- [`agency-admin/001-todays-shifts`](agency-admin/001-todays-shifts.md) — `/admin/todays-shifts/` — Lists today's shifts grouped by caregiver, with clock-in status, scheduled vs actual hours, and total wages.
- [`agency-admin/002-open-shifts`](agency-admin/002-open-shifts.md) — `/admin/open-shifts/` — Lists unassigned shifts ordered by start time, with client and required hours.
- [`agency-admin/003-data-health`](agency-admin/003-data-health.md) — `/admin/data-health/` — Reports v1 data integrity counts (orphan records, stale flags, schedule gaps).
- [`agency-admin/004-hub`](agency-admin/004-hub.md) — `/admin/view-as/hub/` — View As hub — entry point for staff impersonation of caregivers and family members; audit-logged in v1.
- [`agency-admin/005-select`](agency-admin/005-select.md) — `/admin/view-as/family/select/` — View As family selector — choose a family-member account to impersonate; audit-logged in v1.
- [`agency-admin/006-view-as`](agency-admin/006-view-as.md) — `/admin/view-as/<int:user_id>/` — View As session start — step-up confirmation before impersonating a target user; audit-logged in v1.
- [`agency-admin/007-select`](agency-admin/007-select.md) — `/admin/view-as/caregiver/select/` — View As caregiver selector — choose a caregiver account to impersonate; audit-logged in v1.
- [`agency-admin/008-caregiver`](agency-admin/008-caregiver.md) — `/admin/view-as/caregiver/<int:user_id>/` — View As caregiver session start — step-up confirmation before impersonating a caregiver; audit-logged in v1.
- [`agency-admin/009-end`](agency-admin/009-end.md) — `/admin/view-as/end/` — Ends an active View As session and returns the staff user to their own context; audit-logged in v1.
- [`agency-admin/010-status`](agency-admin/010-status.md) — `/admin/view-as/status/` — Reports active View As session state — used by the impersonation banner and middleware.
- [`agency-admin/011-search`](agency-admin/011-search.md) — `/admin/view-as/search/` — User search for selecting a View As target by name or email.
- [`agency-admin/012-stats`](agency-admin/012-stats.md) — `/admin/view-as/stats/` — View As session statistics — initiated counts, terminations, failed attempts.
- [`agency-admin/013-audit-log`](agency-admin/013-audit-log.md) — `/admin/view-as/audit-log/` — View As audit log — IP, action, target, timestamp for every session and forbidden-action attempt.
- [`agency-admin/014-review`](agency-admin/014-review.md) — `/admin/expenses/review/` — Lists pending caregiver expense submissions awaiting Agency Admin approval.
- [`agency-admin/018-role-permissions`](agency-admin/018-role-permissions.md) — `/admin/role-permissions/` — Role-based capability management — toggles which capabilities each role grants.
- [`agency-admin/019-toggle`](agency-admin/019-toggle.md) — `/admin/role-permissions/toggle/` — Toggles a single capability grant for a role; audit-logged in v1.
- [`agency-admin/020-still-current`](agency-admin/020-still-current.md) — `/admin/banners/mileage/still-current/` — January annual mileage-rate verification banner CTA — confirms current rate is correct; v1 stores rate as a single SystemSetting, so refa...
- [`agency-admin/021-snooze`](agency-admin/021-snooze.md) — `/admin/banners/mileage/snooze/` — January annual mileage-rate banner snooze CTA — defers the verification reminder; same single-SystemSetting refactor consideration as the...
- [`agency-admin/025-service-catalog`](agency-admin/025-service-catalog.md) — `/admin/settings/service-catalog/` — Lists the agency's billable service catalog entries (service name, family-facing label, base price, hourly rate, MD-order requirement, re...
- [`agency-admin/026-new`](agency-admin/026-new.md) — `/admin/settings/service-catalog/new/` — Add a new billable service catalog entry.
- [`agency-admin/029-overview`](agency-admin/029-overview.md) — `/charting/overview/` — Lists clients sorted by charting attention priority — overdue, missing today, in progress, complete.
- [`agency-admin/030-client`](agency-admin/030-client.md) — `/charting/client/<int:client_id>/` — Per-client charting tab with active template summary, recent charts, today's stats, and trend links.
- [`agency-admin/031-create-template`](agency-admin/031-create-template.md) — `/charting/client/<int:client_id>/create-template/` — Wizard for adding or editing the client's chart-template sections, items, and inclusion settings.
- [`agency-admin/032-trend`](agency-admin/032-trend.md) — `/charting/vital-signs/<int:client_id>/trend/` — Renders the client's blood pressure, pulse, and temperature trend across a configurable day window.
- [`agency-admin/033-trend`](agency-admin/033-trend.md) — `/charting/glucose/<int:client_id>/trend/` — Renders the client's blood glucose readings as a trend chart with pre/post-meal context flags.
- [`agency-admin/034-summary`](agency-admin/034-summary.md) — `/charting/nursing-notes/<int:client_id>/summary/` — Lists the client's nursing notes in chronological order with author, timestamp, and section context.
- [`agency-admin/035-trend`](agency-admin/035-trend.md) — `/charting/intake-output/<int:client_id>/trend/` — Renders the client's daily fluid intake and urinary output trend with running balance totals.
- [`agency-admin/036-summary`](agency-admin/036-summary.md) — `/charting/bowel-movement/<int:client_id>/summary/` — Lists the client's bowel-movement events with consistency, color, and notes grouped by day.
- [`agency-admin/037-orders`](agency-admin/037-orders.md) — `/charting/medications/<int:client_id>/orders/` — Lists the client's active medication orders with dose, route, frequency, start date, and prescriber.
- [`agency-admin/039-review-queue`](agency-admin/039-review-queue.md) — `/charting/comments/review-queue/` — Staff queue of chart comments awaiting family-visibility approval, filterable by client.
- [`agency-admin/040-generate`](agency-admin/040-generate.md) — `/charting/reports/generate/` — Generates a health-report PDF on demand with client picker, date window, sections, and formatting options.
- [`agency-admin/041-clinical`](agency-admin/041-clinical.md) — `/charting/reports/<int:client_id>/clinical/` — Direct clinical-report PDF download endpoint with a configurable day-window query parameter.
- [`agency-admin/042-preview`](agency-admin/042-preview.md) — `/charting/reports/preview/` — Renders an HTML preview of the health report (clinical or family variant) before PDF generation.
- [`agency-admin/043-email`](agency-admin/043-email.md) — `/charting/reports/email/` — Emails a generated health-report PDF to a recipient with an optional cover message; redirects on completion.
- [`agency-admin/044-batch`](agency-admin/044-batch.md) — `/charting/reports/batch/` — Generates a zip of health reports for multiple selected clients in a single batch run.
- [`agency-admin/045-templates`](agency-admin/045-templates.md) — `/charting/reports/templates/` — Lists report-configuration templates and per-client/caregiver overrides for health-report sections.
- [`agency-admin/047-approval-queue`](agency-admin/047-approval-queue.md) — `/charting/reports/approval-queue/` — Staff queue of caregiver-initiated health-report requests awaiting approval before family delivery.
- [`agency-admin/049-add`](agency-admin/049-add.md) — `/charting/reports/overrides/add/` — Creates a new ReportAccessOverride mapping a caregiver and/or client to a custom set of report sections.
- [`agency-admin/051-schedule`](agency-admin/051-schedule.md) — `/clients/schedule/` — Legacy schedule landing — renders an empty placeholder for staff or redirects family-linked users to the family home; dual-mounted at /sc...
- [`agency-admin/052-calendar`](agency-admin/052-calendar.md) — `/clients/<int:client_id>/calendar/` — Unified per-client calendar with daily, weekly, and monthly views combining scheduled shifts and custom events.
- [`agency-admin/053-api`](agency-admin/053-api.md) — `/clients/<int:client_id>/calendar/api/` — JSON calendar feed for the per-client calendar widget; returns shifts and events with title, time, and type.
- [`agency-admin/054-create`](agency-admin/054-create.md) — `/clients/<int:client_id>/events/create/` — Creates a custom non-shift calendar event (medical appointment, milestone, family note) on a client's calendar.
- [`agency-admin/061-preview`](agency-admin/061-preview.md) — `/clients/<int:client_id>/schedule/preview/` — HTML preview partial for the print-config panel; mirrors the schedule PDF generator's options without producing a PDF.
- [`agency-admin/062-timecards`](agency-admin/062-timecards.md) — `/dashboard/admin/timecards/` — Lists payroll-period timecard summary across all caregivers, with weekly/monthly/yearly period selection.
- [`agency-admin/063-timecards`](agency-admin/063-timecards.md) — `/dashboard/admin/timecards/<int:caregiver_id>/` — Shows individual caregiver's timecard detail for the selected period — visits, clock times, hours, pay.
- [`agency-admin/068-invoices`](agency-admin/068-invoices.md) — `/dashboard/admin/invoices/` — Lists all client invoices, allows uploading new invoice PDFs, and shows the automated weekly billing summary; supports adding standalone ...
- [`agency-admin/071-email`](agency-admin/071-email.md) — `/dashboard/admin/invoices/<int:client_id>/email/` — Form to email the client billing PDF to the client's family members with delivery tracking; logs each send to BillingEmailLog.
- [`agency-admin/073-complete-profile`](agency-admin/073-complete-profile.md) — `/employees/complete-profile/` — Profile-completion form for existing caregivers redirected by the v1 ProfileCompletionMiddleware before they can clock in.
- [`agency-admin/074-draft`](agency-admin/074-draft.md) — `/employees/complete-profile/draft/` — Auto-save endpoint backing the profile-completion form; persists partial caregiver drafts so entered data survives a reload.
- [`agency-admin/075-connect`](agency-admin/075-connect.md) — `/quickbooks/connect/` — Initiates the QuickBooks Online OAuth flow — redirects an Agency Admin to Intuit's consent screen.
- [`agency-admin/076-callback`](agency-admin/076-callback.md) — `/quickbooks/callback/` — Handles the OAuth callback from Intuit; exchanges the auth code for tokens and saves the active connection.
- [`agency-admin/077-disconnect`](agency-admin/077-disconnect.md) — `/quickbooks/disconnect/` — Disconnects the active QuickBooks connection — POST-only; deactivates every active connection row.
- [`agency-admin/078-status`](agency-admin/078-status.md) — `/quickbooks/status/` — Reports QuickBooks connection state as JSON — used by admin pages to render the connection indicator.
- [`agency-admin/079-send-invoice`](agency-admin/079-send-invoice.md) — `/quickbooks/send-invoice/<int:client_id>/` — Sends a client's weekly invoice to QuickBooks; logs the send with a billing snapshot for audit.
- [`agency-admin/080-search`](agency-admin/080-search.md) — `/quickbooks/customers/search/` — Live search across the agency's QuickBooks customers — backs the link-customer modal in Client admin.
- [`agency-admin/081-link`](agency-admin/081-link.md) — `/quickbooks/clients/<int:client_id>/link/` — Links a COREcare client to a QuickBooks customer ID for reliable invoice creation (Issue #329).
- [`agency-admin/082-unlink`](agency-admin/082-unlink.md) — `/quickbooks/clients/<int:client_id>/unlink/` — Removes the QuickBooks customer link from a COREcare client; clears all link metadata fields.
- [`agency-admin/083-accessibility`](agency-admin/083-accessibility.md) — `/legal/accessibility/` — Renders the public accessibility statement page with the agency's accessibility contact email and phone; required for state-law accessibi...
- [`agency-admin/086-password-reset`](agency-admin/086-password-reset.md) — `/password-reset/` — Renders the password-reset request form; rate-limited at 3/hour/IP and timing-safe to defeat email enumeration; audit-logged in v1 with e...
- [`agency-admin/087-sent`](agency-admin/087-sent.md) — `/password-reset/sent/` — Renders the post-submit confirmation page after a reset request; intentionally generic copy to avoid revealing whether the email exists.
- [`agency-admin/089-complete`](agency-admin/089-complete.md) — `/password-reset/complete/` — Renders the success page after a completed password reset; admin password changes also trigger an admin-notification email in v1.

### Care Manager

- [`care-manager/001-care-manager`](care-manager/001-care-manager.md) — `/care-manager/` — `My Caseload` — priority-sorted list of every client assigned to this CM, with attention queue and all-clear groups; scope enforced by `C...
- [`care-manager/002-client`](care-manager/002-client.md) — `/care-manager/client/<int:pk>/` — `Client Focus` — full per-client context for one assigned client across schedule, charting, vitals, and care-request tabs; unassigned-cl...
- [`care-manager/003-expenses`](care-manager/003-expenses.md) — `/care-manager/expenses/` — CM expense list grouped per assigned client, with budget status; status transitions on the linked expenses are audit-logged via `ExpenseS...
- [`care-manager/004-submit`](care-manager/004-submit.md) — `/care-manager/expenses/submit/` — CM expense submission form scoped to assigned clients; submission audit-logged via `ExpenseService.create_expense` workflow events.
- [`care-manager/005-edit`](care-manager/005-edit.md) — `/care-manager/expenses/<int:expense_id>/edit/` — CM expense edit / resubmit form; submitter-only ownership enforced; resubmits on REJECTED expenses route through `ExpenseService.resub...

### Caregiver

- [`caregiver/001-onboarding`](caregiver/001-onboarding.md) — `/caregiver/onboarding/` — 3-step onboarding wizard for new caregivers — personal info, document upload, welcome tour.
- [`caregiver/002-profile`](caregiver/002-profile.md) — `/caregiver/profile/` — Caregiver's own profile-completion form — title, DOB, contact, optional photo and bio; auto-saves via the `/employees/complete-profile/dr...
- [`caregiver/003-dashboard`](caregiver/003-dashboard.md) — `/caregiver/dashboard/` — Daily caregiver landing page — state-machine-driven (IDLE / EMPTY / ACTIVE / POST_SHIFT) showing today's shift, clock-in/out actions, and...
- [`caregiver/004-schedule`](caregiver/004-schedule.md) — `/caregiver/schedule/` — Monthly caregiver schedule with daily/weekly/monthly view modes; navigates by date, displays shifts with client name and time block.
- [`caregiver/005-shift-offers`](caregiver/005-shift-offers.md) — `/caregiver/shift-offers/` — Shift offers page — pending shift assignments with inline accept/decline and per-offer earnings estimate.
- [`caregiver/007-clock`](caregiver/007-clock.md) — `/caregiver/clock/` — Unscheduled clock-in entry page — caregiver picks a client and starts an ad-hoc Visit when no shift is assigned (e.g., last-minute covera...
- [`caregiver/018-clients`](caregiver/018-clients.md) — `/caregiver/clients/<int:client_id>/` — Caregiver-side client profile — read-only view of the client's care details available to assigned caregivers; surfaces care preferences, ...
- [`caregiver/019-submit`](caregiver/019-submit.md) — `/caregiver/expenses/submit/` — Standalone expense submission form — caregiver submits a non-visit-linked expense (e.g., mileage between visits, supplies) with required ...
- [`caregiver/020-expenses`](caregiver/020-expenses.md) — `/caregiver/expenses/` — My-expenses list for the authenticated caregiver — drafts, submitted, approved, rejected with status filters and per-expense totals.
- [`caregiver/023-earnings`](caregiver/023-earnings.md) — `/caregiver/earnings/` — Caregiver earnings dashboard — period totals (hours, gross pay, mileage, reimbursements) computed by the earnings service.
- [`caregiver/024-weekly`](caregiver/024-weekly.md) — `/caregiver/weekly/` — Weekly summary view (HTML) — per-visit list with client name, hours, pay; supports `?week=YYYY-MM-DD` navigation.
- [`caregiver/025-csv`](caregiver/025-csv.md) — `/caregiver/weekly/csv/` — Weekly summary CSV export — caregiver self-service download for the requesting caregiver's own visits.
- [`caregiver/026-pdf`](caregiver/026-pdf.md) — `/caregiver/weekly/pdf/` — Weekly summary PDF export — caregiver self-service download.
- [`caregiver/027-reports`](caregiver/027-reports.md) — `/caregiver/reports/` — Caregiver self-service report request list — past requests with status, type, requested-on date.
- [`caregiver/028-new`](caregiver/028-new.md) — `/caregiver/reports/new/` — New caregiver report request — pick a client (assigned only), report type, date window; submits to the admin approval queue.

### Client

_No captures — v1 has no Client login portal (Client is an object-of-care, not a User)._

### Family Member

- [`family-member/001-dashboard`](family-member/001-dashboard.md) — `/family/dashboard/` — Family Member home — lists every client the user is linked to via `ClientFamilyMember`, one card per link; uses `effective_user` so View-...
- [`family-member/002-client`](family-member/002-client.md) — `/family/client/<int:client_id>/` — Per-client family portal — calendar, events, messages, billing summary, expense receipts, visit notes, care team, client documents, chart...
- [`family-member/003-billing-pdf`](family-member/003-billing-pdf.md) — `/family/client/<int:client_id>/billing-pdf/` — Family invoice PDF for a single linked client across the selected month; auto-generates a draft `Invoice` from billable visits if none ex...
- [`family-member/004-health-report`](family-member/004-health-report.md) — `/family/client/<int:client_id>/health-report/` — Family-variant health-report PDF for a single linked client, generated on demand with selectable sections and a configurable day window; ...

## Skipped routes

Inventory rows with `not_screenshotted: <reason>` — captured neither in this refresh nor in the catalog history. Reason values are from the [locked taxonomy](../README.md#skip-reason-taxonomy):

- **`no_seed_data`** — fixture lacks the entity (visit / expense / event / uuid:token) needed to render the route. Future fixture expansion would unlock these.
- **`non_html_response`** — endpoint returns a binary file (PDF / CSV / Excel); nothing to render.
- **`destructive_endpoint`** / **`auth_redirect`** / **`gated_by_capability`** / **`no_authenticated_surface`** — intentionally not screenshotted; see taxonomy.

### Agency Admin

| Route | Reason | Purpose |
|-------|--------|---------|
| `/admin/expenses/review/<int:expense_id>/approve/` | `no_seed_data` | Approves a single pending expense submission and routes it to reimbursement. |
| `/admin/expenses/review/<int:expense_id>/reimburse/` | `no_seed_data` | Marks an approved expense as reimbursed and records payment metadata. |
| `/admin/expenses/review/<int:expense_id>/reject/` | `no_seed_data` | Rejects a pending expense with a required reason note. |
| `/admin/invoices/<int:invoice_id>/issue-revision/` | `no_seed_data` | Corrected-invoice editor — reissues an InvoiceRevision with concurrent-issue locking; delta H-severity gap. |
| `/admin/settings/service-catalog/<int:entry_id>/edit/` | `no_seed_data` | Edit an existing billable service catalog entry (re-uses the catalog_form_view). |
| `/admin/settings/service-catalog/<int:entry_id>/retire/` | `no_seed_data` | Soft-retires a catalog entry (per Issue #1214 retire-not-delete pattern); preserves invoice history. |
| `/admin/visit-services/<int:vbs_id>/promote/` | `no_seed_data` | Promotes a one-off VisitBillableService to a recurring rule on the parent CarePlan. |
| `/admin/visits/<int:visit_id>/attach-service/` | `no_seed_data` | Wizard for attaching a billable catalog service to a specific visit, with MD-order proof gate and retired-catalog-entry rejection. |
| `/charting/comments/<int:daily_chart_id>/` | `no_seed_data` | Lists chart comments for a daily chart as an HTML partial; consumed by chart pages and the review queue. |
| `/charting/proxy/<int:visit_id>/` | `no_seed_data` | Proxy charting page — a Care Manager or Agency Admin enters chart data on behalf of a caregiver. |
| `/charting/reports/approval/<int:request_id>/` | `no_seed_data` | Approve-or-reject endpoint for a single caregiver-initiated health-report request (POST-only). |
| `/charting/reports/templates/<int:template_id>/edit/` | `no_seed_data` | Edits a report template — section toggles, ordering, formatting defaults, and PDF security settings. |
| `/clients/<int:client_id>/events/<int:event_id>/attachments/<int:attachment_id>/delete/` | `no_seed_data` | Removes a single attachment record and its underlying stored file from a custom calendar event. |
| `/clients/<int:client_id>/events/<int:event_id>/attachments/upload/` | `no_seed_data` | Multi-file upload endpoint for attachments on a custom calendar event; enforces a 50MB cap and an allowed-extension list. |
| `/clients/<int:client_id>/events/<int:event_id>/delete/` | `no_seed_data` | Soft-delete confirmation for a custom calendar event; supports an AJAX path that returns an undo link. |
| `/clients/<int:client_id>/events/<int:event_id>/edit/` | `no_seed_data` | Edits an existing custom calendar event and surfaces its attachments list for inline management. |
| `/clients/<int:client_id>/events/<int:event_id>/restore/` | `no_seed_data` | Restores a previously soft-deleted custom calendar event (the undo handler paired with the delete flow). |
| `/clients/<int:client_id>/schedule/pdf/` | `non_html_response` | Generates a monthly schedule PDF (calendar-grid or agenda layout) for a client; HIPAA-access-logged in v1. |
| `/compliance/files/visits/<int:visit_id>/physician-order/<int:proof_id>/` | `no_seed_data` | Streams a physician-order proof attachment with forced-attachment + nosniff headers; cross-visit IDOR guarded; audit-logged in v1 with vi... |
| `/compliance/files/visits/<int:visit_id>/signature/<int:signature_id>/` | `no_seed_data` | Streams a service-signature image attachment with forced-attachment + nosniff headers; cross-visit IDOR guarded; audit-logged in v1 with ... |
| `/dashboard/admin/invoices/<int:client_id>/billing-pdf/` | `non_html_response` | Generates and downloads a billing PDF for a single client across the selected period; renders via reportlab. |
| `/dashboard/admin/invoices/<int:invoice_id>/delete/` | `no_seed_data` | Deletes a client invoice and its attached PDF; POST-only; destructive. |
| `/dashboard/admin/timecards/<int:caregiver_id>/pdf/` | `non_html_response` | PDF export of a single caregiver's timecard; renders via reportlab; filename is timestamped. |
| `/dashboard/admin/timecards/export/csv/` | `non_html_response` | CSV export of all-staff timecard data for a period; bulk download for accounting workflows. |
| `/dashboard/admin/timecards/export/excel/` | `non_html_response` | Excel (.xlsx) export of all-staff timecard data for a period; same data as the CSV export with Excel formatting. |
| `/dashboard/admin/timecards/export/pdf/` | `non_html_response` | PDF export of all-staff timecard summary for a period; bulk download. |
| `/employees/invitation/<uuid:token>/` | `no_seed_data` | Caregiver invitation acceptance landing — accepts the UUID invitation token, then collects password and profile in one combined form. |
| `/magic-login/<uuid:token>/` | `no_seed_data` | Consumes a single-use 30-minute magic-link token and signs the user in; explicitly blocked for `is_staff`/`is_superuser` users by the vie... |
| `/password-reset/<uuid:token>/` | `no_seed_data` | Validates a single-use UUID reset token and renders the new-password form; rate-limited at 5/min/IP on POST; audit-logged on consume; adm... |

### Care Manager

| Route | Reason | Purpose |
|-------|--------|---------|
| `/care-manager/client/<int:pk>/` | `no_seed_data` | `Client Focus` — full per-client context for one assigned client across schedule, charting, vitals, and care-request tabs; unassigned-cli... |
| `/care-manager/expenses/<int:expense_id>/edit/` | `no_seed_data` | CM expense edit / resubmit form; submitter-only ownership enforced; resubmits on REJECTED expenses route through `ExpenseService.resubmit... |
| `/care-manager/expenses/<int:expense_id>/receipt/<int:receipt_id>/` | `no_seed_data` | Auth-gated download of an expense receipt; access boundary is the submitter, the linked caregiver, or `is_staff` short-circuit at `care_m... |

### Caregiver

| Route | Reason | Purpose |
|-------|--------|---------|
| `/caregiver/clock-out/<int:visit_id>/` | `no_seed_data` | Clock-out flow — closes the active Visit, captures clock-out GPS and time, transitions caregiver state to POST_SHIFT, and redirects to po... |
| `/caregiver/clock-out/<int:visit_id>/add-comment/` | `no_seed_data` | Adds a comment (with optional receipt attachments, ≤5MB each) to the visit during clock-out flow; redirects to visit_detail if completed,... |
| `/caregiver/clock-out/<int:visit_id>/add-mileage/` | `no_seed_data` | Records visit mileage on the Visit aggregate during clock-out flow. Same view as `/caregiver/visit/<int:visit_id>/add-mileage/`. |
| `/caregiver/clock-out/<int:visit_id>/add-reimbursement/` | `no_seed_data` | Submits a reimbursement expense linked to the visit during clock-out flow — type, amount, description, receipt upload required; auto-flow... |
| `/caregiver/expenses/<int:expense_id>/edit/` | `no_seed_data` | Edits a draft or rejected expense — caregiver-owned expenses only; locked once approved or reimbursed. |
| `/caregiver/expenses/<int:expense_id>/receipt/<int:receipt_id>/` | `no_seed_data` | Streams a single uploaded receipt image scoped to the requesting caregiver — view enforces caregiver ownership of the parent expense (or ... |
| `/caregiver/reports/<int:request_id>/download/` | `no_seed_data` | Download an approved caregiver-self-service report as PDF. |
| `/caregiver/reports/<int:request_id>/preview/` | `no_seed_data` | Preview a generated caregiver report (HTML view) once the admin has approved the request. |
| `/caregiver/shift/<int:shift_id>/clock-in/` | `no_seed_data` | Scheduled clock-in flow — POST-only endpoint (rate-limited 10/hr per user) that validates caregiver-shift assignment, records GPS, create... |
| `/caregiver/shift/<int:visit_id>/active/` | `no_seed_data` | Active shift screen — in-flight visit dashboard during a clocked-in visit, with chart entry, comments, mileage, reimbursement actions. |
| `/caregiver/shift/<int:visit_id>/summary/` | `no_seed_data` | Post-shift summary — wrap-up screen after clock-out reviewing visit duration, billable services performed, comments, attachments before n... |
| `/caregiver/visit/<int:visit_id>/` | `no_seed_data` | Completed visit detail — read-mostly view of a completed visit attached to the Visit aggregate; admins can edit times, caregivers can sti... |
| `/caregiver/visit/<int:visit_id>/add-comment/` | `no_seed_data` | Adds a comment (with optional receipt attachments, ≤5MB each) to the visit from the visit-detail flow. |
| `/caregiver/visit/<int:visit_id>/add-mileage/` | `no_seed_data` | Records visit mileage on the Visit aggregate from the visit-detail flow. Same view as `/caregiver/clock-out/<int:visit_id>/add-mileage/`. |
| `/caregiver/visit/<int:visit_id>/add-reimbursement/` | `no_seed_data` | Submits a reimbursement expense linked to the visit from the visit-detail flow. |
| `/charting/medications/<int:visit_id>/` | `no_seed_data` | Caregiver medication list for the visit — today's scheduled medications grouped by time, with one-tap "Given" documentation and a 5-minut... |
| `/charting/medications/<int:visit_id>/history/` | `no_seed_data` | 7-day medication history for the visit's client — grid view of recent medication administrations. |
| `/charting/visit/<int:visit_id>/chart/` | `no_seed_data` | Caregiver charting page for a single visit — section-based chart entry (vitals, glucose, intake/output, bowel-movement, nursing notes) an... |

## Coverage

Run [`../../../scripts/check-v1-catalog-coverage.sh`](../../../scripts/check-v1-catalog-coverage.sh) to verify that every inventory row either has a matching caption file or carries a `not_screenshotted: <reason>` skip-reason. The CI workflow [`v1-catalog-coverage.yml`](../../../.github/workflows/v1-catalog-coverage.yml) runs this check automatically on PRs touching the inventory or this catalog. Current state: **100% coverage, 0 orphans.**

## Generation provenance

This catalog was generated on **2026-05-07** by running the [`tools/v1-screenshot-catalog/`](../../../tools/v1-screenshot-catalog/) crawler against v1 at commit [`9738412a`](https://github.com/hcunanan79/COREcare-access/commit/9738412a6e41064203fc253d9dd2a5c6a9c2e231) with a PHI-scrubbed seed fixture (sha256 [`03b41480…3afdf92`](../../../tools/v1-screenshot-catalog/INVESTIGATIONS.md#fixture-snapshot)). Authoritative crawl ran for ~62 seconds; reproducibility re-run + pixelmatch diff confirmed 166/168 images within the 0.5%-pixel-diff threshold (2 marginal outliers documented in [`reproducibility-report/report.md`](reproducibility-report/report.md)).

The full audit trail — pre-flight gates, network-interception log, PHI placeholder vocabulary used by the fixture, RUN-DATE, route counts — lives in [`RUN-MANIFEST.md`](RUN-MANIFEST.md) alongside the screenshots. Caption bodies (CTAs visible + interaction notes per [`tools/v1-screenshot-catalog/CAPTION-STYLE.md`](../../../tools/v1-screenshot-catalog/CAPTION-STYLE.md)) are tracked in the Phase 3 caption-authoring follow-up issue and land in a follow-up PR.

### Refresh

When v1 advances and the catalog needs a refresh, follow [`tools/v1-screenshot-catalog/PHASE-2-RUNBOOK.md`](../../../tools/v1-screenshot-catalog/PHASE-2-RUNBOOK.md). The runbook documents the v1 bring-up sequence, fixture re-validation, crawler invocation, reproducibility two-run, and PR procedure.
