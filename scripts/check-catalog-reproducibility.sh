#!/usr/bin/env bash
# Compares two v1-UI-catalog directories and emits a per-image pixel-diff
# report. Used to verify T2 of #107: byte-identical (AA-jitter only) re-run.
#
# Approach: convert WebPs to PNG via `sharp`, then run `pixelmatch` from npx.
# Any image with >0.5% pixel diff fails the run.
#
# Usage:
#   scripts/check-catalog-reproducibility.sh <baseline-dir> <rerun-dir>
#     [--threshold-pct N]   default 0.5 (percent of pixels allowed to differ)
#     [--output-dir <path>] default <rerun-dir>/reproducibility-report
#
# Exit codes:
#   0  every image is within threshold
#   1  one or more images exceed threshold
#   2  bad invocation

set -u

THRESHOLD_PCT="0.5"
OUTPUT_DIR=""
BASELINE=""
RERUN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --threshold-pct) THRESHOLD_PCT="$2"; shift 2 ;;
    --output-dir)    OUTPUT_DIR="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    --*)
      echo "unknown flag: $1" >&2
      exit 2 ;;
    *)
      if [[ -z "$BASELINE" ]]; then BASELINE="$1"
      elif [[ -z "$RERUN" ]]; then RERUN="$1"
      else echo "unexpected positional arg: $1" >&2; exit 2
      fi
      shift ;;
  esac
done

if [[ -z "$BASELINE" || -z "$RERUN" ]]; then
  echo "error: must pass two positional args: <baseline-dir> <rerun-dir>" >&2
  exit 2
fi
if [[ ! -d "$BASELINE" ]]; then echo "error: baseline dir not found: $BASELINE" >&2; exit 2; fi
if [[ ! -d "$RERUN" ]]; then echo "error: rerun dir not found: $RERUN" >&2; exit 2; fi
if [[ -z "$OUTPUT_DIR" ]]; then OUTPUT_DIR="$RERUN/reproducibility-report"; fi
mkdir -p "$OUTPUT_DIR"

if ! command -v npx >/dev/null 2>&1; then
  echo "error: npx not found; install Node 20+" >&2
  exit 2
fi

# Find every WebP under the baseline that has a sibling in the rerun.
# Outputs report to <OUTPUT_DIR>/report.md and per-image diffs as PNGs.
REPORT="$OUTPUT_DIR/report.md"
echo "# Catalog reproducibility report" > "$REPORT"
echo "" >> "$REPORT"
echo "**Baseline:** $BASELINE" >> "$REPORT"
echo "**Rerun:** $RERUN" >> "$REPORT"
echo "**Threshold:** ${THRESHOLD_PCT}% per-image pixel diff" >> "$REPORT"
echo "" >> "$REPORT"
echo "| canonical_id | viewport | diff% | status |" >> "$REPORT"
echo "|--------------|----------|------:|--------|" >> "$REPORT"

EXCEEDED=0
TOTAL=0

while IFS= read -r -d '' baseline_file; do
  rel="${baseline_file#$BASELINE/}"
  rerun_file="$RERUN/$rel"
  if [[ ! -f "$rerun_file" ]]; then
    continue   # rerun is missing this image — caught by the coverage script, not here
  fi
  TOTAL=$((TOTAL + 1))

  # canonical_id is the path minus the .{desktop,mobile}.webp suffix
  canonical_id="${rel%.desktop.webp}"
  canonical_id="${canonical_id%.mobile.webp}"
  if [[ "$rel" == *".desktop.webp" ]]; then viewport="desktop"
  elif [[ "$rel" == *".mobile.webp" ]]; then viewport="mobile"
  else continue
  fi

  # Convert both to PNG via sharp (npx). pixelmatch requires PNG.
  baseline_png=$(mktemp -t catrepro-base.XXXXXX.png)
  rerun_png=$(mktemp -t catrepro-rerun.XXXXXX.png)
  diff_png="$OUTPUT_DIR/${canonical_id//\//_}.${viewport}.diff.png"
  mkdir -p "$(dirname "$diff_png")" 2>/dev/null

  npx --yes sharp-cli "$baseline_file" -o "$baseline_png" -f png >/dev/null 2>&1 || true
  npx --yes sharp-cli "$rerun_file"    -o "$rerun_png"    -f png >/dev/null 2>&1 || true

  if [[ ! -s "$baseline_png" || ! -s "$rerun_png" ]]; then
    echo "| $canonical_id | $viewport | n/a | conversion-failed |" >> "$REPORT"
    EXCEEDED=$((EXCEEDED + 1))
    rm -f "$baseline_png" "$rerun_png"
    continue
  fi

  # pixelmatch via npx. Output: number of differing pixels.
  diff_output=$(npx --yes pixelmatch "$baseline_png" "$rerun_png" "$diff_png" 0.1 2>/dev/null || true)
  diff_pixels=$(echo "$diff_output" | grep -oE '[0-9]+' | head -1)
  diff_pixels="${diff_pixels:-0}"

  # Compute total pixels of the baseline (width × height).
  total_pixels=$(npx --yes sharp-cli metadata "$baseline_png" 2>/dev/null | python3 -c "import sys, json; m = json.load(sys.stdin); print(m.get('width', 0) * m.get('height', 0))" 2>/dev/null || echo 1)
  total_pixels="${total_pixels:-1}"
  if [[ "$total_pixels" -le 0 ]]; then total_pixels=1; fi

  diff_pct=$(awk -v d="$diff_pixels" -v t="$total_pixels" 'BEGIN { printf "%.4f", (d * 100.0) / t }')
  ok=$(awk -v d="$diff_pct" -v t="$THRESHOLD_PCT" 'BEGIN { print (d <= t) ? 1 : 0 }')

  if [[ "$ok" == "1" ]]; then
    echo "| $canonical_id | $viewport | ${diff_pct}% | ok |" >> "$REPORT"
  else
    echo "| $canonical_id | $viewport | ${diff_pct}% | EXCEEDED |" >> "$REPORT"
    EXCEEDED=$((EXCEEDED + 1))
  fi

  rm -f "$baseline_png" "$rerun_png"
done < <(find "$BASELINE" -name '*.webp' -type f -print0 2>/dev/null)

echo "" >> "$REPORT"
echo "## Summary" >> "$REPORT"
echo "" >> "$REPORT"
echo "- Total compared: $TOTAL" >> "$REPORT"
echo "- Within threshold: $((TOTAL - EXCEEDED))" >> "$REPORT"
echo "- Exceeded: $EXCEEDED" >> "$REPORT"

cat "$REPORT" | tail -10
echo ""
echo "Report: $REPORT"

if (( EXCEEDED > 0 )); then
  exit 1
fi
exit 0
