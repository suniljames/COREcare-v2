---
canonical_id: agency-admin/031-create-template
route: /charting/client/<int:client_id>/create-template/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" / "Clients" / "Client name" / "Charting" / "Create Template" breadcrumb, "Create Chart Template" header, step indicator "1", "How would you like to start?" prompt, "Start with all sections" preset radio with helper "Include all 10 core sections. You can choose what to remove in the next step.", "Cancel" / "Next" footer CTAs, "Logout" header link.

**Interaction notes:**
- Page load → `create_template_wizard` (`charting/create_template_wizard.html`) walks an admin through configuring the client's chart-template sections, items, and inclusion settings.
- "Next" → ⚠ destructive on final step: POSTs the wizard payload to create or update the `ChartTemplate` row; intermediate steps re-render the wizard with `?step=N` (GET) so the crawler captured the step-1 entry. Skipped by crawler.
- "Cancel" → returns to [agency-admin/030-client](030-client.md) without saving.
- "Start with all sections" preset → seeds the section list with v1's 10 core sections; subsequent steps let the admin toggle excluded sections, mark sections as required, and pick exclusion reasons.
- Wizard step model → enforces a section-then-item ordering so the section toggles in step 2 drive the item picker shown in step 3.
- Same-template re-edit → re-uses this wizard view, pre-populated from the active `ChartTemplate`.
