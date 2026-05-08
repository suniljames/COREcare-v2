---
canonical_id: caregiver/004-schedule
route: /caregiver/schedule/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Prev"/"Today"/"Next", "Day"/"Week"/"Month", per-shift card with "CONFIRMED" + "MORNING" badges, bottom-nav "Home"/"Schedule"/"Earnings"/"Profile", header "Logout".

**Interaction notes:**
- Page load → `my_schedule` (`caregiver_dashboard/views.py:2165`) renders the caregiver's confirmed shifts with status pills + addresses; populated by `Visit` rows for the logged-in caregiver.
- "Prev" / "Today" / "Next" → re-render the same view at a shifted date range (GET).
- "Day" / "Week" / "Month" toggle → switch granularity (GET).
- Per-shift card → leads to the matching active-shift / clock-in flow when the shift window opens (covered by inventory rows for `/caregiver/shift/<id>/active/` and `/caregiver/shift/<id>/clock-in/`).
- Legend area → surfaces shift-status colors (CONFIRMED / MORNING / etc.); decorative match against the badges shown on each card.
- "Logout" → POST sign-out (skipped by crawler).
