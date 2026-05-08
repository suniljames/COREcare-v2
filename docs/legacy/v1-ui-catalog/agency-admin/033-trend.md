---
canonical_id: agency-admin/033-trend
route: /charting/glucose/<int:client_id>/trend/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Blood Glucose Trend" header with client name, "Last 7 days" range toggle, "Blood Glucose (mg/dL)" card, "No glucose readings in last 7 days" empty state, normal-ranges disclaimer ("Normal ranges are timing-based guidelines only and do not constitute clinical advice."), "Logout" header link.

**Interaction notes:**
- Page load → `glucose_trend` (`charting/glucose_trend.html`) renders the client's blood glucose readings as a trend chart with pre/post-meal context flags.
- "Last 7 days" range → re-renders with a `?days=` query (GET); supported windows are 7, 14, 30, and 90.
- Empty state → fixture has no chart entries; populated render shows a glucose time-series with pre/post-meal markers and target-range bands.
- Disclaimer → reminds reviewers that the rendered ranges are timing-based reference values, not clinical guidance.
- Sibling trends → [agency-admin/032-trend](032-trend.md) (vitals), [agency-admin/035-trend](035-trend.md) (intake/output).
