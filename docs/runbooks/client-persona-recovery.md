# Client persona — account recovery runbook

Operational guide for the agency-side recovery path when a Client-as-user
account loses access. Applies to v2 only (v1 has no Client login).

## Standard password reset

The Client uses Clerk's standard email-based password reset on the sign-in
page. The reset email goes to the email address on the Client's User
record, which equals the email used during invite redemption. **No
agency-side action required.**

If the Client never received the reset email:
- Check the Clerk dashboard for delivery status.
- Confirm the user record's email is correct (it must match `clients.email`).
- Re-send the password reset from Clerk if needed.

## Lost access to the email address used during redemption

This is the harder case. The Client's email is the verified-identity field
(per the [Security Engineer review](https://github.com/suniljames/COREcare-v2/issues/125#issuecomment-4399981798)
on issue #125 §3); it is immutable once `clients.client_user_id IS NOT
NULL` to prevent impersonation primitives.

The agency-side recovery path:

1. **Verify the request out-of-band.** Phone the Client (or a known Family
   Member) using the contact information on file. Do **not** rely on the
   inbound channel that originated the request — the working assumption is
   that the email itself was compromised.
2. **Care Manager / Agency Admin opens the Client record** in the v2 admin UI.
3. **Disable the existing account link.** Until a Care-Manager-side
   "email change with audit" feature lands as a follow-up issue, the
   operational path is:
   - Set `users.is_active = false` on the Client's User row (this revokes
     all existing sessions).
   - Update `clients.email` to the new email address. (For v2-MVP this
     happens via direct SQL by the on-call engineer; the future admin
     feature replaces that.)
4. **Reissue the invite.** Care Manager hits the "Send Client invite"
   button on the Client detail page (POST `/api/clients/{id}/invite` with
   the new email).
5. **The Client redeems the new invite** with the new email. Redemption
   creates a fresh User row (or reactivates the existing one) and links
   it to the Client.
6. **Audit:** the audit log captures `client_invite_issued`,
   `client_invite_redeemed`, the User deactivation, and the email change.
   This is the artifact that satisfies HIPAA accounting-of-disclosures
   for the original account's offboarding.

## Suspected account takeover

If there is *evidence* the Client's account was compromised (anomalous login
geo, Family Member reports unfamiliar messages in the thread, agency staff
notice impersonation):

1. **Immediately** set `users.is_active = false` on the Client's User row.
2. Pull the audit log for the past 30 days (`SELECT * FROM audit_events
   WHERE user_id = $1 ORDER BY created_at DESC`) to determine read scope.
3. Notify the Client and any Family Members on the FamilyLink.
4. Run the recovery flow above with a new email address.
5. File an incident report.

## Operational alerting (future)

Per the [SRE review](https://github.com/suniljames/COREcare-v2/issues/125#issuecomment-4399993697)
§2, the structured-log fields are in place for these alerts (delivered as
follow-up issue):

- ≥3 `client_invite_failed_email_mismatch` events on a single token within
  one hour → page on-call.
- Geo-anomaly login (Client ASN ≠ agency ASN) → log + email Care Manager.
- Concurrent Clerk sessions for the same `client_user_id` from different
  IP /24s → log + audit; do not auto-revoke.

The alerting rules ship in a follow-up; the *logs* ship with this issue.

## Out-of-band escalation

If the Client cannot reach the agency (rare) and contacts Anthropic /
COREcare directly: do **not** disclose any account state. Direct them to
their agency. The platform never owns a path to access a Client's account
without the agency's involvement; this is a deliberate trust-boundary
choice.
