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
| clients | 11 | 0 | mounted at `schedule/` and `clients/`; pending |
| compliance | 1 | 0 | mounted at `legal/`; mostly customer-facing; pending |
| dashboard | 25 | 0 | agency dashboard, payroll, expenses; pending |
| employees | 3 | 0 | caregiver employee management; pending |
| charting | 48 | 0 | shared with Care Manager / Caregiver — Agency Admin reachability TBD; pending |
| quickbooks_integration | 8 | 0 | QuickBooks OAuth + sync UI; pending |
| auth_service | TBD | 0 | shared with all personas; pending |
| _(dual-role / portal switching routes in elitecare/urls.py)_ | 5 | 0 | switch-role, portal-chooser, set-default-portal, clear-default-portal, family-signup; treat as Shared routes |
| **total (Agency Admin, current estimate)** | **~130** | **29 (≈22%)** | denominator finalized after each app's rows land |

**Skipped (the 5% headroom):** none yet enumerated; will populate as remaining apps are authored.

**Status note (2026-05-06).** Issue #81 covers Agency Admin row authoring. As of this commit, the top-level admin routes, `billing` app, and `billing_catalogs` app are complete; remaining apps (clients, dashboard, employees, charting, compliance, quickbooks_integration, auth_service) and the dual-role/shared routes are pending. Per the committee's halfway-point rule (below 30% coverage triggers a per-app split), follow-up sub-issues will author each remaining app independently. See #81 halfway-point check-in for the split plan.

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

_last reconciled: 2026-05-06 against v1 commit `9738412`_

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

Routes accessible by more than one persona appear once per persona above with a cross-reference note. This section will list them once row authoring is complete.

_(pending content authoring)_
