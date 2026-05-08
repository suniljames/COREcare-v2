---
canonical_id: agency-admin/035-trend
route: /charting/intake-output/<int:client_id>/trend/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Intake/Output Trend" header with client name, "Last 7 days" range toggle, "Daily Totals (mL)" table with "DATE" / "INTAKE (ML)" / "OUTPUT (ML)" / "BALANCE (ML)" column headers and per-row date cells, "Balance = Intake - Output" formula footer, "Logout" header link.

**Interaction notes:**
- Page load → `intake_output_trend` (`charting/intake_output_trend.html`) renders the client's daily fluid intake and urinary output trend with running balance totals.
- "Last 7 days" range → re-renders with a `?days=` query (GET); supported windows are 7, 14, 30, and 90.
- Daily row → fixture-state values are 0 across the table (no chart entries); populated render shows running totals + a stacked bar chart above the table.
- Balance formula footer → confirms the displayed Balance column is computed as Intake − Output for each day.
- Sibling trends → [agency-admin/032-trend](032-trend.md) (vitals), [agency-admin/033-trend](033-trend.md) (glucose).
