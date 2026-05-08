# Operations runbooks

Operator-facing procedures for time-bounded watches, escalations, and routine ops tasks. Each runbook in this directory is self-contained: open it, follow the steps, post the templated comment.

## Active runbooks

| Runbook | Window | Issue |
|---|---|---|
| [Git LFS bandwidth watch](lfs-bandwidth-watch.md) | 2026-05-07 → 2026-06-07 | [#185](https://github.com/suniljames/COREcare-v2/issues/185) |

## Conventions

- Runbooks use second-person imperative voice. Operators reading at 11pm need clear action verbs, not narrative.
- Every runbook names its closure date and its archive policy. Watches that have closed are moved to `archive/` rather than deleted, so the audit trail stays in git.
- Templates inside runbooks are copy-paste-ready. Where today's date or other dynamic fields apply, prefer a shell helper that prints the pre-filled template (see `scripts/lfs-bandwidth-snapshot.sh`).
