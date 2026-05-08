---
canonical_id: caregiver/007-clock
route: /caregiver/clock/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Back to Schedule", "Select Client" dropdown, "Visit Notes" textarea, green "Clock In" button, "Location unavailable" hint, bottom-nav "Home"/"Schedule"/"Earnings"/"Profile", header "Logout".

**Interaction notes:**
- Page load → `clock_page` (`caregiver_dashboard/views.py:473`) renders the unscheduled clock-in form: client picker, optional visit-note seed, geolocation banner.
- "Clock In" → ⚠ destructive: POSTs to start a `Visit` row (unscheduled flow); writes geolocation coords when granted, then redirects to the active-shift detail. Skipped by crawler.
- "Select Client" picker → populated from the caregiver's assigned clients.
- "Location unavailable" hint → reflects the headless browser's denied geolocation permission. Populated render shows lat/long once the prompt is accepted.
- "Back to Schedule" → [caregiver/004-schedule](004-schedule.md).
