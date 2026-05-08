#!/usr/bin/env bash
# Tests for scripts/check-v1-inventory-mount-prefixes.sh.
# Run from repo root: bash scripts/tests/test_check_v1_inventory_mount_prefixes.sh
#
# Covers the ten cases locked in #211's Test Specification, plus a
# regression-204 fixture round-trip and a live-inventory smoke check.

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/check-v1-inventory-mount-prefixes.sh"
TEST_DIR=$(mktemp -d -t v1-mount-prefix-tests-XXXXXX)
trap 'rm -rf "$TEST_DIR"' EXIT

# Pinned test SHA — matches the live fixture's header so the live-inventory
# smoke check passes against the real repo state. Synthesized cases that need
# a different SHA write their own README + fixture pair.
TEST_SHA="9738412a6e41064203fc253d9dd2a5c6a9c2e231"
ALT_SHA="0000000000000000000000000000000000000000"

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

assert_exit_and_match() {
  local description="$1"
  local expected_code="$2"
  local pattern="$3"
  shift 3
  local actual_output
  actual_output=$("$@" 2>&1)
  local actual_code=$?
  if [[ "$actual_code" == "$expected_code" ]] && [[ "$actual_output" =~ $pattern ]]; then
    echo "  PASS — $description (exit $actual_code, matched /$pattern/)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description (expected exit $expected_code matching /$pattern/, got exit $actual_code)"
    echo "    output: $actual_output"
    FAIL=$((FAIL + 1))
  fi
}

# ---- Helpers -----------------------------------------------------------

write_readme() {
  local path="$1" sha="$2"
  cat > "$path" <<EOF
# V1 Reference Documentation Set

## V1 Reference Commit

- **Repo:** \`hcunanan79/COREcare-access\`
- **Commit SHA:** \`$sha\`
- **Pinned at:** 2026-05-06
EOF
}

write_fixture() {
  local path="$1" sha="$2"; shift 2
  {
    echo "# v1 elitecare/urls.py mount-prefix projection"
    echo "# v1 SHA: $sha"
    for line in "$@"; do
      echo "$line"
    done
  } > "$path"
}

# ---- Case 1: Golden minimal inventory + matching fixture ---------------

setup_case_1() {
  local d="$TEST_DIR/case-1"
  mkdir -p "$d"
  write_readme "$d/README.md" "$TEST_SHA"
  write_fixture "$d/fixture.txt" "$TEST_SHA" \
    'path("caregiver/", include("caregiver_dashboard.urls"))'
  cat > "$d/inv.md" <<'EOF'
# Inventory

## Caregiver

### caregiver_dashboard
_clock-in/out and schedule view; mounted at `/caregiver/` (`caregiver_dashboard/urls.py` is included at `/caregiver/` per `elitecare/urls.py:60`)_

| route | purpose |
|-------|---------|
| `/caregiver/dashboard/` | Caregiver home |
| `/caregiver/schedule/` | Schedule |
EOF
  echo "$d"
}

case1_dir=$(setup_case_1)
assert_exit \
  "Case 1: golden inventory + matching fixture exits 0" \
  0 \
  bash "$SCRIPT" --inventory "$case1_dir/inv.md" --fixture "$case1_dir/fixture.txt" --readme "$case1_dir/README.md"

# ---- Case 2: H3 declares prefix not in fixture -------------------------

setup_case_2() {
  local d="$TEST_DIR/case-2"
  mkdir -p "$d"
  write_readme "$d/README.md" "$TEST_SHA"
  write_fixture "$d/fixture.txt" "$TEST_SHA" \
    'path("caregiver/", include("caregiver_dashboard.urls"))'
  cat > "$d/inv.md" <<'EOF'
# Inventory

## Agency Admin

### bogusapp
_admin surfaces; mounted at `/bogusapp/` (`bogusapp/urls.py` is included at `/bogusapp/` per `elitecare/urls.py:99`)_

| route | purpose |
|-------|---------|
| `/bogusapp/home/` | Home |
EOF
  echo "$d"
}

case2_dir=$(setup_case_2)
assert_exit_and_match \
  "Case 2: prefix not in fixture exits 1 and names H2>H3 + line + literal prefix" \
  1 \
  'Agency Admin > bogusapp.*bogusapp/' \
  bash "$SCRIPT" --inventory "$case2_dir/inv.md" --fixture "$case2_dir/fixture.txt" --readme "$case2_dir/README.md"

# ---- Case 3: H3 prefix mismatches first row ----------------------------

setup_case_3() {
  local d="$TEST_DIR/case-3"
  mkdir -p "$d"
  write_readme "$d/README.md" "$TEST_SHA"
  write_fixture "$d/fixture.txt" "$TEST_SHA" \
    'path("dashboard/", include("dashboard.urls"))' \
    'path("caregiver/", include("caregiver_dashboard.urls"))'
  cat > "$d/inv.md" <<'EOF'
# Inventory

## Family Member

### dashboard
_family portal landing; mounted at `/dashboard/family/` (`dashboard/urls.py` is included at `/dashboard/` per `elitecare/urls.py:186`)_

| route | purpose |
|-------|---------|
| `/family/dashboard/` | Family home |
EOF
  echo "$d"
}

case3_dir=$(setup_case_3)
assert_exit_and_match \
  "Case 3: first-row prefix mismatch exits 1 and names H3 + both prefixes" \
  1 \
  'Family Member > dashboard.*/dashboard/family/.*/family/dashboard/' \
  bash "$SCRIPT" --inventory "$case3_dir/inv.md" --fixture "$case3_dir/fixture.txt" --readme "$case3_dir/README.md"

# ---- Case 4: H3 italic line lacks "mounted at" phrase ------------------

setup_case_4() {
  local d="$TEST_DIR/case-4"
  mkdir -p "$d"
  write_readme "$d/README.md" "$TEST_SHA"
  write_fixture "$d/fixture.txt" "$TEST_SHA" \
    'path("caregiver/", include("caregiver_dashboard.urls"))'
  cat > "$d/inv.md" <<'EOF'
# Inventory

## Family Member

### Cross-reference index
_Routes whose canonical row lives in a persona section._

| route | primary persona |
|-------|-----------------|
| `/charting/proxy/<int:visit_id>/` | Agency Admin |
EOF
  echo "$d"
}

case4_dir=$(setup_case_4)
assert_exit \
  "Case 4: H3 without mount-at phrase is skipped (exit 0)" \
  0 \
  bash "$SCRIPT" --inventory "$case4_dir/inv.md" --fixture "$case4_dir/fixture.txt" --readme "$case4_dir/README.md"

# ---- Case 5: H3 with two backticked prefixes joined by " and " --------

setup_case_5() {
  local d="$TEST_DIR/case-5"
  mkdir -p "$d"
  write_readme "$d/README.md" "$TEST_SHA"
  write_fixture "$d/fixture.txt" "$TEST_SHA" \
    'path("legal/", include("compliance.urls"))' \
    'path("compliance/files/", include("compliance.urls_file_serve"))'
  cat > "$d/inv.md" <<'EOF'
# Inventory

## Agency Admin

### compliance
_public statements + PHI downloads; mounted at `/legal/` and `/compliance/files/` (`compliance/urls.py` and `compliance.urls_file_serve` per `elitecare/urls.py:200`)_

| route | purpose |
|-------|---------|
| `/legal/accessibility/` | Accessibility statement |
| `/compliance/files/<int:file_id>/` | Authenticated file |
EOF
  echo "$d"
}

case5_dir=$(setup_case_5)
assert_exit \
  "Case 5: multi-prefix H3 exits 0 when both validate" \
  0 \
  bash "$SCRIPT" --inventory "$case5_dir/inv.md" --fixture "$case5_dir/fixture.txt" --readme "$case5_dir/README.md"

# ---- Case 6: H3 with "mounted at root prefix with no path component" --

setup_case_6() {
  local d="$TEST_DIR/case-6"
  mkdir -p "$d"
  write_readme "$d/README.md" "$TEST_SHA"
  write_fixture "$d/fixture.txt" "$TEST_SHA" \
    'path("", include("auth_service.urls"))'
  cat > "$d/inv.md" <<'EOF'
# Inventory

## Agency Admin

### auth_service
_password reset + magic-link login; mounted at root prefix with no path component; routes shared across all personas_

| route | purpose |
|-------|---------|
| `/login/` | Login form |
EOF
  echo "$d"
}

case6_dir=$(setup_case_6)
assert_exit \
  "Case 6: root-prefix-no-path H3 is skipped (exit 0)" \
  0 \
  bash "$SCRIPT" --inventory "$case6_dir/inv.md" --fixture "$case6_dir/fixture.txt" --readme "$case6_dir/README.md"

# ---- Case 7: H3 with mount declaration but no rows ---------------------

setup_case_7() {
  local d="$TEST_DIR/case-7"
  mkdir -p "$d"
  write_readme "$d/README.md" "$TEST_SHA"
  write_fixture "$d/fixture.txt" "$TEST_SHA" \
    'path("caregiver/", include("caregiver_dashboard.urls"))'
  cat > "$d/inv.md" <<'EOF'
# Inventory

## Caregiver

### caregiver_dashboard
_clock-in/out and schedule view; mounted at `/caregiver/` (`caregiver_dashboard/urls.py` is included at `/caregiver/` per `elitecare/urls.py:60`)_

(no rows yet — pending authoring)
EOF
  echo "$d"
}

case7_dir=$(setup_case_7)
assert_exit \
  "Case 7: H3 with declaration but no rows exits 0 (first-row check skipped, fixture check still passes)" \
  0 \
  bash "$SCRIPT" --inventory "$case7_dir/inv.md" --fixture "$case7_dir/fixture.txt" --readme "$case7_dir/README.md"

# ---- Case 8: H3 prefix written without leading slash (contract violation)

setup_case_8() {
  local d="$TEST_DIR/case-8"
  mkdir -p "$d"
  write_readme "$d/README.md" "$TEST_SHA"
  write_fixture "$d/fixture.txt" "$TEST_SHA" \
    'path("caregiver/", include("caregiver_dashboard.urls"))'
  cat > "$d/inv.md" <<'EOF'
# Inventory

## Caregiver

### caregiver_dashboard
_clock-in/out and schedule view; mounted at `caregiver/` (no leading slash — contract violation)_

| route | purpose |
|-------|---------|
| `/caregiver/dashboard/` | Caregiver home |
EOF
  echo "$d"
}

case8_dir=$(setup_case_8)
assert_exit_and_match \
  "Case 8: prefix without leading slash exits 1 with contract-violation message" \
  1 \
  'caregiver_dashboard.*leading slash' \
  bash "$SCRIPT" --inventory "$case8_dir/inv.md" --fixture "$case8_dir/fixture.txt" --readme "$case8_dir/README.md"

# ---- Case 9: Fixture header SHA != README V1 Reference Commit SHA -----

setup_case_9() {
  local d="$TEST_DIR/case-9"
  mkdir -p "$d"
  write_readme "$d/README.md" "$TEST_SHA"
  write_fixture "$d/fixture.txt" "$ALT_SHA" \
    'path("caregiver/", include("caregiver_dashboard.urls"))'
  cat > "$d/inv.md" <<'EOF'
# Inventory

## Caregiver

### caregiver_dashboard
_mounted at `/caregiver/`_

| route | purpose |
|-------|---------|
| `/caregiver/dashboard/` | Home |
EOF
  echo "$d"
}

case9_dir=$(setup_case_9)
assert_exit_and_match \
  "Case 9: fixture-vs-README SHA mismatch exits 1 with stale-fixture message" \
  1 \
  'fixture stale|header SHA' \
  bash "$SCRIPT" --inventory "$case9_dir/inv.md" --fixture "$case9_dir/fixture.txt" --readme "$case9_dir/README.md"

# ---- Case 10: README missing or malformed Commit SHA line -------------

setup_case_10() {
  local d="$TEST_DIR/case-10"
  mkdir -p "$d"
  cat > "$d/README.md" <<'EOF'
# V1 Reference Documentation Set

(no Commit SHA line here — the README is malformed for this test)
EOF
  write_fixture "$d/fixture.txt" "$TEST_SHA" \
    'path("caregiver/", include("caregiver_dashboard.urls"))'
  cat > "$d/inv.md" <<'EOF'
# Inventory

## Caregiver

### caregiver_dashboard
_mounted at `/caregiver/`_

| route | purpose |
|-------|---------|
| `/caregiver/dashboard/` | Home |
EOF
  echo "$d"
}

case10_dir=$(setup_case_10)
assert_exit \
  "Case 10: malformed README exits 2 (operator error, distinct from lint failure)" \
  2 \
  bash "$SCRIPT" --inventory "$case10_dir/inv.md" --fixture "$case10_dir/fixture.txt" --readme "$case10_dir/README.md"

# ---- Regression-204 fixture round-trip --------------------------------

REGRESSION="$REPO_ROOT/scripts/tests/fixtures/v1-mount-prefixes/regression-204.md"
if [[ -f "$REGRESSION" ]]; then
  assert_exit_and_match \
    "Regression-204 fixture: family-member dashboard misrouting is flagged" \
    1 \
    'Family Member > dashboard' \
    bash "$SCRIPT" --inventory "$REGRESSION"
else
  echo "  SKIP — regression-204 fixture missing at $REGRESSION"
fi

# ---- Live-inventory smoke check ---------------------------------------

# The script must pass against the actual committed inventory + fixture +
# README state in this repo. This catches "scaffolded fixtures pass but the
# live inventory drifted" regressions.
assert_exit \
  "Live inventory: script passes against real repo state" \
  0 \
  bash "$SCRIPT"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
