#!/usr/bin/env bash
# scripts/setup.sh — bootstrap a fresh checkout for development.
#
# Verifies prerequisites, seeds .env files from examples (without clobbering
# existing files), brings up the Docker stack, waits for health, and seeds
# test data. Idempotent — safe to re-run.
#
# Usage: scripts/setup.sh
#
# Hard requirement: Docker (used for the local stack).
# Soft requirements (warned, not blocked): Node 20 / Python 3.12 / pnpm / uv —
# only needed for non-Docker workflows.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# --- output helpers ---------------------------------------------------------
if [ -t 1 ]; then
  R='\033[31m'; G='\033[32m'; Y='\033[33m'; B='\033[1m'; X='\033[0m'
else
  R=''; G=''; Y=''; B=''; X=''
fi
info()   { printf '%b%s%b\n' "$B" "$*" "$X"; }
ok()     { printf '  %b✓%b %s\n' "$G" "$X" "$*"; }
warn()   { printf '  %b⚠%b %s\n' "$Y" "$X" "$*"; warnings=$((warnings+1)); }
fail()   { printf '  %b✗%b %s\n' "$R" "$X" "$*"; exit 1; }

warnings=0

# --- 1. Prerequisites -------------------------------------------------------
info "1/4  Checking prerequisites..."

if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    ok "Docker is installed and running"
  else
    fail "Docker is installed but not running. Start Docker Desktop and re-run."
  fi
else
  fail "Docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop"
fi

if command -v git >/dev/null 2>&1; then
  ok "git"
else
  fail "git not found"
fi

if command -v git-lfs >/dev/null 2>&1; then
  ok "git-lfs"
else
  warn "git-lfs not installed — v1 UI catalog binaries won't fetch. Install with: brew install git-lfs"
fi

# Soft tool checks (only needed for non-Docker workflows).
if command -v node >/dev/null 2>&1; then
  ok "Node $(node --version)"
else
  warn "node not found — only required for non-Docker workflows"
fi
if command -v python3 >/dev/null 2>&1; then
  ok "Python $(python3 --version 2>&1 | awk '{print $2}')"
else
  warn "python3 not found — only required for non-Docker workflows"
fi
if command -v pnpm >/dev/null 2>&1; then
  ok "pnpm $(pnpm --version)"
else
  warn "pnpm not found — install with: brew install pnpm  (only required for non-Docker workflows)"
fi
if command -v uv >/dev/null 2>&1; then
  ok "uv $(uv --version 2>&1 | awk '{print $2}')"
else
  warn "uv not found — install with: brew install uv  (only required for non-Docker workflows)"
fi

# --- 2. Git LFS -------------------------------------------------------------
info "2/4  Initializing git LFS..."
if command -v git-lfs >/dev/null 2>&1; then
  git lfs install --local >/dev/null
  ok "LFS hooks installed for this clone"
else
  warn "Skipping LFS init (git-lfs not installed)"
fi

# --- 3. Seed .env files -----------------------------------------------------
info "3/4  Seeding .env files (preserving any that already exist)..."

seed_env() {
  local target="$1" example="$2"
  if [ ! -f "$example" ]; then
    warn "Example file $example missing — skipping"
    return
  fi
  if [ -f "$target" ]; then
    printf '  %b↺%b %s already exists — leaving untouched\n' "$Y" "$X" "$target"
  else
    cp "$example" "$target"
    ok "Created $target from $example"
  fi
}

seed_env api/.env       api/.env.example
seed_env web/.env.local web/.env.local.example

# --- 4. Docker stack --------------------------------------------------------
info "4/4  Starting Docker stack (this may take a few minutes on first run)..."
docker compose up -d
ok "Containers started"

info "     Waiting for API healthz (timeout 90s)..."
deadline=$((SECONDS + 90))
while ! curl -sf http://localhost:8000/healthz >/dev/null 2>&1; do
  if (( SECONDS > deadline )); then
    fail "API never came up. Inspect logs with: docker compose logs api"
  fi
  sleep 2
done
ok "API healthy at http://localhost:8000"

# --- Done -------------------------------------------------------------------
echo
printf '%b✅ COREcare v2 stack is up.%b\n' "$G$B" "$X"
echo
info "Next steps"
cat <<'EOF'
  • Open http://localhost:3000 to see the web app.
  • API docs at http://localhost:8000/docs.
  • Run quality gates before committing: make check
  • Run tests:                            make test
  • Stop containers:                      make down

Database schema and seed data are NOT applied automatically — the schema
init / migration sequence has a known issue (no migration creates the
initial tables; SQLModel.metadata.create_all is only used in tests). Once
that's fixed, the next steps will be:

  make api-migrate    # apply migrations
  make api-seed       # seed test accounts

Local auth: by default the API uses a dev fallback — requests sent without
an Authorization header receive a mock super_admin user (api/app/auth.py).
That works against an empty schema for endpoints that don't query a table.

See CONTRIBUTING.md for the full contributor workflow.
EOF

if (( warnings > 0 )); then
  echo
  printf '%b%d warning(s) above — setup completed with non-fatal issues.%b\n' "$Y" "$warnings" "$X"
fi
