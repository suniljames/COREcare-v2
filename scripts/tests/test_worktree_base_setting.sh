#!/usr/bin/env bash
# Tests for the issue #191 invariant: project .claude/settings.json must pin
# worktree.baseRef = "fresh" so EnterWorktree (provided by the Claude Code
# harness, not this repo) cuts new worktrees from origin/<default-branch>
# instead of the local HEAD.
#
# Two test layers:
#   1. Settings-pin assertion — read .claude/settings.json and assert that
#      .worktree.baseRef == "fresh", plus literal-string grep so a renamed
#      key is also caught.
#   2. Contract-analog sandbox — exercise the documented `fresh` behavior
#      against a temp git repo with a fake origin in four scenarios
#      (current / behind / ahead / offline) using `git fetch origin main &&
#      git worktree add -b <name> <dir> origin/main` as the closest
#      mechanical analog of EnterWorktree's `worktree.baseRef: fresh` mode.
#
# This is a sibling test to test_implement_branch_cut.sh — the latter tests
# the bash invariant in implement.md/review.md (the project's defense-in-
# depth guard); this one tests the harness contract surface we depend on.
#
# Run from repo root: bash scripts/tests/test_worktree_base_setting.sh
#
# Negative-mutation smoke test (run before any PR that touches this file or
# .claude/settings.json):
#
#   cp .claude/settings.json /tmp/settings.bak
#   jq 'del(.worktree, ._comment_worktree)' .claude/settings.json > /tmp/m.json
#   cp /tmp/m.json .claude/settings.json
#   bash scripts/tests/test_worktree_base_setting.sh; echo "EXIT=$?"
#   # → expect EXIT=1 with two FAILs
#   cp /tmp/settings.bak .claude/settings.json
#   bash scripts/tests/test_worktree_base_setting.sh; echo "EXIT=$?"
#   # → expect EXIT=0 with all 8 PASS

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SETTINGS_JSON="$REPO_ROOT/.claude/settings.json"

PASS=0
FAIL=0

pass() { echo "  PASS — $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL — $1"; FAIL=$((FAIL + 1)); }

# Defensive cleanup: per-test bodies do `rm -rf "$SANDBOX"` on the success
# path, but if a test is interrupted (Ctrl-C, SIGTERM) the in-flight sandbox
# would otherwise survive until the OS reaper. This trap backstops that by
# removing whatever $SANDBOX currently points at on any script exit.
cleanup_sandbox() {
  if [[ -n "${SANDBOX:-}" && -d "$SANDBOX" ]]; then
    rm -rf "$SANDBOX" 2>/dev/null || true
  fi
}
trap cleanup_sandbox EXIT INT TERM

if ! command -v jq >/dev/null 2>&1; then
  echo "SKIP — jq not installed; tests require jq for JSON assertions"
  exit 0
fi

# ---------------------------------------------------------------------------
# Layer 1 — settings-pin assertions
# ---------------------------------------------------------------------------

test_settings_file_present() {
  if [[ -f "$SETTINGS_JSON" ]]; then
    pass "settings_file_present"
  else
    fail "settings_file_present: $SETTINGS_JSON not found"
  fi
}

test_settings_parses_as_json() {
  if jq empty "$SETTINGS_JSON" 2>/dev/null; then
    pass "settings_parses_as_json"
  else
    fail "settings_parses_as_json: jq could not parse $SETTINGS_JSON"
  fi
}

test_worktree_base_ref_pinned_to_fresh() {
  local actual
  actual=$(jq -r '.worktree.baseRef // "<missing>"' "$SETTINGS_JSON" 2>/dev/null)
  if [[ "$actual" == "fresh" ]]; then
    pass "worktree_base_ref_pinned_to_fresh"
  else
    fail "worktree_base_ref_pinned_to_fresh: got '$actual', expected 'fresh'. Set \"worktree\": {\"baseRef\": \"fresh\"} in .claude/settings.json — see issue #191."
  fi
}

test_worktree_base_ref_literal_string_present() {
  # Defensive: if a future schema rename moves the key elsewhere, jq might
  # still pass on a refactored shape. Grep for the literal string to catch
  # silent removals during settings cleanup.
  if grep -qF '"baseRef"' "$SETTINGS_JSON" && grep -qF '"fresh"' "$SETTINGS_JSON"; then
    pass "worktree_base_ref_literal_string_present"
  else
    fail "worktree_base_ref_literal_string_present: '\"baseRef\"' or '\"fresh\"' literal not found in $SETTINGS_JSON"
  fi
}

# ---------------------------------------------------------------------------
# Layer 2 — contract-analog sandbox
#
# These tests do NOT drive EnterWorktree itself (out of reach without the
# Claude Code runtime). They exercise the documented `worktree.baseRef:
# fresh` contract using its closest mechanical analog: a fetch followed by
# `git worktree add -b <name> <dir> origin/main`. If the documented contract
# ever silently changes shape, these tests fail and we know to revisit.
# ---------------------------------------------------------------------------

cut_worktree_from_origin_main() {
  # Mirror of EnterWorktree's documented `fresh` behavior: fetch, then
  # branch from origin/<default-branch>.
  local branch_name="$1"
  local worktree_dir="$2"
  git fetch origin main || return 1
  local base_sha
  base_sha=$(git rev-parse origin/main 2>/dev/null) || return 1
  if [[ -z "$base_sha" || ! "$base_sha" =~ ^[0-9a-f]{40}$ ]]; then
    echo "ERROR: could not resolve origin/main to a SHA. Aborting." >&2
    return 1
  fi
  git worktree add -b "$branch_name" "$worktree_dir" "$base_sha"
}

make_sandbox() {
  SANDBOX=$(mktemp -d)
  REMOTE="$SANDBOX/remote.git"
  LOCAL="$SANDBOX/local"
  git init --bare --quiet -b main "$REMOTE"

  local seed="$SANDBOX/seed"
  git init --quiet -b main "$seed"
  git -C "$seed" config user.email "test@example.com"
  git -C "$seed" config user.name "Test"
  git -C "$seed" commit --allow-empty -m "initial" --quiet
  git -C "$seed" remote add origin "$REMOTE"
  git -C "$seed" push --quiet origin main
  rm -rf "$seed"

  git clone --quiet "$REMOTE" "$LOCAL"
  git -C "$LOCAL" config user.email "test@example.com"
  git -C "$LOCAL" config user.name "Test"
}

push_commits_to_remote_main() {
  local remote="$1"
  local count="$2"
  local tmp
  tmp=$(mktemp -d)
  git clone --quiet "$remote" "$tmp/c"
  git -C "$tmp/c" config user.email "test@example.com"
  git -C "$tmp/c" config user.name "Test"
  for i in $(seq 1 "$count"); do
    git -C "$tmp/c" commit --allow-empty -m "remote commit $i" --quiet
  done
  git -C "$tmp/c" push --quiet origin main
  rm -rf "$tmp"
}

test_contract_current_local_main() {
  make_sandbox
  cd "$LOCAL"
  if cut_worktree_from_origin_main "feat/wt1" "$SANDBOX/wt1" >/dev/null 2>&1; then
    local parent expected
    parent=$(git -C "$SANDBOX/wt1" rev-parse HEAD)
    expected=$(git rev-parse origin/main)
    if [[ "$parent" == "$expected" ]]; then
      pass "contract_current_local_main"
    else
      fail "contract_current_local_main: parent=$parent expected=$expected"
    fi
  else
    fail "contract_current_local_main: cut function failed"
  fi
  cd "$REPO_ROOT"
  rm -rf "$SANDBOX"
}

test_contract_stale_local_main() {
  make_sandbox
  cd "$LOCAL"
  local stale_sha
  stale_sha=$(git rev-parse main)
  cd "$REPO_ROOT"
  push_commits_to_remote_main "$REMOTE" 3
  cd "$LOCAL"
  # Local main is now 3 commits behind origin/main (without fetching first).
  if cut_worktree_from_origin_main "feat/wt2" "$SANDBOX/wt2" >/dev/null 2>&1; then
    local parent origin_now
    parent=$(git -C "$SANDBOX/wt2" rev-parse HEAD)
    origin_now=$(git rev-parse origin/main)
    if [[ "$parent" == "$origin_now" && "$parent" != "$stale_sha" ]]; then
      pass "contract_stale_local_main"
    else
      fail "contract_stale_local_main: parent=$parent origin_now=$origin_now stale=$stale_sha"
    fi
  else
    fail "contract_stale_local_main: cut function failed"
  fi
  cd "$REPO_ROOT"
  rm -rf "$SANDBOX"
}

test_contract_ignores_local_only_commits() {
  make_sandbox
  cd "$LOCAL"
  git commit --allow-empty -m "local-only" --quiet
  local local_only_sha
  local_only_sha=$(git rev-parse main)
  if cut_worktree_from_origin_main "feat/wt3" "$SANDBOX/wt3" >/dev/null 2>&1; then
    local parent expected
    parent=$(git -C "$SANDBOX/wt3" rev-parse HEAD)
    expected=$(git rev-parse origin/main)
    if [[ "$parent" == "$expected" && "$parent" != "$local_only_sha" ]]; then
      pass "contract_ignores_local_only_commits"
    else
      fail "contract_ignores_local_only_commits: parent=$parent expected=$expected local_only=$local_only_sha"
    fi
  else
    fail "contract_ignores_local_only_commits: cut function failed"
  fi
  cd "$REPO_ROOT"
  rm -rf "$SANDBOX"
}

test_contract_aborts_when_fetch_fails() {
  make_sandbox
  cd "$LOCAL"
  git remote set-url origin "$SANDBOX/nonexistent.git"
  if cut_worktree_from_origin_main "feat/wt4" "$SANDBOX/wt4" >/dev/null 2>&1; then
    fail "contract_aborts_when_fetch_fails: cut function should have returned non-zero"
  else
    if [[ ! -d "$SANDBOX/wt4" ]] && [[ -z "$(git branch --list 'feat/wt4')" ]]; then
      pass "contract_aborts_when_fetch_fails (no branch or worktree created)"
    else
      fail "contract_aborts_when_fetch_fails: branch or worktree was created despite fetch failure"
    fi
  fi
  cd "$REPO_ROOT"
  rm -rf "$SANDBOX"
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

echo "Running issue #191 worktree.baseRef pin + contract-analog tests..."
test_settings_file_present
test_settings_parses_as_json
test_worktree_base_ref_pinned_to_fresh
test_worktree_base_ref_literal_string_present
test_contract_current_local_main
test_contract_stale_local_main
test_contract_ignores_local_only_commits
test_contract_aborts_when_fetch_fails

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -gt 0 ]] && exit 1
exit 0
