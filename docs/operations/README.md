# Operations

Runbooks for operating the running COREcare system — recovery procedures, on-call references, things you grab when something has gone wrong or a user needs help.

## Runbooks

| Runbook | When to use |
|---|---|
| [`client-persona-recovery.md`](client-persona-recovery.md) | A Client-as-user has lost access to their account (forgot password, lost email access, lost the email used at invite redemption). |

## Conventions

- Runbooks should be **task-shaped**, not topic-shaped: the title says what you're trying to *do*, not what the topic is.
- Lead with the standard / happy-path procedure. Edge cases come after.
- If a step requires elevated access (Clerk dashboard, DB shell, Super-Admin route), say so explicitly.

## Cross-references

- Auth questions: [`../adr/003-clerk-authentication.md`](../adr/003-clerk-authentication.md).
- Audit-trail expectations for cross-tenant operations: [ADR-007](../adr/007-event-sourced-audit-logging.md).
- LFS bandwidth posture (a separate operational concern, infra rather than user recovery): see CI workflow `lfs-bandwidth-day30-reminder.yml` and the `make check` LFS-posture guard.
