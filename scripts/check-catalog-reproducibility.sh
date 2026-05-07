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

cd "$TOOL_DIR"
exec pnpm exec tsx check-reproducibility.ts "$@"
