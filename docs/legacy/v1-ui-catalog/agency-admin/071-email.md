---
canonical_id: agency-admin/071-email
route: /dashboard/admin/invoices/<int:client_id>/email/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — POST-only endpoint; the captured WebP is the browser's raw-JSON view (`{"error": "POST required"}`) returned for the GET probe by the crawler.

**Interaction notes:**
- Endpoint → `admin_client_invoice_email` accepts a recipient list and an optional cover message; emails the client billing PDF to the client's family members and logs each send to a `BillingEmailLog` row for delivery tracking.
- ⚠ destructive: form POST → renders the PDF, sends an email per recipient via the configured provider, writes one `BillingEmailLog` row per recipient with status (queued / sent / bounced / failed), and redirects to [agency-admin/068-invoices](068-invoices.md) with a success or error flash. Skipped by crawler.
- Recipient list → seeded from the client's linked family-member emails; the form lets an admin override the seeded set or add ad-hoc recipients.
- GET probe response → `{"error": "POST required"}` is the browser-facing safety net; the real form is rendered as a panel inside the per-client invoice detail.
- Outbound integration → respects the catalog-fixture's `SENDGRID_DISABLED=1` flag at crawl time so no email actually fires.
