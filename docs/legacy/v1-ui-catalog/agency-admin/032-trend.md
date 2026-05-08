---
canonical_id: agency-admin/032-trend
route: /charting/vital-signs/<int:client_id>/trend/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Vital Signs Trend" header with client name, "Last 7 days" range toggle, per-metric card ("BP Systolic" mmHg, "BP Diastolic" mmHg, "Heart Rate" bpm, "Respiratory Rate" breaths/min, "Temperature" °F, "SpO2" %), "No readings in the last 7 days" empty state, "insufficient data" hint, "Logout" header link.

**Interaction notes:**
- Page load → `vital_signs_trend` (`charting/vital_signs_trend.html`) renders a time-series of systolic and diastolic blood pressure, pulse, respiratory rate, temperature, and SpO2 across the configured day window.
- "Last 7 days" range → re-renders with a `?days=` query (GET); supported windows are 7, 14, 30, and 90.
- Per-metric card empty state ("No readings in the last 7 days") → fixture has no chart entries; populated render shows a sparkline with min / max / latest readings and a target-range band.
- "insufficient data" hint → surfaces under each empty card and indicates that the client has fewer readings than the minimum threshold needed to render the trend.
- Sibling trends → [agency-admin/033-trend](033-trend.md) (glucose), [agency-admin/035-trend](035-trend.md) (intake/output).
