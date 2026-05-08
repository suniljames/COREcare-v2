---
canonical_id: agency-admin/051-schedule
route: /clients/schedule/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — legacy schedule landing renders an empty placeholder; the captured WebP shows the bare "Schedule / Simple schedule view / No shifts found." text and nothing else.

**Interaction notes:**
- Page load → renders an empty schedule placeholder (no shifts preloaded by the legacy view); dual-mounted at `/schedule/schedule/`.
- Family-linked users → redirect to the family home rather than seeing this placeholder; staff users see this empty page when they hit the legacy URL.
- Real schedule UI → lives at the per-client calendar [agency-admin/052-calendar](052-calendar.md) and at the caregiver schedule [caregiver/004-schedule](../caregiver/004-schedule.md).
- v2 disposition → the inventory marks this as deprecated (`D`); the route stays for backwards-compatibility links but no longer surfaces real data.
- Removal candidate → safe to delete during the v2 cutover once outbound link audits confirm nothing internal still points at `/clients/schedule/`.
