---
canonical_id: agency-admin/074-draft
route: /employees/complete-profile/draft/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — POST-only auto-save endpoint with no UI of its own; the captured WebP is the post-redirect blank state because the crawler's `intercept-non-GET` discipline prevents the POST from firing. The endpoint is invoked by the [agency-admin/073-complete-profile](073-complete-profile.md) form's auto-save logic.

**Interaction notes:**
- Endpoint → `complete_employee_profile_draft` accepts partial caregiver profile data as JSON and persists a draft so entered values survive a page reload before final submit.
- ⚠ destructive: POST → upserts a `CaregiverProfileDraft` row (or equivalent draft store); returns the saved timestamp and any per-field validation errors. Skipped by crawler.
- Auto-save cadence → fired by the parent form on field blur and on a debounced timer; the response feeds an inline "saved at HH:MM" indicator in the form.
- Validation → does not block the draft save; per-field errors come back so the UI can show them inline without losing data.
- Final submit → drains the draft and writes the persisted `CaregiverProfile` via [agency-admin/073-complete-profile](073-complete-profile.md).
