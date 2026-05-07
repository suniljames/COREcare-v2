# V1 User Journeys

> **Read [`README.md`](README.md) first.** It locks every convention used here.

This document narrates end-to-end user flows in v1, persona by persona. Each journey opens with a one-sentence "what / who / why," followed by a numbered route trace, qualitative side effects (DB writes, notifications, emails), and a one-line "failure-mode UX" call-out where v1 has notable behavior under failure (offline, server error, missing data).

Each journey **cites pages-inventory anchors** rather than redefining route facts. If a route mentioned here is not yet a row in [`v1-pages-inventory.md`](v1-pages-inventory.md), that's a coverage gap to fix.

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

---

## Conventions

- **Route trace:** numbered list of routes the user passes through, each linked to the corresponding pages-inventory row.
- **Side effects:** DB writes / notifications / emails / external-service calls described qualitatively (`creates a Visit record`, `fires a caregiver-assignment notification`), not at schema level. Audit-log writes called out as a separate bullet on every journey traversing an `rls_bypass_by_design=true` row.
- **Failure-mode UX:** one line describing what the user sees when the path fails. Examples: `If clock-in fails offline, v1 queues locally and replays on reconnect.` Omitted entirely when v1 has no notable failure handling on the path.
- **Tenant context:** included only where ambiguous — Super-Admin cross-tenant work, Family Member invite redemption (no-tenant → scoped-tenant transition), View-As impersonation (audit-log identity ≠ active context).
- **Quoted v1 UI strings:** blockquoted with `> v1 displays:` attribution. PHI placeholders only — quote the template, never a rendered example.
- **Sub-block label order is fixed:** `**Route trace:**` → `**Side effects:**` → `**Failure-mode UX:**` (or omitted) → optional inline `> v1 displays:` blocks. Labels exact for parser stability.

---

## Super-Admin

_last reconciled: 2026-05-07 against v1 commit `9738412`_

v1 runs single-tenant per install — "Super-Admin" is any Django superuser inside one agency's deployment. The two journeys below are the cross-cutting platform-operator surfaces v2 must preserve as multi-tenant by design: capability administration with audit-trail, and the View-As impersonation suite. Tenant context is implicit single-tenant in v1; in v2 these flows cross tenant boundaries by design and the operator's audit-log identity must remain distinct from the impersonated user's session context.

### Agency management — capability administration and View-As kill switch

A Super-Admin manages the platform install by reviewing the role × capability matrix, toggling individual capability grants, monitoring the View-As audit log, and using the emergency kill switch when an active impersonation session must be terminated.

**Route trace:**
1. [`/admin/role-permissions/`](v1-pages-inventory.md#agency-admin-top-level) — review the role × capability matrix with current grants.
2. [`/admin/role-permissions/toggle/`](v1-pages-inventory.md#agency-admin-top-level) — flip a single capability bit for a role.
3. [`/admin/view-as/audit-log/`](v1-pages-inventory.md#agency-admin-top-level) — review chronological View-As entries with filters by initiator, target, and date.
4. [`/admin/view-as/kill-all/`](v1-pages-inventory.md#super-admin-top-level) — confirm and terminate every active View-As session immediately.

**Side effects:**
- DB: each capability toggle writes a capability-grant change record on the affected role; the kill switch closes every active ViewAsSession row in one transaction.
- Audit: every capability toggle and the kill action are audit-logged in v1 with actor, target role/session, and timestamp.
- Notifications/email: none on the toggle and audit-review surfaces; the kill switch does not fan out a notification in v1.

**Failure-mode UX:** If the kill switch runs with zero active sessions, v1 still records the operator action but reports "0 sessions terminated" on the confirmation page.

**Tenant context:** v1 single-tenant; v2 elevates these to genuinely cross-tenant operator surfaces — the audit log must continue to capture the operator identity distinct from any impersonated context.

### View-As impersonation with audit trail

A Super-Admin starts a View-As session to reproduce a caregiver- or family-member-specific issue, every step under impersonation written to the v1 audit log.

**Route trace:**
1. [`/admin/view-as/hub/`](v1-pages-inventory.md#agency-admin-top-level) — entry hub listing recent View-As sessions and a search to start a new one.
2. [`/admin/view-as/search/`](v1-pages-inventory.md#agency-admin-top-level) — live search for the target user by name or email.
3. [`/admin/view-as/caregiver/select/`](v1-pages-inventory.md#agency-admin-top-level) or [`/admin/view-as/family/select/`](v1-pages-inventory.md#agency-admin-top-level) — narrow to the caregiver or family-member account to impersonate.
4. [`/admin/view-as/<int:user_id>/`](v1-pages-inventory.md#agency-admin-top-level) — step-up confirmation with target identity and session duration.
5. _(active session — operator now sees the target's portal; every action audit-logged via middleware.)_
6. [`/admin/view-as/status/`](v1-pages-inventory.md#agency-admin-top-level) — banner-driven status check during the session.
7. [`/admin/view-as/end/`](v1-pages-inventory.md#agency-admin-top-level) — explicit end, returning the staff user to their own context.

**Side effects:**
- DB: creates a ViewAsSession row at step-up; appends impersonated-action records throughout the session; closes the session row at end.
- Audit: every step-up, every action under impersonation, every termination, and every forbidden-action attempt is audit-logged with IP, action, target, and timestamp.
- External: none.

**Failure-mode UX:** If the target user is `is_staff` or `is_superuser`, v1 forbids impersonation at the step-up gate and records the forbidden-action attempt to the audit log even though no session was created.

**Tenant context:** v1 single-tenant; in v2 the operator's audit-log identity must remain distinct from the active impersonation context, and the session itself crosses tenant boundaries by design.

> v1 displays: "View As session active — impersonating [CAREGIVER_NAME]. End session."

---

## Agency Admin

_last reconciled: 2026-05-07 against v1 commit `9738412`_

Agency Admin is v1's largest persona surface and v2's highest-volume rebuild target. The five journeys below cover the operational spine: client onboarding, caregiver onboarding, weekly payroll, billing, and credential expiry handling.

### Client intake — onboarding a new client into operations

Once a client record exists in the agency database (Django admin form, excluded from inventory denominator and pending in [#79](https://github.com/suniljames/COREcare-v2/issues/79)), the Agency Admin onboards the client into operations by verifying the agency's billable service catalog, attaching billable services to the first scheduled visit with MD-order proof, and producing the monthly schedule PDF for the family.

**Route trace:**
1. [`/admin/settings/service-catalog/`](v1-pages-inventory.md#billing_catalogs) — verify the agency's billable service catalog has the entries this client's care plan will require.
2. [`/admin/settings/service-catalog/new/`](v1-pages-inventory.md#billing_catalogs) — add a new billable service entry if the client's plan needs a service the catalog lacks.
3. [`/admin/visits/<int:visit_id>/attach-service/`](v1-pages-inventory.md#billing) — attach a catalog service to the client's first scheduled visit, uploading the MD-order proof.
4. [`/clients/<int:client_id>/calendar/`](v1-pages-inventory.md#clients) — confirm the unified per-client calendar reflects the visit and attached service.
5. [`/clients/<int:client_id>/schedule/pdf/`](v1-pages-inventory.md#clients) — generate the monthly schedule PDF for the client and family member of record.

**Side effects:**
- DB: each catalog add/edit creates or updates a `BillableServiceCatalog` row; the attach-service wizard creates a `VisitBillableService` record bound to the visit and proof; the schedule PDF persists no row but reads visits and events for the month.
- Notifications/email: none on these admin surfaces directly; downstream visit notifications fire when the caregiver is assigned (see Caregiver onboarding below).
- External: none.
- Audit: schedule PDF generation is HIPAA-access-logged in v1 (preserve in v2 design).

**Failure-mode UX:** If the catalog wizard's selected entry has been retired since the wizard opened, v1 rejects the attachment with an inline error and forces re-selection from the live catalog.

### Caregiver onboarding — invitation through profile activation

Originating with the Agency Admin sending an invitation, the caregiver redeems the invitation email's UUID token, sets a password, and completes the profile-completion form before the v1 ProfileCompletionMiddleware will let them clock in.

**Route trace:**
1. _(Agency Admin sends the invitation upstream via the v1 invitation flow in `employees/utils.py`; the send form is excluded from inventory denominator.)_
2. [`/employees/invitation/<uuid:token>/`](v1-pages-inventory.md#employees) — caregiver clicks the email link and lands on the acceptance page; sets password and completes the combined profile form.
3. [`/employees/complete-profile/`](v1-pages-inventory.md#employees) — caregiver continues to the profile-completion form (the ProfileCompletionMiddleware will redirect any first-time login here until the form is saved).
4. [`/employees/complete-profile/draft/`](v1-pages-inventory.md#employees) — auto-save endpoint persists partial drafts as the caregiver types so a reload does not lose entered data.

**Side effects:**
- DB: the acceptance page creates the User account and `Caregiver` profile and sets the password hash; auto-save persists partial profile fields between full-form submits.
- Notifications/email: the invitation arrives via SendGrid SMTP using the `emails/invitation` template (`EmailEvent` category `invitation`); a separate confirmation email is not fired on acceptance in v1.
- External: SendGrid SMTP for the invitation email.

**Failure-mode UX:** If the UUID token has expired or already been redeemed, v1 displays a generic "Invitation no longer valid" page without revealing which condition.

> v1 displays: "Welcome to [AGENCY_NAME]. Set your password to activate your account."

### Weekly timesheet review and approval

An Agency Admin reviews the weekly timecard summary, drills into individual caregivers to correct clock-time errors via inline edit, and produces the bulk export that flows into the off-platform payroll workflow.

**Route trace:**
1. [`/dashboard/admin/timecards/`](v1-pages-inventory.md#dashboard) — payroll-period summary across all caregivers with hours, pay totals, and status; weekly/monthly/yearly period selection.
2. [`/dashboard/admin/timecards/<int:caregiver_id>/`](v1-pages-inventory.md#dashboard) — drill into one caregiver; edit clock times via inline AJAX where corrections are needed.
3. [`/dashboard/admin/timecards/<int:caregiver_id>/pdf/`](v1-pages-inventory.md#dashboard) — export the single caregiver's timecard PDF for that caregiver's records on request.
4. [`/dashboard/admin/timecards/export/csv/`](v1-pages-inventory.md#dashboard) (or [`/export/excel/`](v1-pages-inventory.md#dashboard)) — bulk all-staff export feeding the off-platform payroll workflow.

**Side effects:**
- DB: each inline clock-time edit updates the visit's clock-in/clock-out timestamps and recomputes the visit's hours and pay totals.
- Notifications/email: none on the review surface itself; rate-change emails fire upstream when a caregiver's pay rate is adjusted (`emails/shift_rate_changed`, `EmailEvent` category `shift_rate_change`).
- External: CSV / Excel / PDF exports flow into off-platform payroll workflows.

**Failure-mode UX:** If a clock-time edit would make a visit's duration negative or break overlap rules with adjacent visits, v1 surfaces an inline AJAX validation error and reverts the edit.

### Invoice generation and emailing

An Agency Admin generates a per-client weekly billing PDF, emails it to the client's family members of record, and pushes the corresponding invoice to QuickBooks Online for AR reconciliation.

**Route trace:**
1. [`/dashboard/admin/invoices/`](v1-pages-inventory.md#dashboard) — landing with all client invoices, the automated weekly billing summary, and reimbursement entries.
2. [`/dashboard/admin/invoices/<int:client_id>/billing-pdf/`](v1-pages-inventory.md#dashboard) — generate the per-client billing PDF for the selected period.
3. [`/dashboard/admin/invoices/<int:client_id>/email/`](v1-pages-inventory.md#dashboard) — compose and send the billing PDF to the client's linked family members.
4. [`/quickbooks/send-invoice/<int:client_id>/`](v1-pages-inventory.md#quickbooks_integration) — push the same week's invoice to the linked QuickBooks customer record.

**Side effects:**
- DB: PDF generation auto-creates a draft `Invoice` from billable visits if none exists; each email send appends a `BillingEmailLog` row with delivery tracking; each QuickBooks send appends a `QuickBooksInvoiceLog` row with the billing snapshot.
- Notifications/email: SendGrid SMTP delivers the billing PDF to family-member inboxes via `core.email.service.send_email_safely` (`EmailEvent` category `invoice`); subject validated for header injection (rejects `\r\n`, length capped at 200).
- External: QuickBooks Online — invoice line items appear on the agency's QuickBooks customer record for AR reconciliation.

**Failure-mode UX:** If the COREcare client is not linked to a QuickBooks customer, the QB send returns an actionable error referencing the client name with hints to relink or create a customer (Issue #329); the billing PDF and email path is unaffected.

> v1 displays: "Send invoice to [CLIENT_NAME]'s family — preview and confirm."

### Credential expiry handling

A scheduled job emails caregivers whose credentials are nearing expiry, the caregiver re-uploads via the profile-completion form, and the Agency Admin verifies the renewed documents on the data-health dashboard.

**Route trace:**
1. _(Operator-scheduled `check_expiring_credentials` cron fans out the credential-expiry email; cron has no UI surface.)_
2. [`/employees/complete-profile/`](v1-pages-inventory.md#employees) — caregiver re-uploads expiring credential documents alongside profile fields.
3. [`/admin/data-health/`](v1-pages-inventory.md#agency-admin-top-level) — Agency Admin verifies that stale-credential counts have dropped after the renewal.

**Side effects:**
- DB: the profile-completion form replaces the prior `CredentialFile` attachments on the `Caregiver` profile with the newly uploaded versions and clears the stale-flag.
- Notifications/email: the cron triggers the credential-expiry email via SendGrid (`EmailEvent` category `credential_expiry`); template lists the credentials expiring within the configured threshold.
- External: SendGrid SMTP for the reminder email.

**Failure-mode UX:** If the caregiver uploads a document that fails the allowed-extension list (e.g., `.heic` instead of `.pdf`/`.jpg`), v1 surfaces an inline validation error and retains other entered fields so the caregiver does not lose work.

---

## Care Manager

_last reconciled: 2026-05-07 against v1 commit `9738412`_

Care Manager is a caseload-first portal of six pages. v1 gates care-plan template authoring, chart-comment review, health-report approval, and per-client clinical trend views to `is_staff` — the CM role does **not** reach those surfaces. The two journeys below describe what a CM actually does in v1: review the active care plan via the per-client `Client Focus` charting tab (read-only) and submit incidental field expenses scoped to assigned clients. v2 design must not silently collapse the staff gate by granting CMs `is_staff`.

### Care plan review and surfacing — Care Manager oversight (read-only in v1)

A Care Manager opens the caseload, drills into a client's Focus page, and reviews the client's active care-plan / charting summary. v1 does not let the CM edit the template — the authoring routes (`/charting/client/<int:client_id>/create-template/` and adjacent) are `@staff_member_required`. Surfacing observations back to staff happens via the action queue and family care-request flows, not through direct edits.

**Route trace:**
1. [`/care-manager/`](v1-pages-inventory.md#care_manager) — caseload landing with priority-sorted clients and the action queue.
2. [`/care-manager/client/<int:pk>/`](v1-pages-inventory.md#care_manager) — the per-client `Client Focus` page with the charting tab summarizing the active template, recent charts, today's stats, and trend links.
3. _(care-plan authoring lives at [`/charting/client/<int:client_id>/create-template/`](v1-pages-inventory.md#charting) but is staff-gated; CMs do not reach it in v1.)_

**Side effects:**
- DB: navigation only; CM access does not persist any review record; `cm_client_focus` clinical-tab access inherits whatever logging the underlying `charting` services emit (verify per-tab in v2 design).
- Audit: v1 has no audit on the CM caseload or focus pages — v2 must add for HIPAA-minimum-necessary tracking.

**Failure-mode UX:** If the CM attempts to access a non-assigned client's URL directly, v1 raises `Http404` rather than 403 to avoid leaking caseload composition.

**Tenant context:** v1 single-tenant; in v2 the CM's caseload scope must be enforced at the RLS layer keyed on `CareManagerProfile` assignments.

### Team oversight — caseload action queue and field-expense submission

A Care Manager monitors the per-client action queue across the caseload, navigates the per-client care team and family-contact lists, and submits incidental field expenses tied to assigned clients.

**Route trace:**
1. [`/care-manager/`](v1-pages-inventory.md#care_manager) — caseload with severity-colored attention badges, action queue, and daily summary.
2. [`/care-manager/client/<int:pk>/`](v1-pages-inventory.md#care_manager) — per-client Focus with care-team caregiver cards (phone, email) and family-member contacts.
3. [`/care-manager/expenses/`](v1-pages-inventory.md#care_manager) — CM expense list grouped per assigned client, with budget-status banner.
4. [`/care-manager/expenses/submit/`](v1-pages-inventory.md#care_manager) — expense submission form scoped to assigned clients.
5. [`/care-manager/expenses/<int:expense_id>/edit/`](v1-pages-inventory.md#care_manager) — edit or resubmit a rejected expense.

**Side effects:**
- DB: each submit/edit/resubmit creates or mutates an `Expense` row; resubmits on REJECTED expenses route through `ExpenseService.resubmit_expense` and edits through `ExpenseService.edit_expense`.
- Notifications/email: status transitions surface on the Agency Admin expense-review queue (`/admin/expenses/review/`); CMs do not receive per-status emails on the CM portal in v1.
- Audit: `ExpenseService` workflow events log status transitions on submit/edit/resubmit; the list view itself is not audit-logged. Receipt downloads via `/care-manager/expenses/<int:expense_id>/receipt/<int:receipt_id>/` have no v1 audit — v2 design must add.

**Failure-mode UX:** If a CM tries to submit an expense for a client who has been unassigned since the form opened, the submit fails with a "client no longer in your caseload" inline error and the form retains entered fields for re-targeting.

---

## Caregiver

_last reconciled: 2026-05-07 against v1 commit `9738412`_

Caregiver pages are first-person field-flow surfaces — the actor is always the authenticated caregiver and every route's row-level scope reduces to `caregiver_id = self` or `visit_id ∈ self.assigned_visits`. The dominant aggregate is **Visit**: clock state, mileage, expense reimbursements, and charting all attach to a Visit. The four journeys below cover the daily field flow: clock-in/out at a shift, chart-note submission during the visit, expense submission, and the schedule view that surfaces upcoming work.

### Clock in and out at a shift

A caregiver opens the daily dashboard at the start of their shift, clocks in (recording GPS), works through the visit on the active-shift screen, clocks out at the end, and reviews the post-shift summary.

**Route trace:**
1. [`/caregiver/dashboard/`](v1-pages-inventory.md#caregiver_dashboard) — daily landing showing today's assigned shift, clock state, and weekly summary cards.
2. [`/caregiver/shift/<int:shift_id>/clock-in/`](v1-pages-inventory.md#caregiver_dashboard) — POST-only clock-in (rate-limited 10/hr/user); validates assignment, records GPS, creates the Visit.
3. [`/caregiver/shift/<int:visit_id>/active/`](v1-pages-inventory.md#caregiver_dashboard) — in-flight visit dashboard during the clocked-in visit.
4. [`/caregiver/clock-out/<int:visit_id>/`](v1-pages-inventory.md#caregiver_dashboard) — closes the active Visit, captures clock-out GPS and time, transitions caregiver state to POST_SHIFT.
5. [`/caregiver/shift/<int:visit_id>/summary/`](v1-pages-inventory.md#caregiver_dashboard) — post-shift wrap-up with hours, services performed, comment count.

**Side effects:**
- DB: clock-in creates a `Visit` row with start GPS and timestamp; clock-out updates the same Visit with end GPS, end timestamp, and duration; the post-shift summary lazily creates the chart on view if missing.
- Notifications/email: caregivers do not receive their own clock notification; the shift-assignment email (`emails/shift_new_assignment`, `EmailEvent` category `shift_assignment`) fires upstream when the assignment is first made.
- External: none — GPS read is browser-side.

**Failure-mode UX:** If the device is offline at clock-in or clock-out, v1's PWA queues the action locally via service worker and replays on reconnect; the dashboard reflects the queued state until replay completes.

> v1 displays: "Clock in to [CLIENT_NAME]'s shift — confirm your location."

### Chart note submission during a visit

A caregiver enters chart sections (vitals, glucose, intake/output, bowel-movement, nursing notes), documents medications administered, and adds visit comments — optionally with receipt attachments — before finalizing the chart at clock-out.

**Route trace:**
1. [`/caregiver/shift/<int:visit_id>/active/`](v1-pages-inventory.md#caregiver_dashboard) — active shift dashboard with chart-entry buttons and comment thread.
2. [`/charting/visit/<int:visit_id>/chart/`](v1-pages-inventory.md#caregiver-charting) — caregiver charting page; lazy-creates the chart on GET, exposes section-based entry, billable-services list, and signature capture.
3. [`/charting/medications/<int:visit_id>/`](v1-pages-inventory.md#caregiver-charting) — today's scheduled medications grouped by time; one-tap "Given" with a 5-minute undo window.
4. [`/charting/medications/<int:visit_id>/history/`](v1-pages-inventory.md#caregiver-charting) — 7-day medication-administration history grid for context.
5. [`/caregiver/visit/<int:visit_id>/add-comment/`](v1-pages-inventory.md#caregiver_dashboard) — adds a comment with optional receipt attachments (≤5 MB each).

**Side effects:**
- DB: each chart-section save writes a section entry on the `Chart`; the medication "Given" tap appends a `MedicationAdministration`; comments persist as `ChartComment` rows; receipt attachments persist as `Attachment` rows linked to the Visit.
- Notifications/email: chart comments flagged "family-visibility" land in [`/charting/comments/review-queue/`](v1-pages-inventory.md#charting) for staff approval before they surface in the family portal.
- External: none.

**Failure-mode UX:** If the network drops mid-save, the section's JSON save endpoint retries; on persistent failure v1 surfaces an inline error banner without losing local state, so the caregiver can retry once back online.

### Expense submission — visit-linked or standalone

A caregiver submits a reimbursement expense, either linked to the active visit (mileage, supplies for that client) or standalone (mileage between visits, agency-wide supplies), uploads the required receipt, and tracks the expense through admin approval.

**Route trace:**
1. [`/caregiver/visit/<int:visit_id>/add-reimbursement/`](v1-pages-inventory.md#caregiver_dashboard) — visit-linked reimbursement: expense type, amount, description, required receipt upload.
2. [`/caregiver/expenses/submit/`](v1-pages-inventory.md#caregiver_dashboard) — standalone expense submission (one of nine fixed expense classes).
3. [`/caregiver/expenses/`](v1-pages-inventory.md#caregiver_dashboard) — my-expenses list with status filters (drafts, submitted, approved, rejected).
4. [`/caregiver/expenses/<int:expense_id>/edit/`](v1-pages-inventory.md#caregiver_dashboard) — edit a draft or rejected expense and resubmit.

**Side effects:**
- DB: each submit creates an `Expense` row (status SUBMITTED) with attached `ExpenseReceipt`; visit-linked submissions also bind the Expense to the Visit so it auto-flows into the client's weekly invoice.
- Notifications/email: submitted expenses surface on the Agency Admin expense-review queue (`/admin/expenses/review/`); v1 does not email the caregiver on submit; rejection notifications surface as in-portal status only at the pinned commit.
- Audit: `ExpenseService` workflow events log every status transition (submit / edit / resubmit / approve / reject / reimburse). Receipt downloads via `/caregiver/expenses/<int:expense_id>/receipt/<int:receipt_id>/` have no v1 HIPAA-access log — v2 must add.

**Failure-mode UX:** If the receipt upload exceeds the 5 MB cap or uses a disallowed file extension, v1 rejects the file inline and retains the rest of the form so the caregiver can re-attach.

### Schedule view — upcoming shifts and shift-offer acceptance

A caregiver reviews their monthly schedule, accepts pending shift offers inline, and uses the schedule view as the primary surface for upcoming work.

**Route trace:**
1. [`/caregiver/dashboard/`](v1-pages-inventory.md#caregiver_dashboard) — today's shift card with quick links to schedule and shift offers.
2. [`/caregiver/schedule/`](v1-pages-inventory.md#caregiver_dashboard) — calendar grid with shifts per day; daily / weekly / monthly view modes.
3. [`/caregiver/shift-offers/`](v1-pages-inventory.md#caregiver_dashboard) — pending shift offers with inline accept/decline and per-offer earnings estimate.

**Side effects:**
- DB: accepting an offer creates the assignment on the `Shift` (sets `assigned_caregiver`); declining records a `ShiftDeclineEvent` with the chosen decline-reason.
- Notifications/email: a new assignment fires the shift-assignment email (`emails/shift_new_assignment`, `EmailEvent` category `shift_assignment`); a rate change fires `emails/shift_rate_changed` (category `shift_rate_change`); a cancellation fires `emails/shift_canceled` (category `shift_canceled`); the pre-shift reminder fires from a `*/15 * * * *` cron targeting ~8 hours before shift start, gated by 9 PM–7 AM Pacific quiet hours and idempotent via `Shift.pre_shift_reminder_sent_at`.
- External: web push notifications via `pywebpush.webpush()` for caregivers with registered `PushSubscription` rows; gracefully skipped if VAPID keys are unset (the in-app inbox entry and email still arrive).

**Failure-mode UX:** When the device is offline, the schedule view uses cached data via service worker; new offers and reassignments will not appear until the connection returns.

> v1 displays: "New shift offer — [CLIENT_NAME], scheduled time and duration. Accept or decline."

---

## Client

<a id="client-section-journeys"></a>

_last reconciled: 2026-05-07 against v1 commit `9738412`_

**v1 has no Client-as-actor surface.** Per [the inventory's Client section](v1-pages-inventory.md#client-section), clients are subjects of care, not authenticators. The two journeys below are absence notes — they document that v1 has no Client-authenticated route for these flows, and they cite the Family Member journey under which a linked Family Member exercises the equivalent visibility on a client's behalf. The v2 product question of whether to add an authenticated Client portal as a deliberate divergence is tracked in [#109](https://github.com/suniljames/COREcare-v2/issues/109).

### Care plan view — absence note

v1 has no Client-authenticated route for viewing a care plan. The closest v1 reality is a linked Family Member viewing the per-client portal, which surfaces the active care plan summary, family-visibility-approved chart comments, and recent visit notes; that flow is documented under the Family Member persona's [Visit-note view](#visit-note-view-for-a-linked-client) journey.

**Route trace:**
1. v1 has no Client-authenticated route for this journey. See [the inventory's Client section](v1-pages-inventory.md#client-section) for the v1-as-built rationale (clients have no `User` linkage; only `ClientFamilyMember` binds an authenticating account to a Client record). The equivalent flow under the Family Member persona traverses [`/family/dashboard/`](v1-pages-inventory.md#family-member) → [`/family/client/<int:client_id>/`](v1-pages-inventory.md#family-member).

**Side effects:**
- DB: n/a — no Client-authenticated v1 surface.
- Audit: n/a — clients do not authenticate in v1.

### Upcoming-shift view — absence note

v1 has no Client-authenticated route for viewing upcoming shifts. The closest v1 reality is a linked Family Member viewing the per-client calendar; that flow is documented under the Family Member persona's [Visit-note view](#visit-note-view-for-a-linked-client) journey, which traverses the same per-client portal.

**Route trace:**
1. v1 has no Client-authenticated route for this journey. The equivalent flow under the Family Member persona traverses [`/family/client/<int:client_id>/`](v1-pages-inventory.md#family-member) — per-client portal with weekly/daily calendar.

**Side effects:**
- DB: n/a — no Client-authenticated v1 surface.
- Audit: n/a — clients do not authenticate in v1.

---

## Family Member

_last reconciled: 2026-05-07 against v1 commit `9738412`_

Family Member pages serve a client's authorized representative — typically a spouse, adult child, or designated POA. v1 grants visibility through a per-(client, user) link recorded in `ClientFamilyMember`; a single Family Member account may be linked to multiple clients. The three journeys below cover invite redemption (a tenant-context-changing flow), visit-note visibility on a linked client, and care-request messaging back to the agency.

### Invite redemption — from no-tenant to scoped-tenant

A new Family Member receives an invite (email or SMS) containing a code; they redeem the code via the public self-registration page or a magic-link email, creating an account and a `ClientFamilyMember` link in one flow.

**Route trace:**
1. _(Invitation email or SMS sent upstream by an Agency Admin or care-request handoff; the send form is excluded from inventory denominator at the pinned commit.)_
2. [`/family-signup/`](v1-pages-inventory.md#shared-routes) — public, rate-limited (5/h per IP) self-registration with the invite code; optional pre-filled greeting names the linked client when `?code=` is valid.
3. [`/magic-login/<uuid:token>/`](v1-pages-inventory.md#auth_service) — alternative entry path via a 30-minute single-use magic-link email; admins blocked at the view layer.
4. [`/family/dashboard/`](v1-pages-inventory.md#family-member) — first landing after redemption; lists every linked client.

**Side effects:**
- DB: creates the `User` account (Family Member role) and the `ClientFamilyMember` link binding the user to the client; v1 has no active-flag on `ClientFamilyMember` — soft-revocation requires hard-delete in v1, and v2 design must add a soft-revocation path so audit trails of past family-member access survive after a link ends.
- Notifications/email: the invitation email arrives via SendGrid (`emails/invitation`, `EmailEvent` category `invitation`); magic-link emails carry subject `Sign-in link from [AGENCY_NAME]` (`EmailEvent` category `auth_magic_link`).
- External: SendGrid SMTP for the invitation and magic-link emails.
- Audit: v1 has no audit on `/family-signup/`, `/family/dashboard/`, or `ClientFamilyMember` link creation — v2 design must add for HIPAA-compliance and revocation-audit purposes.

**Failure-mode UX:** Invalid or already-redeemed codes display a generic "Invitation no longer valid" page without revealing whether the code never existed or has been spent — same behavior as the password-reset flow's enumeration-defeat copy.

**Tenant context:** the actor moves from no-tenant (pre-redemption) → scoped-to-linked-client (post-redemption) during this single flow. v2 must enforce the scope at the RLS-policy layer keyed on `ClientFamilyMember`; reviewers of the v2 family-portal `/design` cycle should treat absence of that policy as a blocking gap.

> v1 displays: "Welcome to [AGENCY_NAME]'s family portal. You'll see updates for [CLIENT_NAME]."

<a id="visit-note-view-for-a-linked-client"></a>

### Visit-note view for a linked client

A Family Member opens the family portal, drills into a specific linked client, and reviews recent visit notes, family-visibility-approved chart comments, calendar events, billing summary, and care-team contacts.

**Route trace:**
1. [`/family/dashboard/`](v1-pages-inventory.md#family-member) — Family Member home with one card per linked client (uses `effective_user` so View-As sessions render the impersonated user's links).
2. [`/family/client/<int:client_id>/`](v1-pages-inventory.md#family-member) — per-client portal: weekly/daily calendar, today's events, recent messages, billing summary, recent visit notes, care team, family-visibility-approved chart comments.
3. [`/family/client/<int:client_id>/billing-pdf/`](v1-pages-inventory.md#family-member) — optional download of the family invoice PDF (auto-generates a draft `Invoice` from billable visits if none exists; rate-limited 10/h per user).
4. [`/family/client/<int:client_id>/health-report/`](v1-pages-inventory.md#family-member) — optional family-variant health-report PDF with selectable sections and a configurable day window; IDOR-protected via `FamilyPortalService.verify_access`; rate-limited 10/h per user.

**Side effects:**
- DB: navigation only on the dashboard and per-client portal; PDFs read from `Visit` and `Chart` aggregates; chart comments flagged family-visibility surface here only after staff approval at [`/charting/comments/review-queue/`](v1-pages-inventory.md#charting).
- Notifications/email: none on read paths.
- Audit: `/family/dashboard/` and `/family/client/<int:client_id>/` are NOT audit-logged in v1 — v2 design must add. Chart-comment family-views ARE logged separately via `ChartCommentService.log_family_view`. Billing PDF and health-report PDF are HIPAA-access-logged in v1 (preserve in v2).

**Failure-mode UX:** If a Family Member's link to a client has been hard-deleted (v1's only revocation path), v1 returns a 404 from `/family/client/<int:client_id>/` rather than 403 to avoid leaking link history.

### Agency message — sending a care request from the family portal

A Family Member submits a care-request message to the agency from the per-client portal; the message routes to admin staff for triage.

**Route trace:**
1. [`/family/client/<int:client_id>/`](v1-pages-inventory.md#family-member) — POST a care-request message; gated by the link's `can_message_caregivers` permission flag; rate-limited 5/min.

**Side effects:**
- DB: creates a `CareRequest` record bound to the client and the family-member account.
- Notifications/email: fires the care-request notification email to admin (`Care request notification`, `EmailEvent` category appended in `clients/services/care_request_service.py`); admins receive a new-inquiry notification with intake fields.
- External: SendGrid SMTP for the admin notification.
- Audit: v1 logs the family-view side of chart comments via `ChartCommentService.log_family_view`; the care-request submit itself is captured in the `CareRequest` row's metadata but is not separately audit-logged at the pinned commit.

**Failure-mode UX:** If the linked Family Member's `can_message_caregivers` flag is false, the message form is hidden entirely from the per-client portal — a server-side render gate, not a client-side toggle, so the surface is not reachable by URL manipulation.

**Tenant context:** the message is scoped to the linked client only — a Family Member with multiple linked clients sees per-client message threads, never a cross-client surface.

---

## Cross-references

Operational substrate cited across journeys above:

- **SendGrid SMTP backend** — every transactional email fans out through `core.email.backends.SendGridSMTPBackend`. See the [Messaging and notifications substrate row](v1-integrations-and-exports.md#messaging-and-notifications-third-party) in `v1-integrations-and-exports.md`.
- **Email pipeline categories** referenced above (`invitation`, `shift_assignment`, `shift_rate_change`, `shift_canceled`, `pre_shift_reminder`, `credential_expiry`, `invoice`, `auth_magic_link`) — full per-template detail lives in the [Email pipeline section](v1-integrations-and-exports.md#email-pipeline) of `v1-integrations-and-exports.md`.
- **QuickBooks Online** — the Accounting integration cited in Invoice generation. See the [Accounting section](v1-integrations-and-exports.md#accounting) of `v1-integrations-and-exports.md` for OAuth surface and per-send audit row (`QuickBooksInvoiceLog`).
- **`Web Push` delivery** — caregiver-side push notifications via `pywebpush.webpush()` cited in the schedule view journey. See the [`Web Push` row](v1-integrations-and-exports.md#messaging-and-notifications-third-party) in `v1-integrations-and-exports.md` for VAPID-key fallback behavior.
- **Pre-shift reminder cron** (`*/15 * * * *`) and **credential-expiry cron** (`check_expiring_credentials` operator-scheduled) cited in caregiver and credential journeys — see the [Email pipeline section](v1-integrations-and-exports.md#email-pipeline).
