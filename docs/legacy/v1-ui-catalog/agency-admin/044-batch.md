---
canonical_id: agency-admin/044-batch
route: /charting/reports/batch/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Batch Generate Health Reports" header, "Select multiple clients to ..." subtitle, "Report Type" radio ("Clinical" / "Family"), "Date Range" radio ("Last 30 days"), "Clients" multi-select with "Select All" / "Clear All" controls, "No clients with chart access enabled" empty state, "Generate Batch" submit button, "Logout" header link.

**Interaction notes:**
- Page load → `health_report_batch` (`charting/batch_health_report.html`) renders the batch-generate form (multi-select clients, report type, date range).
- "Generate Batch" → ⚠ destructive: POSTs the form to render PDFs for each selected client and stream a zip download; partial-success warnings surface as a flash on redirect when one or more clients failed. Skipped by crawler.
- "Select All" / "Clear All" → toggle the client multi-select; the picker is gated by `view_health_reports` per-client.
- Empty state → fixture has no clients with chart access enabled; populated render shows a checkbox per visible client.
- Sibling routes → [agency-admin/040-generate](040-generate.md) (single), [agency-admin/041-clinical](041-clinical.md) (direct PDF), [agency-admin/042-preview](042-preview.md) (preview), [agency-admin/043-email](043-email.md) (email).
