# Access & Environment Setup

How to get a working development environment for COREcare v2.

## GitHub Identity

All developers (human and AI) operate under a single GitHub identity:

- **GitHub user:** `suniljames`
- **Git config:** `suniljames <suniljames@users.noreply.github.com>`
- **Before any `gh` CLI command:** `gh auth switch --user suniljames`

## GitHub Access Methods

### SSH

Key pair at `~/.ssh/id_ed25519`. Must be registered with GitHub:

```bash
# Start agent and add key
eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519

# Register with GitHub (one-time)
gh ssh-key add ~/.ssh/id_ed25519.pub --title "Mac Mini"

# Verify
ssh -T git@github.com
```

### GitHub CLI (`gh`)

Authenticated via `gh auth login`. Required scopes: `repo`, `read:org`, `workflow`, `admin:public_key`.

```bash
# Check status
gh auth status

# Refresh with broader scopes if needed
gh auth refresh -h github.com -s repo,read:org,admin:org,workflow,admin:public_key
```

Git operations use HTTPS protocol via the `gh` credential helper.

### GitHub MCP (Claude Code)

Configured at `~/.claude/.mcp.json`:

```json
{
  "github": {
    "type": "http",
    "url": "https://api.githubcopilot.com/mcp/",
    "headers": {
      "Authorization": "Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}"
    }
  }
}
```

Requires the `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable (set in `~/.zshrc`).

## Environment Variables

| Variable | Purpose | Where set |
|----------|---------|-----------|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | GitHub MCP auth for Claude Code | `~/.zshrc` |

## Docker Compose (Local Dev)

```bash
# Start all services
docker compose up --build -d

# Verify
curl http://localhost:8000/healthz

# Seed test data
make api-seed
```

Services: API (8000), Web (3000), PostgreSQL, Redis.

Tailscale provides network access from other devices.

## Useful Commands

```bash
make check        # Lint + typecheck + test + build (must pass before PRs)
make test         # All tests
make api-test     # API tests only
make web-test     # Web tests only
make test-e2e     # E2E tests (requires Docker stack)
```
