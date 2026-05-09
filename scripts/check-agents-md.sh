#!/usr/bin/env bash
# Mechanical checks for AGENTS.md (per issue #288 acceptance criteria).
#
# Asserts:
#   1. AGENTS.md exists at repo root.
#   2. Line count <= 150 (reading-budget guard for AI agents).
#   3. Every repo-relative link in AGENTS.md resolves to an existing file or
#      directory. External URLs (http/https/mailto) are not validated here —
#      they go stale and would flake the hook.
#   4. README.md, CLAUDE.md, and GEMINI.md each mention AGENTS.md (the
#      cross-mention discoverability invariant from the design committee).
#
# Run manually: bash scripts/check-agents-md.sh
# Pre-commit:  fires on changes to AGENTS.md, README.md, CLAUDE.md, GEMINI.md.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

FAIL=0
fail() { echo "FAIL: $*" >&2; FAIL=1; }

# ── 1. AGENTS.md exists ──────────────────────────────────────────────────────
if [[ ! -f AGENTS.md ]]; then
  fail "AGENTS.md not found at repo root"
  exit 1
fi

# ── 2. Line-count budget ─────────────────────────────────────────────────────
MAX_LINES=150
LINES=$(wc -l < AGENTS.md | tr -d ' ')
if (( LINES > MAX_LINES )); then
  fail "AGENTS.md is $LINES lines (max $MAX_LINES). Trim before merging."
fi

# ── 3. Internal-link check ───────────────────────────────────────────────────
# Match markdown links: [text](target). Capture the target. Skip external,
# mailto, anchor-only, and image-style links. Check that the file or dir
# referenced exists relative to the repo root.
while IFS= read -r target; do
  # Strip anchor fragment (e.g. "docs/file.md#section" -> "docs/file.md").
  path="${target%%#*}"
  [[ -z "$path" ]] && continue                  # pure anchors like (#foo)
  [[ "$path" =~ ^https?:// ]] && continue       # external URLs
  [[ "$path" =~ ^mailto: ]] && continue
  [[ "$path" =~ ^// ]] && continue              # protocol-relative (rare)
  if [[ ! -e "$path" && ! -d "$path" ]]; then
    fail "AGENTS.md links to '$path' which does not exist"
  fi
done < <(grep -oE '\]\([^)]+\)' AGENTS.md | sed -E 's/^\]\(//; s/\)$//')

# ── 4. Cross-mention discoverability ────────────────────────────────────────
for f in README.md CLAUDE.md GEMINI.md; do
  if [[ ! -f "$f" ]]; then
    fail "$f not found at repo root (cross-mention check skipped)"
    continue
  fi
  if ! grep -q 'AGENTS\.md' "$f"; then
    fail "$f does not mention AGENTS.md (discoverability invariant)"
  fi
done

if (( FAIL == 0 )); then
  echo "AGENTS.md: $LINES/$MAX_LINES lines, links resolve, cross-mentions present."
fi
exit "$FAIL"
