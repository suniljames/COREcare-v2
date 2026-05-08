---
canonical_id: agency-admin/083-accessibility
route: /legal/accessibility/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Logout" header link, "Home" bottom-nav, "Schedule" bottom-nav, "Accessibility" footer link, "Phone:" + "Email:" feedback contacts; the page body itself is read-only legal copy with the agency's WCAG conformance statement.

**Interaction notes:**
- Page load → `accessibility_statement` returns the static `legal/accessibility.html` template with no database writes.
- Public route → no auth required; the captured WebP shows the admin header chrome because the crawler navigated while authenticated, but the same URL renders for anonymous visitors with the public header instead.
- Feedback contacts → renders the configured agency phone and email from the template; swapping production values is a settings/template change, not a per-request read.
- Last-updated stamp → bottom italic line is hard-coded in the template at v1 publish time, not derived from a database column.
- Sibling routes → privacy-policy and terms-of-service follow the same static pattern (out of catalog scope).
