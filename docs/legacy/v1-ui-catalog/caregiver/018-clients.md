---
canonical_id: caregiver/018-clients
route: /caregiver/clients/<int:client_id>/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Navigate (Apple)", "Navigate (Google)", "Open in Maps", "Care Plan" card, "Emergency Contacts" card, bottom-nav "Home"/"Schedule"/"Earnings"/"Profile", header "Logout".

**Interaction notes:**
- Page load → `client_profile` (`caregiver_dashboard/views.py:369`) renders the assigned client's home/care info: address, navigation deep links, care-plan summary, emergency contacts.
- "Navigate (Apple)" / "Navigate (Google)" / "Open in Maps" → external map deep links (`maps:` / `google.com/maps`); navigation only, no v1 mutation.
- "Care Plan" card → surfaces the latest care-plan document for the client; "No care plan documented" empty state appears when none is on file.
- "Emergency Contacts" card → lists the client's emergency contacts; "No emergency contact on file" empty state appears for fixture clients without contacts seeded.
- Route → keyed on the client id; access gated to caregivers with an active assignment to the client.
- "Logout" → POST sign-out (skipped by crawler).
