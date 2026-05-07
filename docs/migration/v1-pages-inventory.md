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
| _(top-level admin routes in elitecare/urls.py)_ | 21 | 21 | Agency Admin admin-prefixed routes outside `include()`; `/admin/view-as/kill-all/` recategorized to [Super-Admin](#super-admin) per #99 (`@user_passes_test(lambda u: u.is_superuser)`); complete |
| billing | 3 | 3 | capability-gated admin custom views; complete |
| billing_catalogs | 4 | 4 | Hazel-managed billable service catalog; complete |
| charting | 22 / 48 raw | 22 | clinical surface; many routes shared with Care Manager and Caregiver, plus 22 JSON-only API endpoints excluded per [README §Coverage target](README.md#coverage-target); complete for Agency Admin |
| clients | 11 | 11 | per-client calendar, events with attachments, schedule PDF/preview; mounted at `schedule/` and `clients/`; complete |
| compliance | 3 | 3 | mounted at `legal/` + `compliance/files/`; 1 public accessibility page + 2 authenticated PHI file streams; complete |
| dashboard | 10 | 10 | timecard summaries + invoice list + billing exports; complete (Agency-Admin-reachable subset of 25 raw routes) |
| employees | 3 | 3 | caregiver invitation acceptance + profile-completion onboarding; complete |
| quickbooks_integration | 8 | 8 | QuickBooks OAuth + invoice send + customer linking; complete |
| auth_service | 5 | 5 | mounted at root prefix; password-reset flow (4) + magic-link login (1); routes shared across all personas; complete |
| _(dual-role / portal switching routes in elitecare/urls.py)_ | 5 | 0 | switch-role, portal-chooser, set-default-portal, clear-default-portal, family-signup; not Agency-Admin-reachable — authored in [Shared routes](#shared-routes) (#89). |
| **total (Agency Admin)** | **95** | **90 (≈95%)** | per-app sum; the 5 dual-role/shared routes are not Agency-Admin-reachable — authored in [Shared routes](#shared-routes) (#89). |

**Skipped (the 5% headroom from authored apps):**
- `dashboard.portal_home` — redirect-only view (excluded per coverage rule).
- `dashboard.admin_visit_edit` — JSON-only AJAX endpoint (excluded; surfaces in `admin_caregiver_timecard` parent UI).
- `dashboard.admin_billing_email_history` — JSON-only AJAX endpoint (excluded; surfaces in `admin_email_billing_pdf` parent UI).
- `dashboard.api_caregiver_info` — JSON-only API (excluded).
- `dashboard.login`, `dashboard.logout`, `dashboard.offline` — shared with all personas; will be authored under `## Shared routes` (#89).
- `dashboard.family_*` (6 routes) — Family Member persona; out of Agency Admin scope.

**Status note (2026-05-07).** Issue #81 covers Agency Admin row authoring; sub-issues #83–#89 split the work per Django app. All ten Django-app sub-sections are now complete: top-level admin routes, `billing`, `billing_catalogs`, `charting` (per #85), `clients` (per #84), `compliance` (per #88), `dashboard` (per #83), `employees` (per #87), `quickbooks_integration` (per #86), and `auth_service` (per #88). Issue #99 then recategorized the `/admin/view-as/kill-all/` row to the Super-Admin section (one route, programmatically gated to Django superusers) and added the Super-Admin sub-table below. Only the dual-role / shared routes remain (#89) — those land in the file's `## Shared routes` section, not under `## Agency Admin`. Coverage at this commit is **90 / 95 ≈ 95%**, meeting the section's ≥95% target; the remaining 5 dual-role routes are the headroom.

### Super-Admin

_Per-Django-app denominators below._

| app | denominator | numerator | notes |
|-----|-------------|-----------|-------|
| _(top-level admin routes in elitecare/urls.py)_ | 1 | 1 | only `view_as_kill_all` is `@user_passes_test(lambda u: u.is_superuser)` in v1; recategorized from Agency Admin in #99 |
| **total (Super-Admin)** | **1** | **1 (100%)** | per-app sum |

**Skipped (excluded by coverage rule, documented in [Super-Admin → Platform ops endpoints](#platform-ops-endpoints-not-in-row-count-denominator)):**
- `/healthz` — JSON-only.
- `/ops/disk-check/` — JSON-only.
- `/status/` — redirect-only.
- `/admin/api/ops-stats/` — JSON-only.

### Caregiver

_Authored under #101. Per-Django-app denominators below._

| app | denominator | numerator | notes |
|-----|-------------|-----------|-------|
| caregiver_dashboard | 30 / 40 raw | 30 | dominant Caregiver-side surface; 40 raw `path()` entries minus 2 admin-only routes (`admin-payroll/`, `admin-payroll/csv/` — authored under [Agency Admin → dashboard](#dashboard)) and 8 JSON-only routes (last-visit-notes, admin shifts/upload-note, notifications ×3, push subscribe/unsubscribe). Complete. |
| charting | 3 / 48 raw | 3 | Caregiver-primary subset: `visit/<int:visit_id>/chart/`, `medications/<int:visit_id>/`, `medications/<int:visit_id>/history/`; the other HTML charting routes are authored under [Agency Admin → charting](#charting). Complete. |
| **total (Caregiver)** | **33** | **33 (100%)** | per-app sum; shared routes (login/logout/offline + dual-role + magic-login) referenced from [Shared routes](#shared-routes) — canonical magic-login row in [Agency Admin → auth_service](#auth_service). |

**Skipped (not counted in denominator, per coverage rule):**
- `caregiver_dashboard.admin_payroll`, `admin_payroll_csv` — `@staff_member_required`; not Caregiver-reachable. Authored under [Agency Admin → dashboard](#dashboard).
- `caregiver_dashboard.get_last_visit_notes` — JSON API endpoint (`api/clients/<id>/last-visit-notes/`).
- `caregiver_dashboard.admin_get_filtered_shifts`, `admin_upload_visit_note` — JSON admin endpoints.
- `caregiver_dashboard.list_notifications`, `mark_notification_read`, `mark_all_notifications_read` — JSON.
- `caregiver_dashboard.push_subscribe`, `push_unsubscribe` — JSON.
- `charting/api/chart/save-*` (5 routes), `api/chart/finalize/`, `api/chart/catalog-services/`, `api/chart/billable-services/<id>/`, `api/chart/record-billable-service/`, `api/chart/capture-signature/` — JSON chart-save endpoints; surface in the active-shift / caregiver-chart UI. Referenced from the [Shared routes cross-reference index](#cross-reference-index) for traceability.

### Care Manager

| app | denominator | numerator | notes |
|-----|-------------|-----------|-------|
| care_manager | 6 | 6 | dedicated CM portal — caseload, client focus, three CM-expense screens, receipt download; complete |
| charting | 1 (proxy_chart_view, gated `is_staff or is_care_manager`) | 0 | row authored under [Agency Admin → charting](#charting); cross-ref only — no duplicate row in this section |
| **total (Care Manager)** | **7** | **6 (≈86% — see note)** | the single charting row is intentionally not duplicated; coverage of *authored-here* rows is 6/6 = 100%. The 7-route total is the persona's full reachable surface; cross-ref discharges authoring obligation per the #82 convention |

**Excluded charting routes (not Care-Manager-reachable in v1).** Chart-comment review queue, health-report approval queue, all per-client clinical trend / summary / order views, and report-template administration are gated `@staff_member_required` in `charting/views.py` at v1 commit `9738412a`. `CareManagerProfile.is_staff = False`, so CMs do not reach them. ~25 routes total; not enumerated here.

**Excluded redirect-only routes (not counted in denominator).** `/care-manager/dashboard/`, `/care-manager/clients/`, `/care-manager/schedule/`, `/care-manager/requests/` are `RedirectView` permanent redirects to `/care-manager/`; excluded per the README coverage rule.

**Status note (2026-05-07).** Issue #100 closes this section. The cross-ref to `proxy_chart_view` discharges the charting authoring obligation per the row-not-duplicated convention. Excluded routes (per the lead paragraph) total ~25 in `charting/` and are not Care-Manager-reachable in v1.

### Client

_v1 has no Client-as-actor surface — see [the Client section absence note](#client-section) below._

| app | denominator | numerator | notes |
|-----|-------------|-----------|-------|
| _(no Django app reachable by Client persona)_ | 0 | 0 | Client is a model record (`clients.models.Client`), not an authenticator. No URL patterns reachable by a logged-in client. |
| **total (Client)** | **0** | **0** | N/A — section is an absence note, not a row table. |

### Family Member

_Per-Django-app denominators below. Family Member's primary-PHI surface is small (dashboard family-prefixed routes only); other Family-Member-reachable routes (per-client calendar, events, auth flows) are authored under primary-persona sections and indexed in the [Cross-reference index](#cross-reference-index)._

| app | denominator | numerator | notes |
|-----|-------------|-----------|-------|
| dashboard | 4 | 4 | family-prefixed HTML routes; complete |
| **total (Family Member, primary)** | **4** | **4 (100%)** | per-app sum; cross-referenced rows from `clients/` and `auth_service` are not counted in this denominator — they are authored under [Agency Admin](#agency-admin) and indexed in [Shared routes](#shared-routes) |

**Skipped (excluded per coverage rules):**
- `dashboard.family_redirect` — `/family/` is a redirect-only view (`elitecare/urls.py:55–59`).
- `dashboard.family_calendar_event_api` — JSON-only API endpoint (`dashboard/urls.py:75–77`).
- `dashboard.family_caregiver_profile_api` — JSON-only API endpoint (`dashboard/urls.py:80–82`).
- `dashboard.family_home` — deprecated alias to `family_dashboard` (`dashboard/urls.py:13–14`).
- `dashboard.family_signup` — authored in [`## Shared routes` row table](#routes-authored-here-no-primary-persona-section); reached via the `family-signup/` public shortcut and indexed there.

**Status note (2026-05-07).** Issue #103 covers Family Member row authoring. All Family-Member-PRIMARY HTML routes are in `dashboard/` (4 rows). Family-Member-reachable routes that go through `ClientFamilyMember`-link gates — per-client calendar, events, schedule PDF — are authored under [Agency Admin → clients](#clients) and indexed in the [cross-reference index](#cross-reference-index). Coverage at this commit is **4 / 4 = 100%** of primary-PHI Family Member routes.

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

_last reconciled: 2026-05-07 against v1 commit `9738412`_

v1 runs single-tenant per install: each agency has its own dedicated Django/Postgres deployment, and "Super-Admin" is effectively any Django superuser inside that single-agency install. The only HTML route v1 programmatically gates to superusers alone is the View-As emergency kill switch — a backstop the agency's own staff cannot reach by design. v2 is multi-tenant from day one; Super-Admin is the platform-operator persona crossing tenant boundaries by design and the authority on every audit-logged RLS-bypass surface. This section catalogs the one v1 route exclusively reachable by superusers, plus a cross-reference index of every Agency-Admin route a v1 Super-Admin also reaches, plus a non-row subsection documenting the platform ops endpoints excluded from the page-row denominator. Together those three subsections form the spine for v2's operator-portal design.

<a id="super-admin-top-level"></a>
### top-level (elitecare/urls.py)
_admin-prefixed routes registered directly in the project root, outside any include()_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/admin/view-as/kill-all/` | Emergency kill switch for all active View As sessions; audit-logged in v1. | Sees: confirmation prompt with active-session count. Can: terminate all sessions immediately. | missing | H | true | true | false | not_screenshotted: pending #79 |  |

### Cross-reference index
_Routes reachable by both Super-Admin and Agency Admin; canonical row in the linked persona section._

**Curation criteria:** Super-Admin's `is_superuser=True` implies `is_staff=True`, so a Super-Admin reaches every `@staff_member_required` route — i.e., every row currently in `## Agency Admin`. This index is the curated subset where v2's operator portal will need to consider Super-Admin chrome treatment distinct from Agency Admin's: the View-As suite (RLS-bypass surfaces), expense review (financial controls), and role-permissions (capability administration). Routes with `phi_displayed=true` (the four expense-review entries) are the highest cross-tenant HIPAA-minimum-necessary considerations.

| route | also reachable by | content branches by role | phi_displayed | row location |
|-------|-------------------|---------------------------|---------------|--------------|
| `/admin/view-as/hub/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/view-as/family/select/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/view-as/<int:user_id>/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/view-as/caregiver/select/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/view-as/caregiver/<int:user_id>/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/view-as/end/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/view-as/status/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/view-as/search/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/view-as/stats/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/view-as/audit-log/` | Agency Admin | yes — Super-Admin sees all sessions, Agency Admin sees own | false | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/expenses/review/` | Agency Admin | no | true | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/expenses/review/<int:expense_id>/approve/` | Agency Admin | no | true | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/expenses/review/<int:expense_id>/reject/` | Agency Admin | no | true | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/expenses/review/<int:expense_id>/reimburse/` | Agency Admin | no | true | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/role-permissions/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |
| `/admin/role-permissions/toggle/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |

### Platform ops endpoints (not in row-count denominator)

These v1 surfaces are excluded from the Super-Admin row-count denominator (JSON or redirect-only per the [README coverage rule](README.md#coverage-target)) but documented here for v2 ops-surface design parity. Reachability: any authenticated `is_staff` user; the platform-operator persona is the primary consumer during oncall response.

| endpoint | response | purpose | v2 design implication |
|----------|----------|---------|------------------------|
| `/healthz` | JSON | Render uptime probe — short-circuit middleware before session/auth so it works during DB outages. | Vercel will need an equivalent at the v2 web app. FastAPI exposes its own; coordinate the topology. |
| `/ops/disk-check/` | JSON, bearer-token | Render cron call into the web container reporting `/var/data/media/` disk utilization. | v2 storage topology differs (Supabase storage). `severity=D` (deliberate divergence) — not a 1:1 port. |
| `/status/` | redirect | Short-circuits to a GitHub-Pages-hosted dashboard so it remains reachable during full Render outages. | Keep the v2 status page out-of-band for the same reason. v2 design owes a host decision. |
| `/admin/api/ops-stats/` | JSON | Staff-only ops counters consumed by the admin index dashboard widgets. | Ties into v2's dashboard widget set; not an independent operator endpoint. |

---

## Agency Admin

_last reconciled: 2026-05-07 against v1 commit `9738412`_

Agency Admin pages cover scheduling, billing, payroll, credentialing, compliance, and team oversight. This is v1's largest surface and v2's highest-volume rebuild target. Rows are grouped by Django app under H3 sub-headings.

<a id="agency-admin-top-level"></a>
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
| `/charting/reports/<int:client_id>/clinical/` | 🔒 PHI · Direct clinical-report PDF download endpoint with a configurable day-window query parameter. | Sees: PDF response with no HTML page. Can: trigger the download via direct URL with `?days=` set to one of 7, 14, 30, or 90. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
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

### dashboard
_admin timecard summaries, caregiver timecard detail, client invoice list, billing PDF + CSV + Excel exports, billing email_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/dashboard/admin/timecards/` | 🔒 PHI · Lists payroll-period timecard summary across all caregivers, with weekly/monthly/yearly period selection. | Sees: caregivers with hours, pay totals, period boundaries, status. Can: switch period, drill to caregiver detail, navigate to exports. | scaffolded |  | true | false | true | not_screenshotted: pending #79 | api/app/routers/payroll.py |
| `/dashboard/admin/timecards/<int:caregiver_id>/` | 🔒 PHI · Shows individual caregiver's timecard detail for the selected period — visits, clock times, hours, pay. | Sees: caregiver's visits with client, clock in/out, hours, pay. Can: edit a visit's clock times via inline AJAX, switch period. | scaffolded |  | true | false | true | not_screenshotted: pending #79 | api/app/routers/payroll.py |
| `/dashboard/admin/timecards/<int:caregiver_id>/pdf/` | 🔒 PHI · PDF export of a single caregiver's timecard; renders via reportlab; filename is timestamped. | Sees: PDF download containing the caregiver's period timecard. Can: save or print. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/dashboard/admin/timecards/export/pdf/` | 🔒 PHI · PDF export of all-staff timecard summary for a period; bulk download. | Sees: PDF with all caregivers' timecard summary. Can: save or print. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/dashboard/admin/timecards/export/csv/` | 🔒 PHI · CSV export of all-staff timecard data for a period; bulk download for accounting workflows. | Sees: CSV with caregivers, hours, pay. Can: download. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/dashboard/admin/timecards/export/excel/` | 🔒 PHI · Excel (.xlsx) export of all-staff timecard data for a period; same data as the CSV export with Excel formatting. | Sees: XLSX download. Can: open in Excel. | missing | L | true | false | true | not_screenshotted: pending #79 |  |
| `/dashboard/admin/invoices/` | 🔒 PHI · Lists all client invoices, allows uploading new invoice PDFs, and shows the automated weekly billing summary; supports adding standalone reimbursements. | Sees: client invoices with date, amount, attached PDF, plus weekly billing summary, plus reimbursement entries. Can: upload invoice, add reimbursement, navigate to per-invoice actions. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/dashboard/admin/invoices/<int:invoice_id>/delete/` | 🔒 PHI · Deletes a client invoice and its attached PDF; POST-only; destructive. | Sees: confirmation feedback after delete. Can: confirm deletion via the parent invoice list. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/dashboard/admin/invoices/<int:client_id>/billing-pdf/` | 🔒 PHI · Generates and downloads a billing PDF for a single client across the selected period; renders via reportlab. | Sees: PDF download containing the client's billing summary with line items. Can: save or print. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/dashboard/admin/invoices/<int:client_id>/email/` | 🔒 PHI · Form to email the client billing PDF to the client's family members with delivery tracking; logs each send to BillingEmailLog. | Sees: form to compose email, recipient list from linked family members. Can: send email and observe send confirmation. | missing | H | true | false | true | not_screenshotted: pending #79 |  |

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

### compliance
_public accessibility statement + authenticated PHI file downloads (physician-order proofs, service signatures); mounted at `legal/` and `compliance/files/`; routes shared with Care Manager and Caregiver via visit access_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/legal/accessibility/` | Renders the public accessibility statement page with the agency's accessibility contact email and phone; required for state-law accessibility compliance per v1 Issue #274. | Sees: WCAG 2.1 AA / state-law accessibility statement, accessibility contact email and phone. Can: read the statement and reach the published contact. | missing | M | true | false | false | not_screenshotted: pending #79 |  |
| `/compliance/files/visits/<int:visit_id>/physician-order/<int:proof_id>/` | 🔒 PHI · Streams a physician-order proof attachment with forced-attachment + nosniff headers; cross-visit IDOR guarded; audit-logged in v1 with visit, proof, and client identifiers. | Sees: file download initiated by browser. Can: open or save the proof blob. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/compliance/files/visits/<int:visit_id>/signature/<int:signature_id>/` | 🔒 PHI · Streams a service-signature image attachment with forced-attachment + nosniff headers; cross-visit IDOR guarded; audit-logged in v1 with visit, signature, and client identifiers. | Sees: file download initiated by browser. Can: open or save the signature image. | missing | H | true | false | true | not_screenshotted: pending #79 |  |

### auth_service
_password-reset flow (4 routes) + magic-link login (1 route); mounted at root prefix with no path component; magic-link blocks `is_staff`/`is_superuser` users at the view layer; routes shared across all personas_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/password-reset/` | Renders the password-reset request form; rate-limited at 3/hour/IP and timing-safe to defeat email enumeration; audit-logged in v1 with email and user-found flag. | Sees: email input form. Can: submit email to receive a reset link. | missing | D | true | false | false | not_screenshotted: pending #79 |  |
| `/password-reset/sent/` | Renders the post-submit confirmation page after a reset request; intentionally generic copy to avoid revealing whether the email exists. | Sees: generic 'check your email' confirmation. Can: navigate back to sign-in. | missing | D | true | false | false | not_screenshotted: pending #79 |  |
| `/password-reset/<uuid:token>/` | Validates a single-use UUID reset token and renders the new-password form; rate-limited at 5/min/IP on POST; audit-logged on consume; admin password changes notify other admins. | Sees: masked email and new-password fields. Can: submit a new password meeting v1's NIST-aligned validators. | missing | D | true | false | false | not_screenshotted: pending #79 |  |
| `/password-reset/complete/` | Renders the success page after a completed password reset; admin password changes also trigger an admin-notification email in v1. | Sees: confirmation that password was reset. Can: navigate to sign-in. | missing | D | true | false | false | not_screenshotted: pending #79 |  |
| `/magic-login/<uuid:token>/` | Consumes a single-use 30-minute magic-link token and signs the user in; explicitly blocked for `is_staff`/`is_superuser` users by the view; audit-logged on use; redirects to caregiver, family-portal, or default dashboard based on profile. | Sees: redirect to caregiver/family/main dashboard, or invalid-token page. Can: complete one-click login (non-admin users only). | missing | D | true | false | false | not_screenshotted: pending #79 |  |

---

## Care Manager

_last reconciled: 2026-05-07 against v1 commit `9738412`_

Care Manager is a dedicated role profile (`CareManagerProfile`, OneToOne with User, `is_staff=False`) — a caseload-first portal of six pages where a CM sees their assigned clients and submits the small expenses they incur in the field. v1's chart-comment review queue, health-report approval queue, per-client clinical trend and order views, and report-template administration are gated `@staff_member_required` in `charting/views.py` at v1 commit `9738412a`; CMs do not reach them, and v2 must not collapse this gate by granting CMs `is_staff`. Audit-log behavior in the CM portal is uneven — `ExpenseService` logs status transitions on submit/edit/resubmit, but `cm_serve_receipt` does not log downloads, and clinical-tab access inside `cm_client_focus` inherits whatever logging the underlying `charting` services emit; each row's `purpose` cell calls out where v1 audit-logs and where v2 must add coverage. The `proxy_chart_view` row lives under [Agency Admin → charting](#charting); see the [cross-reference index](#cross-reference-index) for dual-role portal switching, password reset, magic-link login, and the receipt-route Agency Admin oversight path.

### care_manager
_six HTML routes mounted at `/care-manager/` per `elitecare/urls.py` line 179: caseload, per-client focus, CM expense list, expense submit, expense edit, expense receipt download; four legacy `RedirectView` URLs (`/dashboard/`, `/clients/`, `/schedule/`, `/requests/`) are excluded per the README coverage rule_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/care-manager/` | 🔒 PHI · `My Caseload` — priority-sorted list of every client assigned to this CM, with attention queue and all-clear groups; scope enforced by `CareManagerService.get_assigned_client_ids`; v1 does not audit-log this surface. | Sees: assigned clients with severity-colored attention badges, action queue with caregiver and client context, all-clear group, daily summary. Can: drill to a client's focus page, dismiss or annotate actions via the inline notify links. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/care-manager/client/<int:pk>/` | 🔒 PHI · `Client Focus` — full per-client context for one assigned client across schedule, charting, vitals, and care-request tabs; unassigned-client access raises Http404; clinical-tab audit logging inherits whatever the underlying `charting` services emit (verify per-tab in v2 design). | Sees: client demographics with diagnosis and DNR badge, alert-badge strip, care-team caregiver cards with phone and email, family-member contacts, tab-specific data (schedule grid, charting rollup, vitals trend, request list) with notification dots per tab. Can: switch tabs via querystring, drill to caregivers and family members, take per-tab actions surfaced by the action queue. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/care-manager/expenses/` | 🔒 PHI · CM expense list grouped per assigned client, with budget status; status transitions on the linked expenses are audit-logged via `ExpenseService` workflow events but the list view itself is not. | Sees: per-client expense groupings with status, amount, expense type, submission date; budget status banner; receipt thumbnails. Can: drill to a single expense to edit or resubmit, navigate to the submission form, open a receipt. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/care-manager/expenses/submit/` | 🔒 PHI · CM expense submission form scoped to assigned clients; submission audit-logged via `ExpenseService.create_expense` workflow events. | Sees: budget status, expense-type picker, amount, description, expense date, client picker (assigned clients only), payment-method radio, receipt upload. Can: submit an expense with a single attached receipt; success returns to the expense list with a flash message. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/care-manager/expenses/<int:expense_id>/edit/` | 🔒 PHI · CM expense edit / resubmit form; submitter-only ownership enforced; resubmits on REJECTED expenses route through `ExpenseService.resubmit_expense`, edits route through `ExpenseService.edit_expense` — both audit-logged via workflow events. | Sees: pre-filled form mirroring the submit page with the linked client locked, current status, and an optional receipt upload. Can: update fields and save, attach a new receipt (replaces the previous one), or resubmit a rejected expense. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/care-manager/expenses/<int:expense_id>/receipt/<int:receipt_id>/` | 🔒 PHI · Auth-gated download of an expense receipt; access boundary is the submitter, the linked caregiver, or `is_staff` short-circuit at `care_manager/views.py:733` (Agency Admin oversight path); receipt is verified-bound to its parent expense via `get_object_or_404(ExpenseReceipt, pk=receipt_id, expense=expense)` to prevent cross-receipt IDOR; **v1 has no audit on this route — v2 design must add**. | Sees: file download initiated by the browser with `Content-Disposition: attachment` and a sanitized filename. Can: open or save the receipt blob. | missing | H | true | false | true | not_screenshotted: pending #79 |  |

---

## Caregiver

_last reconciled: 2026-05-07 against v1 commit `9738412`_

Caregiver pages are first-person field-flow surfaces — the actor is always the authenticated caregiver, and every route's row-level scope reduces to `caregiver_id = self` or `visit_id ∈ self.assigned_visits`. The dominant aggregate is **Visit**: clock state, mileage, expense reimbursements, and charting all attach to a Visit, and most routes are keyed on `<int:visit_id>`. v1's `ProfileCompletionMiddleware` redirects the caregiver to `/employees/complete-profile/` (authored under [Agency Admin → employees](#employees)) until the profile is complete; v2 must preserve this gate. Caregivers' own names render across these routes; `phi_displayed` continues to mean *client*-PHI per the README convention. Login/logout/offline, dual-role switching, and magic-link login are referenced via [Shared routes](#shared-routes); the canonical magic-login row lives in [Agency Admin → auth_service](#auth_service).

### caregiver_dashboard
_clock-in/out, schedule view, expense submission, weekly summary, caregiver self-service reports, profile and onboarding (mounted at `/caregiver/`)_

Largest single Caregiver-side surface (40 raw `path()` entries in `caregiver_dashboard/urls.py`). Of the 40, 2 are admin-only (`admin-payroll/`, `admin-payroll/csv/` — `@staff_member_required`, authored under [Agency Admin → dashboard](#dashboard) where the broader payroll surface lives) and 8 are JSON-only (last-visit-notes, admin shifts/upload-note, notifications, push subscribe/unsubscribe), excluded per the [README's coverage rule](README.md#coverage-target). The 30 rows below are workflow-ordered: pre-shift orientation → clock-in → in-shift → annotations → expenses → earnings → reports.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/caregiver/onboarding/` | 3-step onboarding wizard for new caregivers — personal info, document upload, welcome tour. | Sees: progress steps with phone, DOB, address, emergency contact (step 1), Gov ID/cert/TB document upload (step 2), welcome tour (step 3). Can: submit each step, jump back to previous, skip the optional tour. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/caregiver/profile/` | 🔒 PHI · Caregiver's own profile-completion form — title, DOB, contact, optional photo and bio; auto-saves via the `/employees/complete-profile/draft/` endpoint. | Sees: profile fields pre-populated with any data on file, document list, save status. Can: update profile fields, upload photo, save and return to dashboard. | missing | H | true | false | false | not_screenshotted: pending #79 |  |
| `/caregiver/dashboard/` | 🔒 PHI · Daily caregiver landing page — state-machine-driven (IDLE / EMPTY / ACTIVE / POST_SHIFT) showing today's shift, clock-in/out actions, and weekly summary cards. v1 has offline fallback on this route via service worker. | Sees: today's assigned shift with client name, clock state, expense pending count, unread notifications. Can: launch clock-in, navigate to schedule, drill to active shift, review expenses. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/schedule/` | 🔒 PHI · Monthly caregiver schedule with daily/weekly/monthly view modes; navigates by date, displays shifts with client name and time block. | Sees: calendar grid with shifts per day, client names, shift type, week strip with today highlighted. Can: switch view mode, navigate dates, drill to a shift. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/shift-offers/` | 🔒 PHI · Shift offers page — pending shift assignments with inline accept/decline and per-offer earnings estimate. | Sees: pending offers with client name, start/end time, duration, earnings estimate, decline-reason picker. Can: accept inline, decline with reason. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/shift/<int:shift_id>/clock-in/` | 🔒 PHI · Scheduled clock-in flow — POST-only endpoint (rate-limited 10/hr per user) that validates caregiver-shift assignment, records GPS, creates the Visit, and redirects to active shift. v1 has offline fallback via PWA queue. | Sees: success or validation flash after redirect to active shift. Can: submit clock-in with GPS coordinates from the dashboard. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/clock/` | 🔒 PHI · Unscheduled clock-in entry page — caregiver picks a client and starts an ad-hoc Visit when no shift is assigned (e.g., last-minute coverage). v1 has offline fallback via service worker. | Sees: client picker, GPS prompt, validation messages. Can: select a client and start an unscheduled visit, attaching GPS and timestamp. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/shift/<int:visit_id>/active/` | 🔒 PHI · Active shift screen — in-flight visit dashboard during a clocked-in visit, with chart entry, comments, mileage, reimbursement actions. | Sees: visit timer, client info, chart entry buttons, comment thread, mileage and reimbursement totals. Can: enter chart data, add comments, log mileage, submit reimbursements, advance to clock-out. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/visit/<int:visit_id>/` | 🔒 PHI · Completed visit detail — read-mostly view of a completed visit attached to the Visit aggregate; admins can edit times, caregivers can still add notes/mileage/receipts/comments. v1 lazily creates the chart on first read. | Sees: visit summary with client, clock in/out, duration, comments, attachments, chart link. Can: add comments, mileage, reimbursements; admins additionally edit clock times. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/clock-out/<int:visit_id>/` | 🔒 PHI · Clock-out flow — closes the active Visit, captures clock-out GPS and time, transitions caregiver state to POST_SHIFT, and redirects to post-shift summary. v1 has offline fallback for delayed clock-out. | Sees: clock-out confirmation with end time and duration, validation messages. Can: submit clock-out, attach optional final note. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/shift/<int:visit_id>/summary/` | 🔒 PHI · Post-shift summary — wrap-up screen after clock-out reviewing visit duration, billable services performed, comments, attachments before navigating away. | Sees: visit summary with hours, client, services, comment count, attachment count. Can: review and dismiss; lazy-creates chart on view if missing. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/clock-out/<int:visit_id>/add-comment/` | 🔒 PHI · Adds a comment (with optional receipt attachments, ≤5MB each) to the visit during clock-out flow; redirects to visit_detail if completed, else active_shift. Same view as `/caregiver/visit/<int:visit_id>/add-comment/`. | Sees: comment form with text + multi-file picker, success or per-file validation flash after redirect. Can: submit comment text, attach receipt photos. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/visit/<int:visit_id>/add-comment/` | 🔒 PHI · Adds a comment (with optional receipt attachments, ≤5MB each) to the visit from the visit-detail flow. Same view as `/caregiver/clock-out/<int:visit_id>/add-comment/`. | Sees: comment form with text + multi-file picker, success or per-file validation flash after redirect. Can: submit comment text, attach receipt photos. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/clock-out/<int:visit_id>/add-mileage/` | 🔒 PHI · Records visit mileage on the Visit aggregate during clock-out flow. Same view as `/caregiver/visit/<int:visit_id>/add-mileage/`. | Sees: mileage input form, success flash after redirect. Can: enter mileage in miles. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/visit/<int:visit_id>/add-mileage/` | 🔒 PHI · Records visit mileage on the Visit aggregate from the visit-detail flow. Same view as `/caregiver/clock-out/<int:visit_id>/add-mileage/`. | Sees: mileage input form, success flash after redirect. Can: enter mileage in miles. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/clock-out/<int:visit_id>/add-reimbursement/` | 🔒 PHI · Submits a reimbursement expense linked to the visit during clock-out flow — type, amount, description, receipt upload required; auto-flows into client weekly invoice. Same view as `/caregiver/visit/<int:visit_id>/add-reimbursement/`. | Sees: expense type picker, amount, description, required receipt upload, validation messages. Can: submit a per-visit reimbursement that creates an Expense linked to the shift. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/visit/<int:visit_id>/add-reimbursement/` | 🔒 PHI · Submits a reimbursement expense linked to the visit from the visit-detail flow. Same view as `/caregiver/clock-out/<int:visit_id>/add-reimbursement/`. | Sees: expense type picker, amount, description, required receipt upload, validation messages. Can: submit a per-visit reimbursement that creates an Expense linked to the shift. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/clients/<int:client_id>/` | 🔒 PHI · Caregiver-side client profile — read-only view of the client's care details available to assigned caregivers; surfaces care preferences, contact, ADL summary. | Sees: client name, contact, care plan summary, recent visit notes, care preferences. Can: navigate back to schedule or active shift. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/expenses/submit/` | 🔒 PHI · Standalone expense submission form — caregiver submits a non-visit-linked expense (e.g., mileage between visits, supplies) with required receipt; nine fixed expense classes. | Sees: expense type picker, amount, description, mandatory receipt upload, validation messages. Can: submit a stand-alone Expense (status SUBMITTED). | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/expenses/` | 🔒 PHI · My-expenses list for the authenticated caregiver — drafts, submitted, approved, rejected with status filters and per-expense totals. | Sees: expenses grouped by status with amount, type, submitted date, visit linkage. Can: drill into an expense to edit, view receipt, or see admin notes. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/expenses/<int:expense_id>/edit/` | 🔒 PHI · Edits a draft or rejected expense — caregiver-owned expenses only; locked once approved or reimbursed. | Sees: editable expense form with prior values, status badge, receipt list. Can: update fields, replace receipt, resubmit. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/expenses/<int:expense_id>/receipt/<int:receipt_id>/` | 🔒 PHI · Streams a single uploaded receipt image scoped to the requesting caregiver — view enforces caregiver ownership of the parent expense (or `is_staff`); v1 has no HIPAA access log on this stream — v2 must add. | Sees: binary file response (Content-Disposition attachment) with sanitized filename. Can: download the receipt image. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/earnings/` | 🔒 PHI · Caregiver earnings dashboard — period totals (hours, gross pay, mileage, reimbursements) computed by the earnings service. | Sees: period selector, hours, gross pay, mileage total, reimbursement total, per-week breakdown. Can: switch periods, drill to weekly summary. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/weekly/` | 🔒 PHI · Weekly summary view (HTML) — per-visit list with client name, hours, pay; supports `?week=YYYY-MM-DD` navigation. | Sees: visits in selected week with client, clock times, hours, pay; weekly totals. Can: navigate weeks, jump to CSV/PDF export. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/weekly/csv/` | 🔒 PHI · Weekly summary CSV export — caregiver self-service download for the requesting caregiver's own visits. | Sees: CSV download with visit rows. Can: open in spreadsheet apps. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/weekly/pdf/` | 🔒 PHI · Weekly summary PDF export — caregiver self-service download. | Sees: PDF download with visit summary table and totals. Can: save or print. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/reports/` | 🔒 PHI · Caregiver self-service report request list — past requests with status, type, requested-on date. | Sees: prior report requests with status (pending, approved, rejected), client, type, date. Can: drill to a request, request a new report. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/reports/new/` | 🔒 PHI · New caregiver report request — pick a client (assigned only), report type, date window; submits to the admin approval queue. | Sees: client picker (assigned clients only), report type, date window inputs, validation. Can: submit a request that lands in `/charting/reports/approval-queue/`. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/reports/<int:request_id>/preview/` | 🔒 PHI · Preview a generated caregiver report (HTML view) once the admin has approved the request. | Sees: rendered report sections with client PHI per the granted access scope. Can: review before downloading. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/caregiver/reports/<int:request_id>/download/` | 🔒 PHI · Download an approved caregiver-self-service report as PDF. | Sees: PDF download with report content. Can: save or print. | missing | M | true | false | true | not_screenshotted: pending #79 |  |

### charting

<a id="caregiver-charting"></a>

_caregiver-side chart entry and visit-keyed medication views (the routes flagged Caregiver-primary in the charting H3 of [Agency Admin → charting](#charting))_

Three Caregiver-primary HTML routes from the `charting/` app — `@login_required` without `@staff_member_required`, with view-body checks tying access to the visit's caregiver (`charting/views.py` lines 480, 503, 1150 at v1 commit `9738412`). The remaining 22 HTML routes in `charting/` are Agency Admin / Care Manager primary and are authored under [Agency Admin → charting](#charting); JSON chart-save APIs (`/charting/api/chart/save-*`) are excluded per the coverage rule but referenced from the [Shared routes cross-reference index](#cross-reference-index) for traceability.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/charting/visit/<int:visit_id>/chart/` | 🔒 PHI · Caregiver charting page for a single visit — section-based chart entry (vitals, glucose, intake/output, bowel-movement, nursing notes) and finalize action; lazy-creates the chart on GET if missing. | Sees: chart sections with prior entries, billable-services list, signature capture prompt, finalize button. Can: enter section data via JSON-save endpoints, add comments, capture signature, finalize. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/medications/<int:visit_id>/` | 🔒 PHI · Caregiver medication list for the visit — today's scheduled medications grouped by time, with one-tap "Given" documentation and a 5-minute undo window. | Sees: medication groups by scheduled time with name, dose, route; documented status; undo countdown for recently-given items. Can: tap "Given" (POSTs to `/charting/api/medications/document/`), undo within window. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/charting/medications/<int:visit_id>/history/` | 🔒 PHI · 7-day medication history for the visit's client — grid view of recent medication administrations. | Sees: 7-day grid with medication names and given/missed status per scheduled time. Can: review prior administration history; navigation back to medication list. | missing | H | true | false | true | not_screenshotted: pending #79 |  |

---

## Client

<a id="client-section"></a>

_last reconciled: 2026-05-07 against v1 commit `9738412`_

**v1 has no Client-as-actor surface.** Clients are subjects of care, not authenticators. `clients/models.py:15` defines `class Client(models.Model)` with no `User` linkage; the only `User` linkage in the `clients/` app is `class ClientFamilyMember` at `clients/models.py:392`, whose `user = ForeignKey(settings.AUTH_USER_MODEL)` field at `clients/models.py:400` binds a Family Member account to a Client record. Every `<int:client_id>`-parameterized URL pattern in v1 is reached by staff (Agency Admin, Care Manager, Caregiver) under `@staff_member_required` / role decorators, or by a linked Family Member under the `ClientFamilyMember` relationship — never by a logged-in client. v1 carries zero `@client_required`-style decorators (verified by source grep at the pinned commit). The `.claude/pm-context.md` `Stakeholders` table aligns with this reality: it lists Super-Admin, Agency Admin, Care Manager, Caregiver, and Family Member as personas; Client appears in the `Domain Vocabulary` table as a subject term, not in `Stakeholders` as an actor.

**Where client-data visibility actually lives in v1.** Inventory rows that render a client's PHI live under other persona sections:

- the [Family Member section](#family-member) of this inventory — the Family Member persona reaches client-linked dashboards, billing PDFs, health-report downloads, and event calendars under the `ClientFamilyMember` linkage (rows authored under #103).
- [Agency Admin → clients](#clients) — staff reach the per-client unified calendar, custom event creation, attachments, and schedule PDF/preview (rows authored under #84).
- [Agency Admin → charting](#charting) — staff reach the per-client charting tab, trend views, medication orders, chart-comment review, health-report generation and approval, and proxy charting (rows authored under #85).

**v2 product question.** Whether v2 adds an authenticated Client portal as a deliberate divergence from v1 — and the implied new Clerk role plus per-client RLS policy — is tracked separately in [#109](https://github.com/suniljames/COREcare-v2/issues/109) (`needs-pm-input`). This inventory section is faithful to v1 and is intentionally empty of rows.

---

## Family Member

_last reconciled: 2026-05-07 against v1 commit `9738412`_

Family Member pages serve a client's authorized representative — typically a spouse, adult child, or designated POA. v1 grants visibility through a per-(client, user) link recorded in `ClientFamilyMember`; a single Family Member account may be linked to multiple clients. Every row in this section renders PHI scoped to the user's links (linked-client only). Rows lacking the `🔒 PHI · ` prefix or the explicit "linked-client only" scope clause are bugs, not editorial choices.

v1 enforces this scope via Python checks in view bodies (see `clients/views.py:55–59` and `clients/services/family_portal_service.py:142`). v2 must enforce equivalent visibility at the RLS-policy layer keyed on `client_family_members`. Reviewers of v2 family-portal `/design` cycles should treat absence of that policy as a blocking gap.

**v1 has no active-flag on `ClientFamilyMember`** — no soft-delete, no revoked-at, no expiry; the model carries only `unique_together(client, user)` plus per-link permission booleans (`can_view_schedule`, `can_message_caregivers`). Revocation requires hard-delete in v1; v2 design must add a soft-revocation path so audit trails of past family-member access survive after a link ends.

Staff impersonation of Family Member sessions occurs via [Agency Admin's View-As surfaces](#top-level-elitecareurlspy) — those are audit-logged in v1 and must remain audit-logged in v2.

Lowest-frequency persona; gaps are the hardest to detect and the easiest to silently drop. The denominator is small but the visibility-scope discipline is the entire point.

### dashboard
_family portal landing, per-client detail, billing PDF, health-report PDF; mounted under `/family/` in `dashboard/urls.py`_

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/family/dashboard/` | 🔒 PHI · Family Member home — lists every client the user is linked to via `ClientFamilyMember`, one card per link; uses `effective_user` so View-As sessions render the impersonated user's links. linked-client only; v1 has no audit on this route — v2 design must add. | Sees: card per linked client with client name and quick links into the per-client detail page; greeting. Can: drill into a client's family detail page. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/family/client/<int:client_id>/` | 🔒 PHI · Per-client family portal — calendar, events, messages, billing summary, expense receipts, visit notes, care team, client documents, charting summaries, family-visibility-approved chart comments; POST submits a care-request message gated by the link's `can_message_caregivers` flag. linked-client only; v1 has no audit on this route — v2 design must add (chart-comment family-views are logged separately via `ChartCommentService.log_family_view`). | Sees: weekly/daily calendar, today's events, recent messages, billing summary, recent visit notes, care team, family-approved chart comments. Can: submit a care-request message (rate-limited 5/min), navigate calendar by week, drill into linked detail surfaces. | missing | H | true | false | true | not_screenshotted: pending #79 |  |
| `/family/client/<int:client_id>/billing-pdf/` | 🔒 PHI · Family invoice PDF for a single linked client across the selected month; auto-generates a draft `Invoice` from billable visits if none exists; rate-limited 10/h per user. linked-client only; HIPAA-access-logged in v1. | Sees: PDF download initiated by browser. Can: pick month/year/revision via query params; open or save the PDF. | missing | M | true | false | true | not_screenshotted: pending #79 |  |
| `/family/client/<int:client_id>/health-report/` | 🔒 PHI · Family-variant health-report PDF for a single linked client, generated on demand with selectable sections and a configurable day window; IDOR-protected via `FamilyPortalService.verify_access`; rate-limited 10/h per user. linked-client only; HIPAA-access-logged in v1. | Sees: PDF download initiated by browser. Can: pick day window (7/14/30/90) and section subset via query params; open or save the PDF. | missing | M | true | false | true | not_screenshotted: pending #79 |  |

### clients
_per-client calendar + events + schedule PDF reached via `ClientFamilyMember` link gate (`clients/views.py:_check_client_access`); rows authored under [Agency Admin → clients](#clients) and indexed in [Cross-reference index](#cross-reference-index)._

### charting
_chart comments approved with the family-visibility flag are surfaced inside `/family/client/<int:client_id>/` (Phase A2 — `ChartCommentService.log_family_view` audit-logs each surfacing); no Family-Member-direct charting routes exist in v1._

### auth_service
_password-reset flow + magic-login reach Family Member; rows authored under [Agency Admin → auth_service](#auth_service) and indexed in [Cross-reference index](#cross-reference-index)._

---

## Shared routes

_last reconciled: 2026-05-07 against v1 commit `9738412`_

Shared routes serve more than one persona, or sit outside any single persona's surface. v1 has two flavors:

1. **Routes whose row is authored in a primary-persona section and referenced here for discoverability** — listed in the cross-reference index below. These do not duplicate rows; the index points at the persona section that owns the canonical row.
2. **Routes that don't fit any single persona section** — authored in the row table at the bottom of this section. v1 currently has five such routes from `elitecare/urls.py` (project-root registrations outside any app's `include()`): four dual-role portal-switching routes from v1 issue #1224 (gated on a user holding both `caregiver_profile` and `care_manager_profile`; v1 code in `core/dual_role_views.py`, eligibility derived by `core/services/role_service.py:RoleService.get_available_roles`) and one public, rate-limited family self-registration shortcut from v1 issue #65 (`dashboard/views.py:family_signup`, `5/h` per IP).

### Cross-reference index

Routes whose canonical row lives in a persona section.

| route | primary persona | also reachable by | row location |
|-------|-----------------|-------------------|--------------|
| `/charting/proxy/<int:visit_id>/` | Agency Admin | Care Manager | [Agency Admin → charting](#charting) |
| `/charting/comments/<int:daily_chart_id>/` | Agency Admin | Care Manager, Caregiver (family-visibility-approved comments surface inside `/family/client/<int:client_id>/` via `ChartCommentService.log_family_view`; the route itself is not Family-Member-direct) | [Agency Admin → charting](#charting) |
| `/charting/visit/<int:visit_id>/chart/` | Caregiver | Agency Admin (oversight, read-only via `is_staff`), Care Manager | [Caregiver → charting](#caregiver-charting) |
| `/charting/medications/<int:visit_id>/` | Caregiver | Agency Admin (visit-context oversight via `is_staff`) | [Caregiver → charting](#caregiver-charting) |
| `/charting/medications/<int:visit_id>/history/` | Caregiver | Agency Admin (visit-context oversight via `is_staff`) | [Caregiver → charting](#caregiver-charting) |
| `/charting/api/chart/save-vitals/` | Caregiver, Agency Admin, Care Manager | (clinical-section save; gated to `is_staff or is_care_manager`) | excluded — JSON API endpoint |
| `/charting/api/chart/save-glucose/` | Caregiver, Agency Admin, Care Manager | (gated to `is_staff or is_care_manager`) | excluded — JSON API endpoint |
| `/charting/api/chart/save-intake-output/` | Caregiver, Agency Admin, Care Manager | (gated to `is_staff or is_care_manager`) | excluded — JSON API endpoint |
| `/charting/api/chart/save-bowel-movement/` | Caregiver, Agency Admin, Care Manager | (gated to `is_staff or is_care_manager`) | excluded — JSON API endpoint |
| `/clients/<int:client_id>/calendar/` | Agency Admin | Family Member (via `ClientFamilyMember` link gate; staff bypass returns `link=None`) | [Agency Admin → clients](#clients) |
| `/clients/<int:client_id>/calendar/api/` | Agency Admin | Family Member (same family-link gate; powers the calendar widget) | [Agency Admin → clients](#clients) |
| `/clients/<int:client_id>/events/create/` | Agency Admin | Family Member (`can_add_events = is_family or is_admin`) | [Agency Admin → clients](#clients) |
| `/clients/<int:client_id>/events/<int:event_id>/edit/` | Agency Admin | Family Member (`can_edit_events = is_family or is_caregiver` — caregiver reachability authored under future Caregiver section) | [Agency Admin → clients](#clients) |
| `/clients/<int:client_id>/events/<int:event_id>/delete/` | Agency Admin | Family Member (family-link gate) | [Agency Admin → clients](#clients) |
| `/clients/<int:client_id>/events/<int:event_id>/restore/` | Agency Admin | Family Member (family-link gate; AJAX undo handler) | [Agency Admin → clients](#clients) |
| `/clients/<int:client_id>/events/<int:event_id>/attachments/upload/` | Agency Admin | Family Member (family-link gate) | [Agency Admin → clients](#clients) |
| `/clients/<int:client_id>/events/<int:event_id>/attachments/<int:attachment_id>/delete/` | Agency Admin | Family Member (family-link gate) | [Agency Admin → clients](#clients) |
| `/clients/<int:client_id>/schedule/pdf/` | Agency Admin | Family Member (family-link gate; HIPAA-access-logged in v1) | [Agency Admin → clients](#clients) |
| `/clients/<int:client_id>/schedule/preview/` | Agency Admin | Family Member (family-link gate) | [Agency Admin → clients](#clients) |
| `/legal/accessibility/` | Agency Admin | all other personas + unauthenticated visitors (public page) | [Agency Admin → compliance](#compliance) |
| `/compliance/files/visits/<int:visit_id>/physician-order/<int:proof_id>/` | Agency Admin | Care Manager, Caregiver (gated by `@require_visit_access`) | [Agency Admin → compliance](#compliance) |
| `/compliance/files/visits/<int:visit_id>/signature/<int:signature_id>/` | Agency Admin | Care Manager, Caregiver (gated by `@require_visit_access`) | [Agency Admin → compliance](#compliance) |
| `/password-reset/` | Agency Admin | all other personas (auth flow open to every persona with a password) | [Agency Admin → auth_service](#auth_service) |
| `/password-reset/sent/` | Agency Admin | all other personas | [Agency Admin → auth_service](#auth_service) |
| `/password-reset/<uuid:token>/` | Agency Admin | all other personas | [Agency Admin → auth_service](#auth_service) |
| `/password-reset/complete/` | Agency Admin | all other personas | [Agency Admin → auth_service](#auth_service) |
| `/magic-login/<uuid:token>/` | Caregiver | Client, Family Member (admin users `is_staff`/`is_superuser` blocked at the view layer; URL reachable but bounces to invalid-token) | [Agency Admin → auth_service](#auth_service) (canonical row documents the v1 block-for-admins behavior; not duplicated in the Caregiver section) |
| `/care-manager/expenses/<int:expense_id>/receipt/<int:receipt_id>/` | Care Manager | Agency Admin (oversight via `is_staff` short-circuit at `care_manager/views.py:733` in v1) | [Care Manager → care_manager](#care_manager) |

### Routes authored here (no primary-persona section)

These five rows use the same schema as the persona sections plus a leading `persona` cell listing every persona that reaches the route (comma-separated, persona vocabulary verbatim from [README §Personas](README.md#personas)).

| route | persona | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/switch-role/` | Care Manager, Caregiver | POST-only endpoint that switches a dual-role user's active portal role; logs a `RoleSwitchEvent` for analytics. | Sees: no rendered page — redirect-only. Can: switch active role between caregiver and care_manager, landing on the target portal's dashboard. | missing | M | true | false | false | not_screenshotted: pending #79 |  |
| `/portal-chooser/` | Care Manager, Caregiver | Full-page portal selector rendered when a dual-role user hits root with no saved default portal preference. | Sees: list of available roles with labels and descriptions. Can: select one role to enter, optionally saving it as default in the same flow. | missing | M | true | false | false | not_screenshotted: pending #79 |  |
| `/set-default-portal/` | Care Manager, Caregiver | POST-only endpoint that saves a dual-role user's preferred default portal to `UserPreference`, skipping the chooser on next login. | Sees: no rendered page — redirect-only. Can: persist a default-portal preference and proceed to the chosen portal. | missing | M | true | false | false | not_screenshotted: pending #79 |  |
| `/clear-default-portal/` | Care Manager, Caregiver | POST-only endpoint that removes a dual-role user's saved default-portal preference, returning them to the chooser flow. | Sees: no rendered page — redirect-only. Can: clear the saved default-portal preference. | missing | M | true | false | false | not_screenshotted: pending #79 |  |
| `/family-signup/` | Family Member | 🔒 PHI · Public, rate-limited (5/h per IP) self-registration shortcut that redeems a family invite code and creates a Family Member account. | Sees: invite-code field, optional pre-filled greeting naming the linked client when a valid `?code=` param is present (`[CLIENT_NAME]`). Can: submit the code to create the account and join the client's circle. | missing | H | true | false | true | not_screenshotted: pending #79 |  |

**Authoring conventions for this section.** When per-persona authoring sub-issues discover a route reachable by more than one persona, prefer authoring the row in the *primary*-persona section and adding an entry to the cross-reference index above. Use the row table immediately above only when no single persona section is the natural primary. The per-persona section gets a one-line cross-reference under its app group instead — e.g. `see [/switch-role/ in Shared routes](#shared-routes)`.
