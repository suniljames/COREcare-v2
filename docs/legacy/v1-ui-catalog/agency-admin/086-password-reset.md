---
canonical_id: agency-admin/086-password-reset
route: /password-reset/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Forgot Your Password?", "Email Address", "Send Reset Link", "← Back to Login", "Still having trouble?", "Get Access Help" — auth-service form for requesting a reset email.

**Interaction notes:**
- Page load → `PasswordResetRequestView` (`auth_service/password_reset_request.html`) renders the request form; no database writes on GET.
- ⚠ destructive: form POST → submits the email to the same view; on submit, generates a reset token, persists it to a `PasswordResetToken` row, and queues the reset email. Skipped by crawler.
- "Send Reset Link" → on success, redirects to [agency-admin/087-sent](087-sent.md) regardless of whether the email matched a real account (anti-enumeration response).
- "← Back to Login" → returns to the auth login screen; the auth-service login route is out of catalog scope.
- Token lifecycle → expires after the configured TTL; clicking the emailed link lands on the reset-confirm screen (token-bearing URL, out of catalog scope) which redirects to [agency-admin/089-complete](089-complete.md) on success.
