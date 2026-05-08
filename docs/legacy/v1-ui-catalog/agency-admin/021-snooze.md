---
canonical_id: agency-admin/021-snooze
route: /admin/banners/mileage/snooze/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — POST-only endpoint that returns a redirect; the captured WebP is the post-redirect blank state because the crawler's `intercept-non-GET` discipline prevents the POST from firing. The CTA that triggers this endpoint is the "Remind me later" / "Snooze" button rendered on the January annual mileage-rate banner in v1.

**Interaction notes:**
- Endpoint → mileage-rate "snooze" handler that defers the annual verification reminder for a configurable window without recording the rate as verified.
- ⚠ destructive: POST → writes a snooze-until timestamp to the `SystemSetting` row; audit-logs the actor + snooze duration. Skipped by crawler.
- v1 storage model → same single-row `SystemSetting` constraint as [agency-admin/020-still-current](020-still-current.md); the snooze key is platform-wide, not per-agency.
- Banner re-surfaces → after the snooze timestamp elapses; confirming via [agency-admin/020-still-current](020-still-current.md) clears both the snooze and the unverified-rate flag.
- Failure mode → if neither CTA fires before payroll close, mileage reimbursement falls back to the last-verified rate plus an audit-log warning entry.
