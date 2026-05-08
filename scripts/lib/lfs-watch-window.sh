#!/usr/bin/env bash
# Date-window guard for the #185 LFS bandwidth watch.
#
# Window: 2026-05-07 (catalog merge / #107) -> 2026-06-07 (day 30).
# Hardcoded for #185-specific dates per the #233 design synthesis. If a
# second time-bounded watch ships later, generalize this then; do not
# parameterize speculatively.
#
# Usage (sourced):
#   source scripts/lib/lfs-watch-window.sh
#   if is_within_window "$today"; then ... fi
#
# Usage (executed):
#   scripts/lib/lfs-watch-window.sh 2026-05-23   # exit 0 (within)
#   scripts/lib/lfs-watch-window.sh 2026-06-08   # exit 1 (outside)
#
# Exit codes (function return values):
#   0  date is within the watch window (inclusive of both ends)
#   1  date is outside the window or empty/malformed

LFS_WATCH_WINDOW_START='2026-05-07'
LFS_WATCH_WINDOW_END='2026-06-07'

is_within_window() {
  local date="$1"
  if [[ -z "$date" ]]; then
    return 1
  fi
  # Lexicographic comparison works because YYYY-MM-DD sorts correctly.
  if [[ "$date" < "$LFS_WATCH_WINDOW_START" ]]; then
    return 1
  fi
  if [[ "$date" > "$LFS_WATCH_WINDOW_END" ]]; then
    return 1
  fi
  return 0
}

# When invoked directly (not sourced), validate via $1.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  if [[ $# -ne 1 ]]; then
    echo "usage: $0 <YYYY-MM-DD>" >&2
    exit 2
  fi
  is_within_window "$1"
fi
