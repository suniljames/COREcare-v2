---
canonical_id: agency-admin/036-summary
route: /charting/bowel-movement/<int:client_id>/summary/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Bowel Movement Summary" header with client name, "Last 7 days" range toggle, "No bowel movements in the last 7 days" empty-state copy, "Logout" header link.

**Interaction notes:**
- Page load → `bowel_movement_summary` (`charting/bowel_movement_summary.html`) lists the client's bowel-movement events with consistency, color, and notes grouped by day.
- "Last 7 days" range → re-renders with a `?days=` query (GET); supported windows are 7, 14, 30, and 90.
- Per-event row drill-in → returns to the source `DailyChart` (out of catalog scope) so the reviewer can see the original chart context.
- Empty state → fixture has no events for the client; populated render groups entries by date with consistency + color icons + free-text notes.
- Sibling summary → [agency-admin/034-summary](034-summary.md) (nursing notes).
