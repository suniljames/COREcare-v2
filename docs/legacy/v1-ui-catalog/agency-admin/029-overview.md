---
canonical_id: agency-admin/029-overview
route: /charting/overview/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" / "Charting Overview" breadcrumb, "Charting Overview" header, "Active Clients" / "Low Completion" / "Need Setup" stat cards, "All" / "Needs Setup" / "Low Completion" status filter pills, per-client card with "NEEDS SETUP" pill, "Logout" header link.

**Interaction notes:**
- Page load → `charting_overview` (`charting/charting_overview.html`) lists clients sorted by charting attention priority — overdue, missing today, in progress, complete.
- Per-client card → drills to [agency-admin/030-client](030-client.md), the client's charting tab.
- Status filter pills → re-render with a `?status=` query (GET); the active pill is highlighted.
- "NEEDS SETUP" pill → flagged when the client has no chart template configured; tap drills directly into [agency-admin/031-create-template](031-create-template.md).
- Stat cards → roll-up counters across the active filter window; "Need Setup" mirrors the per-card pill count.
