---
canonical_id: care-manager/002-client
route: /care-manager/client/<int:pk>/
persona: Care Manager
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "← Back", "Email" (one per care-team member), "Schedule" tab, "Charting" tab, "Vitals" tab, "Requests" tab, "Remind [CAREGIVER_NAME]", "Alert admin".

**Interaction notes:**
- Page load → renders the `cm_client_focus` view (`care_manager/views.py:337`). The header shows client name, age, primary diagnosis, and an alert-badge strip combining detected actions (severity-colored) with a "DNR" badge when the assigned client has the flag set. The Care Team section lists every caregiver with an active or upcoming shift on this client; the Family Member contacts list (when present) is rendered alongside.
- Tab links (`?tab=schedule|charting|vitals|requests`) → switch the lower-half panel via querystring; the default is the Schedule tab. The Schedule tab renders a per-day grid for the current week with shift status, time range, assigned caregiver, and per-shift action CTAs. A coverage roll-up at the top of the tab reports hours-covered vs hours-required with an uncovered count.
- "Back" link → navigates to [care-manager/001-care-manager](001-care-manager.md).
- ⚠ destructive: "Remind [CAREGIVER_NAME]" and "Alert admin" buttons → POSTs to action-handler URLs that mutate the action queue. Skipped by crawler.

Unassigned-client access raises `Http404` per the authorization check in `cm_client_focus` (line 344): `pk` must be in `CareManagerService.get_assigned_client_ids(request.user)`.
