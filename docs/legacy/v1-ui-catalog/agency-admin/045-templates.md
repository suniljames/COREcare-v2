---
canonical_id: agency-admin/045-templates
route: /charting/reports/templates/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Report Settings" header, "Manage which sections ..." subtitle, "REPORT TEMPLATES" section with "No report access templates have been created yet. ..." empty state, "NOTES IN REPORTS" section with "Include care notes appendix" + "Show caregiver names" toggles, "Save Notes Settings" green button, "CUSTOM RULES" section with "Override section access ... Most specific rule wins." helper, "+ Add Custom Rule" CTA, "Logout" header link.

**Interaction notes:**
- Page load → `admin_report_templates` (`charting/admin_report_templates.html`) lists report-configuration templates and per-client/caregiver overrides for health-report sections.
- Per-template edit (populated render) → drills to `/charting/reports/templates/<int:template_id>/edit/` (out of catalog scope), where a section-toggle list, formatting defaults, and PDF security settings can be saved.
- "Save Notes Settings" → ⚠ destructive: POSTs the appendix + caregiver-names toggle state to the template defaults; audit-logged. Skipped by crawler.
- "+ Add Custom Rule" → [agency-admin/049-add](049-add.md), which creates a `ReportAccessOverride` mapping a caregiver and/or client to a custom set of report sections.
- Override resolution → "Most specific rule wins" copy reflects the v1 resolver: per-(caregiver, client) overrides beat per-caregiver, which beat per-client, which beat the default template.
