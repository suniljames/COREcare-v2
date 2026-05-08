#!/usr/bin/env bash
# Tests for scripts/lib/lfs-report-matcher.sh.
#
# Run from repo root: bash scripts/tests/test_lfs_report_matcher.sh
#
# Five cases per the issue #233 Test Specification:
#   TP1 — anchored report (operator's snapshot-helper output)        → match
#   TN1 — bot reminder ("Weekly check-in #2…")                       → no match
#   TN2 — quoted reference ("the **30-day…** template should…")      → no match
#   TN3 — single-word comment ("lgtm")                               → no match
#   TN4 — fenced code block paste of the template                    → no match

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LIB="$REPO_ROOT/scripts/lib/lfs-report-matcher.sh"
FIXTURES="$SCRIPT_DIR/fixtures/lfs-matcher"

PASS=0
FAIL=0

assert_match() {
  local fixture="$1"
  local body
  body=$(cat "$FIXTURES/$fixture")
  if "$LIB" "$body" >/dev/null 2>&1; then
    echo "  PASS — $fixture matches"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $fixture should match but did not"
    FAIL=$((FAIL + 1))
  fi
}

assert_nomatch() {
  local fixture="$1"
  local body
  body=$(cat "$FIXTURES/$fixture")
  if "$LIB" "$body" >/dev/null 2>&1; then
    echo "  FAIL — $fixture should not match but did"
    FAIL=$((FAIL + 1))
  else
    echo "  PASS — $fixture does not match"
    PASS=$((PASS + 1))
  fi
}

echo "== lfs-report-matcher.sh tests =="

[[ -x "$LIB" ]] || { echo "FAIL — lib not executable at $LIB"; exit 1; }
[[ -d "$FIXTURES" ]] || { echo "FAIL — fixtures dir missing at $FIXTURES"; exit 1; }

assert_match    "tp1-anchored-report.md"
assert_nomatch  "tn1-bot-reminder.md"
assert_nomatch  "tn2-quoted-reference.md"
assert_nomatch  "tn3-single-word.md"
assert_nomatch  "tn4-fenced-template.md"

echo ""
echo "== Summary: $PASS passed, $FAIL failed =="
[[ "$FAIL" -eq 0 ]]
