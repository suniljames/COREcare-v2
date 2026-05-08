---
canonical_id: caregiver/001-onboarding
route: /caregiver/onboarding/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Continue", "Quick Tour" link, persistent "Logout" header link, fixed "Notifications" footer with "Mark all read", bottom-nav "Home"/"Schedule"/"Earnings"/"Profile".

**Interaction notes:**
- Page load → `caregiver_onboarding` (`caregiver_dashboard/views.py:2690`) clamps the requested step to [1,3] and prevents jumping ahead via `step > profile.onboarding_step`. The captured render is step 1 ("Your Info"); steps 2–3 cover credentials upload + a quick tour.
- Step 1 form → renders Phone, Date of birth, Street/City/State/ZIP, Emergency contact name + phone + relationship.
- "Continue" → ⚠ destructive: POSTs to `_onboarding_step1`, validates the personal-info form, advances `CaregiverProfile.onboarding_step` to 2. Skipped by crawler.
- Already-completed profile load → redirects to [caregiver/003-dashboard](003-dashboard.md) before render; capture only happens for wizard-eligible fixtures.
- "Logout" → POST sign-out (skipped by crawler).
