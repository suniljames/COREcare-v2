---
canonical_id: agency-admin/040-generate
route: /charting/reports/generate/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Generate Health Report" header, "Generate a PDF health report ..." subtitle, "Client" select, "Report Type" radio ("Clinical (detailed)" / "Family (plain-language)"), "Date Range" radio ("Last 7 days" / "Last 30 days"), "Sections" multi-select with section keys + labels, "Generate Report" submit button, "Logout" header link.

**Interaction notes:**
- Page load → `health_report_generate` (`charting/generate_health_report.html`) renders the report-builder with client picker, report-type radio, date-range radio, and a section toggle list (vital_signs, blood_glucose, intake_output, bowel_movements, nursing_notes, mood_status, tasks, medications, mood_tracking, care_notes_appendix).
- "Generate Report" → ⚠ destructive: POSTs the form to enqueue PDF generation; redirects to the email or download endpoint depending on the submitted action. Skipped by crawler.
- "Report Type" radio → "Clinical" produces the detailed clinical PDF used internally; "Family" produces the plain-language family-facing variant rendered at [agency-admin/042-preview](042-preview.md).
- Sections multi-select → seeded with the active `ReportTemplate` defaults for the selected client; per-client overrides ([agency-admin/049-add](049-add.md)) narrow the included set.
- Sibling routes → [agency-admin/041-clinical](041-clinical.md) (direct PDF), [agency-admin/042-preview](042-preview.md) (HTML preview), [agency-admin/043-email](043-email.md) (email send), [agency-admin/044-batch](044-batch.md) (batch zip).
