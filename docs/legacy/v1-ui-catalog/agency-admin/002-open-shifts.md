---
canonical_id: agency-admin/002-open-shifts
route: /admin/open-shifts/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Open Shifts" header, "OPEN SHIFTS" / "TOTAL HOURS" / "CAREGIVERS NEEDED" stat cards, per-shift card with "Open" pill, "Logout" header link.

**Interaction notes:**
- Page load → `open_shifts_dashboard` (`admin/open_shifts_dashboard.html`) lists unassigned shifts ordered by start time, with client name and required hours.
- Per-shift card → drills to shift detail to assign a caregiver.
- "OPEN SHIFTS" / "TOTAL HOURS" / "CAREGIVERS NEEDED" → roll-up counters across the unassigned shift queue.
- Page load times → reported as Pacific per the page header copy.
