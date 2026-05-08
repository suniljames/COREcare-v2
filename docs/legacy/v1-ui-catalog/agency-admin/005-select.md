---
canonical_id: agency-admin/005-select
route: /admin/view-as/family/select/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "View As Hub" sub-link, "View As Family Member" header, "Search by name..." search box, per-family-member card with "View As →" CTA, "Back to View As Hub" link, "Logout" header link.

**Interaction notes:**
- Page load → `view_as_family_select` (`core/view_as_family_select.html`) renders a searchable list of family-member accounts that the staff user is permitted to impersonate.
- "View As →" CTA → advances to the step-up confirmation form at [agency-admin/006-view-as](006-view-as.md) keyed on the family member's user id.
- "Search by name..." → filters the visible list against the permitted family-member set (server-side filter on submit).
- "Back to View As Hub" → returns to [agency-admin/004-hub](004-hub.md).
- Selection-only → does not start a session; start fires only after step-up password + reason are submitted on the next screen.
