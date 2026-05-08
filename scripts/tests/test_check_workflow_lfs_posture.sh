#!/usr/bin/env bash
# Tests for scripts/check-workflow-lfs-posture.sh.
#
# Run from repo root: bash scripts/tests/test_check_workflow_lfs_posture.sh
#
# Five fixture cases enumerated in the issue #185 Test Specification:
#   01 — lfs: true with same-line `# rationale: …` comment   → PASS
#   02 — lfs: true without rationale comment                 → FAIL
#   03 — lfs: false                                          → PASS
#   04 — no lfs key set                                      → PASS
#   05 — lfs: key under a non-actions/checkout step          → PASS

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GUARD="$REPO_ROOT/scripts/check-workflow-lfs-posture.sh"
FIXTURES="$SCRIPT_DIR/fixtures/lfs-posture"

PASS=0
FAIL=0

assert_exit() {
  local description="$1"
  local expected_code="$2"
  shift 2
  local actual_output
  actual_output=$("$@" 2>&1 || true)
  local actual_code
  "$@" >/dev/null 2>&1
  actual_code=$?
  if [[ "$actual_code" == "$expected_code" ]]; then
    echo "  PASS — $description (exit $actual_code)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description (expected exit $expected_code, got $actual_code)"
    echo "    output: $actual_output"
    FAIL=$((FAIL + 1))
  fi
}

assert_output_contains() {
  local description="$1"
  local needle="$2"
  shift 2
  local actual_output
  actual_output=$("$@" 2>&1 || true)
  if echo "$actual_output" | grep -qF "$needle"; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description (output did not contain: $needle)"
    echo "    actual: $actual_output"
    FAIL=$((FAIL + 1))
  fi
}

echo "== check-workflow-lfs-posture.sh tests =="

[[ -x "$GUARD" ]] || { echo "FAIL — guard script not executable at $GUARD"; exit 1; }
[[ -d "$FIXTURES" ]] || { echo "FAIL — fixtures dir missing at $FIXTURES"; exit 1; }

# Single-fixture cases.
assert_exit "01 lfs:true + rationale → exit 0" 0 \
  "$GUARD" "$FIXTURES/01-rationale-pass.yml"

assert_exit "02 lfs:true + no rationale → exit 1" 1 \
  "$GUARD" "$FIXTURES/02-no-rationale-fail.yml"

assert_output_contains "02 failure message identifies file:line" \
  "02-no-rationale-fail.yml" \
  "$GUARD" "$FIXTURES/02-no-rationale-fail.yml"

assert_output_contains "02 failure message names the rationale requirement" \
  "rationale" \
  "$GUARD" "$FIXTURES/02-no-rationale-fail.yml"

assert_exit "03 lfs:false explicit → exit 0" 0 \
  "$GUARD" "$FIXTURES/03-explicit-false-pass.yml"

assert_exit "04 no lfs key → exit 0" 0 \
  "$GUARD" "$FIXTURES/04-no-key-pass.yml"

assert_exit "05 lfs:true under non-checkout action → exit 0 (ignored)" 0 \
  "$GUARD" "$FIXTURES/05-non-checkout-ignored-pass.yml"

# Multi-file cases.
assert_exit "multi-file all-pass → exit 0" 0 \
  "$GUARD" \
  "$FIXTURES/01-rationale-pass.yml" \
  "$FIXTURES/03-explicit-false-pass.yml" \
  "$FIXTURES/04-no-key-pass.yml" \
  "$FIXTURES/05-non-checkout-ignored-pass.yml"

assert_exit "multi-file with one bad → exit 1" 1 \
  "$GUARD" \
  "$FIXTURES/01-rationale-pass.yml" \
  "$FIXTURES/02-no-rationale-fail.yml"

# Default scan (no args) runs against the repo's own .github/workflows/.
# All current workflows must already be compliant.
assert_exit "default scan of repo workflows → exit 0" 0 \
  bash -c "cd '$REPO_ROOT' && '$GUARD'"

# Usage error path.
assert_exit "missing-file argument → exit 2" 2 \
  "$GUARD" "$FIXTURES/this-file-does-not-exist.yml"

echo ""
echo "== Summary: $PASS passed, $FAIL failed =="
[[ "$FAIL" -eq 0 ]]
