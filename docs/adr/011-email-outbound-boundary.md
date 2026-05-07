# ADR-011: Email Outbound Boundary

**Status:** Accepted
**Date:** 2026-05-07
**Related:** ADR-002 (RLS), ADR-007 (Event-Sourced Audit Logging)
**Issue:** [#120](https://github.com/suniljames/COREcare-v2/issues/120)

## Context

v1 has two paths for the same client-billing-email surface
(`/dashboard/admin/invoices/<client_id>/email/`):

1. `dashboard/views.py:admin_email_billing_pdf` constructs a raw
   `django.core.mail.EmailMessage` and writes a row to `BillingEmailLog`.
   No subject-injection guards.
2. `billing/services/invoice_email_service.py` validates the subject
   (rejects subjects > 200 chars or containing `\r\n` per
   `invoice_email_service.py:138–144`) and writes a row to
   `InvoiceEmailLog`.

Both end up at the same v1 URL. The dashboard path bypasses the safer helper.
Operators querying "did the family receive the invoice?" must check both
tables, and a malicious display name could inject CRLF and split the message
on the unsafer path. (No known exploitation; design gap, not active
vulnerability.)

v2 has `Invoice` and `InvoiceLineItem` models but no email-send capability,
no `EmailEvent`-equivalent, and no SendGrid wiring. The whole email surface
is greenfield. We can either lock in a single boundary now or repeat v1's
divergence as features ask for email.

## Decision

Introduce a single outbound-email boundary in v2 with eight hard contracts.

### 1. Single sender

`app.services.email.sender.EmailSender.send()` is the only function in v2
that hands a message to a transport. No router, feature service, or
background job calls a transport SDK directly.

### 2. Single audit table

One `email_events` table covers every outbound email category. v1's
`BillingEmailLog` + `InvoiceEmailLog` split is not carried forward.
Per-feature richness lives in:
- `category: EmailCategory` enum
  (`invoice`, `credential_alert`, `shift_offer`, `weekly_health`, `system`)
- `ref_id: UUID` — points at the domain object (`invoice.id`, `credential.id`, …)

Operator query: `SELECT * FROM email_events WHERE agency_id=? AND
category='invoice' AND ref_id=?` — one index seek.

### 3. Audit-first ordering

`EmailEvent` is INSERTed before `transport.deliver()` is invoked. A failed
transport call leaves a row with `status=failed`. There is no "sent but
unlogged" outcome.

### 4. Subject validation, hard-reject

CRLF / NUL / over-200 chars / empty subjects raise
`EmailValidationError`. No sanitize-and-continue. Validation lives at the
boundary, not at call sites.

### 5. Idempotency

`idempotency_key` is `UNIQUE` in the database. Re-sending with the same key
returns the existing event without a transport call. A pending event with
the same key raises `IdempotencyConflict`.

The window definition is the caller's responsibility:
- `invoice`: key = `invoice:{invoice.id}:{recipient}` (one send per invoice
  per recipient, ever).
- `credential_alert`: key = `credential:{cred.id}:{recipient}:{date}` (one
  per recipient per day max).
- `shift_offer`: key = `shift_offer:{shift.id}:{recipient}` (one per shift
  per recipient).

### 6. PHI redaction at write

Outbound delivery sees the rendered subject (PHI included where appropriate;
the family member receiving the invoice deserves the client's actual name).
The `email_events` row stores:

- `subject_redacted` — PHI-scrubbed via
  `app.services.email.redaction.render_subjects`. Named PII parameters
  (`client_name`, `family_name`, `caregiver_name`, …) become tokens
  (`<client>`, `<family>`, `<caregiver>`). A regex pass strips emails,
  phones, SSN-shaped patterns, and dates more granular than year (HIPAA
  Safe Harbor).
- `subject_hash` — SHA-256 of the rendered subject. Useful for dedup and
  diagnostics without storing PHI.

Bodies live in object storage referenced by `body_storage_uri`. The audit
row never carries body content.

### 7. Tenant scoping

`agency_id` is required on `EmailSender.send()` and re-validated against the
session's RLS context (`app.current_tenant_id`). A misrouted email — agency
A's data sent under agency B's context — is the worst-case outcome and is
blocked at multiple layers (caller-supplied `agency_id`, sender re-check,
RLS policy on `email_events` and on the source domain table).

### 8. Architecture-fitness test

`api/app/tests/architecture/test_email_boundary.py` AST-scans every module
under `api/app/` (excluding tests and the email package itself) and fails
CI if any imports `sendgrid`, `smtplib`, or
`app.services.email.transports`, or imports a private symbol from
`app.services.email.*`. Removing or weakening this test requires a new ADR.

## Consequences

### Positive

- One place to look, one place to validate, one place to enforce tenant
  isolation.
- Operator query "did the family receive the invoice?" is a single index
  seek.
- Header-injection class of bug is eliminated at the boundary.
- Future email features (credential alerts, shift offers, weekly health)
  inherit validation, idempotency, and audit guarantees by construction.

### Negative

- One more abstraction between feature code and SendGrid. Trivial cost in
  exchange for the closure of the v1 footgun.
- The PHI redactor is a new module with its own correctness requirements
  (false negatives leak PHI to the audit row; false positives produce
  unhelpful subjects). Tests live with the redactor; extend rules as new
  email categories add fields.

### Risks

- **A future feature reaches around the boundary.** Mitigated by the
  architecture-fitness test (CI hard fail). If a legitimate need arises to
  bypass — there is none we can foresee — it requires a new ADR.
- **PHI leak via a subject template that wasn't redacted.** Mitigated by
  the regex pass in `redact_phi`. If a leak is discovered, extend the
  named-parameter token map in `redaction.py` and add a regression test.
- **Idempotency key collision between features.** Mitigated by the
  `category:{ref_id}:{...}` namespacing convention; categories are mutually
  exclusive.

### Deferred (out of scope for this ADR)

- SendGrid webhook handler for bounce/delivery callbacks (separate issue).
- Delivery canary (separate issue, captured in
  `v1-functionality-delta.md §6.2`).
- v1 → v2 email-log backfill (cutover scope, in `CUTOVER_PLAN.md`).
- Job queue / async delivery infrastructure (separate ADR when justified).
- LLM-generated email content. When this lands, generated text must be
  validated/redacted before reaching `EmailSender.send`; the sender stays
  AI-agnostic.

## Implementation reference

| Concern | Module |
|---|---|
| Sender | `api/app/services/email/sender.py` |
| Transports | `api/app/services/email/transports.py` |
| Redaction | `api/app/services/email/redaction.py` |
| Public surface | `api/app/services/email/__init__.py` |
| Audit row | `api/app/models/email.py` |
| Schema | `api/alembic/versions/0002_email_events.py` |
| Sender unit tests | `api/app/tests/services/email/test_sender.py` |
| Feature tests | `api/app/tests/services/test_billing_email.py` |
| Architecture-fitness | `api/app/tests/architecture/test_email_boundary.py` |
| Settings | `api/app/config.py` (`email_transport`, `email_from_address`, `sendgrid_api_key`) |
