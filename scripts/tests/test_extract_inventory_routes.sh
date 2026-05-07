#!/usr/bin/env bash
# Tests for scripts/extract-inventory-routes.sh
# Run from repo root: bash scripts/tests/test_extract_inventory_routes.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/extract-inventory-routes.sh"
TEST_DIR=$(mktemp -d -t extract-inventory-routes-tests-XXXXXX)
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

assert_json_field() {
  # assert_json_field <description> <jq-expression> <expected-value> <command...>
  local description="$1"
  local jq_expr="$2"
  local expected="$3"
  shift 3
  local actual
  actual=$("$@" 2>/dev/null | jq -r "$jq_expr" 2>/dev/null)
  if [[ "$actual" == "$expected" ]]; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description (expected '$expected', got '$actual')"
    FAIL=$((FAIL + 1))
  fi
}

# --- Fixture builders ---

write_inventory_two_personas() {
  local path="$1"
  cat > "$path" <<'EOF'
# v1 Pages Inventory

## Agency Admin

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/admin/dashboard/` | dashboard | data | scaffolded |  | true | false | false | agency-admin/001-dashboard |  |
| `/admin/clients/` | client list | data | scaffolded |  | true | false | true | not_screenshotted: pending #79 |  |

## Caregiver

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/caregiver/clock-in/` | clock in | data | scaffolded |  | true | false | true | caregiver/001-clock-in |  |
EOF
}

# --- Tests ---

if ! command -v jq >/dev/null 2>&1; then
  echo "SKIP — jq not installed; tests require jq for JSON assertions"
  exit 0
fi

echo "Test: script exists and is executable"
assert_exit "script file exists" 0 test -f "$SCRIPT"
assert_exit "script is executable" 0 test -x "$SCRIPT"

echo ""
echo "Test: missing inventory file fails clearly"
NONEXISTENT="$TEST_DIR/no-such-inventory.md"
assert_exit "missing inventory exits 2" 2 \
  bash "$SCRIPT" --inventory "$NONEXISTENT"

echo ""
echo "Test: emits JSON array"
INVENTORY_A="$TEST_DIR/inv-a.md"
write_inventory_two_personas "$INVENTORY_A"
assert_json_field "output is a JSON array (length 3)" "length" "3" \
  bash "$SCRIPT" --inventory "$INVENTORY_A"

echo ""
echo "Test: each row has persona, route, screenshot_ref fields"
assert_json_field "first row persona is 'Agency Admin'" ".[0].persona" "Agency Admin" \
  bash "$SCRIPT" --inventory "$INVENTORY_A"
assert_json_field "first row route is '/admin/dashboard/'" ".[0].route" "/admin/dashboard/" \
  bash "$SCRIPT" --inventory "$INVENTORY_A"
assert_json_field "first row screenshot_ref is 'agency-admin/001-dashboard'" ".[0].screenshot_ref" "agency-admin/001-dashboard" \
  bash "$SCRIPT" --inventory "$INVENTORY_A"

echo ""
echo "Test: skip-reason rows preserved verbatim in screenshot_ref"
assert_json_field "second row screenshot_ref preserves 'not_screenshotted: pending #79'" ".[1].screenshot_ref" "not_screenshotted: pending #79" \
  bash "$SCRIPT" --inventory "$INVENTORY_A"

echo ""
echo "Test: persona section detection (route under H2 ## Caregiver)"
assert_json_field "third row persona is 'Caregiver'" ".[2].persona" "Caregiver" \
  bash "$SCRIPT" --inventory "$INVENTORY_A"
assert_json_field "third row route is '/caregiver/clock-in/'" ".[2].route" "/caregiver/clock-in/" \
  bash "$SCRIPT" --inventory "$INVENTORY_A"

echo ""
echo "Test: skips non-table content (prose, summary tables, headers)"
INVENTORY_B="$TEST_DIR/inv-b.md"
cat > "$INVENTORY_B" <<'EOF'
# v1 Pages Inventory

This is a prose paragraph that should not be parsed as a row.

## Agency Admin

| app | denominator | numerator | notes |
|-----|-------------|-----------|-------|
| billing | 3 | 3 | summary table — not an inventory row |

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/admin/dashboard/` | dashboard | data | scaffolded |  | true | false | false | agency-admin/001-dashboard |  |
EOF
assert_json_field "summary table rows are skipped (length 1)" "length" "1" \
  bash "$SCRIPT" --inventory "$INVENTORY_B"

echo ""
echo "Test: H3 sub-section under a persona inherits persona context"
INVENTORY_C="$TEST_DIR/inv-c.md"
cat > "$INVENTORY_C" <<'EOF'
# v1 Pages Inventory

## Agency Admin

### billing

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| `/admin/billing/` | billing | data | scaffolded |  | true | false | false | agency-admin/010-billing |  |
EOF
assert_json_field "row under H3 inherits 'Agency Admin' persona" ".[0].persona" "Agency Admin" \
  bash "$SCRIPT" --inventory "$INVENTORY_C"

echo ""
echo "Test: empty inventory (no persona sections, no rows) emits empty array"
INVENTORY_D="$TEST_DIR/inv-d.md"
cat > "$INVENTORY_D" <<'EOF'
# v1 Pages Inventory

Just prose, no tables.
EOF
assert_json_field "empty inventory emits []" "length" "0" \
  bash "$SCRIPT" --inventory "$INVENTORY_D"

echo ""
echo "Test: real repo inventory parses without error"
REAL_INVENTORY="$REPO_ROOT/docs/migration/v1-pages-inventory.md"
if [[ -f "$REAL_INVENTORY" ]]; then
  assert_exit "real inventory parses" 0 \
    bash "$SCRIPT" --inventory "$REAL_INVENTORY"
else
  echo "  SKIP — no docs/migration/v1-pages-inventory.md (run from repo root)"
fi

echo ""
echo "============================="
echo "Total: $((PASS + FAIL))"
echo "PASS: $PASS"
echo "FAIL: $FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
