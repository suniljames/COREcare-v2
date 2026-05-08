#!/usr/bin/env bash
# Body-scoped placeholder check for v1 catalog caption files.
#
# Per tools/v1-screenshot-catalog/CAPTION-STYLE.md §PHI references: caption
# bodies must NOT name placeholder values like [CLIENT_NAME], [CAREGIVER_NAME],
# etc. Use role-based language instead ("the assigned client's chart") so the
# catalog reads cleanly across placeholder vocabulary changes.
#
# Frontmatter (between the leading and trailing `---` markers) is exempt —
# the route field may legitimately reference a placeholder identifier.
#
# Sibling to scripts/check-v1-doc-hygiene.sh (which scans the whole file for
# real-name patterns and forbids real names everywhere). This script
# specifically targets the placeholder-in-caption-body rule that
# check-v1-doc-hygiene.sh treats as allowed.
#
# Usage:
#   scripts/check-v1-caption-phi.sh <caption.md> [<caption2.md> ...]
#
# Exit codes:
#   0  no violations
#   1  one or more files have a placeholder in the caption body
#   2  bad invocation (no files passed)

set -u

if [[ $# -eq 0 ]]; then
  echo "usage: $0 <caption.md> [<caption2.md> ...]" >&2
  exit 2
fi

# The locked placeholder set, drawn from
# scripts/check-v1-doc-hygiene.sh ALLOWED_PLACEHOLDERS_RE.
PLACEHOLDERS_RE='\[(CLIENT_NAME|CLIENT_DOB|CLIENT_MRN|CAREGIVER_NAME|AGENCY_NAME|ADDRESS|PHONE|EMAIL|DIAGNOSIS|MEDICATION|NOTE_TEXT|SHIFT_ID|VISIT_ID|INVOICE_ID|REDACTED)\]'

VIOLATIONS=0

scan_caption() {
  local file="$1"

  if [[ ! -f "$file" ]]; then
    echo "skip: $file not a regular file" >&2
    return 0
  fi

  # Extract the body — everything AFTER the trailing `---` of frontmatter.
  # awk state machine: count `---` markers; emit lines after the second.
  local body
  body=$(awk '
    BEGIN { depth = 0 }
    /^---[[:space:]]*$/ {
      depth++
      next
    }
    depth >= 2 { print }
  ' "$file")

  # Body may be empty (just frontmatter) — that's a pass.
  if [[ -z "$body" ]]; then
    return 0
  fi

  local hits
  hits=$(echo "$body" | grep -nE "$PLACEHOLDERS_RE" || true)
  if [[ -n "$hits" ]]; then
    echo "$file: caption body contains placeholder identifier (forbidden per CAPTION-STYLE.md §PHI references):"
    echo "$hits" | sed 's/^/  /' | head -5
    echo "  → use role-based language instead (e.g., \"the assigned client's chart\")."
    return 1
  fi
  return 0
}

for file in "$@"; do
  scan_caption "$file"
  rc=$?
  if [[ "$rc" != 0 ]]; then
    VIOLATIONS=$((VIOLATIONS + rc))
  fi
done

if [[ "$VIOLATIONS" -gt 0 ]]; then
  echo ""
  echo "Caption-body PHI check FAILED: $VIOLATIONS file(s) with placeholder in body."
  exit 1
fi

exit 0
