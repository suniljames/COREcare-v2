---
canonical_id: agency-admin/020-still-current
route: /admin/banners/mileage/still-current/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — POST-only endpoint that returns a redirect; the captured WebP is the post-redirect blank state because the crawler's `intercept-non-GET` discipline prevents the POST from firing. The CTA that triggers this endpoint is the "Rate is still current" button rendered on the January annual mileage-rate banner in v1.

**Interaction notes:**
- Endpoint → mileage-rate "still-current" confirmation handler that records the current rate as verified for the year and dismisses the banner.
- ⚠ destructive: POST → updates the `SystemSetting` for the verified-this-year flag; audit-logs the actor + rate + verified-at timestamp. Skipped by crawler.
- v1 storage model → the mileage rate lives as a single `SystemSetting` row (single-tenant), which means the v2 refactor has to decide between per-agency and platform-wide mileage rates before this CTA can be ported.
- Sibling endpoint → [agency-admin/021-snooze](021-snooze.md) defers the verification rather than confirming it.
- Annual cadence → the banner re-surfaces every January until either confirmation or snooze is recorded.
