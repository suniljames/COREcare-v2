---
canonical_id: agency-admin/043-email
route: /charting/reports/email/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** Same form layout as [agency-admin/040-generate](040-generate.md) — "Home" breadcrumb, "Generate Health Report" header, "Client" select, "Report Type" radio, "Date Range" radio, "Sections" multi-select; the captured WebP renders the form because the email endpoint always redirects on completion (success or error).

**Interaction notes:**
- Endpoint → `health_report_email` accepts the report parameters plus a recipient address and optional cover message; emails the generated PDF and redirects on completion.
- ⚠ destructive: form POST → renders the PDF, sends an email via the configured provider, logs the send to a `BillingEmailLog`-style audit row, and redirects to [agency-admin/040-generate](040-generate.md) with a success or error flash. Skipped by crawler.
- Recipient list → seeded from the client's linked family-member emails; an admin can override or add ad-hoc recipients.
- Outbound integration → respects the catalog-fixture's `SENDGRID_DISABLED=1` flag at crawl time so no email actually fires.
- Sibling routes → [agency-admin/040-generate](040-generate.md) (form), [agency-admin/042-preview](042-preview.md) (HTML preview), [agency-admin/044-batch](044-batch.md) (batch zip).
