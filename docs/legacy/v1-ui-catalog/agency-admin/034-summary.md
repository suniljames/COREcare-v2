---
canonical_id: agency-admin/034-summary
route: /charting/nursing-notes/<int:client_id>/summary/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Nursing Notes" header with client name, "Last 30 days" range toggle, "No nursing notes in last 30 days" empty-state copy, "Logout" header link.

**Interaction notes:**
- Page load → `nursing_notes_summary` (`charting/nursing_notes_summary.html`) lists the client's nursing notes in chronological order with author, timestamp, and section context.
- "Last 30 days" range → re-renders with a `?days=` query (GET); supported windows are 7, 14, 30, and 90.
- Per-note row drill-in → returns to the source `DailyChart` for full context (out of catalog scope).
- Empty state → fixture has no nursing notes for the client; populated render shows entries grouped by date with author + section breadcrumb.
- Audit usage → matches the entries surfaced in the family-visibility chart-comment review at [agency-admin/039-review-queue](039-review-queue.md) when reviewers approve or reject family-facing comments.
