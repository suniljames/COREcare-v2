#!/usr/bin/env bash
# Validates structural invariants of the v1 reference document set:
#   1. v1-pages-inventory.md has an H2 section for each of the six personas.
#   2. v1-functionality-delta.md has the cross-reference header
#      "For collaborators without v1 access" as its first H2.
#   3. v1-functionality-delta.md contains no "needs confirmation" residue.
#   4. v1-pages-inventory.md's "## Shared routes" section, if present, is
#      populated — no "_(pending content authoring)_" placeholder, and it
#      contains at least one route row (markdown table row whose first cell
#      starts with a backtick — the route slug).
#   5. v1-pages-inventory.md's "## Family Member" section: every authored
#      route row (table row whose first cell is a backticked route slug)
#      must (a) contain the literal substring `linked-client only`, (b)
#      contain exactly one of the two literal audit-posture phrases —
#      `HIPAA-access-logged in v1` OR
#      `v1 has no audit on this route — v2 design must add` — and (c)
#      begin its `purpose` cell (second cell) with the `🔒 PHI · ` prefix.
#      Issue #103 visibility-scope discipline.
#
# Usage:
#   scripts/check-v1-doc-structure.sh [--dir <docs-dir>]
#
# Default --dir is `docs/migration/` (relative to current working directory).
#
# Exit codes:
#   0  all structural invariants hold
#   1  one or more checks failed

set -u

DIR="docs/migration"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) DIR="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

INVENTORY="$DIR/v1-pages-inventory.md"
DELTA="$DIR/v1-functionality-delta.md"

REQUIRED_PERSONAS=(
  "Super-Admin"
  "Agency Admin"
  "Care Manager"
  "Caregiver"
  "Client"
  "Family Member"
)

VIOLATIONS=0
fail() { echo "FAIL: $1"; VIOLATIONS=$((VIOLATIONS + 1)); }

# --- File presence ---
if [[ ! -f "$INVENTORY" ]]; then
  fail "$INVENTORY does not exist"
fi
if [[ ! -f "$DELTA" ]]; then
  fail "$DELTA does not exist"
fi

# --- Inventory: six persona H2 sections ---
if [[ -f "$INVENTORY" ]]; then
  for persona in "${REQUIRED_PERSONAS[@]}"; do
    # Match line starting with "## " followed by the exact persona string.
    # Anchor with end-of-line OR whitespace so "Care Manager" doesn't match
    # "Care Manager Exec" or similar.
    if ! grep -qE "^## ${persona}([[:space:]]|$)" "$INVENTORY"; then
      fail "$INVENTORY missing H2 section for persona: $persona"
    fi
  done
fi

# --- Inventory: Shared routes section, if present, is populated ---
# The shared-routes section gathers dual-role / portal-switching routes that
# multiple personas reach. While the docset is being authored, the section
# carries a "_(pending content authoring)_" placeholder. Once authored, the
# placeholder must be gone AND the section must contain at least one route
# row — a markdown table row whose first non-pipe character is a backtick
# (the route slug, e.g. `| \`/switch-role/\` |`).
if [[ -f "$INVENTORY" ]]; then
  shared_section=$(awk '
    /^## Shared routes([[:space:]]|$)/ { in_section = 1; next }
    in_section && /^## / { in_section = 0 }
    in_section { print }
  ' "$INVENTORY")
  if [[ -n "$shared_section" ]]; then
    if echo "$shared_section" | grep -qE '_\(pending content authoring\)_'; then
      fail "$INVENTORY '## Shared routes' still has '_(pending content authoring)_' placeholder"
    fi
    if ! echo "$shared_section" | grep -qE '^\|[[:space:]]*`'; then
      fail "$INVENTORY '## Shared routes' contains no route rows (no table row whose first cell is a backticked route slug)"
    fi
  fi
fi

# --- Delta: cross-ref header is the FIRST H2-or-deeper section ---
if [[ -f "$DELTA" ]]; then
  # Find the first heading line at H2 or deeper.
  first_section_heading=$(grep -nE '^##+ ' "$DELTA" | head -1 | cut -d: -f2-)
  if [[ -z "$first_section_heading" ]]; then
    fail "$DELTA contains no H2-or-deeper headings"
  elif ! echo "$first_section_heading" | grep -qE '^## For collaborators without v1 access'; then
    fail "$DELTA first H2 is not 'For collaborators without v1 access'"
    echo "  actual first H2: $first_section_heading"
  fi
fi

# --- Delta: no "needs confirmation" residue, scoped to content body ---
# The intro / legend before the first `---` separator is allowed to mention
# the marker as a convention. Any occurrence after the first separator is
# unresolved residue.
if [[ -f "$DELTA" ]]; then
  body_after_first_separator=$(awk '
    BEGIN { past_separator = 0 }
    /^---[[:space:]]*$/ && !past_separator { past_separator = 1; next }
    past_separator { print }
  ' "$DELTA")
  if echo "$body_after_first_separator" | grep -niE 'needs confirmation' >/dev/null; then
    fail "$DELTA still contains 'needs confirmation' residue (in body, past intro)"
    echo "$body_after_first_separator" | grep -niE 'needs confirmation' | head -3 | sed 's/^/  /'
  fi
fi

# --- Inventory: Family Member rows enforce visibility-scope + audit-posture phrasing (#103) ---
# Each authored route row under `## Family Member` (a markdown table row whose
# first cell is a backticked route slug) must:
#   (a) contain the literal substring `linked-client only`
#   (b) contain exactly one of the two literal audit-posture phrases:
#         `HIPAA-access-logged in v1`
#         `v1 has no audit on this route — v2 design must add`
#   (c) begin its second cell (purpose) with the `🔒 PHI · ` prefix
#
# The two audit-posture phrases are exhaustive — no third option. Forces the
# author to verify the v1 view's audit posture explicitly per row.
if [[ -f "$INVENTORY" ]]; then
  family_section=$(awk '
    /^## Family Member([[:space:]]|$)/ { in_section = 1; next }
    in_section && /^## / { in_section = 0 }
    in_section { print }
  ' "$INVENTORY")
  if [[ -n "$family_section" ]]; then
    # Iterate over each authored row (route slug in backticks as first cell).
    while IFS= read -r row; do
      [[ -z "$row" ]] && continue
      # Extract route slug for error messages: between first pair of backticks.
      route_slug=$(echo "$row" | sed -n 's/^|[[:space:]]*`\([^`]*\)`.*/\1/p')
      [[ -z "$route_slug" ]] && route_slug="<unparseable>"
      # (a) `linked-client only` literal
      if ! echo "$row" | grep -qF 'linked-client only'; then
        fail "$INVENTORY '## Family Member' row '$route_slug' missing literal phrase 'linked-client only'"
      fi
      # (b) exactly one of the two audit-posture phrases
      audit_logged=$(echo "$row" | grep -cF 'HIPAA-access-logged in v1')
      audit_missing=$(echo "$row" | grep -cF 'v1 has no audit on this route — v2 design must add')
      audit_count=$((audit_logged + audit_missing))
      if [[ "$audit_count" -ne 1 ]]; then
        fail "$INVENTORY '## Family Member' row '$route_slug' must contain EXACTLY one of the two audit-posture phrases (found $audit_count: HIPAA-access-logged=$audit_logged, no-audit=$audit_missing)"
      fi
      # (c) purpose cell (second cell) begins with `🔒 PHI · `
      # The first cell is the route; the second is purpose. Extract second cell.
      purpose_cell=$(echo "$row" | awk -F'|' '{ gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3 }')
      if [[ "$purpose_cell" != "🔒 PHI · "* ]]; then
        fail "$INVENTORY '## Family Member' row '$route_slug' purpose cell must begin with '🔒 PHI · ' prefix (got: '${purpose_cell:0:40}…')"
      fi
    done < <(echo "$family_section" | grep -E '^\|[[:space:]]*`')
  fi
fi

if [[ "$VIOLATIONS" -gt 0 ]]; then
  echo ""
  echo "Structure check FAILED with $VIOLATIONS violation(s)."
  exit 1
fi

exit 0
