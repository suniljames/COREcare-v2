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

# Like assert_exit, plus asserts that combined stdout+stderr matches a
# bash-regex pattern. Use when exit code alone cannot distinguish a
# correct failure from a near-miss regression (e.g., one rule code firing
# instead of another within the same script).
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

# Boundary fixture: a malformed Shared-routes row placed AFTER ## Family Member
# must NOT be subjected to Family Member per-row rules. Origin: PR #113 Q4 NIT.
mkdir -p "$TEST_DIR/family-shared-boundary"
cat > "$TEST_DIR/family-shared-boundary/v1-pages-inventory.md" <<'EOF'
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

## Shared routes

| route | purpose | persona | v2_status | severity |
|-------|---------|---------|-----------|----------|
| `/family-signup/` | Public signup form. | none | implemented | L |
EOF
write_good_delta "$TEST_DIR/family-shared-boundary/v1-functionality-delta.md"
assert_exit "Family Member structure rules STOP at '## Shared routes' H2 boundary" 0 "$STRUCTURE" --dir "$TEST_DIR/family-shared-boundary"

# =============================================================================
# Integrations-and-exports doc tests (CL-1, CL-2, SL-1..SL-4, EL-1, EL-2)
# =============================================================================
# Helper that writes inventory + delta + a parameterized integrations file.
# Inventory carries enough headings to provide stable anchors used by EL tests:
# #dashboard, #charting, #quickbooks_integration, #auth_service.

write_integrations_inventory() {
  local path="$1"
  cat > "$path" <<'EOF'
# v1 Pages Inventory

## Super-Admin
## Agency Admin

### dashboard
| route | v2_status |

### charting
| route | v2_status |

### quickbooks_integration
| route | v2_status |

### auth_service
| route | v2_status |

## Care Manager
## Caregiver
## Client
## Family Member
EOF
}

# Locked schema header used by every entry table.
INTEGRATIONS_HEADER='| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |'
INTEGRATIONS_SEP='|------|--------------------|---------|--------------------|--------------------|---------------------|-----------|----------|'

write_good_integrations() {
  local path="$1"
  cat > "$path" <<EOF
# V1 Integrations and Exports

## Schema

| Field | Description |
|-------|-------------|
| name | Integration name |

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| QuickBooks Online | Intuit | OAuth connect | outbound; sync | [/quickbooks/](v1-pages-inventory.md#quickbooks_integration) | Sees: connected status. Channel: admin index. | missing | H |

### Payroll

(none)

### Accounting

(none)

### Messaging and notifications (third-party)

(none)

### Identity, auth, and SSO (third-party)

(none)

### Other

(none)

## Internal notification and email backend

### Email pipeline

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Password reset email | internal | User submits reset form | outbound; sync | [/password-reset/](v1-pages-inventory.md#auth_service) | Sees: reset link in inbox. | missing | D |
| Email canary | internal | Operator runs management command | outbound; sync | _no UI surface — operator monitoring_ | Sees: nothing. Operator-only. | missing | M |

### In-app notifications

(none)

## Customer-facing exports

### CSV exports

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Timecard CSV | internal | Admin clicks export | outbound; sync | [/dashboard/admin/timecards/export/csv/](v1-pages-inventory.md#dashboard) | 🔒 PHI · Sees: CSV download. | missing | M |

### PDF exports

(none)

### Other formats

(none)

## Cross-references

(none)
EOF
}

echo ""
echo "== integrations-and-exports doc: CL/SL/EL tests =="

# --- Pass case: full happy-path integrations doc ---
mkdir -p "$TEST_DIR/integrations-good"
write_integrations_inventory "$TEST_DIR/integrations-good/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-good/v1-functionality-delta.md"
write_good_integrations "$TEST_DIR/integrations-good/v1-integrations-and-exports.md"
assert_exit "fully-conformant integrations doc passes" 0 "$STRUCTURE" --dir "$TEST_DIR/integrations-good"

# --- Integrations doc absent: structure check skips it (existing inventory passes) ---
mkdir -p "$TEST_DIR/integrations-absent"
write_integrations_inventory "$TEST_DIR/integrations-absent/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-absent/v1-functionality-delta.md"
assert_exit "integrations doc absent → structure check skips it" 0 "$STRUCTURE" --dir "$TEST_DIR/integrations-absent"

# --- CL-1: missing required H2 (e.g. drop "## Cross-references") ---
mkdir -p "$TEST_DIR/integrations-cl1"
write_integrations_inventory "$TEST_DIR/integrations-cl1/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-cl1/v1-functionality-delta.md"
write_good_integrations "$TEST_DIR/integrations-cl1/v1-integrations-and-exports.md"
# Strip the "## Cross-references" line.
sed -i.bak '/^## Cross-references$/d' "$TEST_DIR/integrations-cl1/v1-integrations-and-exports.md"
rm "$TEST_DIR/integrations-cl1/v1-integrations-and-exports.md.bak"
assert_exit "CL-1: missing required H2 fails" 1 "$STRUCTURE" --dir "$TEST_DIR/integrations-cl1"

# --- CL-1: extra unexpected H2 ---
mkdir -p "$TEST_DIR/integrations-cl1-extra"
write_integrations_inventory "$TEST_DIR/integrations-cl1-extra/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-cl1-extra/v1-functionality-delta.md"
write_good_integrations "$TEST_DIR/integrations-cl1-extra/v1-integrations-and-exports.md"
# Append an extra unexpected H2.
echo '## Appendix' >> "$TEST_DIR/integrations-cl1-extra/v1-integrations-and-exports.md"
assert_exit "CL-1: unexpected extra H2 fails" 1 "$STRUCTURE" --dir "$TEST_DIR/integrations-cl1-extra"

# --- CL-2: External integrations missing one locked H3 ---
mkdir -p "$TEST_DIR/integrations-cl2"
write_integrations_inventory "$TEST_DIR/integrations-cl2/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-cl2/v1-functionality-delta.md"
write_good_integrations "$TEST_DIR/integrations-cl2/v1-integrations-and-exports.md"
# Drop the "### Payroll" line.
sed -i.bak '/^### Payroll$/d' "$TEST_DIR/integrations-cl2/v1-integrations-and-exports.md"
rm "$TEST_DIR/integrations-cl2/v1-integrations-and-exports.md.bak"
assert_exit "CL-2: External integrations missing locked H3 fails" 1 "$STRUCTURE" --dir "$TEST_DIR/integrations-cl2"

# Sub-letter + substring-assertion convention (#196, evolves #174)
#
# Cohort-wide rule, no opt-in, no per-prefix exception:
#
#   1. Any code with ≥2 emit branches in scripts/check-v1-doc-structure.sh is
#      sub-lettered at the awk emit (e.g., SL-1a / SL-1b, SL-3a / SL-3b / SL-3c,
#      EL-2a / EL-2b, CR-1a / CR-1b, GL-3a / GL-3b / GL-3c). At most one
#      sub-letter; canonical regex `^[A-Z]{2}-[0-9]+[a-z]?$`. RR-4a..d follows
#      the same shape. Single-emit codes (SL-2, SL-4, EL-1, etc.) stay bare.
#
#   2. Each sub-lettered code's fixture uses assert_exit_and_match (not bare
#      assert_exit) with the shortest-unique substring of the emit message
#      that distinguishes its branch from siblings. Rationale: exit-code-only
#      assertions cannot tell "right rule fired" from "some rule fired" — a
#      regression that swapped two branches' conditions would still exit 1 and
#      silently pass a bare-exit fixture.
#
#   3. The MT-1 coverage-parity meta-test asserts the set of distinct codes in
#      the awk equals the set referenced as fixture description tokens. Sub-
#      lettered codes are first-class members of those sets (the umbrella-filter
#      drops bare X-N when X-N<letter> exists, so umbrella refs in headers/
#      comments don't pollute parity). MT-2 enforces the canonical regex shape
#      so non-canonical references (e.g., SL-1.1, SL_1a, SL-1ab) fail loudly.
#
# Negative-fixture (assert_exit_and_match) substrings for renamed codes are
# locked in issue #196's Test Specification. Positive fixtures (assert_exit
# expecting exit 0) need no substring; their description token still uses the
# sub-letter so MT-1 sees the branch as covered.

# --- SL-1a: entry-table header column drift ---
mkdir -p "$TEST_DIR/integrations-sl1a"
write_integrations_inventory "$TEST_DIR/integrations-sl1a/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-sl1a/v1-functionality-delta.md"
write_good_integrations "$TEST_DIR/integrations-sl1a/v1-integrations-and-exports.md"
# Replace the locked header with a drifted one (e.g. swap order).
DRIFTED_HEADER='| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | severity | v2_status |'
sed -i.bak "s|^| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |\$|$DRIFTED_HEADER|" \
  "$TEST_DIR/integrations-sl1a/v1-integrations-and-exports.md" 2>/dev/null || true
# More portable: rewrite via python-free in-place edit using awk.
awk -v drift="$DRIFTED_HEADER" '
  /^\| name \| vendor_or_internal \|/ && !done { print drift; done=1; next }
  { print }
' "$TEST_DIR/integrations-sl1a/v1-integrations-and-exports.md" > "$TEST_DIR/integrations-sl1a/_tmp" && \
  mv "$TEST_DIR/integrations-sl1a/_tmp" "$TEST_DIR/integrations-sl1a/v1-integrations-and-exports.md"
rm -f "$TEST_DIR/integrations-sl1a/v1-integrations-and-exports.md.bak"
assert_exit_and_match "SL-1a: drifted entry-table header fails" 1 'SL-1a:.*header does not match' "$STRUCTURE" --dir "$TEST_DIR/integrations-sl1a"

# --- SL-1b: data row with wrong cell count ---
# Realistic shape: a row that's missing the trailing `severity` cell entirely
# (drops to 7 cells). Per issue #196 Security Engineer review, this exercises
# the cell-count check with a regression scenario (column accidentally elided),
# not a synthetic 99-cell strawman. If a future refactor inverts `n - 2 != 8`
# to `n - 2 == 8`, this fixture detects the regression; without it, malformed
# rows would slip past per-cell SL-2/SL-3/SL-4 token validators (those run only
# AFTER the cell-count guard at scripts/check-v1-doc-structure.sh:348).
mkdir -p "$TEST_DIR/integrations-sl1b"
write_integrations_inventory "$TEST_DIR/integrations-sl1b/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-sl1b/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-sl1b/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Bad row | Vendor | Trigger | outbound; sync | [/quickbooks/](v1-pages-inventory.md#quickbooks_integration) | Sees: thing. | missing |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit_and_match "SL-1b: data row with 7 cells fails" 1 'SL-1b:.*cells, expected 8' "$STRUCTURE" --dir "$TEST_DIR/integrations-sl1b"

# --- SL-2: invalid v2_status token ---
# Fixture purity (#174): the bad row's severity cell is intentionally empty.
# v2_status='partial' (invalid) trips SL-2 alone. If severity were set, SL-3
# ("severity set but v2_status != missing") would also fire, masking SL-2
# regressions under exit-code-only assertions.
mkdir -p "$TEST_DIR/integrations-sl2"
write_integrations_inventory "$TEST_DIR/integrations-sl2/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-sl2/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-sl2/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Bad row | Vendor | Trigger | outbound; sync | [/quickbooks/](v1-pages-inventory.md#quickbooks_integration) | Sees: thing. | partial |  |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit_and_match "SL-2: invalid v2_status token fails" 1 'SL-2:' "$STRUCTURE" --dir "$TEST_DIR/integrations-sl2"

# --- SL-3c (set): severity set but v2_status is not "missing" ---
mkdir -p "$TEST_DIR/integrations-sl3-set"
write_integrations_inventory "$TEST_DIR/integrations-sl3-set/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-sl3-set/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-sl3-set/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Bad row | Vendor | Trigger | outbound; sync | [/quickbooks/](v1-pages-inventory.md#quickbooks_integration) | Sees: thing. | implemented | H |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit_and_match "SL-3c: severity set when v2_status != missing fails" 1 'SL-3c:.*set but v2_status' "$STRUCTURE" --dir "$TEST_DIR/integrations-sl3-set"

# --- SL-3b (empty): severity empty but v2_status is "missing" ---
mkdir -p "$TEST_DIR/integrations-sl3-empty"
write_integrations_inventory "$TEST_DIR/integrations-sl3-empty/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-sl3-empty/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-sl3-empty/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Bad row | Vendor | Trigger | outbound; sync | [/quickbooks/](v1-pages-inventory.md#quickbooks_integration) | Sees: thing. | missing |  |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit_and_match "SL-3b: severity empty when v2_status=missing fails" 1 'SL-3b:.*severity is empty' "$STRUCTURE" --dir "$TEST_DIR/integrations-sl3-empty"

# --- SL-3a (bad-token): invalid severity token in {H, M, L, D} set ---
mkdir -p "$TEST_DIR/integrations-sl3-bad-token"
write_integrations_inventory "$TEST_DIR/integrations-sl3-bad-token/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-sl3-bad-token/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-sl3-bad-token/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Bad row | Vendor | Trigger | outbound; sync | [/quickbooks/](v1-pages-inventory.md#quickbooks_integration) | Sees: thing. | missing | X |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit_and_match "SL-3a: invalid severity token fails" 1 'SL-3a:.*not in \{H, M, L, D' "$STRUCTURE" --dir "$TEST_DIR/integrations-sl3-bad-token"

# --- SL-3a (lowercase): regex is case-sensitive — 'h' rejected ---
mkdir -p "$TEST_DIR/integrations-sl3-lowercase"
write_integrations_inventory "$TEST_DIR/integrations-sl3-lowercase/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-sl3-lowercase/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-sl3-lowercase/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Bad row | Vendor | Trigger | outbound; sync | [/quickbooks/](v1-pages-inventory.md#quickbooks_integration) | Sees: thing. | missing | h |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit_and_match "SL-3a: lowercase severity token fails (case-sensitive regex)" 1 'SL-3a:.*not in \{H, M, L, D' "$STRUCTURE" --dir "$TEST_DIR/integrations-sl3-lowercase"

# --- SL-3a (padded): trim() runs before regex — abnormal trailing whitespace accepted ---
# The data row's severity cell has TWO spaces between 'H' and the closing '|' — extra,
# non-standard whitespace. trim() at scripts/check-v1-doc-structure.sh:320 strips it
# before the regex check, so the row passes. Removing trim() would flip this to fail.
# Editor whitespace-stripping should leave this alone (interior, between non-whitespace
# tokens). If this fixture starts failing, first verify the second space survived.
mkdir -p "$TEST_DIR/integrations-sl3-padded"
write_integrations_inventory "$TEST_DIR/integrations-sl3-padded/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-sl3-padded/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-sl3-padded/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Bad row | Vendor | Trigger | outbound; sync | [/quickbooks/](v1-pages-inventory.md#quickbooks_integration) | Sees: thing. | missing | H  |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit "SL-3a: trailing-space severity token passes (trim-then-validate)" 0 "$STRUCTURE" --dir "$TEST_DIR/integrations-sl3-padded"

# --- SL-4: invalid direction_and_sync token ---
mkdir -p "$TEST_DIR/integrations-sl4"
write_integrations_inventory "$TEST_DIR/integrations-sl4/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-sl4/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-sl4/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Bad row | Vendor | Trigger | both ways | [/quickbooks/](v1-pages-inventory.md#quickbooks_integration) | Sees: thing. | missing | H |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit_and_match "SL-4: invalid direction_and_sync fails" 1 'SL-4:' "$STRUCTURE" --dir "$TEST_DIR/integrations-sl4"

# --- EL-1: surfaces_at_routes points at a non-existent inventory anchor ---
mkdir -p "$TEST_DIR/integrations-el1"
write_integrations_inventory "$TEST_DIR/integrations-el1/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-el1/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-el1/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Bad row | Vendor | Trigger | outbound; sync | [/foo/](v1-pages-inventory.md#nonexistent-anchor) | Sees: thing. | missing | H |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit "EL-1: anchor not in inventory fails" 1 "$STRUCTURE" --dir "$TEST_DIR/integrations-el1"

# --- EL-2a: surfaces_at_routes empty (cell has no content) ---
mkdir -p "$TEST_DIR/integrations-el2a"
write_integrations_inventory "$TEST_DIR/integrations-el2a/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-el2a/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-el2a/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Bad row | Vendor | Trigger | outbound; sync |  | Sees: thing. | missing | H |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit_and_match "EL-2a: empty surfaces_at_routes fails" 1 'EL-2a:.*surfaces_at_routes is empty' "$STRUCTURE" --dir "$TEST_DIR/integrations-el2a"

# --- EL-2b: surfaces_at_routes non-empty but has no inventory link and no marker ---
# Cell content is a plain prose phrase — no `(v1-pages-inventory.md#...)` link
# and no `_no UI surface_` marker. Exercises the third branch of EL-2's
# decision tree at scripts/check-v1-doc-structure.sh:397-399.
mkdir -p "$TEST_DIR/integrations-el2b"
write_integrations_inventory "$TEST_DIR/integrations-el2b/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-el2b/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-el2b/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Bad row | Vendor | Trigger | outbound; sync | see the dashboard somewhere | Sees: thing. | missing | H |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit_and_match "EL-2b: surfaces with no link and no marker fails" 1 'EL-2b:.*no inventory link and no' "$STRUCTURE" --dir "$TEST_DIR/integrations-el2b"

# --- EL-2 positive: "_no UI surface_" marker is allowed ---
mkdir -p "$TEST_DIR/integrations-el2-marker"
write_integrations_inventory "$TEST_DIR/integrations-el2-marker/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-el2-marker/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-el2-marker/v1-integrations-and-exports.md" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments
### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Sentry | Sentry | Uncaught exception | outbound; async | _no UI surface — operator-only_ | Sees: nothing. | missing | L |

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit "EL-2: '_no UI surface_' marker passes" 0 "$STRUCTURE" --dir "$TEST_DIR/integrations-el2-marker"

# =====================================================================
# v1-user-journeys.md checks (#104)
# =====================================================================

# Inventory fixture used by every journey test below: minimal but with
# H3 anchors for journeys to cite, plus an explicit <a id> case.
write_journeys_inventory() {
  local path="$1"
  cat > "$path" <<'EOF'
# v1 Pages Inventory

## Super-Admin

<a id="super-admin-top-level"></a>
### top-level (elitecare/urls.py)

## Agency Admin

### dashboard
### employees
### auth_service

## Care Manager

### care_manager

## Caregiver

### caregiver_dashboard

### charting

<a id="caregiver-charting"></a>

## Client

<a id="client-section"></a>

## Family Member

### dashboard

## Shared routes

EOF
}

# Helper: write an AUTHORED journeys doc that satisfies all checks.
write_good_journeys() {
  local path="$1"
  cat > "$path" <<'EOF'
# V1 User Journeys

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

## Super-Admin

### Journey 1
A Super-Admin manages.

**Route trace:**
1. [a](v1-pages-inventory.md#super-admin-top-level) — does thing.

**Side effects:**
- DB: writes a row.

### Journey 2
A Super-Admin investigates.

**Route trace:**
1. [a](v1-pages-inventory.md#super-admin-top-level) — does thing.

**Side effects:**
- DB: writes a row.

## Agency Admin

### J1
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#dashboard) — x.

**Side effects:**
- DB: y.

### J2
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#dashboard) — x.

**Side effects:**
- DB: y.

### J3
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#dashboard) — x.

**Side effects:**
- DB: y.

### J4
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#dashboard) — x.

**Side effects:**
- DB: y.

### J5
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#employees) — x.

**Side effects:**
- DB: y.

## Care Manager

### J1
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#care_manager) — x.

**Side effects:**
- DB: y.

### J2
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#care_manager) — x.

**Side effects:**
- DB: y.

## Caregiver

### J1
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#caregiver_dashboard) — x.

**Side effects:**
- DB: y.

### J2
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#caregiver-charting) — x.

**Side effects:**
- DB: y.

### J3
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#caregiver_dashboard) — x.

**Side effects:**
- DB: y.

### J4
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#caregiver_dashboard) — x.

**Side effects:**
- DB: y.

## Client

### J1
v1 has no Client-as-actor surface — see [the Client section](v1-pages-inventory.md#client-section).

**Route trace:**
1. v1 has no Client-authenticated route for this journey.

**Side effects:**
- DB: n/a — no Client-authenticated v1 surface.

### J2
v1 has no Client-as-actor surface — see [the Client section](v1-pages-inventory.md#client-section).

**Route trace:**
1. v1 has no Client-authenticated route for this journey.

**Side effects:**
- DB: n/a — no Client-authenticated v1 surface.

## Family Member

### J1
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#family-member) — x.

**Side effects:**
- DB: y.

### J2
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#family-member) — x.

**Side effects:**
- DB: y.

### J3
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#family-member) — x.

**Side effects:**
- DB: y.
EOF
}

echo ""
echo "-- v1-user-journeys.md (#104) --"

# --- Pass: SCAFFOLDED status skips block-level gates ---
mkdir -p "$TEST_DIR/journeys-scaffolded"
write_good_inventory "$TEST_DIR/journeys-scaffolded/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/journeys-scaffolded/v1-functionality-delta.md"
cat > "$TEST_DIR/journeys-scaffolded/v1-user-journeys.md" <<'EOF'
# V1 User Journeys

**Status:** SCAFFOLDED.

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client
## Family Member
EOF
assert_exit "JL: SCAFFOLDED status skips JL-3..JL-6, passes" 0 "$STRUCTURE" --dir "$TEST_DIR/journeys-scaffolded"

# --- Pass: fully AUTHORED journeys ---
mkdir -p "$TEST_DIR/journeys-good"
write_journeys_inventory "$TEST_DIR/journeys-good/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/journeys-good/v1-functionality-delta.md"
write_good_journeys "$TEST_DIR/journeys-good/v1-user-journeys.md"
assert_exit "JL: AUTHORED journeys with all checks satisfied passes" 0 "$STRUCTURE" --dir "$TEST_DIR/journeys-good"

# --- JL-1: missing status line ---
mkdir -p "$TEST_DIR/jl1-missing"
write_good_inventory "$TEST_DIR/jl1-missing/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl1-missing/v1-functionality-delta.md"
cat > "$TEST_DIR/jl1-missing/v1-user-journeys.md" <<'EOF'
# V1 User Journeys

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client
## Family Member
EOF
assert_exit "JL-1: missing **Status:** header fails" 1 "$STRUCTURE" --dir "$TEST_DIR/jl1-missing"

# --- JL-1: malformed status line ---
mkdir -p "$TEST_DIR/jl1-bad"
write_good_inventory "$TEST_DIR/jl1-bad/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl1-bad/v1-functionality-delta.md"
cat > "$TEST_DIR/jl1-bad/v1-user-journeys.md" <<'EOF'
# V1 User Journeys

**Status:** AUTHORED maybe.

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client
## Family Member
EOF
assert_exit "JL-1: malformed **Status:** header fails" 1 "$STRUCTURE" --dir "$TEST_DIR/jl1-bad"

# --- JL-2: missing persona H2 ---
mkdir -p "$TEST_DIR/jl2-missing"
write_good_inventory "$TEST_DIR/jl2-missing/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl2-missing/v1-functionality-delta.md"
cat > "$TEST_DIR/jl2-missing/v1-user-journeys.md" <<'EOF'
# V1 User Journeys

**Status:** SCAFFOLDED.

## Super-Admin
## Agency Admin
## Care Manager
## Caregiver
## Client
EOF
assert_exit "JL-2: missing 'Family Member' H2 fails" 1 "$STRUCTURE" --dir "$TEST_DIR/jl2-missing"

# --- JL-3: under-min journey count ---
mkdir -p "$TEST_DIR/jl3"
write_journeys_inventory "$TEST_DIR/jl3/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl3/v1-functionality-delta.md"
write_good_journeys "$TEST_DIR/jl3/v1-user-journeys.md"
# Drop one Caregiver H3 — make it 3, below the min of 4.
# Use sed to remove one specific H3 block.
python3 - "$TEST_DIR/jl3/v1-user-journeys.md" <<'PY'
import sys, re, pathlib
p = pathlib.Path(sys.argv[1])
text = p.read_text()
# Remove the J4 block under Caregiver (between "### J4" under Caregiver and the next ### or ##).
# Caregiver has J1..J4 in our fixture. Find the second ### J4 occurrence (Caregiver only has one J4).
text = re.sub(r"### J4\nLead\.\n\n\*\*Route trace:\*\*\n1\. \[a\]\(v1-pages-inventory\.md#caregiver_dashboard\) — x\.\n\n\*\*Side effects:\*\*\n- DB: y\.\n\n", "", text, count=1)
p.write_text(text)
PY
assert_exit "JL-3: Caregiver below min (3<4) fails" 1 "$STRUCTURE" --dir "$TEST_DIR/jl3"

# --- JL-4: pending placeholder still present ---
mkdir -p "$TEST_DIR/jl4"
write_journeys_inventory "$TEST_DIR/jl4/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl4/v1-functionality-delta.md"
write_good_journeys "$TEST_DIR/jl4/v1-user-journeys.md"
# Inject placeholder.
python3 - "$TEST_DIR/jl4/v1-user-journeys.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
p.write_text(p.read_text().replace("Lead.", "_pending content authoring_", 1))
PY
assert_exit "JL-4: '_pending content authoring_' placeholder fails" 1 "$STRUCTURE" --dir "$TEST_DIR/jl4"

# --- JL-5: Failure-mode UX None filler ---
mkdir -p "$TEST_DIR/jl5"
write_journeys_inventory "$TEST_DIR/jl5/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl5/v1-functionality-delta.md"
write_good_journeys "$TEST_DIR/jl5/v1-user-journeys.md"
python3 - "$TEST_DIR/jl5/v1-user-journeys.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
p.write_text(p.read_text() + "\n**Failure-mode UX:** None\n")
PY
assert_exit "JL-5: '**Failure-mode UX:** None' filler fails" 1 "$STRUCTURE" --dir "$TEST_DIR/jl5"

# --- JL-6: missing Route trace ---
mkdir -p "$TEST_DIR/jl6-route"
write_journeys_inventory "$TEST_DIR/jl6-route/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl6-route/v1-functionality-delta.md"
write_good_journeys "$TEST_DIR/jl6-route/v1-user-journeys.md"
python3 - "$TEST_DIR/jl6-route/v1-user-journeys.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
# Strip the **Route trace:** line from the first journey only.
text = p.read_text()
text = text.replace("**Route trace:**\n1. [a](v1-pages-inventory.md#super-admin-top-level) — does thing.\n\n", "", 1)
p.write_text(text)
PY
assert_exit "JL-6: missing **Route trace:** sub-block fails" 1 "$STRUCTURE" --dir "$TEST_DIR/jl6-route"

# --- JL-6: missing Side effects ---
mkdir -p "$TEST_DIR/jl6-side"
write_journeys_inventory "$TEST_DIR/jl6-side/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl6-side/v1-functionality-delta.md"
write_good_journeys "$TEST_DIR/jl6-side/v1-user-journeys.md"
python3 - "$TEST_DIR/jl6-side/v1-user-journeys.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
text = p.read_text()
text = text.replace("**Side effects:**\n- DB: writes a row.\n", "", 1)
p.write_text(text)
PY
assert_exit "JL-6: missing **Side effects:** sub-block fails" 1 "$STRUCTURE" --dir "$TEST_DIR/jl6-side"

# --- JL-7: bad anchor ---
mkdir -p "$TEST_DIR/jl7"
write_journeys_inventory "$TEST_DIR/jl7/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl7/v1-functionality-delta.md"
write_good_journeys "$TEST_DIR/jl7/v1-user-journeys.md"
python3 - "$TEST_DIR/jl7/v1-user-journeys.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
text = p.read_text()
text = text.replace("v1-pages-inventory.md#super-admin-top-level", "v1-pages-inventory.md#nonexistent-anchor", 1)
p.write_text(text)
PY
assert_exit "JL-7: orphan inventory anchor fails" 1 "$STRUCTURE" --dir "$TEST_DIR/jl7"

# --- JL-7: orphan absolute GitHub URL anchor fails ---
mkdir -p "$TEST_DIR/jl7-abs-orphan"
write_journeys_inventory "$TEST_DIR/jl7-abs-orphan/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl7-abs-orphan/v1-functionality-delta.md"
write_good_journeys "$TEST_DIR/jl7-abs-orphan/v1-user-journeys.md"
python3 - "$TEST_DIR/jl7-abs-orphan/v1-user-journeys.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
text = p.read_text()
text = text.replace(
    "(v1-pages-inventory.md#super-admin-top-level)",
    "(https://github.com/suniljames/COREcare-v2/blob/main/docs/migration/v1-pages-inventory.md#nonexistent-anchor)",
    1,
)
p.write_text(text)
PY
assert_exit "JL-7: orphan absolute-URL anchor fails" 1 "$STRUCTURE" --dir "$TEST_DIR/jl7-abs-orphan"

# --- JL-7: valid absolute GitHub URL anchor passes ---
mkdir -p "$TEST_DIR/jl7-abs-valid"
write_journeys_inventory "$TEST_DIR/jl7-abs-valid/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl7-abs-valid/v1-functionality-delta.md"
write_good_journeys "$TEST_DIR/jl7-abs-valid/v1-user-journeys.md"
python3 - "$TEST_DIR/jl7-abs-valid/v1-user-journeys.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
text = p.read_text()
text = text.replace(
    "(v1-pages-inventory.md#super-admin-top-level)",
    "(https://github.com/suniljames/COREcare-v2/blob/main/docs/migration/v1-pages-inventory.md#super-admin-top-level)",
    1,
)
p.write_text(text)
PY
assert_exit "JL-7: valid absolute-URL anchor passes" 0 "$STRUCTURE" --dir "$TEST_DIR/jl7-abs-valid"

# --- JL-7: orphan ../blob/<branch> anchor fails ---
mkdir -p "$TEST_DIR/jl7-blob-orphan"
write_journeys_inventory "$TEST_DIR/jl7-blob-orphan/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl7-blob-orphan/v1-functionality-delta.md"
write_good_journeys "$TEST_DIR/jl7-blob-orphan/v1-user-journeys.md"
python3 - "$TEST_DIR/jl7-blob-orphan/v1-user-journeys.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
text = p.read_text()
text = text.replace(
    "(v1-pages-inventory.md#super-admin-top-level)",
    "(../blob/main/docs/migration/v1-pages-inventory.md#nonexistent-anchor)",
    1,
)
p.write_text(text)
PY
assert_exit "JL-7: orphan ../blob/<branch> anchor fails" 1 "$STRUCTURE" --dir "$TEST_DIR/jl7-blob-orphan"

# --- JL-7: valid ../blob/<branch> anchor passes ---
mkdir -p "$TEST_DIR/jl7-blob-valid"
write_journeys_inventory "$TEST_DIR/jl7-blob-valid/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/jl7-blob-valid/v1-functionality-delta.md"
write_good_journeys "$TEST_DIR/jl7-blob-valid/v1-user-journeys.md"
python3 - "$TEST_DIR/jl7-blob-valid/v1-user-journeys.md" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
text = p.read_text()
text = text.replace(
    "(v1-pages-inventory.md#super-admin-top-level)",
    "(../blob/main/docs/migration/v1-pages-inventory.md#super-admin-top-level)",
    1,
)
p.write_text(text)
PY
assert_exit "JL-7: valid ../blob/<branch> anchor passes" 0 "$STRUCTURE" --dir "$TEST_DIR/jl7-blob-valid"

# =====================================================================
# v1-glossary.md checks (#105)
# =====================================================================
#
# GL-1: status header form — "**Status:** SCAFFOLDED" prefix gates block-level
#       checks off; "**Status:** AUTHORED. Last reconciled: YYYY-MM-DD against
#       v1 commit `<sha>`." (exact form) gates them on; missing or malformed
#       fails. Mirrors JL-1.
# GL-2: when AUTHORED, no placeholder/pending markers remain — `_(pending)_`,
#       `_(definitions pending)_`, `_(definitions pending content authoring;`,
#       `_(pending content authoring)_`. Anything that announces itself as
#       not-yet-authored.
# GL-3: every link from the glossary to v1-pages-inventory.md#anchor,
#       v1-user-journeys.md#anchor, or v1-integrations-and-exports.md#anchor
#       resolves against an existing heading or explicit <a id> in the target
#       doc. Always-on, mirrors JL-7. The integrations doc is permitted as a
#       link target only when present; absent, glossary links into it must
#       not exist (the glossary cannot point at a doc the docset omits).

write_glossary_inventory() {
  local path="$1"
  cat > "$path" <<'EOF'
# v1 Pages Inventory

## Super-Admin

<a id="super-admin-top-level"></a>
### top-level (elitecare/urls.py)

## Agency Admin

### dashboard
### employees
### auth_service
### billing
### charting
### clients

## Care Manager

### care_manager

## Caregiver

### caregiver_dashboard

## Client

<a id="client-section"></a>

## Family Member

### dashboard

## Shared routes

EOF
}

write_glossary_journeys() {
  local path="$1"
  cat > "$path" <<'EOF'
# V1 User Journeys

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

## Super-Admin

### View-As impersonation with audit trail
A Super-Admin starts a View-As session.

**Route trace:**
1. [a](v1-pages-inventory.md#super-admin-top-level) — does thing.

**Side effects:**
- DB: writes a row.

### Agency management — capability administration and View-As kill switch
A Super-Admin manages.

**Route trace:**
1. [a](v1-pages-inventory.md#super-admin-top-level) — does thing.

**Side effects:**
- DB: writes a row.

## Agency Admin

### J1
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#dashboard) — x.

**Side effects:**
- DB: y.

### J2
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#dashboard) — x.

**Side effects:**
- DB: y.

### J3
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#dashboard) — x.

**Side effects:**
- DB: y.

### J4
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#dashboard) — x.

**Side effects:**
- DB: y.

### J5
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#employees) — x.

**Side effects:**
- DB: y.

## Care Manager

### Team oversight — caseload action queue and field-expense submission
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#care_manager) — x.

**Side effects:**
- DB: y.

### J2
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#care_manager) — x.

**Side effects:**
- DB: y.

## Caregiver

### J1
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#caregiver_dashboard) — x.

**Side effects:**
- DB: y.

### J2
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#caregiver_dashboard) — x.

**Side effects:**
- DB: y.

### J3
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#caregiver_dashboard) — x.

**Side effects:**
- DB: y.

### J4
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#caregiver_dashboard) — x.

**Side effects:**
- DB: y.

## Client

### J1
v1 has no Client-as-actor surface — see [the Client section](v1-pages-inventory.md#client-section).

**Route trace:**
1. v1 has no Client-authenticated route for this journey.

**Side effects:**
- DB: n/a — no Client-authenticated v1 surface.

### J2
v1 has no Client-as-actor surface — see [the Client section](v1-pages-inventory.md#client-section).

**Route trace:**
1. v1 has no Client-authenticated route for this journey.

**Side effects:**
- DB: n/a — no Client-authenticated v1 surface.

## Family Member

### J1
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#family-member) — x.

**Side effects:**
- DB: y.

### J2
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#family-member) — x.

**Side effects:**
- DB: y.

### J3
Lead.

**Route trace:**
1. [a](v1-pages-inventory.md#family-member) — x.

**Side effects:**
- DB: y.
EOF
}

# A glossary-shaped integrations doc the script's existing CL/SL/EL checks
# also tolerate — minimal entries, valid schema; only used as a link target
# for GL-3 anchor resolution.
write_glossary_integrations() {
  local path="$1"
  cat > "$path" <<EOF
# V1 Integrations and Exports

## Schema

table.

## External integrations

### Billing and payments

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| QuickBooks Online | Intuit | OAuth | outbound; sync | _no UI surface — operator-only_ | Sees: nothing. | missing | H |

### Payroll
### Accounting
### Messaging and notifications (third-party)

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Magic-link login email | internal | User submits form | outbound; sync | _no UI surface — operator-only_ | Sees: link in inbox. | missing | D |

### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

### Email pipeline

$INTEGRATIONS_HEADER
$INTEGRATIONS_SEP
| Overpayment consent request | internal | Recovery initiated | outbound; sync | _no UI surface — operator-only_ | Sees: consent link. | missing | H |

## Customer-facing exports

## Cross-references
EOF
}

write_authored_glossary() {
  local path="$1"
  cat > "$path" <<'EOF'
# V1 Glossary

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

## Entries

- **`elitecare`** — v1 Django project root. See [the Agency Admin top-level routes](v1-pages-inventory.md#dashboard).
- **`MagicLinkToken`** — v1 model. See [the magic-link login email entry](v1-integrations-and-exports.md#email-pipeline).
- **View-As impersonation** — v1 platform-operator surface. See [the View-As journey](v1-user-journeys.md#view-as-impersonation-with-audit-trail).
EOF
}

echo ""
echo "-- v1-glossary.md (#105) --"

# --- Pass: SCAFFOLDED status skips block-level gates ---
mkdir -p "$TEST_DIR/glossary-scaffolded"
write_glossary_inventory "$TEST_DIR/glossary-scaffolded/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/glossary-scaffolded/v1-functionality-delta.md"
cat > "$TEST_DIR/glossary-scaffolded/v1-glossary.md" <<'EOF'
# V1 Glossary

**Status:** SCAFFOLDED. Entries are pending authoring.

## Pending entries

- **`elitecare`** — pending.

_(definitions pending content authoring; each will resolve to one-line text + first-use link)_
EOF
assert_exit "GL: SCAFFOLDED status skips GL-2, passes" 0 "$STRUCTURE" --dir "$TEST_DIR/glossary-scaffolded"

# --- Pass: fully AUTHORED glossary ---
mkdir -p "$TEST_DIR/glossary-good"
write_glossary_inventory "$TEST_DIR/glossary-good/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/glossary-good/v1-functionality-delta.md"
write_glossary_journeys "$TEST_DIR/glossary-good/v1-user-journeys.md"
write_glossary_integrations "$TEST_DIR/glossary-good/v1-integrations-and-exports.md"
write_authored_glossary "$TEST_DIR/glossary-good/v1-glossary.md"
assert_exit "GL: AUTHORED glossary with all checks satisfied passes" 0 "$STRUCTURE" --dir "$TEST_DIR/glossary-good"

# --- GL-1: missing status line ---
mkdir -p "$TEST_DIR/gl1-missing"
write_glossary_inventory "$TEST_DIR/gl1-missing/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/gl1-missing/v1-functionality-delta.md"
cat > "$TEST_DIR/gl1-missing/v1-glossary.md" <<'EOF'
# V1 Glossary

## Entries

- **`elitecare`** — v1 Django project root.
EOF
assert_exit "GL-1: missing **Status:** header fails" 1 "$STRUCTURE" --dir "$TEST_DIR/gl1-missing"

# --- GL-1: malformed status line ---
mkdir -p "$TEST_DIR/gl1-bad"
write_glossary_inventory "$TEST_DIR/gl1-bad/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/gl1-bad/v1-functionality-delta.md"
cat > "$TEST_DIR/gl1-bad/v1-glossary.md" <<'EOF'
# V1 Glossary

**Status:** AUTHORED maybe.

## Entries

- **`elitecare`** — v1 Django project root.
EOF
assert_exit "GL-1: malformed **Status:** header fails" 1 "$STRUCTURE" --dir "$TEST_DIR/gl1-bad"

# --- GL-2: AUTHORED with `_(pending)_` marker fails ---
mkdir -p "$TEST_DIR/gl2-pending"
write_glossary_inventory "$TEST_DIR/gl2-pending/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/gl2-pending/v1-functionality-delta.md"
write_glossary_journeys "$TEST_DIR/gl2-pending/v1-user-journeys.md"
write_glossary_integrations "$TEST_DIR/gl2-pending/v1-integrations-and-exports.md"
cat > "$TEST_DIR/gl2-pending/v1-glossary.md" <<'EOF'
# V1 Glossary

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

## Entries

- **`elitecare`** — v1 Django project root.

## Cross-cutting v1 conventions

_(pending)_
EOF
assert_exit "GL-2: AUTHORED with '_(pending)_' marker fails" 1 "$STRUCTURE" --dir "$TEST_DIR/gl2-pending"

# --- GL-2: AUTHORED with `_(definitions pending)_` marker fails ---
mkdir -p "$TEST_DIR/gl2-defs-pending"
write_glossary_inventory "$TEST_DIR/gl2-defs-pending/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/gl2-defs-pending/v1-functionality-delta.md"
write_glossary_journeys "$TEST_DIR/gl2-defs-pending/v1-user-journeys.md"
write_glossary_integrations "$TEST_DIR/gl2-defs-pending/v1-integrations-and-exports.md"
cat > "$TEST_DIR/gl2-defs-pending/v1-glossary.md" <<'EOF'
# V1 Glossary

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

## Entries

- **`elitecare`** — v1 Django project root.

_(definitions pending content authoring; each will resolve to one-line text + first-use link)_
EOF
assert_exit "GL-2: AUTHORED with '_(definitions pending)_' marker fails" 1 "$STRUCTURE" --dir "$TEST_DIR/gl2-defs-pending"

# --- GL-2: AUTHORED with `_(definitions pending content authoring` substring fails ---
# Note the substring shape — script's pattern array deliberately matches the
# scaffold suffix without requiring a closing `_`, so any partial-author
# placeholder of this shape is caught.
mkdir -p "$TEST_DIR/gl2-defs-authoring-substr"
write_glossary_inventory "$TEST_DIR/gl2-defs-authoring-substr/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/gl2-defs-authoring-substr/v1-functionality-delta.md"
write_glossary_journeys "$TEST_DIR/gl2-defs-authoring-substr/v1-user-journeys.md"
write_glossary_integrations "$TEST_DIR/gl2-defs-authoring-substr/v1-integrations-and-exports.md"
cat > "$TEST_DIR/gl2-defs-authoring-substr/v1-glossary.md" <<'EOF'
# V1 Glossary

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

## Entries

- **`elitecare`** — v1 Django project root.

_(definitions pending content authoring; partial draft)_
EOF
assert_exit "GL-2: AUTHORED with '_(definitions pending content authoring' substring fails" 1 "$STRUCTURE" --dir "$TEST_DIR/gl2-defs-authoring-substr"

# --- GL-2: AUTHORED with `_(pending content authoring)_` marker fails ---
mkdir -p "$TEST_DIR/gl2-pending-authoring"
write_glossary_inventory "$TEST_DIR/gl2-pending-authoring/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/gl2-pending-authoring/v1-functionality-delta.md"
write_glossary_journeys "$TEST_DIR/gl2-pending-authoring/v1-user-journeys.md"
write_glossary_integrations "$TEST_DIR/gl2-pending-authoring/v1-integrations-and-exports.md"
cat > "$TEST_DIR/gl2-pending-authoring/v1-glossary.md" <<'EOF'
# V1 Glossary

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

## Entries

- **`elitecare`** — v1 Django project root.

## Cross-cutting v1 conventions

_(pending content authoring)_
EOF
assert_exit "GL-2: AUTHORED with '_(pending content authoring)_' marker fails" 1 "$STRUCTURE" --dir "$TEST_DIR/gl2-pending-authoring"

# --- GL-3a: AUTHORED with link to nonexistent inventory anchor fails ---
mkdir -p "$TEST_DIR/gl3-bad-inventory"
write_glossary_inventory "$TEST_DIR/gl3-bad-inventory/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/gl3-bad-inventory/v1-functionality-delta.md"
write_glossary_journeys "$TEST_DIR/gl3-bad-inventory/v1-user-journeys.md"
write_glossary_integrations "$TEST_DIR/gl3-bad-inventory/v1-integrations-and-exports.md"
cat > "$TEST_DIR/gl3-bad-inventory/v1-glossary.md" <<'EOF'
# V1 Glossary

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

## Entries

- **`elitecare`** — v1 Django project root. See [a section](v1-pages-inventory.md#nonexistent-anchor).
EOF
assert_exit_and_match "GL-3a: orphan inventory anchor fails" 1 'GL-3a:.*not found in v1-pages-inventory' "$STRUCTURE" --dir "$TEST_DIR/gl3-bad-inventory"

# --- GL-3b: AUTHORED with link to nonexistent journeys anchor fails ---
mkdir -p "$TEST_DIR/gl3-bad-journeys"
write_glossary_inventory "$TEST_DIR/gl3-bad-journeys/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/gl3-bad-journeys/v1-functionality-delta.md"
write_glossary_journeys "$TEST_DIR/gl3-bad-journeys/v1-user-journeys.md"
write_glossary_integrations "$TEST_DIR/gl3-bad-journeys/v1-integrations-and-exports.md"
cat > "$TEST_DIR/gl3-bad-journeys/v1-glossary.md" <<'EOF'
# V1 Glossary

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

## Entries

- **View-As impersonation** — v1 platform-operator surface. See [the View-As journey](v1-user-journeys.md#nonexistent-journey).
EOF
assert_exit_and_match "GL-3b: orphan journeys anchor fails" 1 'GL-3b:.*not found in v1-user-journeys' "$STRUCTURE" --dir "$TEST_DIR/gl3-bad-journeys"

# --- GL-3c: AUTHORED with link to nonexistent integrations anchor fails ---
mkdir -p "$TEST_DIR/gl3-bad-integrations"
write_glossary_inventory "$TEST_DIR/gl3-bad-integrations/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/gl3-bad-integrations/v1-functionality-delta.md"
write_glossary_journeys "$TEST_DIR/gl3-bad-integrations/v1-user-journeys.md"
write_glossary_integrations "$TEST_DIR/gl3-bad-integrations/v1-integrations-and-exports.md"
cat > "$TEST_DIR/gl3-bad-integrations/v1-glossary.md" <<'EOF'
# V1 Glossary

**Status:** AUTHORED. Last reconciled: 2026-05-07 against v1 commit `9738412`.

## Entries

- **`MagicLinkToken`** — v1 model. See [the magic-link login email entry](v1-integrations-and-exports.md#nonexistent-section).
EOF
assert_exit_and_match "GL-3c: orphan integrations anchor fails" 1 'GL-3c:.*not found in v1-integrations-and-exports' "$STRUCTURE" --dir "$TEST_DIR/gl3-bad-integrations"

# --- GL-3 positive: AUTHORED with valid anchors across all three docs passes ---
# (Already covered by glossary-good above; listed for symmetry.)
mkdir -p "$TEST_DIR/gl3-all-good"
write_glossary_inventory "$TEST_DIR/gl3-all-good/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/gl3-all-good/v1-functionality-delta.md"
write_glossary_journeys "$TEST_DIR/gl3-all-good/v1-user-journeys.md"
write_glossary_integrations "$TEST_DIR/gl3-all-good/v1-integrations-and-exports.md"
write_authored_glossary "$TEST_DIR/gl3-all-good/v1-glossary.md"
assert_exit "GL-3 valid anchors across inventory + journeys + integrations passes" 0 "$STRUCTURE" --dir "$TEST_DIR/gl3-all-good"

# =============================================================================
# Cross-reference index phi_displayed consistency tests (#124)
# CR-1: route at index not found at linked anchor (or no anchor link in row location)
# CR-2: route slug duplicated under linked anchor (canonical lookup ambiguous)
# CR-3: phi_displayed value disagreement between index row and canonical row
# CR-4: phi_displayed value outside {true, false} on either side
#
# Trigger: only when the cross-reference-index table header contains BOTH
# `phi_displayed` and `row location` columns (header-intersection rule).
# =============================================================================

# Helper: write a six-persona inventory with a Super-Admin cross-reference index
# linking to an Agency-Admin canonical row. Both phi_displayed values are
# parameterized so each test case can flip them independently.
write_xref_inventory() {
  local path="$1"
  local canon_phi="$2"
  local index_phi="$3"
  cat > "$path" <<EOF
# v1 Pages Inventory

## Super-Admin

### Cross-reference index

| route | also reachable by | content branches by role | phi_displayed | row location |
|-------|-------------------|--------------------------|---------------|--------------|
| \`/admin/expenses/review/\` | Agency Admin | no | $index_phi | [Agency Admin → top-level](#agency-admin-top-level) |

## Agency Admin

<a id="agency-admin-top-level"></a>
### top-level

| route | phi_displayed |
|-------|---------------|
| \`/admin/expenses/review/\` | $canon_phi |

## Care Manager

## Caregiver

## Client

## Family Member
EOF
}

echo ""
echo "== cross-reference index phi_displayed consistency tests (#124) =="

# --- Test 1: index value matches canonical → pass ---
mkdir -p "$TEST_DIR/xref-match"
write_xref_inventory "$TEST_DIR/xref-match/v1-pages-inventory.md" "true" "true"
write_good_delta "$TEST_DIR/xref-match/v1-functionality-delta.md"
assert_exit "CR-3: index phi_displayed matches canonical → pass" 0 "$STRUCTURE" --dir "$TEST_DIR/xref-match"

# --- Test 2: index says false, canonical says true → CR-3 fail ---
mkdir -p "$TEST_DIR/xref-mismatch-false-true"
write_xref_inventory "$TEST_DIR/xref-mismatch-false-true/v1-pages-inventory.md" "true" "false"
write_good_delta "$TEST_DIR/xref-mismatch-false-true/v1-functionality-delta.md"
assert_exit "CR-3: index 'false' vs canonical 'true' fails" 1 "$STRUCTURE" --dir "$TEST_DIR/xref-mismatch-false-true"

# --- Test 3: index says true, canonical says false → CR-3 fail (symmetric) ---
mkdir -p "$TEST_DIR/xref-mismatch-true-false"
write_xref_inventory "$TEST_DIR/xref-mismatch-true-false/v1-pages-inventory.md" "false" "true"
write_good_delta "$TEST_DIR/xref-mismatch-true-false/v1-functionality-delta.md"
assert_exit "CR-3: index 'true' vs canonical 'false' fails (symmetric)" 1 "$STRUCTURE" --dir "$TEST_DIR/xref-mismatch-true-false"

# --- Test 4: cross-reference index without phi_displayed column → pass (no-op) ---
# The Shared routes shape: header is `| route | persona | row location |`. Header
# intersection with canonical-row header excludes phi_displayed entirely, so the
# rule must not fire even though anchors and routes match.
mkdir -p "$TEST_DIR/xref-no-phi-col"
cat > "$TEST_DIR/xref-no-phi-col/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin

## Agency Admin

<a id="agency-admin-top-level"></a>
### top-level

| route | phi_displayed |
|-------|---------------|
| `/admin/expenses/review/` | true |

## Care Manager

## Caregiver

## Client

## Family Member

## Shared routes

### Cross-reference index

| route | primary persona | row location |
|-------|-----------------|--------------|
| `/admin/expenses/review/` | Agency Admin | [Agency Admin → top-level](#agency-admin-top-level) |
EOF
write_good_delta "$TEST_DIR/xref-no-phi-col/v1-functionality-delta.md"
assert_exit "header-intersection: index without phi_displayed column → no-op pass" 0 "$STRUCTURE" --dir "$TEST_DIR/xref-no-phi-col"

# --- Test 5: anchor in row location does not exist in inventory → CR-1b fail ---
mkdir -p "$TEST_DIR/xref-bad-anchor"
cat > "$TEST_DIR/xref-bad-anchor/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin

### Cross-reference index

| route | also reachable by | content branches by role | phi_displayed | row location |
|-------|-------------------|--------------------------|---------------|--------------|
| `/admin/expenses/review/` | Agency Admin | no | true | [Agency Admin → top-level](#nonexistent-anchor) |

## Agency Admin

<a id="agency-admin-top-level"></a>
### top-level

| route | phi_displayed |
|-------|---------------|
| `/admin/expenses/review/` | true |

## Care Manager

## Caregiver

## Client

## Family Member
EOF
write_good_delta "$TEST_DIR/xref-bad-anchor/v1-functionality-delta.md"
assert_exit_and_match "CR-1b: anchor in row location does not exist fails" 1 'CR-1b:.*not found at anchor' "$STRUCTURE" --dir "$TEST_DIR/xref-bad-anchor"

# --- Test 6: route slug duplicated under linked anchor → CR-2 fail ---
mkdir -p "$TEST_DIR/xref-dup-canonical"
cat > "$TEST_DIR/xref-dup-canonical/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin

### Cross-reference index

| route | also reachable by | content branches by role | phi_displayed | row location |
|-------|-------------------|--------------------------|---------------|--------------|
| `/admin/foo/` | Agency Admin | no | true | [Agency Admin → top-level](#agency-admin-top-level) |

## Agency Admin

<a id="agency-admin-top-level"></a>
### top-level

| route | phi_displayed |
|-------|---------------|
| `/admin/foo/` | true |
| `/admin/foo/` | false |

## Care Manager

## Caregiver

## Client

## Family Member
EOF
write_good_delta "$TEST_DIR/xref-dup-canonical/v1-functionality-delta.md"
assert_exit "CR-2: duplicate canonical row under anchor fails" 1 "$STRUCTURE" --dir "$TEST_DIR/xref-dup-canonical"

# --- Test 7: route slug not present at the linked anchor → CR-1b fail ---
mkdir -p "$TEST_DIR/xref-missing-route"
cat > "$TEST_DIR/xref-missing-route/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin

### Cross-reference index

| route | also reachable by | content branches by role | phi_displayed | row location |
|-------|-------------------|--------------------------|---------------|--------------|
| `/admin/expenses/review/` | Agency Admin | no | true | [Agency Admin → top-level](#agency-admin-top-level) |

## Agency Admin

<a id="agency-admin-top-level"></a>
### top-level

| route | phi_displayed |
|-------|---------------|
| `/admin/some-other-route/` | true |

## Care Manager

## Caregiver

## Client

## Family Member
EOF
write_good_delta "$TEST_DIR/xref-missing-route/v1-functionality-delta.md"
assert_exit_and_match "CR-1b: route slug not at linked anchor fails" 1 'CR-1b:.*not found at anchor' "$STRUCTURE" --dir "$TEST_DIR/xref-missing-route"

# --- Test 7a: row location cell has NO anchor link (plain prose) → CR-1a fail ---
# Per issue #196, the no-anchor-link branch at scripts/check-v1-doc-structure.sh:893
# was previously unfixtured — both Test 5 and Test 7 above exercise the
# "anchor present but not found" branch (line 899). This fixture's row location
# cell is plain prose with no `(#anchor)` markup, exercising the first emit.
mkdir -p "$TEST_DIR/xref-no-anchor-link"
cat > "$TEST_DIR/xref-no-anchor-link/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin

### Cross-reference index

| route | also reachable by | content branches by role | phi_displayed | row location |
|-------|-------------------|--------------------------|---------------|--------------|
| `/admin/expenses/review/` | Agency Admin | no | true | Agency Admin → top-level (no link) |

## Agency Admin

<a id="agency-admin-top-level"></a>
### top-level

| route | phi_displayed |
|-------|---------------|
| `/admin/expenses/review/` | true |

## Care Manager

## Caregiver

## Client

## Family Member
EOF
write_good_delta "$TEST_DIR/xref-no-anchor-link/v1-functionality-delta.md"
assert_exit_and_match "CR-1a: row location cell has no anchor link fails" 1 'CR-1a:.*has no anchor link in row location cell' "$STRUCTURE" --dir "$TEST_DIR/xref-no-anchor-link"

# --- Test 8: index cell has 'yes' instead of 'true' → CR-4 fail ---
mkdir -p "$TEST_DIR/xref-vocab-index"
write_xref_inventory "$TEST_DIR/xref-vocab-index/v1-pages-inventory.md" "true" "yes"
write_good_delta "$TEST_DIR/xref-vocab-index/v1-functionality-delta.md"
assert_exit "CR-4: index phi_displayed='yes' (not in {true,false}) fails" 1 "$STRUCTURE" --dir "$TEST_DIR/xref-vocab-index"

# --- Test 9: canonical cell empty → CR-4 fail ---
mkdir -p "$TEST_DIR/xref-vocab-canonical"
write_xref_inventory "$TEST_DIR/xref-vocab-canonical/v1-pages-inventory.md" "" "true"
write_good_delta "$TEST_DIR/xref-vocab-canonical/v1-functionality-delta.md"
assert_exit "CR-4: canonical phi_displayed='' (not in {true,false}) fails" 1 "$STRUCTURE" --dir "$TEST_DIR/xref-vocab-canonical"

# --- Test 10: GFM-derived anchor (no explicit <a id>) → pass ---
mkdir -p "$TEST_DIR/xref-gfm-anchor"
cat > "$TEST_DIR/xref-gfm-anchor/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin

### Cross-reference index

| route | also reachable by | content branches by role | phi_displayed | row location |
|-------|-------------------|--------------------------|---------------|--------------|
| `/admin/expenses/review/` | Agency Admin | no | true | [Agency Admin → top level](#some-section) |

## Agency Admin

### Some Section

| route | phi_displayed |
|-------|---------------|
| `/admin/expenses/review/` | true |

## Care Manager

## Caregiver

## Client

## Family Member
EOF
write_good_delta "$TEST_DIR/xref-gfm-anchor/v1-functionality-delta.md"
assert_exit "GFM-derived anchor resolution → pass" 0 "$STRUCTURE" --dir "$TEST_DIR/xref-gfm-anchor"

# --- Test 11: explicit <a id> anchor used in link → pass (canonical row resolves
#              via explicit anchor even though the heading text would also yield
#              its own GFM anchor) ---
mkdir -p "$TEST_DIR/xref-explicit-anchor"
cat > "$TEST_DIR/xref-explicit-anchor/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin

### Cross-reference index

| route | also reachable by | content branches by role | phi_displayed | row location |
|-------|-------------------|--------------------------|---------------|--------------|
| `/admin/expenses/review/` | Agency Admin | no | true | [Agency Admin → top-level](#agency-admin-top-level) |

## Agency Admin

<a id="agency-admin-top-level"></a>
### top-level

| route | phi_displayed |
|-------|---------------|
| `/admin/expenses/review/` | true |

## Care Manager

## Caregiver

## Client

## Family Member
EOF
write_good_delta "$TEST_DIR/xref-explicit-anchor/v1-functionality-delta.md"
assert_exit "explicit <a id> anchor resolution → pass" 0 "$STRUCTURE" --dir "$TEST_DIR/xref-explicit-anchor"

# --- Test 12: two cross-reference index sub-sections, only the second has a
#              CR-3 violation → fail (guards against early-exit bug). ---
mkdir -p "$TEST_DIR/xref-two-indexes"
cat > "$TEST_DIR/xref-two-indexes/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin

### Cross-reference index

| route | also reachable by | content branches by role | phi_displayed | row location |
|-------|-------------------|--------------------------|---------------|--------------|
| `/admin/expenses/review/` | Agency Admin | no | true | [Agency Admin → top-level](#agency-admin-top-level) |

## Agency Admin

<a id="agency-admin-top-level"></a>
### top-level

| route | phi_displayed |
|-------|---------------|
| `/admin/expenses/review/` | true |
| `/charting/proxy/<int:visit_id>/` | true |

## Care Manager

## Caregiver

## Client

## Family Member

## Shared routes

### Cross-reference index

| route | also reachable by | content branches by role | phi_displayed | row location |
|-------|-------------------|--------------------------|---------------|--------------|
| `/charting/proxy/<int:visit_id>/` | Care Manager | no | false | [Agency Admin → top-level](#agency-admin-top-level) |
EOF
write_good_delta "$TEST_DIR/xref-two-indexes/v1-functionality-delta.md"
assert_exit "two cross-ref indexes; second has CR-3 violation → fail" 1 "$STRUCTURE" --dir "$TEST_DIR/xref-two-indexes"

# --- Test 13: pass-1 xref-skip is load-bearing — explicit `<a id>` anchor
#              aliasing pre-binds an xref-index sub-section to the same
#              anchor as a canonical persona section. With the skip, only
#              the canonical row lands in the pass-1 map, so pass 2 emits
#              CR-3 (phi disagreement). WITHOUT the skip, both rows would
#              hit the same key, triggering CANONICAL_DUP → CR-2 instead.
#              Exit-code-only assertion would not distinguish the two —
#              hence the rule-code match in `assert_exit_and_match`. ---
mkdir -p "$TEST_DIR/xref-anchor-alias-skip"
cat > "$TEST_DIR/xref-anchor-alias-skip/v1-pages-inventory.md" <<'EOF'
# v1 Pages Inventory

## Super-Admin

<a id="agency-admin-top-level"></a>
### Cross-reference index

| route | also reachable by | content branches by role | phi_displayed | row location |
|-------|-------------------|--------------------------|---------------|--------------|
| `/admin/foo/` | Agency Admin | no | false | [Agency Admin → top-level](#agency-admin-top-level) |

## Agency Admin

<a id="agency-admin-top-level"></a>
### top-level

| route | phi_displayed |
|-------|---------------|
| `/admin/foo/` | true |

## Care Manager

## Caregiver

## Client

## Family Member
EOF
write_good_delta "$TEST_DIR/xref-anchor-alias-skip/v1-functionality-delta.md"
assert_exit_and_match \
  "CR-3 (not CR-2) fires when xref index aliases canonical anchor — pass 1 skip is load-bearing" \
  1 'CR-3:' \
  "$STRUCTURE" --dir "$TEST_DIR/xref-anchor-alias-skip"

# === Refresh-runbook rule group (RR-N) — Issue #132 =========================
#
# RR-1 — `## Refresh runbook` H2 exists in README.md.
# RR-2 — `### Refresh order — Agency Admin first` H3 exists, placed inside
#        the Refresh runbook section.
# RR-3 — Each `### <Persona> section …` H3 (persona from REQUIRED_PERSONAS) is
#        placed inside the Refresh runbook section.
# RR-4a — Each persona-section override body contains `V1 Reference Commit`.
# RR-4b — Each persona-section override body contains
#         `Baseline at the currently-pinned SHA:`.
# RR-4c — Each persona-section override body contains BOTH
#         `If any diff is non-empty:` AND `If all diffs are empty:`.
# RR-4d — Each persona-section override body contains the literal `'*/urls.py'`
#         AND ≥3 distinct `git diff <old>..<new> -- ` invocations.
# RR-5 — Every `(#<anchor>)` link in README.md resolves to a heading in the
#        same README.

write_good_readme() {
  local path="$1"
  cat > "$path" <<'EOF'
# v1 Reference Set

## Refresh runbook

When v1 receives material changes, refresh this docset against the new SHA.

### Family Member section — extra diff checks before re-authoring

Family Member is the lowest-frequency persona surface. Run these checks every time the `V1 Reference Commit` above is bumped.

In your local v1 checkout, against the previously-pinned SHA:

- `git diff <old>..<new> -- '*/urls.py'` — surfaces new family-prefixed routes.
- `git diff <old>..<new> -- clients/` — surfaces permission-gating changes.
- `git diff <old>..<new> -- clients/models.py` — surfaces schema shifts.

Baseline at the currently-pinned SHA: `ClientFamilyMember` has no `is_active`.

If any diff is non-empty: re-author affected rows. If all diffs are empty: still bump `last reconciled`.

### Refresh order — Agency Admin first

Agency Admin is the most-iterated persona surface. Refresh first.

See [Family Member section](#family-member-section--extra-diff-checks-before-re-authoring) above.

## Workflow secrets

Closing section.
EOF
}

# --- RR pass case: good README + good inventory + good delta → pass ---
mkdir -p "$TEST_DIR/rr-good"
write_good_inventory "$TEST_DIR/rr-good/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-good/v1-functionality-delta.md"
write_good_readme    "$TEST_DIR/rr-good/README.md"
assert_exit "RR: good README passes" 0 "$STRUCTURE" --dir "$TEST_DIR/rr-good"

# --- RR-1: missing `## Refresh runbook` H2 → fail ---
mkdir -p "$TEST_DIR/rr-1-missing-runbook"
write_good_inventory "$TEST_DIR/rr-1-missing-runbook/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-1-missing-runbook/v1-functionality-delta.md"
write_good_readme    "$TEST_DIR/rr-1-missing-runbook/README.md"
# Demote the Refresh runbook H2 to a paragraph mention.
sed -i.bak 's|^## Refresh runbook$|Refresh runbook is described below.|' "$TEST_DIR/rr-1-missing-runbook/README.md"
rm -f "$TEST_DIR/rr-1-missing-runbook/README.md.bak"
assert_exit "RR-1: missing '## Refresh runbook' H2 fails" 1 "$STRUCTURE" --dir "$TEST_DIR/rr-1-missing-runbook"

# --- RR-2: missing `### Refresh order — Agency Admin first` H3 → fail ---
mkdir -p "$TEST_DIR/rr-2-missing-h3"
write_good_inventory "$TEST_DIR/rr-2-missing-h3/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-2-missing-h3/v1-functionality-delta.md"
write_good_readme    "$TEST_DIR/rr-2-missing-h3/README.md"
# Remove the Agency-Admin-first H3 line (and its body paragraph).
sed -i.bak '/^### Refresh order — Agency Admin first$/,/^Agency Admin is the most-iterated/d' "$TEST_DIR/rr-2-missing-h3/README.md"
rm -f "$TEST_DIR/rr-2-missing-h3/README.md.bak"
assert_exit "RR-2: missing '### Refresh order — Agency Admin first' H3 fails" 1 "$STRUCTURE" --dir "$TEST_DIR/rr-2-missing-h3"

# --- RR-2 placement: Agency-Admin-first H3 placed AFTER `## Workflow secrets` (out of section) → fail ---
mkdir -p "$TEST_DIR/rr-2-placement"
write_good_inventory "$TEST_DIR/rr-2-placement/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-2-placement/v1-functionality-delta.md"
cat > "$TEST_DIR/rr-2-placement/README.md" <<'EOF'
# v1 Reference Set

## Refresh runbook

### Family Member section — extra diff checks before re-authoring

Family Member is the lowest-frequency persona surface. Run these checks every time the `V1 Reference Commit` above is bumped.

- `git diff <old>..<new> -- '*/urls.py'` — surfaces new family-prefixed routes.
- `git diff <old>..<new> -- clients/` — surfaces permission-gating changes.
- `git diff <old>..<new> -- clients/models.py` — surfaces schema shifts.

Baseline at the currently-pinned SHA: `ClientFamilyMember` has no `is_active`.

If any diff is non-empty: re-author. If all diffs are empty: still bump `last reconciled`.

## Workflow secrets

### Refresh order — Agency Admin first

Agency Admin is the most-iterated persona surface.
EOF
assert_exit "RR-2 placement: H3 outside Refresh runbook section fails" 1 "$STRUCTURE" --dir "$TEST_DIR/rr-2-placement"

# --- RR-3 placement: persona-section H3 placed BEFORE `## Refresh runbook` → fail ---
mkdir -p "$TEST_DIR/rr-3-placement"
write_good_inventory "$TEST_DIR/rr-3-placement/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-3-placement/v1-functionality-delta.md"
cat > "$TEST_DIR/rr-3-placement/README.md" <<'EOF'
# v1 Reference Set

## Some other section

### Family Member section — extra diff checks before re-authoring

Family Member is the lowest-frequency persona surface. Run these checks every time the `V1 Reference Commit` above is bumped.

- `git diff <old>..<new> -- '*/urls.py'` — surfaces new family-prefixed routes.
- `git diff <old>..<new> -- clients/` — surfaces permission-gating changes.
- `git diff <old>..<new> -- clients/models.py` — surfaces schema shifts.

Baseline at the currently-pinned SHA: `ClientFamilyMember` has no `is_active`.

If any diff is non-empty: re-author. If all diffs are empty: still bump `last reconciled`.

## Refresh runbook

### Refresh order — Agency Admin first

Agency Admin is the most-iterated persona surface.

## Workflow secrets

Closing.
EOF
assert_exit "RR-3 placement: persona-section H3 outside Refresh runbook section fails" 1 "$STRUCTURE" --dir "$TEST_DIR/rr-3-placement"

# --- RR-3: persona-name typo (`Family Members section`) → fail ---
# Typo means the H3 won't match the locked persona regex AND there is no valid
# persona-section override H3 inside the runbook section. The structure script
# treats this as zero-overrides plus an unrecognized H3 in the section.
mkdir -p "$TEST_DIR/rr-3-typo"
write_good_inventory "$TEST_DIR/rr-3-typo/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-3-typo/v1-functionality-delta.md"
write_good_readme    "$TEST_DIR/rr-3-typo/README.md"
# Add a typo'd persona H3 (`Members` plural) inside the runbook section. Without
# the locked persona name, RR-3 must fail.
sed -i.bak 's|^### Family Member section — extra diff checks before re-authoring$|### Family Members section — extra diff checks before re-authoring|' "$TEST_DIR/rr-3-typo/README.md"
rm -f "$TEST_DIR/rr-3-typo/README.md.bak"
assert_exit "RR-3: persona-name typo ('Family Members' plural) fails" 1 "$STRUCTURE" --dir "$TEST_DIR/rr-3-typo"

# --- RR-4a: `V1 Reference Commit` literal removed → fail ---
mkdir -p "$TEST_DIR/rr-4a"
write_good_inventory "$TEST_DIR/rr-4a/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-4a/v1-functionality-delta.md"
write_good_readme    "$TEST_DIR/rr-4a/README.md"
sed -i.bak 's|`V1 Reference Commit`|the pinned commit|' "$TEST_DIR/rr-4a/README.md"
rm -f "$TEST_DIR/rr-4a/README.md.bak"
assert_exit "RR-4a: 'V1 Reference Commit' literal removed fails" 1 "$STRUCTURE" --dir "$TEST_DIR/rr-4a"

# --- RR-4b: `Baseline at the currently-pinned SHA:` literal removed → fail ---
mkdir -p "$TEST_DIR/rr-4b"
write_good_inventory "$TEST_DIR/rr-4b/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-4b/v1-functionality-delta.md"
write_good_readme    "$TEST_DIR/rr-4b/README.md"
sed -i.bak 's|Baseline at the currently-pinned SHA:|At the pinned SHA today:|' "$TEST_DIR/rr-4b/README.md"
rm -f "$TEST_DIR/rr-4b/README.md.bak"
assert_exit "RR-4b: 'Baseline at the currently-pinned SHA:' literal removed fails" 1 "$STRUCTURE" --dir "$TEST_DIR/rr-4b"

# --- RR-4c: only one of {non-empty, all-empty} branches present → fail ---
mkdir -p "$TEST_DIR/rr-4c"
write_good_inventory "$TEST_DIR/rr-4c/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-4c/v1-functionality-delta.md"
write_good_readme    "$TEST_DIR/rr-4c/README.md"
# Strip the empty-diff branch sentence — leaves only the non-empty branch.
sed -i.bak 's| If all diffs are empty: still bump `last reconciled`.||' "$TEST_DIR/rr-4c/README.md"
rm -f "$TEST_DIR/rr-4c/README.md.bak"
assert_exit "RR-4c: missing 'If all diffs are empty:' branch fails" 1 "$STRUCTURE" --dir "$TEST_DIR/rr-4c"

# --- RR-4d count: only 2 distinct `git diff` invocations → fail ---
mkdir -p "$TEST_DIR/rr-4d-count"
write_good_inventory "$TEST_DIR/rr-4d-count/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-4d-count/v1-functionality-delta.md"
write_good_readme    "$TEST_DIR/rr-4d-count/README.md"
# Remove the third `git diff … clients/models.py` line.
sed -i.bak '/`git diff <old>..<new> -- clients\/models.py`/d' "$TEST_DIR/rr-4d-count/README.md"
rm -f "$TEST_DIR/rr-4d-count/README.md.bak"
assert_exit "RR-4d count: only 2 git-diff invocations fails" 1 "$STRUCTURE" --dir "$TEST_DIR/rr-4d-count"

# --- RR-4d literal: `'*/urls.py'` narrowed to `'dashboard/urls.py'` → fail ---
mkdir -p "$TEST_DIR/rr-4d-literal"
write_good_inventory "$TEST_DIR/rr-4d-literal/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-4d-literal/v1-functionality-delta.md"
write_good_readme    "$TEST_DIR/rr-4d-literal/README.md"
sed -i.bak "s|'\\*/urls.py'|'dashboard/urls.py'|" "$TEST_DIR/rr-4d-literal/README.md"
rm -f "$TEST_DIR/rr-4d-literal/README.md.bak"
assert_exit "RR-4d literal: '*/urls.py' narrowed to 'dashboard/urls.py' fails" 1 "$STRUCTURE" --dir "$TEST_DIR/rr-4d-literal"

# --- RR-5: typo in anchor target inside README → fail ---
mkdir -p "$TEST_DIR/rr-5"
write_good_inventory "$TEST_DIR/rr-5/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/rr-5/v1-functionality-delta.md"
write_good_readme    "$TEST_DIR/rr-5/README.md"
# Break the (#…) link target so it no longer resolves to any heading.
sed -i.bak 's|(#family-member-section--extra-diff-checks-before-re-authoring)|(#family-mmber-section)|' "$TEST_DIR/rr-5/README.md"
rm -f "$TEST_DIR/rr-5/README.md.bak"
assert_exit "RR-5: orphan anchor link in README fails" 1 "$STRUCTURE" --dir "$TEST_DIR/rr-5"

# =============================================================================
# WF-1 — workflow path resolution. Issue #169.
#
# Every backticked reference in `docs/migration/README.md` matching the form
# `.github/workflows/<name>.yml` must point to a file that exists on disk.
# Resolution root is configurable via `--repo-root <path>` (default: CWD).
#
# Six fixture-driven cases per the issue's Test Specification:
#   1. Happy path — three real backticked refs all resolve, exit 0.
#   2. Single unresolved citation — exit 1, one WF-1 line.
#   3. Multiple distinct unresolved citations — both reported.
#   4. Same path cited twice, both unresolved — both cite-sites reported.
#   5. Non-backticked mention is ignored.
#   6. Out-of-scope path class is ignored.
# =============================================================================

write_wf1_readme() {
  # README skeleton that satisfies RR-1..RR-5 plus a WF-references block whose
  # contents the caller customizes by passing extra lines on stdin.
  local path="$1"
  local extra="$2"
  cat > "$path" <<EOF
# v1 Reference Set

## Refresh runbook

When v1 receives material changes, refresh this docset against the new SHA.

### Family Member section — extra diff checks before re-authoring

Family Member is the lowest-frequency persona surface. Run these checks every time the \`V1 Reference Commit\` above is bumped.

In your local v1 checkout, against the previously-pinned SHA:

- \`git diff <old>..<new> -- '*/urls.py'\` — surfaces new family-prefixed routes.
- \`git diff <old>..<new> -- clients/\` — surfaces permission-gating changes.
- \`git diff <old>..<new> -- clients/models.py\` — surfaces schema shifts.

Baseline at the currently-pinned SHA: \`ClientFamilyMember\` has no \`is_active\`.

If any diff is non-empty: re-author affected rows. If all diffs are empty: still bump \`last reconciled\`.

### Refresh order — Agency Admin first

Agency Admin is the most-iterated persona surface. Refresh first.

See [Family Member section](#family-member-section--extra-diff-checks-before-re-authoring) above.

## Workflow secrets

${extra}
EOF
}

# --- WF-1 happy path: three real backticked refs all resolve → pass ---
mkdir -p "$TEST_DIR/wf-good/.github/workflows"
touch "$TEST_DIR/wf-good/.github/workflows/v1-doc-hygiene.yml"
touch "$TEST_DIR/wf-good/.github/workflows/v1-sha-bump-diff-report.yml"
write_good_inventory "$TEST_DIR/wf-good/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/wf-good/v1-functionality-delta.md"
write_wf1_readme     "$TEST_DIR/wf-good/README.md" "$(cat <<'BLOCK'
CI workflow: `.github/workflows/v1-doc-hygiene.yml`. Runs on PRs.

CI posts diffs as a sticky PR comment — see `.github/workflows/v1-sha-bump-diff-report.yml`.

Used by `.github/workflows/v1-sha-bump-diff-report.yml` to clone v1.
BLOCK
)"
assert_exit "WF-1 happy path: three real backticked refs resolve" 0 "$STRUCTURE" --dir "$TEST_DIR/wf-good" --repo-root "$TEST_DIR/wf-good"

# --- WF-1 single unresolved citation → fail ---
mkdir -p "$TEST_DIR/wf-1-single/.github/workflows"
write_good_inventory "$TEST_DIR/wf-1-single/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/wf-1-single/v1-functionality-delta.md"
write_wf1_readme     "$TEST_DIR/wf-1-single/README.md" "$(cat <<'BLOCK'
See `.github/workflows/does-not-exist.yml`.
BLOCK
)"
assert_exit "WF-1 single unresolved: missing workflow path fails" 1 "$STRUCTURE" --dir "$TEST_DIR/wf-1-single" --repo-root "$TEST_DIR/wf-1-single"

# Confirm the WF-1 message names the missing path with file:line: prefix.
assert_output_contains() {
  local description="$1"
  local needle="$2"
  shift 2
  local actual_output
  actual_output=$("$@" 2>&1) || true
  if echo "$actual_output" | grep -qF "$needle"; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description"
    echo "    needle: $needle"
    echo "    output: $actual_output"
    FAIL=$((FAIL + 1))
  fi
}
assert_output_contains "WF-1 single unresolved: error message names the missing path" \
  "WF-1: workflow path '.github/workflows/does-not-exist.yml' not found on disk" \
  "$STRUCTURE" --dir "$TEST_DIR/wf-1-single" --repo-root "$TEST_DIR/wf-1-single"

# --- WF-1 multiple distinct unresolved citations → fail; both reported ---
mkdir -p "$TEST_DIR/wf-1-multi/.github/workflows"
write_good_inventory "$TEST_DIR/wf-1-multi/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/wf-1-multi/v1-functionality-delta.md"
write_wf1_readme     "$TEST_DIR/wf-1-multi/README.md" "$(cat <<'BLOCK'
See `.github/workflows/missing-one.yml`.

Also see `.github/workflows/missing-two.yml`.
BLOCK
)"
assert_exit "WF-1 multi: two distinct missing workflow paths fail" 1 "$STRUCTURE" --dir "$TEST_DIR/wf-1-multi" --repo-root "$TEST_DIR/wf-1-multi"
assert_output_contains "WF-1 multi: first missing path reported" \
  "WF-1: workflow path '.github/workflows/missing-one.yml' not found on disk" \
  "$STRUCTURE" --dir "$TEST_DIR/wf-1-multi" --repo-root "$TEST_DIR/wf-1-multi"
assert_output_contains "WF-1 multi: second missing path reported" \
  "WF-1: workflow path '.github/workflows/missing-two.yml' not found on disk" \
  "$STRUCTURE" --dir "$TEST_DIR/wf-1-multi" --repo-root "$TEST_DIR/wf-1-multi"

# --- WF-1 same path cited twice, both unresolved → both cite-sites reported (no dedup) ---
mkdir -p "$TEST_DIR/wf-1-dup/.github/workflows"
write_good_inventory "$TEST_DIR/wf-1-dup/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/wf-1-dup/v1-functionality-delta.md"
write_wf1_readme     "$TEST_DIR/wf-1-dup/README.md" "$(cat <<'BLOCK'
See `.github/workflows/v1-sha-bump-diff-report.yml`.

Used by `.github/workflows/v1-sha-bump-diff-report.yml` to clone v1.
BLOCK
)"
# Run the script once and capture output; assert two distinct line-number cites
# of the same missing workflow file appear.
DUP_OUT=$("$STRUCTURE" --dir "$TEST_DIR/wf-1-dup" --repo-root "$TEST_DIR/wf-1-dup" 2>&1 || true)
DUP_HITS=$(echo "$DUP_OUT" | grep -cF "WF-1: workflow path '.github/workflows/v1-sha-bump-diff-report.yml' not found on disk")
if [[ "$DUP_HITS" == 2 ]]; then
  echo "  PASS — WF-1 dup: same missing path on two lines yields two violations (no dedup)"
  PASS=$((PASS + 1))
else
  echo "  FAIL — WF-1 dup: expected 2 violations for repeated path, got $DUP_HITS"
  echo "    output: $DUP_OUT"
  FAIL=$((FAIL + 1))
fi

# --- WF-1 non-backticked mention is ignored → pass ---
mkdir -p "$TEST_DIR/wf-1-prose/.github/workflows"
write_good_inventory "$TEST_DIR/wf-1-prose/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/wf-1-prose/v1-functionality-delta.md"
write_wf1_readme     "$TEST_DIR/wf-1-prose/README.md" "$(cat <<'BLOCK'
Plain prose mention .github/workflows/foo.yml lives somewhere.

[link form](.github/workflows/foo.yml) is also out of scope.

<!-- HTML comment with .github/workflows/foo.yml -->
BLOCK
)"
assert_exit "WF-1 prose: non-backticked mentions of missing workflow are ignored" 0 "$STRUCTURE" --dir "$TEST_DIR/wf-1-prose" --repo-root "$TEST_DIR/wf-1-prose"

# --- WF-1 out-of-scope path class is ignored → pass ---
# Backticked references to scripts/*.sh — even missing ones — must not trip WF-1.
mkdir -p "$TEST_DIR/wf-1-scope/.github/workflows"
write_good_inventory "$TEST_DIR/wf-1-scope/v1-pages-inventory.md"
write_good_delta     "$TEST_DIR/wf-1-scope/v1-functionality-delta.md"
write_wf1_readme     "$TEST_DIR/wf-1-scope/README.md" "$(cat <<'BLOCK'
See `scripts/check-v1-doc-hygiene.sh` (real, exists upstream — but irrelevant to WF-1).

Also see `scripts/does-not-exist.sh`.
BLOCK
)"
assert_exit "WF-1 scope: backticked non-workflow paths are ignored" 0 "$STRUCTURE" --dir "$TEST_DIR/wf-1-scope" --repo-root "$TEST_DIR/wf-1-scope"

# --- Test 13: smoke-check against the actual repo inventory → pass (no false positives) ---
# This guarantees the new check does not regress against current main content.
# Locate the repo's docs/migration relative to the test file; bail with a skip
# if it isn't present (in case the test is run in a degraded checkout).
REPO_DOCS="$REPO_ROOT/docs/migration"
if [[ -f "$REPO_DOCS/v1-pages-inventory.md" && -f "$REPO_DOCS/v1-functionality-delta.md" ]]; then
  assert_exit "smoke: real docs/migration content passes (no false positives)" 0 "$STRUCTURE" --dir "$REPO_DOCS" --repo-root "$REPO_ROOT"
else
  echo "  SKIP — real docs/migration not found at $REPO_DOCS; smoke test skipped."
fi

# ============================================================================
# Coverage parity meta-test (MT-1) — Issue #173
# ============================================================================
# Asserts that for every coverage-code prefix in scripts/check-v1-doc-structure.sh,
# the set of distinct codes referenced by the structure script equals the set of
# distinct codes asserted by this test file's fixtures.
#
# Prefixes covered (in the order they appear in the structure script's header):
#   CL  (#98)        H2/H3 lock for v1-integrations-and-exports.md
#   SL  (#98)        entry-table column order and per-cell token validity
#   EL  (#98)        surfaces_at_routes inventory link resolution
#   JL  (#104, #134) v1-user-journeys.md structure + anchor resolution
#   GL  (#105)       v1-glossary.md structure + cross-doc anchor resolution
#   CR  (#124)       cross-reference index ↔ canonical row consistency
#   RR  (#132)       ## Refresh runbook invariants
#   WF  (#169)       .github/workflows/*.yml path resolution from README
#
# Refactor sensitivity:
#   The src-side regex matches `[A-Z]{2}-[0-9]+[a-z]*` anywhere in the structure
#   script (comments and emit lines). The test-side regex matches the same
#   pattern at the start of `assert_exit` / `assert_exit_and_match` description
#   strings. If either source is restructured — emit lines move into a helper,
#   a new assertion helper lands, the prefix scheme grows beyond two letters —
#   these regexes must be updated in lockstep.
#
# Granularity (per-emit-branch — issue #196):
#   Parity is asserted at the *per-emit-branch* level. Any code with ≥2 emit
#   branches is sub-lettered in the awk (SL-1a / SL-1b, SL-3a / SL-3b / SL-3c,
#   EL-2a / EL-2b, CR-1a / CR-1b, GL-3a / GL-3b / GL-3c, RR-4a / RR-4b / RR-4c
#   / RR-4d). The cohort-wide convention is documented at the SL-* convention
#   comment near line 577. MT-2 (below) enforces the canonical code shape
#   `^[A-Z]{2}-[0-9]+[a-z]?$` so a future contributor who introduces a
#   non-canonical reference (SL-1.1, SL_1a, SL-1ab) trips a hard error rather
#   than a silent miss.
#
# Umbrella codes (e.g., RR-4, SL-1) are filtered out by `_filter_umbrellas`
# when sub-letter codes (RR-4a..d, SL-1a..b) exist for the same prefix-and-
# number. Header doc-blocks and prose comments may mention umbrella codes for
# discoverability ("the SL-1 family checks the entry-table shape"); the filter
# keeps those references from polluting parity.
#
# See: https://github.com/suniljames/COREcare-v2/issues/196 (per-branch parity),
#      https://github.com/suniljames/COREcare-v2/issues/173 (distinct-code parity, predecessor),
#      https://github.com/suniljames/COREcare-v2/issues/128 (architectural source).

_extract_source_codes() {
  # Distinct two-letter-prefix codes referenced anywhere in the source script.
  grep -hoE '[A-Z]{2}-[0-9]+[a-z]*' "$1" | sort -u
}

_extract_test_codes() {
  # Distinct codes referenced as the leading token of assert_exit* descriptions.
  grep -oE 'assert_exit(_and_match)?[[:space:]]+"[A-Z]{2}-[0-9]+[a-z]*' "$1" \
    | grep -oE '[A-Z]{2}-[0-9]+[a-z]*' | sort -u
}

_filter_umbrellas() {
  # Drop "X-N" when "X-N<letter>" exists in the same set.
  local codes="$1"
  local out=""
  while IFS= read -r code; do
    [[ -z "$code" ]] && continue
    if [[ "$code" =~ ^([A-Z]+-[0-9]+)$ ]]; then
      local base="${BASH_REMATCH[1]}"
      if echo "$codes" | grep -qE "^${base}[a-z]\$"; then
        continue
      fi
    fi
    out+="${code}"$'\n'
  done <<< "$codes"
  printf '%s' "$out"
}

_compute_coverage_parity() {
  # stdout: full failure message on mismatch, empty on parity. Exit 1 on mismatch.
  local awk_path="$1"
  local test_path="$2"
  local src_codes test_codes
  src_codes=$(_filter_umbrellas "$(_extract_source_codes "$awk_path")")
  test_codes=$(_filter_umbrellas "$(_extract_test_codes "$test_path")")

  local prefixes
  prefixes=$(printf '%s\n%s\n' "$src_codes" "$test_codes" | grep -oE '^[A-Z]{2}' | sort -u)

  local violations=""
  local prefix
  while IFS= read -r prefix; do
    [[ -z "$prefix" ]] && continue
    local src_prefix test_prefix src_only test_only
    src_prefix=$(echo "$src_codes" | grep -E "^${prefix}-" || true)
    test_prefix=$(echo "$test_codes" | grep -E "^${prefix}-" || true)
    src_only=$(comm -23 <(echo "$src_prefix") <(echo "$test_prefix") | grep -v '^$' | tr '\n' ' ' | sed 's/ $//')
    test_only=$(comm -13 <(echo "$src_prefix") <(echo "$test_prefix") | grep -v '^$' | tr '\n' ' ' | sed 's/ $//')
    if [[ -n "$src_only" || -n "$test_only" ]]; then
      [[ -z "$src_only" ]]  && src_only="(none)"
      [[ -z "$test_only" ]] && test_only="(none)"
      violations+="  ${prefix}: codes in awk only: ${src_only}"$'\n'
      violations+="      codes in tests only: ${test_only}"$'\n'
    fi
  done <<< "$prefixes"

  if [[ -n "$violations" ]]; then
    echo "coverage parity (MT-1)"
    echo "  awk:   $awk_path"
    echo "  tests: $test_path"
    printf '%s' "$violations"
    return 1
  fi
  return 0
}

assert_coverage_parity() {
  # Args: <description> <awk_path> <test_path> <expected_exit> [<expected_pattern>]
  local description="$1"
  local awk_path="$2"
  local test_path="$3"
  local expected_exit="$4"
  local expected_pattern="${5:-}"
  local out rc
  out=$(_compute_coverage_parity "$awk_path" "$test_path" 2>&1)
  rc=$?
  local pattern_ok=1
  if [[ -n "$expected_pattern" ]] && ! [[ "$out" =~ $expected_pattern ]]; then
    pattern_ok=0
  fi
  if [[ "$rc" == "$expected_exit" && "$pattern_ok" == 1 ]]; then
    echo "  PASS — $description (exit $rc)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description (expected exit $expected_exit${expected_pattern:+ matching /$expected_pattern/}, got exit $rc)"
    echo "    output: $out"
    FAIL=$((FAIL + 1))
  fi
}

# A. Real-state — every coverage code in the structure script has a fixture and vice versa.
assert_coverage_parity \
  "MT-1: real-state coverage parity holds" \
  "$STRUCTURE" \
  "$REPO_ROOT/scripts/tests/test_check_v1_doc_structure.sh" \
  0

# B. Self-test — synthesized awk-side gap (all SL-3 references stripped) is detected.
# `sed '/SL-3/d'` removes every SL-3 mention (emit lines, dedicated comment
# lines, AND the multi-code header at line 285). This works because:
# 1. _extract_source_codes is a line-anywhere grep that picks up codes from
#    comments AND emit lines indistinguishably — so for the gap to register,
#    BOTH must go.
# 2. The line-285 multi-code header (`# SL-1, SL-2, SL-3, SL-4 ...`) gets
#    removed too, but SL-1/SL-2/SL-4 each have their own dedicated emit and
#    comment lines elsewhere; they survive.
#
# A future refactor that consolidates ALL code mentions onto fewer multi-code
# comment lines could mask gaps. Two options when that becomes a real concern:
# (a) tighten this sed to emit-line-only AND tighten _extract_source_codes
#     to match (handles 3 emit styles in the structure script — awk-print,
#     fail-with-code-suffix, fail-without-code), or (b) construct the
#     synthesized fixture from scratch instead of stripping. Either is a
#     bigger lift than this self-test warrants today.
mkdir -p "$TEST_DIR/mt-1-awk-gap"
sed '/SL-3/d' "$STRUCTURE" > "$TEST_DIR/mt-1-awk-gap/check.sh"
assert_coverage_parity \
  "MT-1 self-test: awk-side gap (SL-3 stripped) is detected as orphan fixture" \
  "$TEST_DIR/mt-1-awk-gap/check.sh" \
  "$REPO_ROOT/scripts/tests/test_check_v1_doc_structure.sh" \
  1 \
  "codes in tests only: SL-3"

# C. Self-test — synthesized test-side gap (SL-2 fixture stripped) is detected.
mkdir -p "$TEST_DIR/mt-1-test-gap"
sed '/assert_exit.*"SL-2/d' "$REPO_ROOT/scripts/tests/test_check_v1_doc_structure.sh" > "$TEST_DIR/mt-1-test-gap/test.sh"
assert_coverage_parity \
  "MT-1 self-test: test-side gap (SL-2 fixture stripped) is detected as uncovered awk branch" \
  "$STRUCTURE" \
  "$TEST_DIR/mt-1-test-gap/test.sh" \
  1 \
  "codes in awk only: SL-2"

# D. Self-test — synthesized awk-side per-branch gap (SL-1b stripped) is detected.
# Strips every line containing "SL-1b" from a copy of the awk; tests still
# reference SL-1b as a fixture description token. MT-1 must report the
# branch-level gap. This guards the per-branch parity contract from #196:
# without sub-letters, this gap would be invisible to MT-1.
mkdir -p "$TEST_DIR/mt-1-sl1b-gap"
sed '/SL-1b/d' "$STRUCTURE" > "$TEST_DIR/mt-1-sl1b-gap/check.sh"
assert_coverage_parity \
  "MT-1 self-test: per-branch gap (SL-1b stripped) is detected as orphan fixture" \
  "$TEST_DIR/mt-1-sl1b-gap/check.sh" \
  "$REPO_ROOT/scripts/tests/test_check_v1_doc_structure.sh" \
  1 \
  "codes in tests only: SL-1b"

# ============================================================================
# Code-shape lint (MT-2) — Issue #196
# ============================================================================
# Asserts that every code reference in scripts/check-v1-doc-structure.sh
# matches the canonical regex `^[A-Z]{2}-[0-9]+[a-z]?$`. Hard trip-wire on
# labeling drift: SL-1.1, SL_1a, SL-1ab all fail.
#
# Detection regex `[A-Z]{2}[-_][0-9]+[A-Za-z0-9_]*` is broader than canonical
# so it captures plausible drift forms. Period is excluded from the trailing
# class so prose punctuation ("CR-3.") doesn't false-positive.

_assert_canonical_code_shape() {
  local file="$1"
  local non_canonical
  non_canonical=$(grep -hoE '[A-Z]{2}[-_][0-9]+[A-Za-z0-9_]*' "$file" \
                   | grep -vE '^[A-Z]{2}-[0-9]+[a-z]?$' \
                   | sort -u || true)
  if [[ -n "$non_canonical" ]]; then
    echo "code-shape lint (MT-2)"
    echo "  file: $file"
    echo "  non-canonical code references (must match ^[A-Z]{2}-[0-9]+[a-z]?\$):"
    while IFS= read -r ref; do
      [[ -n "$ref" ]] && echo "    $ref"
    done <<< "$non_canonical"
    return 1
  fi
  return 0
}

assert_canonical_code_shape() {
  local description="$1"
  local file="$2"
  local out rc
  out=$(_assert_canonical_code_shape "$file" 2>&1)
  rc=$?
  if [[ "$rc" == 0 ]]; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description"
    echo "    output: $out"
    FAIL=$((FAIL + 1))
  fi
}

# E. Real-state — every code reference in the structure script is canonical-shape.
assert_canonical_code_shape \
  "MT-2: real-state code-shape lint holds" \
  "$STRUCTURE"

# F. Self-test — synthesized non-canonical reference is detected.
# Constructs a faux awk by appending a comment with a multi-letter sub-letter
# (intentionally broken — represents the drift form `SL-1ab` or similar).
mkdir -p "$TEST_DIR/mt-2-bad-shape"
{
  cat "$STRUCTURE"
  # Use a sentinel inside a literal multi-letter form. The exact string here
  # IS non-canonical by design — it's the regression we want MT-2 to catch.
  printf '# drift test: %s should fail the shape lint.\n' 'SL-1ab'
} > "$TEST_DIR/mt-2-bad-shape/check.sh"
mt2_out=$(_assert_canonical_code_shape "$TEST_DIR/mt-2-bad-shape/check.sh" 2>&1)
mt2_rc=$?
if [[ "$mt2_rc" == 1 && "$mt2_out" =~ SL-1ab ]]; then
  echo "  PASS — MT-2 self-test: non-canonical reference is detected"
  PASS=$((PASS + 1))
else
  echo "  FAIL — MT-2 self-test: expected exit 1 with non-canonical ref in output, got exit $mt2_rc"
  echo "    output: $mt2_out"
  FAIL=$((FAIL + 1))
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
