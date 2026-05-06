#!/usr/bin/env bash
# Validates structural invariants of the v1 reference document set:
#   1. v1-pages-inventory.md has an H2 section for each of the six personas.
#   2. v1-functionality-delta.md has the cross-reference header
#      "For collaborators without v1 access" as its first H2.
#   3. v1-functionality-delta.md contains no "needs confirmation" residue.
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

# --- Delta: no "needs confirmation" residue ---
if [[ -f "$DELTA" ]]; then
  if grep -niE 'needs confirmation' "$DELTA" >/dev/null; then
    fail "$DELTA still contains 'needs confirmation' residue"
    grep -niE 'needs confirmation' "$DELTA" | head -3 | sed 's/^/  /'
  fi
fi

if [[ "$VIOLATIONS" -gt 0 ]]; then
  echo ""
  echo "Structure check FAILED with $VIOLATIONS violation(s)."
  exit 1
fi

exit 0
