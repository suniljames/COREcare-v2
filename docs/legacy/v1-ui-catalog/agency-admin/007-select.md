---
canonical_id: agency-admin/007-select
route: /admin/view-as/caregiver/select/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "View As Hub" header with "Caregivers" tab active and the "Family Members" tab inactive, "Search caregivers by name..." search box, per-caregiver card with "View As →" CTA, "Back to Dashboard" link, "Logout" header link.

**Interaction notes:**
- Page load → `view_as_hub` with `?tab=caregiver` (`core/view_as_hub.html`) renders the caregiver tab of the View As hub; the same template + view as [agency-admin/004-hub](004-hub.md) with a different active tab.
- "View As →" CTA → advances to the step-up confirmation form at [agency-admin/008-caregiver](008-caregiver.md) keyed on the caregiver's user id.
- "Search caregivers by name..." → filters the visible list against permitted caregiver targets (server-side filter on submit; live search drives [agency-admin/011-search](011-search.md)).
- Tab switch → reloads with `?tab=family` to surface [agency-admin/004-hub](004-hub.md) with the family tab active.
- "Back to Dashboard" → returns to the admin index without starting a session.
