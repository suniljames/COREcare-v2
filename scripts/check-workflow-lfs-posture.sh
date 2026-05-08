#!/usr/bin/env bash
# Scans GitHub Actions workflow YAML for `lfs: true` set on `actions/checkout`
# steps that lack a same-line `# rationale: <text>` comment.
#
# Per ADR-010 and issue #185, the v1 UI catalog is stored via Git LFS and
# workflows that do not need to read the binaries skip LFS smudging. Any
# workflow that legitimately opts into LFS smudging must declare why on the
# same line as `lfs: true`. This guard enforces the declaration so reviewers
# can reject silent flips of the convention.
#
# Usage:
#   scripts/check-workflow-lfs-posture.sh                  # scan .github/workflows/*.yml
#   scripts/check-workflow-lfs-posture.sh <file> [<file>…] # scan named files
#
# Exit codes:
#   0  no violations
#   1  one or more files violate the rationale-comment requirement
#   2  usage error (e.g. file not found)

set -u

if [[ $# -eq 0 ]]; then
  shopt -s nullglob
  files=(.github/workflows/*.yml .github/workflows/*.yaml)
  if [[ ${#files[@]} -eq 0 ]]; then
    # No workflows is not a failure; nothing to enforce.
    exit 0
  fi
else
  files=("$@")
  for f in "${files[@]}"; do
    if [[ ! -f "$f" ]]; then
      echo "ERROR: file not found: $f" >&2
      exit 2
    fi
  done
fi

violations=$(awk '
  function trim(s) {
    sub(/^[[:space:]]+/, "", s)
    sub(/[[:space:]]+$/, "", s)
    return s
  }
  FNR == 1 { last_uses = "" }
  /^[[:space:]]*-?[[:space:]]*uses:[[:space:]]*/ {
    line = $0
    sub(/^[[:space:]]*-?[[:space:]]*uses:[[:space:]]*/, "", line)
    sub(/[[:space:]]*#.*$/, "", line)
    last_uses = trim(line)
    next
  }
  /^[[:space:]]*lfs:[[:space:]]*(true|false)([[:space:]]|$|#)/ {
    if (last_uses ~ /^actions\/checkout(@|$)/) {
      val = $0
      sub(/^[[:space:]]*lfs:[[:space:]]*/, "", val)
      if (match(val, /^(true|false)/)) {
        v = substr(val, RSTART, RLENGTH)
        rest = substr(val, RSTART + RLENGTH)
        if (v == "true") {
          if (rest !~ /#[[:space:]]*rationale:[[:space:]]*[^[:space:]]/) {
            print FILENAME ":" FNR ": lfs: true on actions/checkout requires same-line `# rationale: <text>` comment"
          }
        }
      }
    }
    next
  }
' "${files[@]}")

if [[ -n "$violations" ]]; then
  echo "$violations" >&2
  exit 1
fi
exit 0
