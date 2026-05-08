#!/usr/bin/env bash
# Emits the v1 pages inventory as a JSON array of {persona, route, screenshot_ref}
# objects. Single source of truth for inventory parsing — consumed by:
#   - scripts/check-v1-catalog-coverage.sh (parity check, PR-A)
#   - tools/v1-screenshot-catalog/crawl.ts (catalog crawler, PR-C)
#
# Inventory schema (locked in docs/migration/README.md §Locked conventions):
#   Each persona is an H2 heading: ## Agency Admin / ## Care Manager / etc.
#   Tables under that heading have 10 columns; the route column is col 2
#   (backtick-wrapped) and screenshot_ref is col 10. Rows in summary tables
#   (different schema) are excluded by the "route starts with backtick-slash"
#   filter.
#
# Usage:
#   scripts/extract-inventory-routes.sh
#     [--inventory <path>]   default: docs/migration/v1-pages-inventory.md
#
# Output: JSON array on stdout. Exits 0 on success, 2 on missing inventory.

set -u

INVENTORY="docs/migration/v1-pages-inventory.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --inventory) INVENTORY="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *)
      echo "unknown arg: $1" >&2
      exit 2 ;;
  esac
done

if [[ ! -f "$INVENTORY" ]]; then
  echo "error: inventory file not found: $INVENTORY" >&2
  exit 2
fi

# Locked persona vocabulary (matches docs/migration/README.md §Personas).
# Order matches the canonical persona section order in the inventory.
# MUST match scripts/check-v1-doc-structure.sh REQUIRED_PERSONAS — see #236.
LOCKED_PERSONAS=(
  "Agency Admin"
  "Care Manager"
  "Caregiver"
  "Client"
  "Family Member"
)

# awk emits one JSON object per inventory row. We track the active persona
# section by watching H2 headings and resetting when a new H2 appears. The
# route filter (col 2 starts with backtick-slash) excludes summary tables and
# the schema-definition table.
awk -F'|' -v personas="${LOCKED_PERSONAS[*]}" '
  BEGIN {
    n = split(personas, plist, " ")
    # Build an associative array of locked persona names. Multi-word personas
    # were space-separated by the IFS join; rejoin them.
    # Rather than guess, hardcode the locked set:
    # MUST match scripts/check-v1-doc-structure.sh REQUIRED_PERSONAS — see #236.
    locked["Agency Admin"] = 1
    locked["Care Manager"] = 1
    locked["Caregiver"] = 1
    locked["Client"] = 1
    locked["Family Member"] = 1
    current_persona = ""
    first = 1
    print "["
  }

  # Match H2 headings. On match, set current_persona if it is a locked persona,
  # otherwise clear (we are no longer inside a persona section).
  /^## / {
    candidate = $0
    sub(/^## /, "", candidate)
    sub(/[[:space:]]*$/, "", candidate)
    if (candidate in locked) {
      current_persona = candidate
    } else {
      current_persona = ""
    }
    next
  }

  # Inventory row: 12 awk-fields under -F"|", route field (col 2) starts with
  # backtick-slash. Must be inside a persona section.
  current_persona != "" && NF == 12 {
    route = $2
    sub(/^[[:space:]]+/, "", route); sub(/[[:space:]]+$/, "", route)
    if (route !~ /^`\//) next

    # Strip surrounding backticks
    sub(/^`/, "", route); sub(/`$/, "", route)

    ref = $10
    sub(/^[[:space:]]+/, "", ref); sub(/[[:space:]]+$/, "", ref)

    # JSON-escape: backslash and double-quote.
    persona_json = current_persona
    route_json = route
    ref_json = ref
    gsub(/\\/, "\\\\", persona_json)
    gsub(/\\/, "\\\\", route_json)
    gsub(/\\/, "\\\\", ref_json)
    gsub(/"/, "\\\"", persona_json)
    gsub(/"/, "\\\"", route_json)
    gsub(/"/, "\\\"", ref_json)

    if (!first) print ","
    first = 0
    printf "  {\"persona\":\"%s\",\"route\":\"%s\",\"screenshot_ref\":\"%s\"}", \
      persona_json, route_json, ref_json
  }

  END {
    if (!first) print ""
    print "]"
  }
' "$INVENTORY"
