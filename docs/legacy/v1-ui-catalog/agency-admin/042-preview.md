---
canonical_id: agency-admin/042-preview
route: /charting/reports/preview/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** Same form layout as [agency-admin/040-generate](040-generate.md) — "Home" breadcrumb, "Generate Health Report" header, "Client" select, "Report Type" radio ("Clinical" / "Family"), "Date Range" radio, "Sections" multi-select; the captured WebP renders the form because the preview endpoint redirects to it when the request lacks the GET parameters needed to render a preview body.

**Interaction notes:**
- Endpoint → `health_report_preview` renders an HTML preview of the health report (clinical or family variant) before PDF generation when the request includes `client_id`, `report_type`, and `days` GET parameters.
- Bare GET → redirects back to [agency-admin/040-generate](040-generate.md) so the operator can compose the parameters; the captured WebP is that redirect target.
- Sibling routes → [agency-admin/040-generate](040-generate.md) (form), [agency-admin/041-clinical](041-clinical.md) (direct PDF), [agency-admin/043-email](043-email.md) (email send).
- Used by → the operator's "preview before sending" workflow when finalizing a health report; the rendered preview applies the formatting options (orientation, font size, detail level) selected on [agency-admin/045-templates](045-templates.md).
- Security → consumed inside the staff-only domain; PHI in the preview body is rendered server-side and gated on the `view_health_reports` capability.
