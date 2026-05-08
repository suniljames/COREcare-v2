# V1 Glossary

> **Read [`README.md`](README.md) first.** It locks the persona vocabulary.

Terms specific to COREcare v1 (`hcunanan79/COREcare-access`) that appear across this docset. **Persona names** (`Super-Admin`, `Agency Admin`, `Care Manager`, `Caregiver`, `Client`, `Family Member`) and general homecare vocabulary (`Care Plan`, `Visit`, `Shift`, `ADLs`, `PHI`) are defined in the canonical [`docs/GLOSSARY.md`](../GLOSSARY.md), not duplicated here.

This file extends the canonical glossary with v1-specific terms — model names, internal feature names, and Django app names that come up when reading v1 source.

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

---

## Format

For each term: one-line definition, then a link to its first significant use in this docset (a heading anchor in `v1-pages-inventory.md`, `v1-user-journeys.md`, or `v1-integrations-and-exports.md`).

---

## Entries

- **9-category expense workflow** — v1's unified `Expense` model uses nine fixed categories (supplies, equipment, transportation, meals, training, medical, groceries, admin, other) and eight workflow states (draft, submitted, pending, approved, processed, adjusted, rejected, reimbursed). See [the expense submission journey](v1-user-journeys.md#expense-submission--visit-linked-or-standalone).
- **Action queue** — v1 deterministic-detection feed of items needing a coordinator response (no-shows at 15-minute grace, overdue care requests, vital-sign trend flags); priority-sorted on the Care Manager caseload page. Distinct from v2's planned AI-driven coordination assistant, which is inferred rather than rule-based. See [the Care Manager caseload journey](v1-user-journeys.md#team-oversight--caseload-action-queue-and-field-expense-submission).
- **Active shift** — the in-flight visit dashboard rendered while a caregiver is clocked in, surfacing chart entry, comments, mileage, and reimbursement actions. See [the Caregiver caregiver_dashboard section](v1-pages-inventory.md#caregiver_dashboard).
- **`BillableServiceCatalog`** — v1 model for the agency-managed catalog of add-on billable services with internal name, family-facing label, base price, estimated hours, hourly overage rate, MD-order requirement flag, and a soft-retire pattern that preserves invoice history. See [the Agency Admin billing_catalogs section](v1-pages-inventory.md#billing_catalogs).
- **`ChartTemplate`** — v1 charting model with a one-active-per-client invariant via `is_active`; owns `ChartTemplateSection` and `ChartTemplateSectionItem` rows that drive per-section inclusion, requirement, and exclusion-reason controls. See [the Agency Admin charting section](v1-pages-inventory.md#charting).
- <a id="client-v1-vs-v2"></a>**`Client` (v1 record)** — `clients.models.Client`, a v1 subject of care with no `User` linkage and no authenticated route — clients never log in to v1. Distinct from a future v2-hypothetical Client-as-user persona (tracked in [#125](https://github.com/suniljames/COREcare-v2/issues/125)) which would add a Clerk role and RLS policy. See [the Client section](v1-pages-inventory.md#client-section).
- **`ClientFamilyMember`** — v1 model linking a Django `User` to a `Client` for family-portal visibility, with `unique_together(client, user)` plus per-link permission booleans (`can_view_schedule`, `can_message_caregivers`); v1 has no soft-delete, no active flag, and no expiry — revocation is hard-delete. See [the Family Member section](v1-pages-inventory.md#family-member).
- **Django superuser** — v1 user flag (`is_superuser=True`) that grants the strictly Super-Admin-only surface in v1 (the View-As emergency kill switch); necessary-but-not-sufficient for the v2 Super-Admin persona, which adds tenant-bypass policy on top. See [the Super-Admin section](v1-pages-inventory.md#super-admin).
- **`elitecare`** — the v1 Django project root (the `elitecare/` directory containing `settings.py` and `urls.py`); not a Django app name. Top-level admin routes are registered in `elitecare/urls.py` outside any `include()`. See [the Agency Admin top-level routes](v1-pages-inventory.md#agency-admin-top-level).
- **Health report approval queue** — v1 staff queue of caregiver-initiated health-report requests awaiting approval before family delivery; v1 generates reports in two parallel versions (family-friendly and clinical) and gates the family-facing version behind explicit staff sign-off. See [the Agency Admin charting section](v1-pages-inventory.md#charting).
- **`InvoiceRevision`** — v1 model representing a corrected, reissued invoice with revision numbering and concurrent-issue row locking; the corrected-invoice editor route depends on it. See [the Agency Admin billing section](v1-pages-inventory.md#billing).
- **`issue_revision_editor()`** — v1 view function for the corrected-invoice editor flow that reissues an `InvoiceRevision` with concurrent-issue locking. See [the Agency Admin billing section](v1-pages-inventory.md#billing).
- **kill-all** — v1 View-As emergency control that terminates every active impersonation session at once; the only HTML route programmatically gated to Django superusers alone via `@user_passes_test(lambda u: u.is_superuser)`. See [the Super-Admin top-level routes](v1-pages-inventory.md#super-admin-top-level).
- <a id="magiclinktoken"></a>**`MagicLinkToken`** — v1 model backing email-based magic-link login; a 30-minute single-use UUID token explicitly disabled for `is_staff`/`is_superuser` users at the view layer (a security stance, not a UX stance — staff are routed through the password-reset flow). See [the Agency Admin auth_service section](v1-pages-inventory.md#auth_service).
- **Meal-break waiver** — v1 caregiver-consent record (`MealPeriodWaiver`) for waiving meal breaks under state labor rules; an immutable IP-stamped attestation per `BaseAttestation` semantics, gated on `shift_hours > 5` at clock-out, with non-voluntary waivers rolling up into `DailyTimesheet.meal_penalty_count` for premium-pay calculation. See [the clock in and out journey](v1-user-journeys.md#clock-in-and-out-at-a-shift).
- **Overpayment consent** — v1 acknowledgment record (`OverpaymentConsent`) for caregivers to accept an overpayment correction before deduction; legally-defensible immutable IP-stamped attestation per `BaseAttestation` semantics, mandatory under California labor law and FLSA before any unilateral paycheck deduction. See [the email pipeline integrations section](v1-integrations-and-exports.md#email-pipeline).
- **Post-shift summary** — the wrap-up screen rendered after clock-out, reviewing visit duration, billable services performed, comments, and attachments. See [the Caregiver caregiver_dashboard section](v1-pages-inventory.md#caregiver_dashboard).
- **Profile completion gate** — v1 onboarding control that blocks caregivers from accepting shifts or clocking in until required profile fields are filled; enforced at the middleware layer rather than per-view. See [the caregiver onboarding journey](v1-user-journeys.md#caregiver-onboarding--invitation-through-profile-activation).
- **`ProfileCompletionMiddleware`** — v1 middleware that redirects caregivers to `/employees/complete-profile/` until their profile is complete; the enforcement layer behind the Profile completion gate. See [the caregiver onboarding journey](v1-user-journeys.md#caregiver-onboarding--invitation-through-profile-activation).
- **`promote_to_recurring_view()`** — v1 view function that converts a one-off `VisitBillableService` attachment into a recurring rule on the parent `CarePlan`; gated by capability and exposed at `/admin/visit-services/<int:vbs_id>/promote/`. See [the Agency Admin billing section](v1-pages-inventory.md#billing).
- <a id="rls-bypass-surface"></a>**RLS-bypass surface** — v2 architectural concept naming the set of routes a platform-operator persona reaches across tenant boundaries by design; v1's audit-logged View-As suite is the precedent, and v2 design treats every cross-tenant-reachable route as an RLS-bypass surface requiring audit logging. See [the Super-Admin section](v1-pages-inventory.md#super-admin).
- **Shift offer** — a pending shift assignment surfaced to a caregiver for inline accept or decline before the shift starts. See [the Caregiver caregiver_dashboard section](v1-pages-inventory.md#caregiver_dashboard).
- <a id="view-as-impersonation"></a>**View-As impersonation** — v1 super-admin feature for assuming an Agency-Admin context to reproduce user-specific issues, with a full audit trail; the operator's audit-log identity remains distinct from the impersonated user's session context, and every step under impersonation writes to the v1 audit log. The v1 precedent for the v2 RLS-bypass surface concept. See [the View-As impersonation journey](v1-user-journeys.md#view-as-impersonation-with-audit-trail).
- **Visit (v1 aggregate)** — the field-flow aggregate root for caregivers; clock state, mileage, expense reimbursements, comments, and charting all attach to a Visit, and most caregiver routes are keyed on `<int:visit_id>`. See [the Caregiver section](v1-pages-inventory.md#caregiver).

---

## Cross-cutting v1 conventions

A recurring v1 pattern surfaces across this docset: route handlers that stream files or render scoped landings frequently lack audit logging, and v2 must close those gaps. Rows flagged this way include the Family Member dashboard, the family-portal access helper `_check_client_access`, expense-receipt downloads on both the Caregiver and Care Manager portals, and the Care Manager `cm_serve_receipt` handler. The pattern is consistent enough that v2 design should treat any new download or scoped-landing handler as audit-required by default rather than opt-in. Magic-link login is already audit-logged on use in v1 and serves as the worked example of the desired posture.
