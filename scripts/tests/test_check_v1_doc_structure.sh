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

# --- SL-3: severity set but v2_status is not "missing" ---
mkdir -p "$TEST_DIR/integrations-sl3"
write_integrations_inventory "$TEST_DIR/integrations-sl3/v1-pages-inventory.md"
write_good_delta "$TEST_DIR/integrations-sl3/v1-functionality-delta.md"
cat > "$TEST_DIR/integrations-sl3/v1-integrations-and-exports.md" <<EOF
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
assert_exit "SL-3: severity set when v2_status != missing fails" 1 "$STRUCTURE" --dir "$TEST_DIR/integrations-sl3"

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

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
