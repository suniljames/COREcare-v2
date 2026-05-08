---
canonical_id: caregiver/005-shift-offers
route: /caregiver/shift-offers/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Accept", "Decline" per offer card; per-card "Needs Response" badge; bottom-nav "Home"/"Schedule"/"Earnings"/"Profile"; header "Logout".

**Interaction notes:**
- Page load → `shift_offers` (`caregiver_dashboard/views.py:131`) lists pending shift offers for the caregiver, with hourly rate + estimated earnings per offer.
- "Accept" / "Decline" → ⚠ destructive: inline POST per card; mutates the matching `ShiftOffer` row's status and triggers downstream notifications. Skipped by crawler.
- Top counter ("N shift(s) need your response") → count of offers in `Needs Response` state.
- Accepted offer → appears on [caregiver/004-schedule](004-schedule.md) and gates a "Ready to Clock In" card on [caregiver/003-dashboard](003-dashboard.md).
