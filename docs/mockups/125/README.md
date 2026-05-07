# Client persona mockups — issue #125

Mobile-first (375×812) mockups for the three v2 Client-as-user views authored under [#125](https://github.com/suniljames/COREcare-v2/issues/125):

| File | View | Purpose |
|------|------|---------|
| `01-care-plan.svg` | Care plan (read-only, plain language) | Client reads their own care plan summary, care team, allergies, "what we'll help with" |
| `02-schedule.svg` | Upcoming shifts | Client sees today's caregiver + this week's visits |
| `03-messages.svg` | Agency message thread | Client messages the agency (non-urgent) — emergency disclaimer banner |

Design tokens drawn from `docs/design-system/TOKENS.md`. Voice & content rules from `docs/design-system/CONTENT_GUIDE.md`. Accessibility per `docs/design-system/ACCESSIBILITY.md` (WCAG 2.1 AA).

Notes for `/implement`:
- Mobile-first because the typical Client persona skews older and phone-led; desktop layout is a graceful widening, not a separate design.
- Bottom tab bar with three destinations: **Care plan / Schedule / Messages**. Matches the locked minimum view set on this issue.
- No PHI in headers, push titles, or URLs. The Client's own data is shown only inside the authenticated app body.
- Plain-language copy. No clinical jargon ("range-of-motion exercise" → "gentle stretches"). Writer's review enforces this.
