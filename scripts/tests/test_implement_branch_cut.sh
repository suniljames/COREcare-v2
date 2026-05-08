#!/usr/bin/env bash
# Tests for the issue #176 invariant: /implement and /review must cut feature
# branches from a freshly-fetched origin/main, not stale local main.
#
# Two test layers:
#   1. Behavioral — exercise the bash invariant against a temp git repo with a
#      fake origin in four scenarios (current / behind / ahead / offline).
#   2. Sync — grep the .claude/commands/{implement,review}.md files for the
#      key git commands so we catch silent drift between the two files.
#
# Run from repo root: bash scripts/tests/test_implement_branch_cut.sh

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
IMPLEMENT_MD="$REPO_ROOT/.claude/commands/implement.md"
REVIEW_MD="$REPO_ROOT/.claude/commands/review.md"

PASS=0
FAIL=0

pass() { echo "  PASS — $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL — $1"; FAIL=$((FAIL + 1)); }

# ---------------------------------------------------------------------------
# The function under test mirrors the bash block embedded in implement.md /
# review.md. The sync tests below assert the markdown files contain the same
# key commands so this duplication can't drift silently.
# ---------------------------------------------------------------------------
cut_feature_branch() {
  local branch_name="$1"
  git fetch origin main || return 1
  local base_sha
  base_sha=$(git rev-parse origin/main 2>/dev/null) || return 1
  if [[ -z "$base_sha" || ! "$base_sha" =~ ^[0-9a-f]{40}$ ]]; then
    echo "ERROR: could not resolve origin/main to a SHA. Aborting." >&2
    return 1
  fi
  echo "Cutting from origin/main @ ${base_sha:0:8}"
  local local_behind
  local_behind=$(git rev-list --count "main..origin/main" 2>/dev/null || echo 0)
  if [[ "$local_behind" -gt 0 ]]; then
    echo "Local main was $local_behind commits behind origin/main; using origin/main as the base."
  fi
  git checkout -b "$branch_name" "$base_sha"
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

# ---------------------------------------------------------------------------
# Behavioral tests
# ---------------------------------------------------------------------------

test_branch_parent_matches_origin_main() {
  make_sandbox
  cd "$LOCAL"
  if cut_feature_branch "feat/test1" >/dev/null 2>&1; then
    local parent expected
    parent=$(git rev-parse HEAD)
    expected=$(git rev-parse origin/main)
    if [[ "$parent" == "$expected" ]]; then
      pass "branch_parent_matches_origin_main (current local main)"
    else
      fail "branch_parent_matches_origin_main: parent=$parent expected=$expected"
    fi
  else
    fail "branch_parent_matches_origin_main: function failed"
  fi
  cd "$REPO_ROOT"
  rm -rf "$SANDBOX"
}

test_does_not_use_stale_local_main() {
  make_sandbox
  cd "$LOCAL"
  local stale_sha
  stale_sha=$(git rev-parse main)
  cd "$REPO_ROOT"
  push_commits_to_remote_main "$REMOTE" 3
  cd "$LOCAL"
  # Local main is now 3 commits behind origin/main (without fetching first).
  if cut_feature_branch "feat/test2" >/dev/null 2>&1; then
    local parent origin_now
    parent=$(git rev-parse HEAD)
    origin_now=$(git rev-parse origin/main)
    if [[ "$parent" == "$origin_now" && "$parent" != "$stale_sha" ]]; then
      pass "does_not_use_stale_local_main"
    else
      fail "does_not_use_stale_local_main: parent=$parent origin_now=$origin_now stale=$stale_sha"
    fi
  else
    fail "does_not_use_stale_local_main: function failed"
  fi
  cd "$REPO_ROOT"
  rm -rf "$SANDBOX"
}

test_does_not_use_local_only_commits() {
  make_sandbox
  cd "$LOCAL"
  git commit --allow-empty -m "local-only" --quiet
  local local_only_sha
  local_only_sha=$(git rev-parse main)
  if cut_feature_branch "feat/test3" >/dev/null 2>&1; then
    local parent expected
    parent=$(git rev-parse HEAD)
    expected=$(git rev-parse origin/main)
    if [[ "$parent" == "$expected" && "$parent" != "$local_only_sha" ]]; then
      pass "does_not_use_local_only_commits"
    else
      fail "does_not_use_local_only_commits: parent=$parent expected=$expected local_only=$local_only_sha"
    fi
  else
    fail "does_not_use_local_only_commits: function failed"
  fi
  cd "$REPO_ROOT"
  rm -rf "$SANDBOX"
}

test_aborts_when_fetch_fails() {
  make_sandbox
  cd "$LOCAL"
  git remote set-url origin "$SANDBOX/nonexistent.git"
  if cut_feature_branch "feat/test4" >/dev/null 2>&1; then
    fail "aborts_when_fetch_fails: function should have returned non-zero"
  else
    if [[ -z "$(git branch --list 'feat/test4')" ]]; then
      pass "aborts_when_fetch_fails (no branch created)"
    else
      fail "aborts_when_fetch_fails: branch was created despite fetch failure"
    fi
  fi
  cd "$REPO_ROOT"
  rm -rf "$SANDBOX"
}

# ---------------------------------------------------------------------------
# Sync tests: assert markdown files contain the key invariant commands.
# These catch silent drift between implement.md and review.md.
# ---------------------------------------------------------------------------

assert_markdown_contains_invariant() {
  local label="$1"
  local file="$2"
  local missing=0
  local needles=(
    "git fetch origin main"
    "git rev-parse origin/main"
    "git checkout -b"
    "see issue #176"
  )
  for needle in "${needles[@]}"; do
    if ! grep -qF "$needle" "$file"; then
      fail "$label missing literal: $needle"
      missing=1
    fi
  done
  [[ "$missing" -eq 0 ]] && pass "$label contains the invariant"
}

test_implement_md_contains_invariant() {
  assert_markdown_contains_invariant "implement.md" "$IMPLEMENT_MD"
}

test_review_md_contains_invariant() {
  assert_markdown_contains_invariant "review.md" "$REVIEW_MD"
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

echo "Running issue #176 branch-cut invariant tests..."
test_branch_parent_matches_origin_main
test_does_not_use_stale_local_main
test_does_not_use_local_only_commits
test_aborts_when_fetch_fails
test_implement_md_contains_invariant
test_review_md_contains_invariant

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -gt 0 ]] && exit 1
exit 0
