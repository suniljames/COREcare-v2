#!/usr/bin/env bash
# Tests for scripts/lib/lfs-watch-window.sh.
#
# Run from repo root: bash scripts/tests/test_lfs_watch_window.sh
#
# Six cases per the issue #233 Test Specification:
#   TP1 — 2026-05-07 (window start)              → within
#   TP2 — 2026-05-23 (mid-window Saturday)       → within
#   TP3 — 2026-06-07 (window end)                → within
#   TN1 — 2026-05-06 (one day before)            → outside
#   TN2 — 2026-06-08 (one day after)             → outside
#   TN3 — 2027-05-23 (next year, accidental fire)→ outside

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LIB="$REPO_ROOT/scripts/lib/lfs-watch-window.sh"

PASS=0
FAIL=0

assert_within() {
  local date="$1"
  if "$LIB" "$date" >/dev/null 2>&1; then
    echo "  PASS — $date is within window"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $date should be within window but was rejected"
    FAIL=$((FAIL + 1))
  fi
}

assert_outside() {
  local date="$1"
  if "$LIB" "$date" >/dev/null 2>&1; then
    echo "  FAIL — $date should be outside window but was accepted"
    FAIL=$((FAIL + 1))
  else
    echo "  PASS — $date is outside window"
    PASS=$((PASS + 1))
  fi
}

echo "== lfs-watch-window.sh tests =="

[[ -x "$LIB" ]] || { echo "FAIL — lib not executable at $LIB"; exit 1; }

assert_within  "2026-05-07"
assert_within  "2026-05-23"
assert_within  "2026-06-07"
assert_outside "2026-05-06"
assert_outside "2026-06-08"
assert_outside "2027-05-23"

echo ""
echo "== Summary: $PASS passed, $FAIL failed =="
[[ "$FAIL" -eq 0 ]]
