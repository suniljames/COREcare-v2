---
canonical_id: agency-admin/001-todays-shifts
route: /admin/todays-shifts/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Today's Shifts" header, "SCHEDULED HOURS" / "TOTAL WAGES" / "CAREGIVERS" stat cards, status legend ("Not Started" / "Working" / "Completed"), per-shift card with caregiver avatar + status pill ("Not clocked in"), "Logout" header link.

**Interaction notes:**
- Page load → `todays_shifts_dashboard` (`admin/todays_shifts_dashboard.html`) renders today's shifts grouped by caregiver with clock-in status, scheduled vs. actual hours, and total wages.
- Per-shift card → drills to the shift or visit detail.
- Status pills ("Not Started" / "Working" / "Completed") → derived from the shift's clock state; visit hasn't started, in progress, or finalized.
- Page times → reported as Pacific per the page header copy.
- Header breadcrumb ("Home" → "Today's Shifts") → returns to the admin index when tapped.
