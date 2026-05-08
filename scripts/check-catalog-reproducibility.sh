#!/usr/bin/env bash
# Compares two v1-UI-catalog directories and emits a per-image pixel-diff
# report. T2 of #107: byte-identical (AA-jitter only) re-run.
#
# Phase 2A rewrote the comparison logic in TypeScript (sharp + pixelmatch +
# pngjs in-process, no per-image npx overhead). This bash file is a thin
# wrapper that invokes the TS implementation via `pnpm check-reproducibility`.
#
# Usage:
#   scripts/check-catalog-reproducibility.sh <baseline-dir> <rerun-dir>
#     [--threshold-pct N]   default 0.5
#     [--output-dir <path>] default <rerun-dir>/reproducibility-report
#
# Exit codes:
#   0  every image is within threshold AND fixture hashes match
#   1  any image exceeds threshold OR fixture hashes diverge
#   2  bad invocation

set -eu

# Resolve the crawler-tool dir relative to this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_DIR="$(cd "$SCRIPT_DIR/../tools/v1-screenshot-catalog" && pwd)"

if [[ ! -d "$TOOL_DIR/node_modules" ]]; then
  echo "error: node_modules missing in $TOOL_DIR — run \`cd $TOOL_DIR && pnpm install\`" >&2
  exit 2
fi

# Convert any relative path-shaped arguments to absolute so they survive
# the cd into TOOL_DIR. Flags and the next-arg of known path-flags both get
# resolved; bare numeric values (e.g., "0.5" for --threshold-pct) pass
# through unchanged.
# Convert relative path-shaped args to absolute so they survive the cd
# into TOOL_DIR. Flags pass through; positional path args are resolved
# against the user's PWD; the value following a path-flag is also resolved.
PWD_ABS="$(pwd)"
RESOLVED_ARGS=()
prev_was_path_flag=false
abs_path() {
  case "$1" in
    /*) echo "$1" ;;
    *)  echo "$PWD_ABS/$1" ;;
  esac
}
for arg in "$@"; do
  if $prev_was_path_flag; then
    RESOLVED_ARGS+=("$(abs_path "$arg")")
    prev_was_path_flag=false
    continue
  fi
  case "$arg" in
    --output-dir|--baseline|--rerun)
      RESOLVED_ARGS+=("$arg")
      prev_was_path_flag=true
      ;;
    --*)
      RESOLVED_ARGS+=("$arg")
      ;;
    /*)
      RESOLVED_ARGS+=("$arg")
      ;;
    *)
      if [[ "$arg" == */* || -e "$arg" ]]; then
        RESOLVED_ARGS+=("$(abs_path "$arg")")
      else
        RESOLVED_ARGS+=("$arg")
      fi
      ;;
  esac
done

cd "$TOOL_DIR"
exec pnpm exec tsx check-reproducibility.ts "${RESOLVED_ARGS[@]}"
