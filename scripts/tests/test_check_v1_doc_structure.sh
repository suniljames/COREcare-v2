#!/usr/bin/env bash
# Tests for scripts/check-v1-doc-structure.sh
# Run from repo root: bash scripts/tests/test_check_v1_doc_structure.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STRUCTURE="$REPO_ROOT/scripts/check-v1-doc-structure.sh"
TEST_DIR=$(mktemp -d -t v1-structure-tests-XXXXXX)
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

write_good_inventory() {
  local path="$1"
  cat > "$path" <<'EOF'
# v1 Pages Inventory

## Super-Admin
| route | v2_status |

## Agency Admin
| route | v2_status |

## Care Manager
| route | v2_status |

## Caregiver
| route | v2_status |

## Client
| route | v2_status |

## Family Member
| route | v2_status |
EOF
}

write_good_delta() {
  local path="$1"
  cat > "$path" <<'EOF'
# v1 Functionality Delta

## For collaborators without v1 access

See `v1-pages-inventory.md`, `v1-user-journeys.md`, `v1-integrations-and-exports.md`.

## Severity matrix

| H | M | L | D |
EOF
}

echo "== check-v1-doc-structure.sh tests =="

[[ -x "$STRUCTURE" ]] || { echo "FAIL — structure script not executable at $STRUCTURE"; exit 1; }

# --- Pass case: good fixtures ---
mkdir -p "$TEST_DIR/good"
write_good_inventory "$TEST_DIR/good/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/good/v1-functionality-delta.md"
assert_exit "fully-conformant docs pass" 0 "$STRUCTURE" --dir "$TEST_DIR/good"

# --- Missing persona ---
mkdir -p "$TEST_DIR/missing-persona"
cat > "$TEST_DIR/missing-persona/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client
EOF
write_good_delta "$TEST_DIR/missing-persona/v1-functionality-delta.md"
assert_exit "inventory missing one persona fails" 1 "$STRUCTURE" --dir "$TEST_DIR/missing-persona"

# --- "needs confirmation" residue past intro separator ---
mkdir -p "$TEST_DIR/needs-confirmation"
write_good_inventory "$TEST_DIR/needs-confirmation/v1-pages-inventory.md"
cat > "$TEST_DIR/needs-confirmation/v1-functionality-delta.md" <<'EOF'
# v1 Functionality Delta

Intro mentioning the **needs confirmation** marker convention.

---

## For collaborators without v1 access

See `v1-pages-inventory.md`.

## Open items

The dual-rate model needs confirmation against v1 source.
EOF
assert_exit "delta with 'needs confirmation' residue past intro fails" 1 "$STRUCTURE" --dir "$TEST_DIR/needs-confirmation"

# --- "needs confirmation" mentioned ONLY in legend (before first separator) is allowed ---
mkdir -p "$TEST_DIR/legend-only"
write_good_inventory "$TEST_DIR/legend-only/v1-pages-inventory.md"
cat > "$TEST_DIR/legend-only/v1-functionality-delta.md" <<'EOF'
# v1 Functionality Delta

Intro that defines the **needs confirmation** marker convention.

---

## For collaborators without v1 access

See `v1-pages-inventory.md`.

## Body

Real content with no flagged items.
EOF
assert_exit "delta with 'needs confirmation' only in pre-separator legend passes" 0 "$STRUCTURE" --dir "$TEST_DIR/legend-only"

# --- Wrong top header in delta ---
mkdir -p "$TEST_DIR/wrong-header"
write_good_inventory "$TEST_DIR/wrong-header/v1-pages-inventory.md"
cat > "$TEST_DIR/wrong-header/v1-functionality-delta.md" <<'EOF'
# v1 Functionality Delta

## Severity matrix

| H | M | L | D |

## For collaborators without v1 access

(too far down)
EOF
assert_exit "delta with cross-ref header NOT first H2 fails" 1 "$STRUCTURE" --dir "$TEST_DIR/wrong-header"

# --- Missing files ---
mkdir -p "$TEST_DIR/missing-files"
assert_exit "missing both files fails" 1 "$STRUCTURE" --dir "$TEST_DIR/missing-files"

# --- Default dir resolves to "docs/migration" relative to cwd; with a non-existent
# path it should fail. Using a fake empty dir to verify default behavior without
# a subshell so the FAIL counter propagates correctly.
mkdir -p "$TEST_DIR/empty-cwd"
PREV_PWD="$PWD"
cd "$TEST_DIR/empty-cwd"
assert_exit "default-dir invocation fails when docs/migration/ absent" 1 "$STRUCTURE"
cd "$PREV_PWD"

# --- Shared routes: section absent is allowed (no check fires) ---
mkdir -p "$TEST_DIR/no-shared-section"
write_good_inventory "$TEST_DIR/no-shared-section/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/no-shared-section/v1-functionality-delta.md"
assert_exit "Shared routes absent → no failure" 0 "$STRUCTURE" --dir "$TEST_DIR/no-shared-section"

# --- Shared routes: section present but pending-content placeholder fails ---
mkdir -p "$TEST_DIR/shared-pending"
cat > "$TEST_DIR/shared-pending/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client
## Family Member

## Shared routes

_(pending content authoring)_
EOF
write_good_delta "$TEST_DIR/shared-pending/v1-functionality-delta.md"
assert_exit "Shared routes still pending fails" 1 "$STRUCTURE" --dir "$TEST_DIR/shared-pending"

# --- Shared routes: section present with no rows fails ---
mkdir -p "$TEST_DIR/shared-empty"
cat > "$TEST_DIR/shared-empty/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client
## Family Member

## Shared routes

Routes accessible by more than one persona.
EOF
write_good_delta "$TEST_DIR/shared-empty/v1-functionality-delta.md"
assert_exit "Shared routes with no rows fails" 1 "$STRUCTURE" --dir "$TEST_DIR/shared-empty"

# --- Shared routes: section present with at least one route row passes ---
mkdir -p "$TEST_DIR/shared-populated"
cat > "$TEST_DIR/shared-populated/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client
## Family Member

## Shared routes

| route | persona | v2_status |
|-------|---------|-----------|
| `/switch-role/` | Care Manager, Caregiver | missing |
EOF
write_good_delta "$TEST_DIR/shared-populated/v1-functionality-delta.md"
assert_exit "Shared routes with one row passes" 0 "$STRUCTURE" --dir "$TEST_DIR/shared-populated"

# --- Family Member: section with placeholder rows passes (no real route rows yet) ---
mkdir -p "$TEST_DIR/family-placeholder"
cat > "$TEST_DIR/family-placeholder/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client

## Family Member

| route | purpose |
|-------|---------|
| _(rows pending content authoring)_ | |
EOF
write_good_delta "$TEST_DIR/family-placeholder/v1-functionality-delta.md"
assert_exit "Family Member with placeholder rows only passes" 0 "$STRUCTURE" --dir "$TEST_DIR/family-placeholder"

# --- Family Member: row missing 'linked-client only' fails ---
mkdir -p "$TEST_DIR/family-missing-scope"
cat > "$TEST_DIR/family-missing-scope/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client

## Family Member

| route | purpose |
|-------|---------|
| `/family/dashboard/` | 🔒 PHI · Lists clients linked to user; HIPAA-access-logged in v1. |
EOF
write_good_delta "$TEST_DIR/family-missing-scope/v1-functionality-delta.md"
assert_exit "Family Member row missing 'linked-client only' fails" 1 "$STRUCTURE" --dir "$TEST_DIR/family-missing-scope"

# --- Family Member: row missing audit-posture phrase fails ---
mkdir -p "$TEST_DIR/family-missing-audit"
cat > "$TEST_DIR/family-missing-audit/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client

## Family Member

| route | purpose |
|-------|---------|
| `/family/dashboard/` | 🔒 PHI · Lists clients linked to the user; linked-client only. |
EOF
write_good_delta "$TEST_DIR/family-missing-audit/v1-functionality-delta.md"
assert_exit "Family Member row missing audit-posture phrase fails" 1 "$STRUCTURE" --dir "$TEST_DIR/family-missing-audit"

# --- Family Member: row missing PHI prefix fails ---
mkdir -p "$TEST_DIR/family-missing-phi"
cat > "$TEST_DIR/family-missing-phi/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client

## Family Member

| route | purpose |
|-------|---------|
| `/family/dashboard/` | Lists linked clients; linked-client only; HIPAA-access-logged in v1. |
EOF
write_good_delta "$TEST_DIR/family-missing-phi/v1-functionality-delta.md"
assert_exit "Family Member row missing '🔒 PHI ·' prefix fails" 1 "$STRUCTURE" --dir "$TEST_DIR/family-missing-phi"

# --- Family Member: row containing BOTH audit-posture phrases fails (must be exactly one) ---
mkdir -p "$TEST_DIR/family-both-audit"
cat > "$TEST_DIR/family-both-audit/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client

## Family Member

| route | purpose |
|-------|---------|
| `/family/dashboard/` | 🔒 PHI · Lists linked clients; linked-client only; HIPAA-access-logged in v1; v1 has no audit on this route — v2 design must add. |
EOF
write_good_delta "$TEST_DIR/family-both-audit/v1-functionality-delta.md"
assert_exit "Family Member row containing BOTH audit phrases fails" 1 "$STRUCTURE" --dir "$TEST_DIR/family-both-audit"

# --- Family Member: well-formed PHI row with 'linked-client only' + HIPAA-logged passes ---
mkdir -p "$TEST_DIR/family-good-logged"
cat > "$TEST_DIR/family-good-logged/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client

## Family Member

| route | purpose |
|-------|---------|
| `/family/billing-pdf/` | 🔒 PHI · Family invoice PDF; linked-client only; HIPAA-access-logged in v1. |
EOF
write_good_delta "$TEST_DIR/family-good-logged/v1-functionality-delta.md"
assert_exit "Family Member well-formed row with 'HIPAA-access-logged in v1' passes" 0 "$STRUCTURE" --dir "$TEST_DIR/family-good-logged"

# --- Family Member: well-formed PHI row with 'no audit' phrase passes ---
mkdir -p "$TEST_DIR/family-good-noaudit"
cat > "$TEST_DIR/family-good-noaudit/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client

## Family Member

| route | purpose |
|-------|---------|
| `/family/dashboard/` | 🔒 PHI · Lists linked clients; linked-client only; v1 has no audit on this route — v2 design must add. |
EOF
write_good_delta "$TEST_DIR/family-good-noaudit/v1-functionality-delta.md"
assert_exit "Family Member well-formed row with 'no audit' phrase passes" 0 "$STRUCTURE" --dir "$TEST_DIR/family-good-noaudit"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
