# V1 Pages Inventory

> **Read [`README.md`](README.md) first.** It locks every convention used here: persona vocabulary, v2-status enum, severity rubric, visual markers, PHI placeholder set, voice, anchor stability, v1 commit pin.

This document is the **authoritative route catalogue** for v1's customer-facing surface. Every other doc in this set cites into it; do not redefine routes elsewhere. One row per (route, persona) tuple — a route accessible to multiple personas appears in multiple rows.

**Status:** SCAFFOLDED. Persona sections are in place; rows are pending content authoring against `suniljames/COREcare-access` at the [pinned commit](README.md#v1-reference-commit). Until rows are filled, the [`v1-functionality-delta.md`](v1-functionality-delta.md) is the most complete view of v1's feature surface.

---

## Coverage

Coverage is measured per persona section, not globally. Each persona's denominator is the count of distinct v1 URL patterns reachable by that persona, rendering HTML, per the rules in [README §Coverage target](README.md#coverage-target).

### Enumeration method (deterministic, reproducible)

```
For each Django app in v1 (suniljames/COREcare-access):
  1. Read app/urls.py — collect every path()/re_path() entry.
  2. Filter to those rendering HTML (skip JsonResponse, redirect-only, static).
  3. For each URL, read the view (FBV or CBV) — confirm the persona can reach
     it (check permission decorators, mixins, get_queryset filters, nav inclusion).
  4. Sum per-persona, per-app. Record both per-app counts and the section total.
```

The denominator is captured BEFORE row authoring begins; the numerator updates as rows are authored.

### Agency Admin

_Enumeration in progress (#81). Per-Django-app denominators below._

| app | denominator | numerator | notes |
|-----|-------------|-----------|-------|
| _(top-level admin routes in elitecare/urls.py)_ | 22 | 22 | Agency Admin admin-prefixed routes outside `include()`; complete |
| billing | 3 | 3 | capability-gated admin custom views; complete |
| billing_catalogs | 4 | 4 | Hazel-managed billable service catalog; complete |
| charting | 22 / 48 raw | 22 | clinical surface; many routes shared with Care Manager and Caregiver, plus 22 JSON-only API endpoints excluded per [README §Coverage target](README.md#coverage-target); complete for Agency Admin |
| clients | 11 | 11 | per-client calendar, events with attachments, schedule PDF/preview; mounted at `schedule/` and `clients/`; complete |
| compliance | 1 | 0 | mounted at `legal/`; mostly customer-facing; pending |
| dashboard | 25 | 0 | agency dashboard, payroll, expenses; pending |
| employees | 3 | 3 | caregiver invitation acceptance + profile-completion onboarding; complete |
| quickbooks_integration | 8 | 8 | QuickBooks OAuth + invoice send + customer linking; complete |
| auth_service | TBD | 0 | shared with all personas; pending |
| _(dual-role / portal switching routes in elitecare/urls.py)_ | 5 | 0 | switch-role, portal-chooser, set-default-portal, clear-default-portal, family-signup; treat as Shared routes |
| **total (Agency Admin, current estimate)** | **~130** | **73 (≈56%)** | denominator finalized after each app's rows land |

**Skipped (the 5% headroom):** none yet enumerated; will populate as remaining apps are authored.

**Status note (2026-05-07).** Issue #81 covers Agency Admin row authoring. As of this commit, the top-level admin routes, `billing`, `billing_catalogs`, `charting` (per #85), `clients` (per #84), `employees` (per #87), and `quickbooks_integration` (per #86) apps are complete; remaining apps (dashboard, compliance, auth_service) and the dual-role/shared routes are pending. Per the committee's halfway-point rule (below 30% coverage triggers a per-app split), follow-up sub-issues author each remaining app independently. See #81 halfway-point check-in for the split plan.

---

---

## Schema

Each persona section below uses this row schema. Authors: do not add or remove columns without updating [README §Locked conventions](README.md#locked-conventions) and the structure check.

| Field | Description |
|-------|-------------|
| `route` | URL pattern (kebab-case where v1 used it; otherwise the literal Django path) |
| `purpose` | What the page is for, ≤80 chars |
| `what_user_sees_can_do` | Key data + primary actions, ≤2 lines |
| `v2_status` | `implemented` / `scaffolded` / `missing` |
| `severity` | `H` / `M` / `L` / `D` (only when `v2_status=missing`) |
| `multi_tenant_refactor` | `true` if v1 single-tenant assumption requires v2 rework |
| `rls_bypass_by_design` | `true` for Super-Admin / View-As impersonation surfaces |
| `phi_displayed` | `true` if route renders any PHI in v1 |
| `screenshot_ref` | filename in `docs/legacy/v1-ui-catalog/<persona>/` once #79 lands; otherwise `not_screenshotted: <reason>` |
| `v2_link` | Single canonical repo-relative path when `v2_status` ≠ `missing` |

---

## Super-Admin

_last reconciled: 2026-05-06 against v1 commit `9738412`_

Super-Admin pages are platform-operator surfaces that bypass tenant isolation by design. v1 was single-tenant per install, so v1's "super-admin" features sit at the elitecare project level (cross-agency Django admin views, support tooling, View-As impersonation). v2 must preserve every audit-log behavior on these routes — RLS bypass is a load-bearing control, not a convenience.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| _(rows pending content authoring)_ | | | | | | | | | |

---

## Agency Admin

_last reconciled: 2026-05-07 against v1 commit `9738412`_

Agency Admin pages cover scheduling, billing, payroll, credentialing, compliance, and team oversight. This is v1's largest surface and v2's highest-volume rebuild target. Rows are grouped by Django app under H3 sub-headings.

### top-level (elitecare/urls.py)
_admin-prefixed routes registered directly in the project root, outside any include()_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/admin/todays-shifts/` | 🔒 PHI · Lists today's shifts grouped by caregiver, with clock-in status, scheduled vs actual hours, and total wages. | Sees: shifts by caregiver, clock status (not_started/clocked_in/completed), summary stats. Can: drill to shift or visit detail. | scaffolded |  | true | false | true | not_screenshotted: pending #79 | api/app/routers/dashboard.py |
| `/admin/open-shifts/` | 🔒 PHI · Lists unassigned shifts ordered by start time, with client and required hours. | Sees: list of shifts without caregiver, total count, total hours. Can: drill to shift to assign. | scaffolded |  | true | false | true | not_screenshotted: pending #79 | api/app/routers/shifts.py |
| `/admin/data-health/` | Reports v1 data integrity counts (orphan records, stale flags, schedule gaps). | Sees: counts and lists of integrity issues across major models. Can: navigate to flagged records to fix. | missing | M | true | false | false | not_screenshotted: pending #79 |  |
| `/admin/view-as/hub/` | View As hub — entry point for staff impersonation of caregivers and family members; audit-logged in v1. | Sees: list of recent View As sessions, search to start a new one. Can: start session by selecting target user. | missing | H | true | true | false | not_screenshotted: pending #79 |  |
| `/admin/view-as/family/select/` | View As family selector — choose a family-member account to impersonate; audit-logged in v1. | Sees: searchable list of family-member accounts. Can: select a target to start session. | missing | H | true | true | false | not_screenshotted: pending #79 |  |
| `/admin/view-as/<int:user_id>/` | View As session start — step-up confirmation before impersonating a target user; audit-logged in v1. | Sees: confirmation form with target identity and session duration. Can: confirm and start the session. | missing | H | true | true | false | not_screenshotted: pending #79 |  |
| `/admin/view-as/caregiver/select/` | View As caregiver selector — choose a caregiver account to impersonate; audit-logged in v1. | Sees: searchable list of caregivers. Can: select a target to start session. | missing | H | true | true | false | not_screenshotted: pending #79 |  |
| `/admin/view-as/caregiver/<int:user_id>/` | View As caregiver session start — step-up confirmation before impersonating a caregiver; audit-logged in v1. | Sees: confirmation form with caregiver identity and session duration. Can: confirm and start. | missing | H | true | true | false | not_screenshotted: pending #79 |  |
| `/admin/view-as/end/` | Ends an active View As session and returns the staff user to their own context; audit-logged in v1. | Sees: confirmation that session ended. Can: navigate back to admin. | missing | H | true | true | false | not_screenshotted: pending #79 |  |
| `/admin/view-as/status/` | Reports active View As session state — used by the impersonation banner and middleware. | Sees: active-session indicator and elapsed time. Can: end the session inline. | missing | H | true | true | false | not_screenshotted: pending #79 |  |
| `/admin/view-as/search/` | User search for selecting a View As target by name or email. | Sees: live search results matching staff-permitted target users. Can: select to advance to step-up. | missing | H | true | true | false | not_screenshotted: pending #79 |  |
| `/admin/view-as/stats/` | View As session statistics — initiated counts, terminations, failed attempts. | Sees: session counts by status, time-window filters. Can: drill to session detail or audit log. | missing | H | true | true | false | not_screenshotted: pending #79 |  |
| `/admin/view-as/kill-all/` | Emergency kill switch for all active View As sessions; audit-logged in v1; superuser-only in v1. | Sees: confirmation prompt with active-session count. Can: terminate all sessions immediately. | missing | H | true | true | false | not_screenshotted: pending #79 |  |
| `/admin/view-as/audit-log/` | View As audit log — IP, action, target, timestamp for every session and forbidden-action attempt. | Sees: chronological audit entries with filters by initiator, target, date. Can: drill into a single session's full action trail. | missing | H | true | true | false | not_screenshotted: pending #79 |  |
| `/admin/expenses/review/` | 🔒 PHI · Lists pending caregiver expense submissions awaiting Agency Admin approval. | Sees: pending expenses with submitter, amount, category, attached receipts. Can: filter, drill to detail, batch select. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/admin/expenses/review/<int:expense_id>/approve/` | Approves a single pending expense submission and routes it to reimbursement. | Sees: confirmation dialog with expense summary. Can: approve and add an optional note. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/admin/expenses/review/<int:expense_id>/reject/` | Rejects a pending expense with a required reason note. | Sees: rejection form requiring a reason. Can: reject and notify the submitter. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/admin/expenses/review/<int:expense_id>/reimburse/` | Marks an approved expense as reimbursed and records payment metadata. | Sees: reimbursement form with payment method and reference number. Can: confirm reimbursement. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/admin/role-permissions/` | Role-based capability management — toggles which capabilities each role grants. | Sees: matrix of roles × capabilities with current grants. Can: navigate to toggle endpoint. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/admin/role-permissions/toggle/` | Toggles a single capability grant for a role; audit-logged in v1. | Sees: toggle confirmation. Can: flip a single capability bit for a role. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/admin/banners/mileage/still-current/` | January annual mileage-rate verification banner CTA — confirms current rate is correct; v1 stores rate as a single SystemSetting, so refactor depends on v2 deciding per-agency vs platform-wide. | Sees: confirmation form with the current mileage rate. Can: confirm rate and dismiss banner for the year. | missing | L | true | false | false | not_screenshotted: pending #79 |  |
| `/admin/banners/mileage/snooze/` | January annual mileage-rate banner snooze CTA — defers the verification reminder; same single-SystemSetting refactor consideration as the still-current CTA. | Sees: snooze confirmation. Can: snooze the banner for a configurable window. | missing | L | true | false | false | not_screenshotted: pending #79 |  |

### billing
_capability-gated admin custom views for visit-service attachment, recurring-service promotion, and corrected-invoice issuance_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/admin/visits/<int:visit_id>/attach-service/` | 🔒 PHI · Wizard for attaching a billable catalog service to a specific visit, with MD-order proof gate and retired-catalog-entry rejection. | Sees: visit summary with client and caregiver, catalog picker, MD-order proof upload, admin note. Can: select catalog entry, upload proof, submit attachment. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/admin/visit-services/<int:vbs_id>/promote/` | 🔒 PHI · Promotes a one-off VisitBillableService to a recurring rule on the parent CarePlan. | Sees: visit-service summary with client and recurrence options. Can: confirm recurrence pattern and promote. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/admin/invoices/<int:invoice_id>/issue-revision/` | 🔒 PHI · Corrected-invoice editor — reissues an InvoiceRevision with concurrent-issue locking; delta H-severity gap. | Sees: original invoice with line items, revision editor with reason field. Can: edit lines, add reason, issue revision. | missing | H | true | false | true | not_screenshotted: pending #79 |  |

### billing_catalogs
_Hazel-managed billable service catalog (#1333 PR 3); delta H-severity gap_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/admin/settings/service-catalog/` | Lists the agency's billable service catalog entries (service name, family-facing label, base price, hourly rate, MD-order requirement, retired flag). | Sees: catalog table with all entries, filter by retired status. Can: navigate to add or edit. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/admin/settings/service-catalog/new/` | Add a new billable service catalog entry. | Sees: catalog form with internal name, family label, base price, est. hours, hourly overage rate, MD-order required toggle. Can: submit to create. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/admin/settings/service-catalog/<int:entry_id>/edit/` | Edit an existing billable service catalog entry (re-uses the catalog_form_view). | Sees: same catalog form pre-filled with current values. Can: edit and save. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/admin/settings/service-catalog/<int:entry_id>/retire/` | Soft-retires a catalog entry (per Issue #1214 retire-not-delete pattern); preserves invoice history. | Sees: confirmation prompt with usage count for the entry. Can: confirm soft-retire. | missing | H | true | false | false | not_screenshotted: pending #79 |  |

### charting
_clinical charting overview, per-client trend views, medication orders, chart-comment review, health-report generation and approval, and proxy charting on behalf of caregivers_

Largest single Django app surface (48 raw `path()` entries). Of the 48, 22 JSON-only API endpoints back the HTML pages and are excluded from the inventory denominator per the `README` rule; 4 HTML routes are Caregiver-primary (visit-keyed medications, caregiver chart view) and are authored under the future `## Caregiver` section. The 22 rows below are the routes Agency Admin reaches as their primary use, verified by `@staff_member_required` decorators in `charting/views.py` (or, for `proxy/<visit_id>/`, an explicit `is_staff or is_care_manager` body check). Permission-decorator and view-source citations live in the source repo; the row prose stays implementation-free.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/charting/overview/` | 🔒 PHI · Lists clients sorted by charting attention priority — overdue, missing today, in progress, complete. | Sees: clients ranked by attention priority with chart-status badges and per-client counts. Can: drill to a client's charting tab. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/client/<int:client_id>/` | 🔒 PHI · Per-client charting tab with active template summary, recent charts, today's stats, and trend links. | Sees: active template name and section list, recent chart history, today's chart counts, medication count. Can: navigate to template wizard, recent charts, trend views, medication orders. | scaffolded |  | true | false | true | not_screenshotted: pending #79 | api/app/routers/charts.py |
| `/charting/client/<int:client_id>/create-template/` | 🔒 PHI · Wizard for adding or editing the client's chart-template sections, items, and inclusion settings. | Sees: section list with included/required/excluded toggles, default item set, exclusion-reason picker. Can: configure sections and items, save the template. | scaffolded |  | true | false | true | not_screenshotted: pending #79 | api/app/routers/charts.py |
| `/charting/vital-signs/<int:client_id>/trend/` | 🔒 PHI · Renders the client's blood pressure, pulse, and temperature trend across a configurable day window. | Sees: time-series chart of systolic/diastolic blood pressure, pulse, temperature; range filters. Can: change the day window. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/glucose/<int:client_id>/trend/` | 🔒 PHI · Renders the client's blood glucose readings as a trend chart with pre/post-meal context flags. | Sees: time-series glucose chart with pre/post-meal markers and target-range bands. Can: change the day window. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/nursing-notes/<int:client_id>/summary/` | 🔒 PHI · Lists the client's nursing notes in chronological order with author, timestamp, and section context. | Sees: chronological nursing-note entries with author and timestamp. Can: drill back to the source chart. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/intake-output/<int:client_id>/trend/` | 🔒 PHI · Renders the client's daily fluid intake and urinary output trend with running balance totals. | Sees: stacked daily intake-and-output chart, balance indicator, range filters. Can: change the day window. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/bowel-movement/<int:client_id>/summary/` | 🔒 PHI · Lists the client's bowel-movement events with consistency, color, and notes grouped by day. | Sees: bowel-movement events per day with consistency, color, notes. Can: drill back to the source chart. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/medications/<int:client_id>/orders/` | 🔒 PHI · Lists the client's active medication orders with dose, route, frequency, start date, and prescriber. | Sees: active medication orders with dose, route, frequency, start date, prescriber. Can: drill into a single order. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/comments/<int:daily_chart_id>/` | 🔒 PHI · Lists chart comments for a daily chart as an HTML partial; consumed by chart pages and the review queue. | Sees: comment list with author, timestamp, content, and family-visibility flag. Can: trigger inline add, soft-delete, or submit-for-review (via JSON endpoints). | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/comments/review-queue/` | 🔒 PHI · Staff queue of chart comments awaiting family-visibility approval, filterable by client. | Sees: pending comments with chart context, submitter, content, and family-visibility flag; client filter. Can: approve, reject, annotate, drill to the chart. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/reports/generate/` | 🔒 PHI · Generates a health-report PDF on demand with client picker, date window, sections, and formatting options. | Sees: client picker, report type (clinical or family), day window, section toggles, orientation, font size, detail-level controls. Can: generate and download the PDF. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/reports/<int:client_id>/clinical/` | 🔒 PHI · Direct clinical-report PDF download endpoint with a configurable day-window query parameter. | Sees: PDF response with no HTML page. Can: trigger the download via direct URL with `?days=7|14|30|90`. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/reports/preview/` | 🔒 PHI · Renders an HTML preview of the health report (clinical or family variant) before PDF generation. | Sees: rendered report sections with PHI content and applied formatting options. Can: tweak inputs and re-preview. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/reports/email/` | 🔒 PHI · Emails a generated health-report PDF to a recipient with an optional cover message; redirects on completion. | Sees: success or error flash message after redirect. Can: submit recipient email and cover message via the generate form. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/reports/batch/` | 🔒 PHI · Generates a zip of health reports for multiple selected clients in a single batch run. | Sees: client multi-select, report type, day window; partial-success warning on errors. Can: submit batch and download the zip. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/reports/templates/` | 🔒 PHI · Lists report-configuration templates and per-client/caregiver overrides for health-report sections. | Sees: templates with section assignments, formatting defaults, security flags; overrides showing caregiver and client targets. Can: navigate to edit a template or add an override. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/reports/templates/<int:template_id>/edit/` | Edits a report template — section toggles, ordering, formatting defaults, and PDF security settings. | Sees: template form with section list, formatting controls, PDF password and watermark settings. Can: save changes. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/charting/reports/approval-queue/` | 🔒 PHI · Staff queue of caregiver-initiated health-report requests awaiting approval before family delivery. | Sees: pending report requests with submitter, client, and sections requested. Can: drill to the approval action. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/reports/approval/<int:request_id>/` | 🔒 PHI · Approve-or-reject endpoint for a single caregiver-initiated health-report request (POST-only). | Sees: success or error flash after redirect to the queue. Can: approve, reject, or annotate the request. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/reports/overrides/add/` | Creates a new ReportAccessOverride mapping a caregiver and/or client to a custom set of report sections. | Sees: success or error flash after redirect. Can: submit caregiver, client, and section selections from the parent template page. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/charting/proxy/<int:visit_id>/` | 🔒 PHI · Proxy charting page — a Care Manager or Agency Admin enters chart data on behalf of a caregiver. | Sees: visit details, full chart sections with proxy-mode badge, audit-required provenance prompts. Can: enter, edit, delete entries, finalize the chart on behalf of the caregiver. | missing | H | true | false | true | not_screenshotted: pending #79 |  |

### clients
_per-client unified calendar (Issue #40); custom non-shift events with attachments; monthly schedule PDF and HTML preview (Issues #455, #1106); the underlying app is dual-mounted at /schedule/ and /clients/_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/clients/schedule/` | Legacy schedule landing — renders an empty placeholder for staff or redirects family-linked users to the family home; dual-mounted at /schedule/schedule/. | Sees: empty schedule placeholder (no shifts preloaded by the legacy view). Can: navigate elsewhere — this URL no longer surfaces real data. | missing | D | true | false | false | not_screenshotted: pending #79 |  |
| `/clients/<int:client_id>/calendar/` | 🔒 PHI · Unified per-client calendar with daily, weekly, and monthly views combining scheduled shifts and custom events. | Sees: client name, calendar grid with shifts and events, caregiver-color legend, DST transition annotations on monthly. Can: switch view mode, navigate dates, drill to detail. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/clients/<int:client_id>/calendar/api/` | 🔒 PHI · JSON calendar feed for the per-client calendar widget; returns shifts and events with title, time, and type. | Sees: serialized calendar entries (id, title with shift or event icon, start, end, className, type, editable). Can: drive the calendar widget asynchronously. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/clients/<int:client_id>/events/create/` | 🔒 PHI · Creates a custom non-shift calendar event (medical appointment, milestone, family note) on a client's calendar. | Sees: client context, event-type picker, title, start and end date and time, location, description fields. Can: submit to create the event and return to the calendar. | missing | L | true | false | true | not_screenshotted: pending #79 |  |
| `/clients/<int:client_id>/events/<int:event_id>/edit/` | 🔒 PHI · Edits an existing custom calendar event and surfaces its attachments list for inline management. | Sees: the same event form pre-filled with current values, attached files list with delete controls. Can: update fields, save, or remove attachments inline. | missing | L | true | false | true | not_screenshotted: pending #79 |  |
| `/clients/<int:client_id>/events/<int:event_id>/delete/` | 🔒 PHI · Soft-delete confirmation for a custom calendar event; supports an AJAX path that returns an undo link. | Sees: confirmation prompt with event title and time. Can: confirm soft-delete via form post or AJAX, then undo via the returned restore link. | missing | L | true | false | true | not_screenshotted: pending #79 |  |
| `/clients/<int:client_id>/events/<int:event_id>/restore/` | 🔒 PHI · Restores a previously soft-deleted custom calendar event (the undo handler paired with the delete flow). | Sees: AJAX success JSON or redirect to the calendar with a success message. Can: trigger via the post-delete undo link. | missing | L | true | false | true | not_screenshotted: pending #79 |  |
| `/clients/<int:client_id>/events/<int:event_id>/attachments/upload/` | 🔒 PHI · Multi-file upload endpoint for attachments on a custom calendar event; enforces a 50MB cap and an allowed-extension list. | Sees: JSON with uploaded list and per-file errors. Can: attach pdf, doc, image, audio, or video files to the event. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/clients/<int:client_id>/events/<int:event_id>/attachments/<int:attachment_id>/delete/` | 🔒 PHI · Removes a single attachment record and its underlying stored file from a custom calendar event. | Sees: AJAX success JSON or redirect back to the event edit form. Can: delete one attachment and free its storage. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/clients/<int:client_id>/schedule/pdf/` | 🔒 PHI · Generates a monthly schedule PDF (calendar-grid or agenda layout) for a client; HIPAA-access-logged in v1. | Sees: downloadable PDF with client name, caregiver names, shift times, optional weekend column. Can: pick format, orientation, font size, color mode, weekend visibility. | missing | L | true | false | true | not_screenshotted: pending #79 |  |
| `/clients/<int:client_id>/schedule/preview/` | 🔒 PHI · HTML preview partial for the print-config panel; mirrors the schedule PDF generator's options without producing a PDF. | Sees: HTML preview rendered with the chosen format and options. Can: re-render with different format, orientation, font size, color, or weekend toggle. | missing | L | true | false | true | not_screenshotted: pending #79 |  |

### employees
_caregiver invitation acceptance and profile-completion onboarding (mounted at `/employees/`); Agency Admin initiates upstream via the invitation send flow_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/employees/invitation/<uuid:token>/` | Caregiver invitation acceptance landing — accepts the UUID invitation token, then collects password and profile in one combined form. | Sees: invitation summary, password setup, profile fields (DOB, contact, optional photo). Can: set password, complete profile, submit to activate the caregiver account. | missing | M | true | false | false | not_screenshotted: pending #79 |  |
| `/employees/complete-profile/` | Profile-completion form for existing caregivers redirected by the v1 ProfileCompletionMiddleware before they can clock in. | Sees: profile fields pre-populated with any data on file (title, DOB, contact, optional photo and bio). Can: save the completed profile and return to the caregiver dashboard. | missing | M | true | false | false | not_screenshotted: pending #79 |  |
| `/employees/complete-profile/draft/` | Auto-save endpoint backing the profile-completion form; persists partial caregiver drafts so entered data survives a reload. | Sees: no UI of its own — invoked by the complete-profile form's auto-save logic. Can: post partial profile data as JSON; receives saved timestamp and field errors. | missing | M | true | false | false | not_screenshotted: pending #79 |  |

### quickbooks_integration
_QuickBooks Online OAuth + invoice send + COREcare-client-to-QB-customer linking; mounted at `quickbooks/` in elitecare/urls.py_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/quickbooks/connect/` | Initiates the QuickBooks Online OAuth flow — redirects an Agency Admin to Intuit's consent screen. | Sees: redirect to Intuit's authorization page. Can: authorize the COREcare app to access the agency's QuickBooks Online company. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/quickbooks/callback/` | Handles the OAuth callback from Intuit; exchanges the auth code for tokens and saves the active connection. | Sees: success or error message on the admin index after the redirect; success shows the connected QuickBooks company name. Can: complete the OAuth handshake. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/quickbooks/disconnect/` | Disconnects the active QuickBooks connection — POST-only; deactivates every active connection row. | Sees: success message on the admin index after POST. Can: confirm the disconnect. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/quickbooks/status/` | Reports QuickBooks connection state as JSON — used by admin pages to render the connection indicator. | Sees: JSON with connected boolean, QuickBooks company name, connected-at timestamp. Can: poll connection status from the admin UI. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/quickbooks/send-invoice/<int:client_id>/` | 🔒 PHI · Sends a client's weekly invoice to QuickBooks; logs the send with a billing snapshot for audit. | Sees: JSON success or detailed error referencing the client name with hints to relink or create a customer. Can: trigger the send via POST with week_offset and an optional QB customer override. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/quickbooks/customers/search/` | 🔒 PHI · Live search across the agency's QuickBooks customers — backs the link-customer modal in Client admin. | Sees: JSON list of matching customers with display name, email, phone, balance. Can: pick a QB customer to link to a COREcare client. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/quickbooks/clients/<int:client_id>/link/` | 🔒 PHI · Links a COREcare client to a QuickBooks customer ID for reliable invoice creation (Issue #329). | Sees: JSON success or duplicate-link error naming the conflicting client. Can: submit a QB customer ID to bind to this client. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/quickbooks/clients/<int:client_id>/unlink/` | Removes the QuickBooks customer link from a COREcare client; clears all link metadata fields. | Sees: JSON success or not-linked error. Can: confirm the unlink via POST. | missing | H | true | false | false | not_screenshotted: pending #79 |  |

---

## Care Manager

_last reconciled: 2026-05-06 against v1 commit `9738412`_

Care Manager pages cover care plan authoring, supervisory review, and team-level oversight of caregivers. Distinct from Agency Admin in clinical scope; distinct from Caregiver in supervisory authority.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| _(rows pending content authoring)_ | | | | | | | | | |

---

## Caregiver

_last reconciled: 2026-05-06 against v1 commit `9738412`_

Caregiver pages are field-facing: clock-in/out, schedule view, chart-note submission, expense submission, profile and credentials. Highest-volume, lowest-patience persona. Mobile-first ergonomics matter most here.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| _(rows pending content authoring)_ | | | | | | | | | |

---

## Client

_last reconciled: 2026-05-06 against v1 commit `9738412`_

Client pages cover the care recipient's view of their care plan, upcoming shifts, and assigned caregivers. Lower frequency than Caregiver; PHI handling is paramount because the client is the subject.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| _(rows pending content authoring)_ | | | | | | | | | |

---

## Family Member

_last reconciled: 2026-05-06 against v1 commit `9738412`_

Family Member pages cover the limited-visibility view granted to a client's authorized representative. Invite redemption, recent visit notes, agency messaging. Lowest frequency; gaps here are the hardest to detect and easiest to silently drop.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| _(rows pending content authoring)_ | | | | | | | | | |

---

## Shared routes

Routes accessible by more than one persona are authored as a row once, in their primary-persona section, and indexed here for cross-reference. This section is the canonical pointer; persona sections do not duplicate rows for shared routes.

| route | primary persona | also reachable by | row location |
|-------|-----------------|-------------------|--------------|
| `/charting/proxy/<int:visit_id>/` | Agency Admin | Care Manager | [Agency Admin → charting](#charting) |
| `/charting/comments/<int:daily_chart_id>/` | Agency Admin | Care Manager, Caregiver | [Agency Admin → charting](#charting) |
| `/charting/visit/<int:visit_id>/chart/` | Caregiver | Agency Admin (oversight, read-only via `is_staff`), Care Manager | (pending Caregiver section) |
| `/charting/medications/<int:visit_id>/` | Caregiver | Agency Admin (visit-context oversight via `is_staff`) | (pending Caregiver section) |
| `/charting/medications/<int:visit_id>/history/` | Caregiver | Agency Admin (visit-context oversight via `is_staff`) | (pending Caregiver section) |
| `/charting/api/chart/save-vitals/` | Caregiver, Agency Admin, Care Manager | (clinical-section save; gated to `is_staff or is_care_manager`) | excluded — JSON API endpoint |
| `/charting/api/chart/save-glucose/` | Caregiver, Agency Admin, Care Manager | (gated to `is_staff or is_care_manager`) | excluded — JSON API endpoint |
| `/charting/api/chart/save-intake-output/` | Caregiver, Agency Admin, Care Manager | (gated to `is_staff or is_care_manager`) | excluded — JSON API endpoint |
| `/charting/api/chart/save-bowel-movement/` | Caregiver, Agency Admin, Care Manager | (gated to `is_staff or is_care_manager`) | excluded — JSON API endpoint |
