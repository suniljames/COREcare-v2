#!/usr/bin/env bash
# Acceptance test for issue #88: Agency Admin pages-inventory rows for
# compliance and auth_service apps (bundled). Asserts:
#   1. ## Agency Admin contains ### compliance and ### auth_service H3
#      sub-sections, in that order, each with a one-line summary.
#   2. Each H3 sub-section has at least one populated row (not the
#      placeholder "rows pending content authoring").
#   3. Coverage subsection's per-app table has non-zero numerators for
#      both compliance and auth_service.
#   4. ## Shared routes references both apps' routes.
#   5. Hygiene + structure scanners pass over the file.
#
# Run from repo root: bash scripts/tests/test_issue_88_compliance_auth_service.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INVENTORY="$REPO_ROOT/docs/migration/v1-pages-inventory.md"
HYGIENE="$REPO_ROOT/scripts/check-v1-doc-hygiene.sh"
STRUCTURE="$REPO_ROOT/scripts/check-v1-doc-structure.sh"

PASS=0
FAIL=0

assert() {
  local description="$1"; shift
  if "$@"; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description"
    FAIL=$((FAIL + 1))
  fi
}

# Extract the body between two markers (exclusive). Used to scope a check
# to the Agency Admin H2 section.
extract_section() {
  local file="$1"; local start="$2"; local end="$3"
  awk -v start="$start" -v end="$end" '
    $0 ~ start { in_section = 1; next }
    in_section && $0 ~ end { in_section = 0 }
    in_section { print }
  ' "$file"
}

agency_section_has_h3_compliance() {
  extract_section "$INVENTORY" '^## Agency Admin' '^## Care Manager' \
    | grep -qE '^### compliance$'
}

agency_section_has_h3_auth_service() {
  extract_section "$INVENTORY" '^## Agency Admin' '^## Care Manager' \
    | grep -qE '^### auth_service$'
}

h3_compliance_has_summary() {
  # The H3 line must be followed (within 2 lines) by an underscored
  # one-line summary `_..._`.
  awk '
    /^### compliance$/ { found = 1; next }
    found && /^_.+_$/ { ok = 1; exit }
    found && /^### / { exit }
    found { lines++; if (lines > 3) exit }
    END { exit (ok ? 0 : 1) }
  ' "$INVENTORY"
}

h3_auth_service_has_summary() {
  awk '
    /^### auth_service$/ { found = 1; next }
    found && /^_.+_$/ { ok = 1; exit }
    found && /^### / { exit }
    found { lines++; if (lines > 3) exit }
    END { exit (ok ? 0 : 1) }
  ' "$INVENTORY"
}

h3_section_has_real_rows() {
  # Walk from the given H3 to the next H3 or H2 — confirm at least one
  # row line starts with a backticked route (not the placeholder `rows
  # pending content authoring`).
  local h3="$1"
  awk -v h3="$h3" '
    $0 ~ "^" h3 "$" { in_section = 1; next }
    in_section && /^### / { exit }
    in_section && /^## / { exit }
    in_section && /^\| `\// { count++ }
    END { exit (count > 0 ? 0 : 1) }
  ' "$INVENTORY"
}

coverage_compliance_numerator_nonzero() {
  # The Coverage subsection has a row like:
  # | compliance | <denom> | <numer> | ... |
  # Look for compliance row and verify numerator != 0.
  awk '
    /^### Agency Admin/ { in_section = 1; next }
    in_section && /^### / && !/^### Agency Admin/ { exit }
    in_section && /^\| compliance \|/ {
      # split on pipes; numerator is 4th cell (1=empty, 2=app, 3=denom, 4=numer)
      n = split($0, cells, "|")
      gsub(/^[ \t]+|[ \t]+$/, "", cells[4])
      if (cells[4] != "0" && cells[4] != "") found = 1
      exit
    }
    END { exit (found ? 0 : 1) }
  ' "$INVENTORY"
}

coverage_auth_service_numerator_nonzero() {
  awk '
    /^### Agency Admin/ { in_section = 1; next }
    in_section && /^### / && !/^### Agency Admin/ { exit }
    in_section && /^\| auth_service \|/ {
      n = split($0, cells, "|")
      gsub(/^[ \t]+|[ \t]+$/, "", cells[4])
      if (cells[4] != "0" && cells[4] != "" && cells[4] != "TBD") found = 1
      exit
    }
    END { exit (found ? 0 : 1) }
  ' "$INVENTORY"
}

shared_routes_references_compliance() {
  awk '
    /^## Shared routes/ { in_section = 1; next }
    in_section && /^## / { exit }
    in_section && /compliance/ { found = 1 }
    END { exit (found ? 0 : 1) }
  ' "$INVENTORY"
}

shared_routes_references_auth_service() {
  awk '
    /^## Shared routes/ { in_section = 1; next }
    in_section && /^## / { exit }
    in_section && /auth_service/ { found = 1 }
    END { exit (found ? 0 : 1) }
  ' "$INVENTORY"
}

hygiene_passes() {
  bash "$HYGIENE" "$INVENTORY" >/dev/null 2>&1
}

structure_passes() {
  bash "$STRUCTURE" --dir "$REPO_ROOT/docs/migration" >/dev/null 2>&1
}

echo "== Issue #88 acceptance tests =="

assert "Agency Admin has ### compliance H3" agency_section_has_h3_compliance
assert "Agency Admin has ### auth_service H3" agency_section_has_h3_auth_service
assert "### compliance has one-line summary" h3_compliance_has_summary
assert "### auth_service has one-line summary" h3_auth_service_has_summary
assert "### compliance has at least one route row" h3_section_has_real_rows '### compliance'
assert "### auth_service has at least one route row" h3_section_has_real_rows '### auth_service'
assert "Coverage shows non-zero numerator for compliance" coverage_compliance_numerator_nonzero
assert "Coverage shows non-zero numerator for auth_service" coverage_auth_service_numerator_nonzero
assert "## Shared routes references compliance" shared_routes_references_compliance
assert "## Shared routes references auth_service" shared_routes_references_auth_service
assert "hygiene scanner passes over inventory" hygiene_passes
assert "structure scanner passes over docs/migration/" structure_passes

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
