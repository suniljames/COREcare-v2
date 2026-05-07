#!/usr/bin/env bash
# Tests for scripts/check-v1-catalog-coverage.sh
# Run from repo root: bash scripts/tests/test_check_v1_catalog_coverage.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/check-v1-catalog-coverage.sh"
TEST_DIR=$(mktemp -d -t catalog-coverage-tests-XXXXXX)
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
  actual_output=$("$@" 2>&1)
  if echo "$actual_output" | grep -qF "$needle"; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description (output did not contain '$needle')"
    echo "    output: $actual_output"
    FAIL=$((FAIL + 1))
  fi
}

# --- Fixture builders ---

write_inventory_header() {
  local path="$1"
  cat > "$path" <<'EOF'
# v1 Pages Inventory

## Agency Admin

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
EOF
}

append_inventory_row() {
  # append_inventory_row <path> <route> <screenshot_ref>
  local path="$1"
  local route="$2"
  local screenshot_ref="$3"
  echo "| \`${route}\` | purpose | what | scaffolded |  | true | false | false | ${screenshot_ref} |  |" >> "$path"
}

write_caption() {
  # write_caption <catalog_dir> <persona-slug> <id> <canonical_id>
  local catalog_dir="$1"
  local persona_slug="$2"
  local id="$3"
  local canonical_id="$4"
  mkdir -p "$catalog_dir/$persona_slug"
  cat > "$catalog_dir/$persona_slug/${id}.md" <<EOF
---
canonical_id: ${canonical_id}
route: /admin/example/
persona: Agency Admin
viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-07
---
**CTAs visible:** Example.

**Interaction notes**:
- Example button → POSTs.
EOF
}

# --- Tests ---

echo "Test: script exists and is executable"
assert_exit "script file exists" 0 test -f "$SCRIPT"
assert_exit "script is executable" 0 test -x "$SCRIPT"

echo ""
echo "Test: missing inventory file fails clearly"
NONEXISTENT="$TEST_DIR/no-such-inventory.md"
assert_exit "missing inventory exits 2" 2 \
  bash "$SCRIPT" --inventory "$NONEXISTENT" --catalog "$TEST_DIR/catalog"
assert_output_contains "missing inventory error message" "inventory" \
  bash "$SCRIPT" --inventory "$NONEXISTENT" --catalog "$TEST_DIR/catalog"

echo ""
echo "Test: empty catalog with all-skip-reason inventory passes (PR-A pre-PR-C state)"
INVENTORY_A="$TEST_DIR/inv-a.md"
write_inventory_header "$INVENTORY_A"
append_inventory_row "$INVENTORY_A" "/admin/dashboard/" "not_screenshotted: pending #79"
append_inventory_row "$INVENTORY_A" "/admin/clients/" "not_screenshotted: pending #79"
append_inventory_row "$INVENTORY_A" "/admin/shifts/" "not_screenshotted: pending #79"
mkdir -p "$TEST_DIR/cat-a"
assert_exit "all skip-reason, empty catalog → pass" 0 \
  bash "$SCRIPT" --inventory "$INVENTORY_A" --catalog "$TEST_DIR/cat-a"
assert_output_contains "reports skip-reason count" "skip-reason" \
  bash "$SCRIPT" --inventory "$INVENTORY_A" --catalog "$TEST_DIR/cat-a"

echo ""
echo "Test: catalog dir does not exist (graceful)"
assert_exit "catalog dir missing, all skip-reason → pass" 0 \
  bash "$SCRIPT" --inventory "$INVENTORY_A" --catalog "$TEST_DIR/cat-a-nonexistent"

echo ""
echo "Test: matched inventory ↔ caption pair"
INVENTORY_B="$TEST_DIR/inv-b.md"
write_inventory_header "$INVENTORY_B"
append_inventory_row "$INVENTORY_B" "/admin/dashboard/" "agency-admin/001-dashboard"
write_caption "$TEST_DIR/cat-b" "agency-admin" "001-dashboard" "agency-admin/001-dashboard"
assert_exit "matched ref ↔ caption → pass" 0 \
  bash "$SCRIPT" --inventory "$INVENTORY_B" --catalog "$TEST_DIR/cat-b"
assert_output_contains "reports matched count >= 1" "matched: 1" \
  bash "$SCRIPT" --inventory "$INVENTORY_B" --catalog "$TEST_DIR/cat-b"

echo ""
echo "Test: inventory ref but caption missing (unmatched) fails"
INVENTORY_C="$TEST_DIR/inv-c.md"
write_inventory_header "$INVENTORY_C"
append_inventory_row "$INVENTORY_C" "/admin/dashboard/" "agency-admin/001-dashboard"
mkdir -p "$TEST_DIR/cat-c/agency-admin"
assert_exit "unmatched ref (caption missing) → fail" 1 \
  bash "$SCRIPT" --inventory "$INVENTORY_C" --catalog "$TEST_DIR/cat-c"
assert_output_contains "names the broken ref" "agency-admin/001-dashboard" \
  bash "$SCRIPT" --inventory "$INVENTORY_C" --catalog "$TEST_DIR/cat-c"

echo ""
echo "Test: orphan caption (caption with no matching inventory ref) fails"
INVENTORY_D="$TEST_DIR/inv-d.md"
write_inventory_header "$INVENTORY_D"
append_inventory_row "$INVENTORY_D" "/admin/dashboard/" "not_screenshotted: pending #79"
write_caption "$TEST_DIR/cat-d" "agency-admin" "999-orphan" "agency-admin/999-orphan"
assert_exit "orphan caption → fail" 1 \
  bash "$SCRIPT" --inventory "$INVENTORY_D" --catalog "$TEST_DIR/cat-d"
assert_output_contains "names the orphan caption" "agency-admin/999-orphan" \
  bash "$SCRIPT" --inventory "$INVENTORY_D" --catalog "$TEST_DIR/cat-d"

echo ""
echo "Test: threshold breach"
INVENTORY_E="$TEST_DIR/inv-e.md"
write_inventory_header "$INVENTORY_E"
# 1 matched + 0 skip-reason = 1/2 = 50% < 95% threshold (mixed: rest is plain blank screenshot_ref)
append_inventory_row "$INVENTORY_E" "/admin/dashboard/" "agency-admin/001-dashboard"
append_inventory_row "$INVENTORY_E" "/admin/clients/" "agency-admin/002-clients"
write_caption "$TEST_DIR/cat-e" "agency-admin" "001-dashboard" "agency-admin/001-dashboard"
# 002-clients is referenced but caption missing → unmatched (already covered).
# This fixture also covers the threshold path: matched=1, unmatched=1, skip=0.
assert_exit "1 matched + 1 unmatched → fail" 1 \
  bash "$SCRIPT" --inventory "$INVENTORY_E" --catalog "$TEST_DIR/cat-e"

echo ""
echo "Test: skip-reason bypass passes threshold"
INVENTORY_F="$TEST_DIR/inv-f.md"
write_inventory_header "$INVENTORY_F"
append_inventory_row "$INVENTORY_F" "/admin/r1/" "not_screenshotted: destructive_endpoint"
append_inventory_row "$INVENTORY_F" "/admin/r2/" "not_screenshotted: gated_by_capability"
append_inventory_row "$INVENTORY_F" "/admin/r3/" "not_screenshotted: no_seed_data"
mkdir -p "$TEST_DIR/cat-f"
assert_exit "all skip-reason variants → pass" 0 \
  bash "$SCRIPT" --inventory "$INVENTORY_F" --catalog "$TEST_DIR/cat-f"

echo ""
echo "Test: --threshold flag accepts override"
INVENTORY_G="$TEST_DIR/inv-g.md"
write_inventory_header "$INVENTORY_G"
append_inventory_row "$INVENTORY_G" "/admin/r1/" "agency-admin/001-r1"
append_inventory_row "$INVENTORY_G" "/admin/r2/" "not_screenshotted: pending #79"
append_inventory_row "$INVENTORY_G" "/admin/r3/" "not_screenshotted: pending #79"
write_caption "$TEST_DIR/cat-g" "agency-admin" "001-r1" "agency-admin/001-r1"
# 1 matched + 2 skip = 3/3 = 100%. Should pass at threshold 95.
assert_exit "1 matched + 2 skip @ threshold=95 → pass" 0 \
  bash "$SCRIPT" --inventory "$INVENTORY_G" --catalog "$TEST_DIR/cat-g" --threshold 95

echo ""
echo "Test: --threshold flag below 95 still passes"
assert_exit "@ threshold=50 → pass" 0 \
  bash "$SCRIPT" --inventory "$INVENTORY_G" --catalog "$TEST_DIR/cat-g" --threshold 50

echo ""
echo "Test: caption with mismatched canonical_id (file at wrong path) is orphan"
INVENTORY_H="$TEST_DIR/inv-h.md"
write_inventory_header "$INVENTORY_H"
append_inventory_row "$INVENTORY_H" "/admin/r1/" "agency-admin/001-r1"
# File on disk is 001-r1.md but its frontmatter says canonical_id: care-manager/001-r1
mkdir -p "$TEST_DIR/cat-h/agency-admin"
cat > "$TEST_DIR/cat-h/agency-admin/001-r1.md" <<'EOF'
---
canonical_id: care-manager/001-r1
route: /admin/r1/
persona: Agency Admin
viewport: desktop
---
EOF
assert_exit "mismatched canonical_id → fail (unmatched + orphan)" 1 \
  bash "$SCRIPT" --inventory "$INVENTORY_H" --catalog "$TEST_DIR/cat-h"

echo ""
echo "============================="
echo "Total: $((PASS + FAIL))"
echo "PASS: $PASS"
echo "FAIL: $FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
