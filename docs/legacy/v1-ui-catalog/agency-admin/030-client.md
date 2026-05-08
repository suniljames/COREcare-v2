---
canonical_id: agency-admin/030-client
route: /charting/client/<int:client_id>/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" / "Clients" / "Client name" / "Charting" breadcrumb, "Charting" header, "Back to Client" link, "No chart template yet" empty-state card, "+ Create Chart Template" green CTA, helper copy ("Templates include all sections by default. You'll choose which to ..."), "Logout" header link.

**Interaction notes:**
- Page load → `client_charting_tab` (`charting/client_charting_tab.html`) renders the per-client charting tab with active-template summary, recent charts, today's stats, and trend links.
- "+ Create Chart Template" → [agency-admin/031-create-template](031-create-template.md).
- "Back to Client" → returns to the client detail page (out of catalog scope).
- Per-trend nav links (populated render) → drill to the matching trend / summary surfaces ([agency-admin/032-trend](032-trend.md) for vital signs, [agency-admin/033-trend](033-trend.md) for glucose, [agency-admin/034-summary](034-summary.md) for nursing notes, etc.).
- "No chart template yet" empty state → reflects the fixture's first-touch state for this client; populated render shows the template name, section list, and a "Recent Charts" history block.
