# Safety & Guardrails

## Behavioral Rules

- **Never delete** repositories, services, or databases
- **Never** `rm -rf` on broad paths (`/`, `~`, `.`, `/Users`, etc.)
- **Never** `git push --force` (use `--force-with-lease` if necessary)
- **Never** `git reset --hard`, `git clean -f`, `git branch -D main`
- **Never** `DROP DATABASE`, `DROP TABLE`, `TRUNCATE TABLE`
- **Never** pipe remote content to shell (`curl | bash`)
- **Never** `chmod 777`, `pkill -9`, `killall -9`
- **Never** expose PHI in logs, error messages, or API responses
- **Never** commit secrets (.env files, API keys)
- **Stop and ask** if a destructive action seems genuinely necessary

## Safe Branch-Switching

1. Prefer `git worktree` over stash
2. If stashing, use `git stash push -m "descriptive message"`
3. Never drop a stash after failed pop
4. Verify restoration after switching back

## Docker Safety

- Never `docker system prune -a` without confirmation
- Always use `docker compose down` (not `docker compose down -v`) to preserve data
- Back up database volumes before destructive operations

## Multi-Tenancy Safety

- All queries must go through RLS-enforced sessions
- Never bypass RLS except for super-admin operations
- Test tenant isolation in every data-access service test
- Log all cross-tenant access attempts
