# Safety & Guardrails (COREcare-Specific)

For universal safety rules, see the [engineering directives](https://github.com/suniljames/directives/blob/main/framework/safety.md). For HIPAA-specific rules, see the [healthcare overlay](https://github.com/suniljames/directives/blob/main/overlays/healthcare/safety-addendum.md).

This file covers COREcare project-specific safety only.

## Docker Safety

- Never `docker system prune -a` without confirmation
- Always use `docker compose down` (not `docker compose down -v`) to preserve data
- Back up database volumes before destructive operations

## Multi-Tenancy Safety

- All queries must go through RLS-enforced sessions
- Never bypass RLS except for super-admin operations
- Test tenant isolation in every data-access service test
- Log all cross-tenant access attempts

## Safe Branch-Switching

1. Prefer `git worktree` over stash
2. If stashing, use `git stash push -m "descriptive message"`
3. Never drop a stash after failed pop
4. Verify restoration after switching back

## Branch-cut invariants

Every feature branch must be cut from a freshly-fetched `origin/<default-branch>` SHA — never from stale local `main` (see issues #146 / #176 / #191).

- Bash invariant lives in [`.claude/commands/implement.md`](../../.claude/commands/implement.md) (Branch base block) and the mirror copy in [`.claude/commands/review.md`](../../.claude/commands/review.md), with regression coverage in [`scripts/tests/test_implement_branch_cut.sh`](../../scripts/tests/test_implement_branch_cut.sh).
- Harness contract pin: `worktree.baseRef: "fresh"` in [`.claude/settings.json`](../../.claude/settings.json), with regression coverage in [`scripts/tests/test_worktree_base_setting.sh`](../../scripts/tests/test_worktree_base_setting.sh).
