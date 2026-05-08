---
canonical_id: agency-admin/073-complete-profile
route: /employees/complete-profile/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "stand-in" — the captured WebP shows the admin index. The actual route renders a profile-completion form for caregivers redirected by the v1 `ProfileCompletionMiddleware`; the fixture's super-admin already has a complete profile so the middleware bounces straight to the admin home (see Interaction notes).

**Interaction notes:**
- Endpoint → `complete_employee_profile` renders the profile-completion form for existing caregivers redirected by the v1 `ProfileCompletionMiddleware` before they can clock in.
- ⚠ destructive: form POST → writes the completed `CaregiverProfile` row (title, DOB, contact, optional photo and bio) and redirects to the caregiver dashboard. Skipped by crawler.
- Middleware gate → caregivers without a completed profile get redirected to this URL on every authenticated request until they finish the form; the middleware exempts staff users, which is why the captured response is the admin-index stand-in.
- Auto-save backing → [agency-admin/074-draft](074-draft.md) persists partial drafts so entered data survives a reload before submit.
- Pre-population → the form is pre-filled with any data already on file from the onboarding wizard at [caregiver/001-onboarding](../caregiver/001-onboarding.md).
