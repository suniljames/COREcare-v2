#!/usr/bin/env bash
# Validates parity between the v1 pages inventory and the v1 UI screenshot
# catalog (#79).
#
# For each row in `docs/migration/v1-pages-inventory.md`, the row's
# `screenshot_ref` field must be one of:
#   - a canonical_id of the form `<persona-slug>/<NNN-route>` matching a caption
#     file at `docs/legacy/v1-ui-catalog/<persona-slug>/<NNN-route>.md` whose
#     YAML frontmatter `canonical_id:` field holds the same value, OR
#   - `not_screenshotted: <reason>` (skip-reason bypass).
#
# Pass conditions:
#   - (matched + skipped) / total inventory rows >= threshold (default 95%).
#   - 0 unmatched (inventory ref to caption that does not exist or has wrong
#     canonical_id).
#   - 0 orphan captions (caption file whose canonical_id is not referenced by
#     any inventory row).
#
# Usage:
#   scripts/check-v1-catalog-coverage.sh
#     [--inventory <path>]   default: docs/migration/v1-pages-inventory.md
#     [--catalog <path>]     default: docs/legacy/v1-ui-catalog
#     [--threshold N]        default: 95 (integer 0-100)
#
# Exit codes:
#   0  parity holds
#   1  unmatched ref, orphan caption, or threshold breach
#   2  bad invocation (missing inventory, bad arg)

set -u

INVENTORY="docs/migration/v1-pages-inventory.md"
CATALOG="docs/legacy/v1-ui-catalog"
THRESHOLD=95

while [[ $# -gt 0 ]]; do
  case "$1" in
    --inventory) INVENTORY="$2"; shift 2 ;;
    --catalog)   CATALOG="$2"; shift 2 ;;
    --threshold) THRESHOLD="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
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
case "$THRESHOLD" in
  ''|*[!0-9]*) echo "error: --threshold must be an integer 0-100" >&2; exit 2 ;;
esac
if (( THRESHOLD < 0 || THRESHOLD > 100 )); then
  echo "error: --threshold must be 0-100" >&2
  exit 2
fi

# ---------------------------------------------------------------------------
# Stage 1 — parse inventory rows.
#
# An inventory row is a markdown table line with NF==12 (under awk -F'|') AND
# whose route field (col 2) starts with `` `/`` (backtick + slash). The
# screenshot_ref field is column 10 (1-indexed in the awk sense, so $10).
#
# Output of this stage: two parallel files in a tmpdir:
#   inv_refs.txt — one ref per line (canonical_id values, route-pointing rows)
#   inv_skipped.txt — one route per line (rows with not_screenshotted:)
# ---------------------------------------------------------------------------

WORK=$(mktemp -d -t catalog-coverage-XXXXXX)
trap 'rm -rf "$WORK"' EXIT

INV_REFS="$WORK/inv_refs.txt"
INV_SKIPPED="$WORK/inv_skipped.txt"
INV_BAD="$WORK/inv_bad.txt"
: > "$INV_REFS"
: > "$INV_SKIPPED"
: > "$INV_BAD"

awk -F'|' '
  NF == 12 {
    route = $2
    sub(/^[[:space:]]+/, "", route); sub(/[[:space:]]+$/, "", route)
    # Inventory rows have route wrapped in backticks: `route_pattern`
    if (route !~ /^`\//) next

    ref = $10
    sub(/^[[:space:]]+/, "", ref); sub(/[[:space:]]+$/, "", ref)

    if (ref == "" ) {
      print route > "'"$INV_BAD"'"
      next
    }
    if (ref ~ /^not_screenshotted:/) {
      print route > "'"$INV_SKIPPED"'"
      next
    }
    # Otherwise: canonical_id reference
    print ref > "'"$INV_REFS"'"
  }
' "$INVENTORY"

INV_TOTAL_REFS=$(wc -l < "$INV_REFS" | tr -d ' ')
INV_TOTAL_SKIP=$(wc -l < "$INV_SKIPPED" | tr -d ' ')
INV_TOTAL_BAD=$(wc -l < "$INV_BAD" | tr -d ' ')
INV_TOTAL=$((INV_TOTAL_REFS + INV_TOTAL_SKIP + INV_TOTAL_BAD))

# ---------------------------------------------------------------------------
# Stage 2 — parse caption canonical_ids.
#
# For every .md file under <catalog>/*/*.md, extract the YAML frontmatter
# canonical_id field (first occurrence between leading --- markers).
# Output: cap_ids.txt — one canonical_id per caption file.
# ---------------------------------------------------------------------------

CAP_IDS="$WORK/cap_ids.txt"
: > "$CAP_IDS"

if [[ -d "$CATALOG" ]]; then
  while IFS= read -r -d '' caption_file; do
    # Extract frontmatter canonical_id. awk reads only between the first two
    # --- markers; first canonical_id wins.
    cid=$(awk '
      BEGIN { in_fm = 0; depth = 0 }
      /^---[[:space:]]*$/ {
        depth++
        if (depth == 1) { in_fm = 1; next }
        if (depth == 2) { exit }
      }
      in_fm && /^canonical_id:[[:space:]]/ {
        sub(/^canonical_id:[[:space:]]+/, "")
        sub(/[[:space:]]+$/, "")
        print
        exit
      }
    ' "$caption_file")
    if [[ -n "$cid" ]]; then
      echo "$cid" >> "$CAP_IDS"
    fi
  done < <(find "$CATALOG" -mindepth 2 -maxdepth 2 -name '*.md' -type f -print0 2>/dev/null)
fi

CAP_TOTAL=$(wc -l < "$CAP_IDS" | tr -d ' ')

# ---------------------------------------------------------------------------
# Stage 3 — cross-check.
# ---------------------------------------------------------------------------

# Sorted dedupe for join-style comparison.
sort -u "$INV_REFS" > "$WORK/inv_refs_sorted.txt"
sort -u "$CAP_IDS"  > "$WORK/cap_ids_sorted.txt"

MATCHED_FILE="$WORK/matched.txt"
UNMATCHED_FILE="$WORK/unmatched.txt"
ORPHAN_FILE="$WORK/orphans.txt"

comm -12 "$WORK/inv_refs_sorted.txt" "$WORK/cap_ids_sorted.txt" > "$MATCHED_FILE"
comm -23 "$WORK/inv_refs_sorted.txt" "$WORK/cap_ids_sorted.txt" > "$UNMATCHED_FILE"
comm -13 "$WORK/inv_refs_sorted.txt" "$WORK/cap_ids_sorted.txt" > "$ORPHAN_FILE"

MATCHED=$(wc -l < "$MATCHED_FILE" | tr -d ' ')
UNMATCHED=$(wc -l < "$UNMATCHED_FILE" | tr -d ' ')
ORPHANS=$(wc -l < "$ORPHAN_FILE" | tr -d ' ')

# Coverage percentage on the inventory side.
if (( INV_TOTAL > 0 )); then
  COVERED=$((MATCHED + INV_TOTAL_SKIP))
  COVERAGE_PCT=$(( (COVERED * 100) / INV_TOTAL ))
else
  COVERAGE_PCT=100
fi

# ---------------------------------------------------------------------------
# Stage 4 — report.
# ---------------------------------------------------------------------------

echo "v1 catalog coverage check"
echo "  inventory:  $INVENTORY"
echo "  catalog:    $CATALOG"
echo "  threshold:  ${THRESHOLD}%"
echo ""
echo "Inventory rows:    $INV_TOTAL  (refs: $INV_TOTAL_REFS, skip-reason: $INV_TOTAL_SKIP, blank: $INV_TOTAL_BAD)"
echo "Caption files:     $CAP_TOTAL"
echo ""
echo "matched: $MATCHED"
echo "skip-reason: $INV_TOTAL_SKIP"
echo "unmatched: $UNMATCHED"
echo "orphan captions: $ORPHANS"
echo "coverage: ${COVERAGE_PCT}%"

FAILED=0

if (( UNMATCHED > 0 )); then
  echo ""
  echo "FAIL: $UNMATCHED inventory ref(s) point at captions that do not exist or have mismatched canonical_id:"
  sed 's/^/  - /' "$UNMATCHED_FILE"
  FAILED=1
fi

if (( ORPHANS > 0 )); then
  echo ""
  echo "FAIL: $ORPHANS caption(s) have no matching inventory row:"
  sed 's/^/  - /' "$ORPHAN_FILE"
  FAILED=1
fi

if (( INV_TOTAL_BAD > 0 )); then
  echo ""
  echo "FAIL: $INV_TOTAL_BAD inventory row(s) have a blank screenshot_ref field:"
  sed 's/^/  - /' "$INV_BAD"
  FAILED=1
fi

if (( COVERAGE_PCT < THRESHOLD )); then
  echo ""
  echo "FAIL: coverage ${COVERAGE_PCT}% below threshold ${THRESHOLD}%"
  FAILED=1
fi

if (( FAILED == 0 )); then
  echo ""
  echo "OK: catalog coverage holds"
fi

exit $FAILED
