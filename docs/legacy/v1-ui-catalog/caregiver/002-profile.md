---
canonical_id: caregiver/002-profile
route: /caregiver/profile/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Back to Dashboard", "Choose File" (photo + credential), "Upload Photo", "Save Profile", "Add Credential", persistent "Logout" header link.

**Interaction notes:**
- "Save Profile" → ⚠ destructive: POSTs `action=update_profile` to `my_profile` (`caregiver_dashboard/views.py:2280`); writes first_name/last_name/email to the user record. Skipped by crawler.
- "Upload Photo" → ⚠ destructive: POSTs `action=update_photo` (multipart); validates JPG/PNG and 5 MB cap, stores on `CaregiverProfile.profile_picture`. Skipped by crawler.
- "Add Credential" → ⚠ destructive: POSTs `action=add_credential` (multipart); creates an `EmployeeCredential` row keyed on credential type, document, expiration date, notes. Skipped by crawler.
- "My Credentials" empty state → reflects the fixture's blank credential set; populated render shows expirations + per-row delete actions.
- Username field → read-only; only email and name fields are editable from this screen.
- "Back to Dashboard" → [caregiver/003-dashboard](003-dashboard.md).
