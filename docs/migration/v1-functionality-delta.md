# COREcare v1 → v2 Functionality Delta

**Purpose.** This document inventories functionality that exists in COREcare v1 (`COREcare-access`, the Django monolith) but is **not described** in the v2 customer-facing artifacts (the press release at `[07]-Press-Release.md` and the external FAQ at `[08]-FAQ-(External).md`). The goal is to make sure the v2 ground-up rebuild doesn't silently drop existing capability before we lock the v1.0 scope.

**Method.** I read both v2 docs end-to-end, then ran a structured inventory across all v1 Django apps (models, views, services, management commands, integrations, scheduled jobs). For each v1 capability I checked whether the v2 docs cover it explicitly, implicitly, or not at all. "Not at all" or "only handwaved" entries are the gaps below.

**How to read this.** Severity classifications:
- **H — High.** Mission-critical for the existing customer base; rebuild will lose paying customers if dropped.
- **M — Medium.** Real operational feature customers use today; absence will generate support tickets and rebuild-regret.
- **L — Low.** Internal tooling, edge case, or convenience. Worth tracking but not table-stakes for v1.0 GA.
- **D — Deliberate divergence.** v2 docs make an explicit different choice. Listed for the record, not as a gap.

The v2 docs are *customer-facing*, so absence here doesn't always mean "not built" — sometimes a feature is implied. Where I'm unsure, I've called it out as **needs confirmation**.

---

## For collaborators without v1 access

If you do not have access to `suniljames/COREcare-access` (the v1 Django repo), this document on its own is **not enough** to rebuild v1's customer-facing surface in v2. It catalogues feature and data-model gaps, but it does not describe v1's pages, user journeys, or integrations.

Read these companion documents in `docs/migration/`:

- **[`README.md`](README.md)** — locked conventions for the docset (personas, severity rubric, status enum, PHI placeholder set, voice, refresh runbook, v1 reference commit pin).
- **[`v1-pages-inventory.md`](v1-pages-inventory.md)** — persona × page matrix for all six personas, with v2 status, severity, multi-tenant refactor flags, and PHI flags. Authoritative route catalogue; other docs cite into it.
- **[`v1-user-journeys.md`](v1-user-journeys.md)** — narrated end-to-end flows per persona, with route trace and qualitative side effects.
- **[`v1-integrations-and-exports.md`](v1-integrations-and-exports.md)** — external integrations, internal notification/email backend, and customer-facing exports.
- **[`v1-glossary.md`](v1-glossary.md)** — v1-specific terms cited across the set.

The four documents above are scaffolded but their content is being authored issue-by-issue. The most current state of each lives in this repo.

---

## 1. Billing & Revenue Operations

### 1.1 Invoice revisions / corrected invoices — **H**

v1 has a first-class `InvoiceRevision` model with revision numbering, concurrent-issue row locking, and an explicit corrected-invoice editor (`issue_revision_editor()`). Real agencies need to reissue invoices after errors, payer disputes, or service-attachment changes.

**v2 docs say:** "QuickBooks-ready billing" (Q54) — generic invoicing only. Nothing about correcting an invoice that's already been sent.

### 1.2 Service catalog (Hazel-managed billable services) — **H**

v1 has `BillableServiceCatalog`: agency-managed catalog of add-on billable services with internal name, family-facing label, base price, estimated hours, hourly overage rate, MD-order requirement flag, and soft-retire pattern (Issue #1214). Used to attach add-on services to specific visits.

**v2 docs say:** Nothing. Pricing model in v2 is per-active-client, but agencies still need to bill clients/families/payers for add-on services beyond the standard care plan.

### 1.3 Recurring billable services tied to care plans — **H**

v1 has `RecurringBillableService` linked to a master `CarePlan`, automatically generating invoice lines on the schedule. Care plan ↔ billing is a single graph.

**v2 docs say:** Care plans are described in Q39 and invoicing in Q30/Q54, but they're never connected. The v2 model treats "what care happens" and "what gets billed" as separate tracks. Real agencies bill *from* the care plan.

### 1.4 Physician order proof / MD-order gating — **H**

v1 has `PhysicianOrderProof` (document storage) and gates billing service attachment on a valid MD order being on file. State LTC and LTC-insurance audits commonly verify this.

**v2 docs say:** Q34 mentions physician orders as *input* to AI care plan drafting. Nothing about storing them as proof or gating billable services on them. This is an audit/compliance hole.

### 1.5 Visit-to-service attachment workflow with capability gate — **M**

v1 has `visit_attach_service_view()` — an admin wizard for attaching catalog services to a visit, gated by a `VISIT_SERVICE_ATTACH` capability and MD-order validation, with a `promote_to_recurring_view()` to convert one-off attachments into recurring care plan items.

**v2 docs say:** Nothing about ad-hoc add-on services attached to a single visit. Common in practice (e.g., a one-off shopping trip, a special service).

### 1.6 Per-visit billable rate vs. caregiver pay rate (split rate model) — **M**

v1's `Shift` model carries both `pay_rate` (caregiver earnings, `shifts/models.py:92`) and `bill_rate` (client charge, `shifts/models.py:101`) as first-class `DecimalField`s. The pay path is consumed in payroll cost (`caregiver_dashboard/admin.py:890-897`); the bill path is consumed in invoicing (`billing/services/billing_service.py:271-272`). Both are core to gross-margin reporting.

v1 also captures resolved rates at clock-in via `Visit.pay_rate_snapshot` and `Visit.bill_rate_snapshot` (`caregiver_dashboard/models.py:180-201`), with `RateResolutionService` walking a deterministic chain — `snapshot → shift → client/profile default → fallback` (`billing/services/rate_resolution_service.py:42-46`). The snapshot semantics make mid-shift rate changes immune to retroactive payroll edits.

**v2 docs say:** Q30 mentions "QuickBooks integration takes the same data and posts payroll/billing entries" without articulating the dual-rate or snapshot model. v2 must preserve snapshot-at-clock-in semantics or accept retroactive payroll edits as a behavior change.

---

## 2. Caregiver & Personnel Operations

### 2.1 Rate change scheduling (effective-dated) — **H**

v1 has `RateChangeSchedule`: pending pay rate changes that take effect on a future date, applied via the daily `apply_scheduled_rate_changes.py` job. Agencies legally and operationally need to schedule rate changes (e.g., after annual reviews, minimum wage adjustments) without retroactive surprises.

**v2 docs say:** Nothing about pay rate history or scheduled changes.

### 2.2 Overpayment consent and deduction workflow — **H**

v1 has `OverpaymentConsent` (signed e-consent for deducting overpaid amounts from future paychecks) plus `apply_overpayment_deductions.py` to apply them. **California labor law and FLSA prohibit unilateral paycheck deductions** — this is a real legal feature, not a nice-to-have.

**v2 docs say:** Nothing.

### 2.3 Meal period waivers — **M** *(California labor code; analogous laws in OR/NV/KY/NJ not separately handled in v1)*

v1's `MealPeriodWaiver` (`caregiver_dashboard/models.py:1173`, Issue #275) is a one-to-one record per `Visit`. It inherits `BaseAttestation` (`compliance/models/base.py:18`), which captures `user`, `signed_at`, `ip_address`, `user_agent`, and `session_key`, and is immutable after create — this is a legally-defensible attestation, not a boolean flag. The clock-out flow gates waiver creation on `shift_hours > 5` (`caregiver_dashboard/views.py:757-765,858`), and waivers where `waived_voluntarily=False` roll up into `DailyTimesheet.meal_penalty_count` for premium-pay calculation (`payroll/management/commands/generate_timesheets.py:96-100`).

The 5-hour threshold and the only state-aware artifact in v1 — the `California Labor Code` notice copy — are CA-specific (`compliance/tests/test_messages.py:84-95`). There is no `state_code` column on `MealPeriodWaiver` and no per-state branching for OR/NV/KY/NJ analogues.

**v2 docs say:** Nothing about meal/rest break tracking or waivers. v2 targets US private-duty agencies (Q2). v2 must preserve immutable IP-stamped attestation semantics if it implements an equivalent, and should make per-state branching explicit if it expands beyond CA.

### 2.4 Standardized caregiver titles + auto-generated employee IDs — **M**

v1 has `CaregiverTitle` enum (RN, LVN, CNA, HHA, lead caregiver, MD, NP, OT, PA, PT, RT, admin, other) and auto-generated employee IDs starting at 202653. Used for payroll exports, credential/title-to-permission mapping (Issue #375).

**v2 docs say:** Q22 implies caregiver titles affect documentation paths but doesn't describe taxonomy or ID generation.

### 2.5 Mileage pay & reimbursement — **M**

v1 stores per-visit miles on `Visit.mileage` and surfaces mileage in two distinct pathways:

- **Caregiver-facing payroll:** `SummaryService.get_weekly_summary_data` (`caregiver_dashboard/services/summary_service.py:75-149`) aggregates `total_mileage_reimbursement` per week and feeds the caregiver weekly PDF (`caregiver_dashboard/views.py:1420-1421`) and CSV exports (`caregiver_dashboard/views.py:1547,1592`).
- **Invoice-facing billing:** `InvoiceLine.line_type` carries `mileage` as a discrete enum value alongside `service` and `expense` (`billing/models.py:347`), with `BillingCalculationService.build_mileage_details` constructing the line items (`billing/services/billing_calculation_service.py:262-295`).

The rate is sourced from a single system-wide setting `caregiver_mileage_reimbursement_rate` (`core/settings_accessors.py:39`) — no per-client override, by design (Issue #1440).

**v2 docs say:** Q30 acknowledges this in passing ("mileage if you reimburse per mile and the caregiver enters trip distance") — present but lightweight. v2 must preserve both pathways (caregiver payroll rollup and invoice line-item type) or document the divergence explicitly.

### 2.6 Comprehensive expense management for caregivers and care managers — **H**

v1 has a unified `Expense` model with **9 categories** (supplies, equipment, transportation, meals, training, medical, groceries, admin, other), **8 workflow states** (draft → submitted → pending → approved → processed → adjusted → rejected → reimbursed), payment-method tracking (out-of-pocket vs company card), receipt upload with HIPAA-compliant filenames, adjustment workflow with edit-reason audit, and submitter-role attribution. Consolidated from three legacy models in Issue #604.

**v2 docs say:** Nothing about expense reimbursement at all. Caregivers buy supplies/groceries/meds on behalf of clients constantly; care managers travel to multiple clients. This is a daily workflow, not an edge case.

### 2.7 Profile completion onboarding gate — **M**

v1 has middleware that redirects caregivers with incomplete profiles to onboarding (e.g., missing W9, missing TB results) before letting them clock in.

**v2 docs say:** Q14 describes a 14-day customer onboarding flow but not a per-caregiver completion gate. Without this, caregivers can clock in without legally required paperwork.

---

## 3. Clinical Documentation & Charting

### 3.1 Per-client customizable chart templates — **H**

v1's charting model is `ChartTemplate` (`charting/models.py:55`) keyed by `client = ForeignKey(Client)` with a one-active-per-client invariant via `is_active`. Each template owns multiple `ChartTemplateSection` rows (`charting/models.py:254`), each in turn owning `ChartTemplateSectionItem` rows (`charting/models.py:358`). The 11 section types are defined in the `SectionType` enum (`charting/models.py:30-43`).

Per-section customization lives on `ChartTemplateSection`: `section_status` ∈ `{included, required, excluded}` (`InclusionStatus` enum, `charting/models.py:16-19`); `exclusion_reason` is a free-text field (max 500); `exclusion_reason_category` is enum-bounded with values `not_applicable, client_condition, clinical_decision, family_request, other` (`ExclusionReasonCategory` enum, `charting/models.py:22-26`; field definitions at `charting/models.py:294-300`).

**v2 docs say:** Q22 mentions "the care plan presents a checklist (ADLs completed, vitals, tasks)" — implies templates but treats them as derived from the care plan, not as separately configurable per-client. v2's care-plan-derived shape does not match v1's per-client section-override model; v2 must either denormalize care-plan tasks or introduce a parallel template layer.

### 3.2 Structured clinical chart entry types — **H**

v1 has dedicated models for `VitalSigns` (BP, HR, temp, O2 sat, weight), `GlucoseReading`, `BowelMovement`, `IntakeOutput`, `MedicationAdministration`, `NursingNote` (staff-only). Each has its own validation, ranges, and reporting paths.

**v2 docs say:** Q22 mentions "non-clinical vitals" and Q31–32 talk about ADL/observations. The deeper clinical structure (intake/output, BM tracking, glucose readings, structured medication administration events, RN-only nursing notes) is not described. Many LTC clients require this depth.

### 3.3 Health reports — family-friendly + clinical, with approval workflow — **H**

v1 generates health reports in **two parallel versions** (family-friendly language vs clinical detail), with a **report approval queue** — staff must sign off before the family-facing version is sent. Templates: `health_report_preview_family.html`, `health_report_preview_clinical.html`. Batch generation supported.

**v2 docs say:** Q42 mentions "visit summaries" in the family portal — single-version, no formal periodic report, no staff approval gate. This is a real customer-facing artifact today.

### 3.4 Client medication schedule (master record) — **M**

v1 has `ClientMedicationSchedule` and `ClientMedication` for the long-running medication regimen ("Margaret takes lisinopril 10mg every morning"), separate from per-visit medication-administration events.

**v2 docs say:** Q22 mentions structured tasks and care plan tasks, but the persistent "what meds is this client on" master record isn't called out. Nurses and supervisors need this for medication reconciliation.

### 3.5 Client document repository — **M**

v1 has `ClientDocument` for storing arbitrary per-client documents (medical records, signed consents, advance directives, POA paperwork, physician orders).

**v2 docs say:** Nothing. Q34 mentions "physician orders" as care plan input but no general-purpose document store.

---

## 4. Care Coordination

### 4.1 Care manager action detection (no-shows, overdue requests, vital trends) — **M**

v1's `CareManagerService` has explicit logic: no-show detection at 15-min grace, overdue care requests (>1 day old), vital sign trend flags (BP delta >10 mmHg, systolic >130). Surfaces as priority-sorted action queue.

**v2 docs say:** Q34 describes AI-flagged "patterns — sudden ADL decline, fall events, repeated medication refusal." That overlaps but is *different*: v1's rules are deterministic, fast, and explainable; v2's are AI-inferred. **Worth confirming** the v2 supervisor still gets a deterministic action queue (no-shows, late docs) and isn't entirely dependent on AI noticing things.

### 4.2 Client-caregiver compatibility history — **L**

v1's data model implies prior-visit history per caregiver-client pair (Q33's AI ranking uses "worked with this client 8 prior visits") and v2 references this in scheduling AI. Likely covered, but verify the persistent compatibility record is captured.

### 4.3 Secure client messaging beyond caregiver↔scheduler and family↔agency — **L**

v1 has `ClientMessage` with audit trail. v2 covers caregiver↔scheduler (Q23) and family↔agency (Q45). v1's broader cross-role messaging (supervisor↔caregiver about a specific client, client↔care team) may or may not be in scope.

---

## 5. Auth & Identity

### 5.1 Magic link login + role-based session expiry — **M**

v1 has `MagicLinkToken` (one-click login, 30-min expiry, **disabled for staff** as a security stance) and `PasswordResetToken` with role-based expiry (admin 30min, caregiver 1hr, family 4hr). These choices reflect deliberate security/UX tradeoffs.

**v2 docs say:** Just "secure login." Worth confirming v2 keeps the staff-magic-link prohibition and role-tuned expirations rather than reverting to one-size-fits-all.

### 5.2 View As (sudo / impersonation) for support — **H**

v1 has `ViewAsSession`, `ViewAsPageView`, `ViewAsFailedAttempt` — staff can impersonate caregivers and family members to debug issues, with full IP-and-action audit trail and forbidden-action logging.

**v2 docs say:** Nothing. v2 promises 1-business-hour phone support at Scale (Q59) but offers no in-product way to see what the user sees. Without impersonation, support effectiveness collapses on mobile-app issues.

### 5.3 Capability-based access control (granular admin capabilities) — **M**

v1 has a custom capability layer (Issue #1255) overlaying Django permissions — fine-grained capabilities like `VISIT_SERVICE_ATTACH`. v2 mentions only RBAC tiers (super-admin, admin, manager, caregiver, family) per ADR-003.

**v2 docs say:** Q46 mentions RBAC in a single line. Coarse roles are simpler but lose the granularity that lets agencies, e.g., let a billing clerk attach services without giving them full admin.

### 5.4 Family invite codes for self-registration — **M**

v1 has `FamilyInviteCode`: family members self-register via a code (codes expire, one-time use). The agency hands out a code; family signs themselves up.

**v2 docs say:** Q43 says "you can grant access in seconds when a new family member needs it" — suggests admin-driven invitation. The self-service-via-code pattern is faster operationally and may not be preserved.

---

## 6. System & Operational Features

### 6.1 In-app notification inbox — **M**

v1 has a `Notification` model with typed notifications (credential_expiring, credential_expired, general), an inbox UI, and read/unread tracking. Agency-side staff get a single place to triage alerts.

**v2 docs say:** Q26/Q27/Q57 mention push notifications and SMS but no central in-app inbox for office users. Email is mentioned but not a queryable in-product list.

### 6.2 Email reliability infrastructure — **M (partial)**

v1 has `EmailEvent` (logs every send/bounce/click), SendGrid webhook handler, `email_delivery_canary.py` (periodic test send to verify delivery pipeline). Critical because credential alerts and shift offers go via email.

**v2 status (post-#120):** Substrate present — single `EmailSender` boundary, single `email_events` audit table with the same lifecycle states as v1's `EmailEvent` (sent/failed/bounced/delivered/opened/clicked), idempotency keys, and PHI-redacted subject storage. See [`ADR-011`](../adr/011-email-outbound-boundary.md). **Still missing:** SendGrid webhook handler for bounce/delivery callbacks, delivery canary, message-delivery SLO. Each is a follow-up issue.

### 6.3 System Settings UI with confirmable changes — **M**

v1 has `SystemSetting` with change-reason tracking and confirmable workflow (e.g., changing the mileage rate, the overtime threshold, the family-billing default produces a confirm-with-explanation dialog). All changes audited.

**v2 docs say:** Nothing about agency-configurable settings or the audit trail on setting changes.

### 6.4 Data Health Snapshots & weekly health email — **L**

v1 has `DataHealthSnapshot` (daily counts of users/caregivers/clients/shifts/visits, conflicting roles, query duration) plus `send_weekly_health_email.py` to admins.

**v2 docs say:** Q60 promises a public uptime dashboard "by Year 2." No equivalent of agency-level data-health visibility. This is internal tooling but caregiver/client count is also a *billing* signal (Q10's projected next-month bill).

### 6.5 Status page / DB-down resilience — **L**

v1 has a status endpoint that short-circuits before DB queries (so a DB outage doesn't take the status page down with it).

**v2 docs say:** Q60 SLA but no architectural commitment to a non-DB-dependent status surface.

### 6.6 Schedule export (CSV) for printing/operations — **L**

v1 has schedule-export controls (CSV) used by office staff for hard-copy distribution.

**v2 docs say:** Q62 covers CSV export for cancellation/data portability but nothing about scheduled-shift CSV exports for daily ops.

### 6.7 Rate limiting on critical endpoints — **L** *(implied baseline)*

v1 has explicit `ClockInRateThrottle`, `ChartEntryRateThrottle`, `LoginRateThrottle`. Standard but worth carrying forward to defeat fat-finger floods and credential stuffing.

**v2 docs say:** Nothing — but Q46/Q49 imply a security baseline where this fits.

### 6.8 Operational data tooling (audit / backfill / reconciliation) — **L**

v1 has 80+ management commands across `audit_*.py`, `backfill_*.py`, `reconcile_*.py`, `fix_*.py`. These are the accumulated operational maturity from running v1 in production. Internal only — but rebuilding will rediscover the bugs they were written to detect.

**v2 docs say:** N/A. Just flagging that operational tooling is a non-customer-visible bucket of v1 capability that needs to be re-grown.

---

## 7. Configuration & Admin

### 7.1 Multi-tenant data isolation — **D / forward**

v1 is **single-tenant** (`elitecare/` is the project, single agency per install). v2 explicitly adds RLS-based multi-tenancy (Q49, ADR-002).

**This is a v2 *gain*, not a gap** — listed here only so it doesn't get conflated with the rest of this list. Worth confirming v1 customers can be migrated cleanly into the new tenant model.

### 7.2 GPS at clock-in — **D**

v1 captures lat/long with accuracy on every clock-in/out (`LocationFenceService`). v2 explicitly says **no real-time GPS** (Q19) and offers Wi-Fi fingerprint, NFC, signature, photo, family confirm as alternatives.

**This is deliberate divergence** — listed for the record. Confirm v2's verification mechanisms satisfy the same audit/insurance use cases v1's GPS data does today.

---

## 8. Things v2 Adds (forward-looking, for completeness)

Briefly, things v2 docs commit to that are not in v1:

- **AI features at every tier** (Q31–38): visit documentation structuring, scheduling fit-ranking, care plan drafting, trend surfacing.
- **Per-active-client pricing** with tier overage (v1 has no commercial pricing layer at all).
- **"Your price never goes up" promise** + **annual cost-savings disclosure** (Q8, Q9).
- **99.9% SLA with auto credit** (Q60).
- **Public roadmap with monthly updates** (Q63).
- **14-day onboarding commitment** (Q13).
- **90-day post-cancellation grace + one-click data export** (Q62).
- **Earned wage access integrations** (DailyPay, Tapcheck — Q56).
- **EVV aggregator integration** (Q50) — v1 captures GPS but doesn't push into HHAeXchange/Sandata today.
- **Webhooks API** (Scale tier — Q58).
- **Multi-state operations** + **HCBS waiver workflow** + **pediatric care plans** (v2 mid-2027 — Q63).

---

## 9. Recommended Next Steps

1. **Decide which H-severity items are in v1.0 GA scope** vs. fast-follow. Suggested must-have: 1.1 (invoice revisions), 1.2 (service catalog), 1.3 (recurring billables on care plans), 1.4 (MD orders), 2.1 (rate change scheduling), 2.2 (overpayment consent), 2.6 (expense management), 3.1 (chart templates), 3.2 (structured clinical entries), 3.3 (health reports w/ approval), 5.2 (View As).

2. **Confirm or refute the M-severity needs-confirmation items** by reading v2 ADRs and existing schema (`api/app/models/`). Several may already be partially built; the v2 docs just don't surface them externally.

3. **Add an explicit "labor compliance" bucket to v2 product scope** (covers 2.1–2.3, 2.5, 2.7). v2 targets US private-duty agencies but the v2 docs don't explicitly own state-specific labor obligations the way v1 silently does.

4. **Decide the operational-tooling rebuild strategy** (Section 6.8). Cherry-pick the most-used v1 audit/reconcile commands to seed the v2 ops command set during cutover, rather than relearning the bugs.

5. **For each gap promoted to v1.0 scope, file a GitHub issue** referencing this doc, so the work is tracked through the standard `/define → /design → /implement → /review` pipeline.

---

*Generated 2026-05-06 from press release `[07]-Press-Release.md` + external FAQ `[08]-FAQ-(External).md` against v1 codebase `suniljames/COREcare-access` (commit pinned in [`README.md`](README.md#v1-reference-commit)). The v2 docs are customer-facing; some items below may already be implemented or planned in internal artifacts not surveyed here.*
