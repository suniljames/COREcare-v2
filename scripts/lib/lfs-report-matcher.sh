#!/usr/bin/env bash
# Matcher for the LFS bandwidth report comment signature on issue #185.
#
# Per the #233 design synthesis, the matcher anchors at the start of the
# comment body on the exact bold marker:
#
#   **30-day Git LFS bandwidth report**
#
# Conservative by design — false positives are worse than false negatives;
# the manual cleanup section of docs/operations/lfs-bandwidth-watch.md is
# the documented fallback when the matcher misses.
#
# The snapshot helper (scripts/lfs-bandwidth-snapshot.sh) emits exactly
# this signature as the first non-blank content of the day-30 closure
# template, so an operator who pastes verbatim will always match.
#
# Usage (sourced):
#   source scripts/lib/lfs-report-matcher.sh
#   if is_report_comment "$body"; then ... fi
#
# Usage (executed):
#   scripts/lib/lfs-report-matcher.sh "$comment_body"   # exit 0 if matches
#
# Exit codes (function return values):
#   0  body matches the report signature
#   1  body does not match

is_report_comment() {
  local body="$1"
  local pattern='^\*\*30-day Git LFS bandwidth report\*\*'
  [[ "$body" =~ $pattern ]]
}

# When invoked directly (not sourced), validate via $1.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  if [[ $# -ne 1 ]]; then
    echo "usage: $0 <comment-body>" >&2
    exit 2
  fi
  is_report_comment "$1"
fi
