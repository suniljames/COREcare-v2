#!/usr/bin/env bash
# Tests for scripts/lfs-bandwidth-snapshot.sh.
#
# Run from repo root: bash scripts/tests/test_lfs_bandwidth_snapshot.sh
#
# Two assertions per the #185 Test Specification:
#   1. Output golden test — stdout matches fixtures/lfs-snapshot-expected.txt
#      after both sides are normalized via:
#        sed -E 's/[0-9]{4}-[0-9]{2}-[0-9]{2}/YYYY-MM-DD/g'
#      No other normalization is permitted.
#   2. No-network assertion — `bash -x …` trace plus stdout must not contain
#      any of: curl, wget, gh api, nc<space>, ssh<space>.

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SNAPSHOT="$REPO_ROOT/scripts/lfs-bandwidth-snapshot.sh"
EXPECTED="$SCRIPT_DIR/fixtures/lfs-snapshot-expected.txt"

PASS=0
FAIL=0

echo "== lfs-bandwidth-snapshot.sh tests =="

[[ -x "$SNAPSHOT" ]] || { echo "FAIL — snapshot script not executable at $SNAPSHOT"; exit 1; }
[[ -f "$EXPECTED" ]] || { echo "FAIL — golden file missing at $EXPECTED"; exit 1; }

# --- Golden output test ---

normalize() {
  sed -E 's/[0-9]{4}-[0-9]{2}-[0-9]{2}/YYYY-MM-DD/g'
}

actual_normalized=$("$SNAPSHOT" | normalize)
expected_normalized=$(normalize < "$EXPECTED")

if [[ "$actual_normalized" == "$expected_normalized" ]]; then
  echo "  PASS — stdout matches golden fixture (after ISO-date normalization)"
  PASS=$((PASS + 1))
else
  echo "  FAIL — stdout differs from golden fixture"
  echo "  --- diff (expected | actual) ---"
  diff <(echo "$expected_normalized") <(echo "$actual_normalized") || true
  echo "  --- end diff ---"
  FAIL=$((FAIL + 1))
fi

# --- No-network assertion ---
# Run with `bash -x` and merge stderr into stdout. The combined stream must
# not contain any of the network primitives we explicitly forbid.

trace=$(bash -x "$SNAPSHOT" 2>&1 || true)
forbidden_pattern='(curl|wget|gh api|nc |ssh )'

if echo "$trace" | grep -qE "$forbidden_pattern"; then
  echo "  FAIL — bash -x trace or stdout contains a forbidden network primitive"
  echo "  --- offending lines ---"
  echo "$trace" | grep -nE "$forbidden_pattern" || true
  echo "  --- end offending lines ---"
  FAIL=$((FAIL + 1))
else
  echo "  PASS — no curl/wget/gh-api/nc/ssh in trace or stdout"
  PASS=$((PASS + 1))
fi

echo ""
echo "== Summary: $PASS passed, $FAIL failed =="
[[ "$FAIL" -eq 0 ]]
