---
canonical_id: care-manager/001-care-manager
route: /care-manager/
persona: Care Manager
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Logout", "Alert admin", "Followed up", per-action "Remind <caregiver>" buttons, "View full client details ›".

**Interaction notes:**
- Page load → renders the `cm_caseload` view (`care_manager/views.py:86`). The day header reports today's coverage roll-up (shift count, percent covered, on-clock count). Below it, a "Needs attention" section groups assigned clients with active actions; each client row expands to show its action queue with action type, severity, age, and per-action follow-up CTAs.
- "View full client details ›" link → navigates to [care-manager/002-client](002-client.md) for the row's assigned client.
- ⚠ destructive: "Alert admin" and "Followed up" buttons → POSTs to action-handler URLs that mutate the action queue. Skipped by crawler.
- "Logout" → ends the session and redirects to the login page.
