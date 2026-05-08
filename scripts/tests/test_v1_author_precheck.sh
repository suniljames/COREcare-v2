#!/usr/bin/env bash
# Tests for scripts/v1-author-precheck.sh
# Run from repo root: bash scripts/tests/test_v1_author_precheck.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/v1-author-precheck.sh"
TEST_DIR=$(mktemp -d -t v1-author-precheck-tests-XXXXXX)
trap 'rm -rf "$TEST_DIR"' EXIT

PASS=0
FAIL=0

assert_exit() {
  local description="$1"
  local expected_code="$2"
  shift 2
  local actual_output
  actual_output=$("$@" 2>&1)
  local actual_code=$?
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

write_manifest() {
  local path="$1"
  local sha="$2"
  cat > "$path" <<EOF
# RUN-MANIFEST — v1 UI catalog crawl

**Generated:** 2026-05-08T00:10:39.997Z
**v1 commit:** 9738412a6e41064203fc253d9dd2a5c6a9c2e231
**Fixture sha256:** $sha
**Operator:** suniljames
EOF
}

echo "== v1-author-precheck.sh tests =="

[[ -x "$SCRIPT" ]] || { echo "FAIL — script not executable at $SCRIPT"; exit 1; }

# --- Pass: fixture sha matches manifest ---
SHA1="03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92"
echo "fixture-content-1" > "$TEST_DIR/fixture1.json"
ACTUAL_SHA=$(shasum -a 256 "$TEST_DIR/fixture1.json" | awk '{print $1}')
write_manifest "$TEST_DIR/manifest_match.md" "$ACTUAL_SHA"
assert_exit "matching sha passes" 0 \
  "$SCRIPT" \
  --fixture "$TEST_DIR/fixture1.json" \
  --manifest "$TEST_DIR/manifest_match.md"

# --- Fail: fixture sha mismatch ---
write_manifest "$TEST_DIR/manifest_mismatch.md" "$SHA1"
assert_exit "mismatched sha fails" 1 \
  "$SCRIPT" \
  --fixture "$TEST_DIR/fixture1.json" \
  --manifest "$TEST_DIR/manifest_mismatch.md"
assert_output_contains "mismatch reports manifest sha" "$SHA1" \
  "$SCRIPT" \
  --fixture "$TEST_DIR/fixture1.json" \
  --manifest "$TEST_DIR/manifest_mismatch.md"
assert_output_contains "mismatch reports actual sha" "$ACTUAL_SHA" \
  "$SCRIPT" \
  --fixture "$TEST_DIR/fixture1.json" \
  --manifest "$TEST_DIR/manifest_mismatch.md"
assert_output_contains "mismatch tells operator to STOP" "STOP" \
  "$SCRIPT" \
  --fixture "$TEST_DIR/fixture1.json" \
  --manifest "$TEST_DIR/manifest_mismatch.md"

# --- Fail: fixture file missing ---
assert_exit "missing fixture file bails (exit 2)" 2 \
  "$SCRIPT" \
  --fixture "$TEST_DIR/does-not-exist.json" \
  --manifest "$TEST_DIR/manifest_match.md"
assert_output_contains "missing fixture mentions path" "does-not-exist.json" \
  "$SCRIPT" \
  --fixture "$TEST_DIR/does-not-exist.json" \
  --manifest "$TEST_DIR/manifest_match.md"

# --- Fail: manifest file missing ---
assert_exit "missing manifest file bails (exit 2)" 2 \
  "$SCRIPT" \
  --fixture "$TEST_DIR/fixture1.json" \
  --manifest "$TEST_DIR/does-not-exist.md"

# --- Fail: manifest has no Fixture sha256 line ---
cat > "$TEST_DIR/manifest_no_sha.md" <<'EOF'
# RUN-MANIFEST
**Generated:** 2026-05-08
**v1 commit:** 9738412a
EOF
assert_exit "manifest without Fixture sha256 line bails" 2 \
  "$SCRIPT" \
  --fixture "$TEST_DIR/fixture1.json" \
  --manifest "$TEST_DIR/manifest_no_sha.md"
assert_output_contains "no-sha-in-manifest reports it" "Fixture sha256" \
  "$SCRIPT" \
  --fixture "$TEST_DIR/fixture1.json" \
  --manifest "$TEST_DIR/manifest_no_sha.md"

# --- Bad invocation ---
assert_exit "no args bails (exit 2)" 2 "$SCRIPT"
assert_exit "unknown flag bails (exit 2)" 2 "$SCRIPT" --bogus
assert_exit "missing arg value bails (exit 2)" 2 "$SCRIPT" --fixture

# --- Defaults ---
# When run without flags, defaults to expected production paths. We can't fully
# test the default path (it'd require ~/Code/COREcare-access/...), but the
# script must at least not error on flag parsing.
# Instead: confirm --help works.
assert_exit "--help exits 0" 0 "$SCRIPT" --help

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
