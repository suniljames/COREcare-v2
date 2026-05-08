---
canonical_id: agency-admin/089-complete
route: /password-reset/complete/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Password Updated!", "Go to Login" — success page rendered after the reset-confirm form successfully writes the new password hash.

**Interaction notes:**
- Page load → `PasswordResetCompleteView` (`auth_service/password_reset_complete.html`) renders the success state; reached as the redirect target of a successful reset-confirm POST.
- "Go to Login" → returns to the auth-service login screen (out of catalog scope).
- ⚠ destructive predecessor → the reset-confirm view (token-bearing URL, out of catalog scope) is what actually rotates the password hash and invalidates the token; this page is the post-success terminal.
- Session safety → the visitor remains logged out; the new password must be entered at the login screen before any session is granted.
- Sibling routes → request at [agency-admin/086-password-reset](086-password-reset.md), sent confirmation at [agency-admin/087-sent](087-sent.md).
