---
canonical_id: care-manager/001-care-manager
route: /care-manager/
persona: Care Manager
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Logout".

**Interaction notes:**
- "Logout" → ends the session and redirects to the login page.
- Page load → renders the `cm_caseload` view (`care_manager/views.py:86`). The logged-in user has zero assigned clients in the captured fixture, so the page shows the empty state: a roster icon, the heading `No Clients Assigned`, and a hint that schedules, care plans, and action items appear once the administrator assigns clients.
- With assigned clients (not visible at this `seed_state`) → the same view renders priority-sorted caseload groups, an action queue, an all-clear group, and a daily summary per `templates/care_manager/caseload.html`. Action-queue links would route to per-client and per-action targets but are not exercised here.
