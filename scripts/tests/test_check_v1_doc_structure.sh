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

# --- SL-1: entry-table header column drift ---
mkdir -p "$TEST_DIR/integrations-sl1"
write_integrations_inventory "$TEST_DIR/integrations-sl1/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-sl1/v1-functionality-delta.md"
write_good_integrations "$TEST_DIR/integrations-sl1/v1-integrations-and-exports.md"
# Replace the locked header with a drifted one (e.g. swap order).
DRIFTED_HEADER='| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | severity | v2_status |'
sed -i.bak "s|^| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |\$|$DRIFTED_HEADER|" \
  "$TEST_DIR/integrations-sl1/v1-integrations-and-exports.md" 2>/dev/null || true
# More portable: rewrite via python-free in-place edit using awk.
awk -v drift="$DRIFTED_HEADER" '
  /^\| name \| vendor_or_internal \|/ && !done { print drift; done=1; next }
  { print }
' "$TEST_DIR/integrations-sl1/v1-integrations-and-exports.md" > "$TEST_DIR/integrations-sl1/_tmp" && \
  mv "$TEST_DIR/integrations-sl1/_tmp" "$TEST_DIR/integrations-sl1/v1-integrations-and-exports.md"
rm -f "$TEST_DIR/integrations-sl1/v1-integrations-and-exports.md.bak"
assert_exit "SL-1: drifted entry-table header fails" 1 "$STRUCTURE" --dir "$TEST_DIR/integrations-sl1"

# --- SL-2: invalid v2_status token ---
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
| Bad row | Vendor | Trigger | outbound; sync | [/quickbooks/](v1-pages-inventory.md#quickbooks_integration) | Sees: thing. | partial | H |

### Payroll
### Accounting
### Messaging and notifications (third-party)
### Identity, auth, and SSO (third-party)
### Other

## Internal notification and email backend

## Customer-facing exports

## Cross-references
EOF
assert_exit "SL-2: invalid v2_status token fails" 1 "$STRUCTURE" --dir "$TEST_DIR/integrations-sl2"

# --- SL-3 (set): severity set but v2_status is not "missing" ---
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
assert_exit "SL-3: severity set when v2_status != missing fails" 1 "$STRUCTURE" --dir "$TEST_DIR/integrations-sl3-set"

# --- SL-3 (empty): severity empty but v2_status is "missing" ---
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
assert_exit "SL-3: severity empty when v2_status=missing fails" 1 "$STRUCTURE" --dir "$TEST_DIR/integrations-sl3-empty"

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
assert_exit "SL-4: invalid direction_and_sync fails" 1 "$STRUCTURE" --dir "$TEST_DIR/integrations-sl4"

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

# --- EL-2: surfaces_at_routes empty (no link, no marker) ---
mkdir -p "$TEST_DIR/integrations-el2"
write_integrations_inventory "$TEST_DIR/integrations-el2/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-el2/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-el2/v1-integrations-and-exports.md" <<EOF
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
assert_exit "EL-2: empty surfaces_at_routes fails" 1 "$STRUCTURE" --dir "$TEST_DIR/integrations-el2"

# --- EL-2: "_no UI surface_" marker is allowed ---
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

# --- GL-3: AUTHORED with link to nonexistent inventory anchor fails ---
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
assert_exit "GL-3: orphan inventory anchor fails" 1 "$STRUCTURE" --dir "$TEST_DIR/gl3-bad-inventory"

# --- GL-3: AUTHORED with link to nonexistent journeys anchor fails ---
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
assert_exit "GL-3: orphan journeys anchor fails" 1 "$STRUCTURE" --dir "$TEST_DIR/gl3-bad-journeys"

# --- GL-3: AUTHORED with link to nonexistent integrations anchor fails ---
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
assert_exit "GL-3: orphan integrations anchor fails" 1 "$STRUCTURE" --dir "$TEST_DIR/gl3-bad-integrations"

# --- GL-3: AUTHORED with valid anchors across all three docs passes ---
# (Already covered by glossary-good above; listed for symmetry.)
mkdir -p "$TEST_DIR/gl3-all-good"
write_glossary_inventory "$TEST_DIR/gl3-all-good/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/gl3-all-good/v1-functionality-delta.md"
write_glossary_journeys "$TEST_DIR/gl3-all-good/v1-user-journeys.md"
write_glossary_integrations "$TEST_DIR/gl3-all-good/v1-integrations-and-exports.md"
write_authored_glossary "$TEST_DIR/gl3-all-good/v1-glossary.md"
assert_exit "GL-3: valid anchors across inventory + journeys + integrations passes" 0 "$STRUCTURE" --dir "$TEST_DIR/gl3-all-good"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
