# Content Guide

## Voice & Tone

COREcare speaks with **warmth**, **clarity**, and **confidence**. We serve people in stressful situations — caregivers managing heavy workloads, families worried about loved ones. Our words should reduce anxiety, not add to it.

### Principles

1. **Be direct.** Say what happened, what to do next. No jargon, no hedging.
2. **Be human.** Use natural language. "Your shift starts in 30 minutes" not "Shift commencement notification."
3. **Be calm.** Even errors should feel manageable. "We couldn't save that — try again" not "CRITICAL ERROR: Save failed!"
4. **Be HIPAA-safe.** Never expose patient names, diagnoses, or health details in notifications, errors, or logs.

## Error Messages

### Structure
1. **What happened** (brief, factual)
2. **Why** (if helpful and non-technical)
3. **What to do** (specific action)

### Examples

| Scenario | Message |
|----------|---------|
| Network error | "Couldn't connect to the server. Check your internet and try again." |
| Validation | "Please enter a valid phone number (e.g., 555-123-4567)." |
| Permission denied | "You don't have access to this page. Contact your agency admin if you need access." |
| Not found | "We couldn't find that page. It may have been moved or removed." |
| Session expired | "Your session has expired. Please sign in again." |
| Rate limited | "Too many attempts. Please wait a moment and try again." |

### Anti-Patterns
- "An error occurred" (too vague)
- "Error 500: Internal Server Error" (technical jargon)
- "Invalid input" (unhelpful — which input? what's wrong?)
- "Contact support" (without first suggesting self-service)

## Empty States

Every empty state needs:
1. **What this area shows** (when there's data)
2. **Why it's empty** (if not obvious)
3. **What to do** (call to action)

| Page | Empty State |
|------|-------------|
| Schedule | "No shifts scheduled. Your manager will post shifts here when they're available." |
| Notifications | "You're all caught up! New notifications will appear here." |
| Client list | "No clients yet. Add your first client to get started." + [Add Client] button |
| Visit history | "No visits recorded for this client yet." |
| Dashboard charts | "Not enough data to show trends. Check back after a few shifts." |

## Button Labels

Use **action verbs** that describe the outcome:

| Instead of | Use |
|-----------|-----|
| Submit | Save Changes / Create Shift / Send Invite |
| OK | Got It / Continue |
| Cancel | Discard / Go Back |
| Delete | Remove Client / Delete Shift |
| Yes/No | Delete / Keep (in confirmation dialogs) |

### Confirmation Dialogs

```
Delete this shift?

This will remove the shift from the schedule and notify the assigned caregiver.
This action cannot be undone.

[Keep Shift]  [Delete Shift]
```

The destructive action button is always labeled with the specific action, never just "Delete" or "Yes".

## Notification Copy

### HIPAA-Safe Patterns

| Type | Safe | Unsafe |
|------|------|--------|
| Shift reminder | "You have a shift starting at 8:00 AM" | "Shift with John Smith for medication administration at 123 Oak St" |
| New message | "You have a new message" | "Message from Dr. Jones about patient's condition" |
| Visit complete | "A visit has been documented" | "Visit for diabetes care completed" |
| Credential alert | "A credential is expiring soon" | "Your RN license expires March 15" |

### Push Notification Format

```
Title: COREcare (always the app name)
Body: <generic action description>
```

Details are shown only after the user opens the app and authenticates.

## Date & Time

- Always show timezone for scheduled events
- Use 12-hour format with AM/PM (matches US healthcare conventions)
- Relative time for recent events: "5 minutes ago", "Yesterday at 3:00 PM"
- Absolute time for scheduled events: "Monday, March 10 at 8:00 AM PST"

## Numbers & Units

- Currency: $1,234.56 (USD, always two decimal places)
- Hours worked: "6h 30m" (short form in summaries), "6 hours, 30 minutes" (long form in reports)
- Distances: "0.3 miles away" (for geofencing display)
- Percentages: "87%" (no decimals unless precision matters)
