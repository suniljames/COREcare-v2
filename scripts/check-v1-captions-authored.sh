#!/usr/bin/env bash
# Asserts no `<!-- TODO: author CTAs` placeholder markers remain in any
# caption file under the v1 UI catalog.
#
# The crawler (tools/v1-screenshot-catalog/crawl.ts) emits caption files with
# a TODO marker for the body. Phase 3 of #107 (issue #184) replaces those
# markers with authored CTAs + interaction notes. This script is the gate
# that closes the loop: once authoring is complete, no marker remains.
#
# Usage:
#   scripts/check-v1-captions-authored.sh
#     [--catalog <path>]   default: docs/legacy/v1-ui-catalog
#
# Exit codes:
#   0  no TODO markers in any caption file
#   1  one or more caption files contain a TODO marker
#   2  bad invocation (missing/non-existent catalog dir, bad arg)

set -u

CATALOG="docs/legacy/v1-ui-catalog"
MARKER='<!-- TODO: author CTAs'

while [[ $# -gt 0 ]]; do
  case "$1" in
    --catalog)
      if [[ $# -lt 2 ]]; then
        echo "error: --catalog requires a value" >&2
        exit 2
      fi
      CATALOG="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *)
      echo "error: unknown arg: $1" >&2
      exit 2 ;;
  esac
done

if [[ ! -d "$CATALOG" ]]; then
  echo "error: catalog dir not found: $CATALOG" >&2
  exit 2
fi

# Find caption files containing the TODO marker. Caption files live at depth
# exactly 2 (catalog/<persona>/<NNN>-<slug>.md) — match the structure the
# crawler emits and the coverage script reads.
HITS=$(find "$CATALOG" -mindepth 2 -maxdepth 2 -name '*.md' -type f \
         -exec grep -l "$MARKER" {} + 2>/dev/null || true)

if [[ -n "$HITS" ]]; then
  COUNT=$(echo "$HITS" | wc -l | tr -d ' ')
  echo "FAIL: $COUNT caption file(s) still contain TODO marker:"
  echo "$HITS" | sed 's/^/  - /'
  echo ""
  echo "  Expected marker: $MARKER"
  echo "  Replace with body content per tools/v1-screenshot-catalog/CAPTION-STYLE.md."
  exit 1
fi

echo "OK: no TODO markers in caption files under $CATALOG"
exit 0
