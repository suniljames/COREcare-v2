# T7 Cold-Smoke Tasks — v1 UI Catalog Phase 3 (#184)

> **SEALED ENVELOPE.** This file commits to the repo at the START of Phase 3 authoring (PR 0 of #184). Do NOT read or edit this file during authoring sessions. The tasks remain sealed until the cold-smoke session is convened (PR 6 of #184). Authoring must not train to these specific tasks.

## Why sealed-envelope

Per QA + UX committee review (#184): a cold-smoke test that the author has read in advance is a self-test, not an outside-eyes test. Author training to the specific tasks invalidates the signal. Locking the tasks at PR 0 commit time, before any caption is authored, prevents that.

## Test protocol

- **Two testers**, neither involved in authoring.
- **No v1 access** — testers read the catalog only (`docs/legacy/v1-ui-catalog/`).
- **Per task:** tester reads the prompt, scans the catalog, reports the canonical_id of the page they believe matches, and articulates the page's purpose in one sentence.
- **Pass criterion:** 60 seconds per task; correct canonical_id named; one-sentence purpose articulated. **6/6 across both testers must pass.**
- **Recorder** (separate from tester): runs a stopwatch per task, captures the canonical_id named + the one-sentence purpose, marks pass/fail.

## Locked tasks

The three tasks below are committed to this file at PR 0 commit time. They cover ≥2 personas (one desktop-lead, one mobile-lead) and include one task that requires reading both `**CTAs visible:**` AND `**Interaction notes:**` to identify (depth task, not just title-match).

### Task 1 — Desktop-lead (Agency Admin), title-match difficulty

> **Prompt:** "Find the page where an agency admin reviews and approves caregiver timesheets in bulk."

- Expected canonical_id pattern: an Agency Admin route under `agency-admin/` whose caption mentions a timesheet approval CTA.
- Difficulty: title-match (the route title or canonical_id likely contains "timesheet" or "approve").
- Recorder confirms: one-sentence purpose articulated (e.g., "shows pending timesheets and lets the admin approve or reject each one").

### Task 2 — Mobile-lead (Caregiver), title-match difficulty

> **Prompt:** "Find the page a caregiver uses to clock in at the start of a shift."

- Expected canonical_id pattern: a Caregiver route under `caregiver/` whose caption mentions clock-in.
- Difficulty: title-match.
- Recorder confirms: one-sentence purpose articulated.

### Task 3 — Depth difficulty (reads BOTH CTAs and Interaction notes)

> **Prompt:** "Find the page that contains a button that triggers a destructive action (POST/DELETE that mutates billing data) — name it, name the destructive action, and confirm the crawler skipped that interaction."

- Expected: any caption whose interaction notes contain `⚠ destructive:` AND whose CTAs visible list includes the matching button label, in a billing/financial context (could be `agency-admin/`, possibly `family-member/`).
- Difficulty: depth — requires reading interaction notes, not just route names. Title alone won't reveal it.
- Recorder confirms: tester names the destructive button, names the affected resource path, and confirms the `⚠ destructive: ... Skipped by crawler.` annotation is present.

## Recording the results

After the session, replace the table below with actual results (do not delete the locked tasks above):

| Tester | Task 1 (canonical_id) | T1 time | T1 purpose | T1 pass? | Task 2 ... | T2 ... | T3 ... | Overall |
|--------|------------------------|---------|------------|----------|------------|--------|--------|---------|
| (name 1) | | | | ☐ | | | | ☐ |
| (name 2) | | | | ☐ | | | | ☐ |

**Overall pass:** 6/6 cells marked pass = T7 passes. Anything less = fail; root-cause the gap (catalog gap? caption ambiguity? task ambiguity?) and remediate before merging the final acceptance PR.

## Tamper-evidence

This file's content above the "Recording the results" section MUST NOT be edited between PR 0 commit and the cold-smoke session. Reviewer of the final acceptance PR (PR 6) confirms via `git log` that the locked tasks section was unchanged across the authoring window.
