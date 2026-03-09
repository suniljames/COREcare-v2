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
