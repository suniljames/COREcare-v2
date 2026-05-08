---
canonical_id: agency-admin/063-timecards
route: /dashboard/admin/timecards/<int:caregiver_id>/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Back to Staff Summary" link, "All times in Pacific Time" subtitle, week paginator ("<" / "05/04 - 05/10/2026" / ">"), "Shift Earnings" hero stat card, "REGULAR HOURS" / "OVERTIME HOURS" / "SHIFT EARNINGS" / "MILEAGE (0.0 MI)" stat cards, "Logout" header link.

**Interaction notes:**
- Page load → `admin_caregiver_timecard` (`dashboard/admin_caregiver_timecard.html`) shows the individual caregiver's timecard detail for the selected period — visits, clock times, hours, pay.
- Per-visit row (populated render) → editable inline via AJAX (clock-in / clock-out time fields); ⚠ destructive on save.
- Week paginator → steps the visible window (GET).
- Stat cards → derived from the period's `Visit` rows: REGULAR HOURS sums non-overtime, OVERTIME HOURS sums overtime, SHIFT EARNINGS sums hourly + differential, MILEAGE sums approved mileage at the active rate.
- Adjacent endpoints → `/dashboard/admin/timecards/<int:caregiver_id>/pdf/` (out of catalog scope) renders the printable PDF via `reportlab` with a timestamped filename.
- "Back to Staff Summary" → [agency-admin/062-timecards](062-timecards.md).
