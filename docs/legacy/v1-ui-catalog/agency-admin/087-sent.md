---
canonical_id: agency-admin/087-sent
route: /password-reset/sent/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Check Your Email", "Tip:", "Didn't receive the email?", "Try Again", "Get Access Help", "← Back to Login" — confirmation page rendered after a reset-request submit.

**Interaction notes:**
- Page load → `PasswordResetSentView` (`auth_service/password_reset_sent.html`) renders the post-submit confirmation; reached as the redirect target of the request POST.
- "Try Again" → returns to [agency-admin/086-password-reset](086-password-reset.md) for visitors who mistyped the email; the response is the same either way.
- Anti-enumeration copy → the page text is intentionally generic ("If an account exists for this email...") so the response for an unknown email is indistinguishable from the response for a real one.
- "Get Access Help" → drills out to the support-contact path (out of catalog scope).
- Inbox guidance → tip callout reminds the visitor to check spam; no client-side polling, the tab simply waits for the visitor to click the link in the delivered email.
