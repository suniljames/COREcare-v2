---
canonical_id: caregiver/003-dashboard
route: /caregiver/dashboard/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Clock In Now" hero, "On Shift Now", "Tap to review →" notification CTA, "Clock In", "+ Start Unscheduled Visit", "View Full Schedule", "Mark all read", "My Profile & Credentials", "My Expenses", bottom-nav "Home"/"Schedule"/"Earnings"/"Profile", header "Logout".

**Interaction notes:**
- Page load → `caregiver_dashboard` (`caregiver_dashboard/views.py:57`) routes through `DashboardStateService.get_state` to pick the IDLE / EMPTY / ACTIVE / POST_SHIFT fragment. The captured render is the IDLE state with an upcoming "Ready to Clock In" card.
- "Clock In Now" / "Clock In" → POST to `clock_in_shift` (`caregiver_dashboard/urls.py:51`) for the next scheduled visit. Skipped by crawler.
- "+ Start Unscheduled Visit" → [caregiver/007-clock](007-clock.md).
- "Tap to review →" → [caregiver/005-shift-offers](005-shift-offers.md) when shift offers need a response.
- "View Full Schedule" → [caregiver/004-schedule](004-schedule.md).
- "My Profile & Credentials" → [caregiver/002-profile](002-profile.md). "My Expenses" → [caregiver/020-expenses](020-expenses.md).
- "Earnings" band ("~$0.00 EARNED") → fixture artifact; populated render shows current-week dollars from `weekly_summary` data.
- Notifications list → pulled from `NotificationService.get_unread_count` + `/api/notifications/`. "Mark all read" → POST to `mark_all_notifications_read`. Skipped by crawler.
- `@ensure_csrf_cookie` decorator → required so the JS clock-in flow can read the CSRF token from the cookie.
