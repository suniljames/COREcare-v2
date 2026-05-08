#!/usr/bin/env bash
# Voice + format lint for v1 catalog caption files.
#
# Enforces tools/v1-screenshot-catalog/CAPTION-STYLE.md rules that the PHI
# hygiene scripts cannot detect:
#
#   1. Voice — no second person, no first person, no speculation, no
#      editorial commentary.
#   2. Format — every "Interaction notes:" bullet contains the `→` arrow;
#      no prose paragraphs under "Interaction notes:".
#   3. CTA quoting — every comma-separated item under "CTAs visible:"
#      contains a quoted label (or the line is the literal read-only
#      exception).
#   4. Cross-references — markdown links pointing to another caption file
#      have link text equal to the target's canonical_id (e.g.,
#      `agency-admin/016-shift-detail`), not arbitrary prose.
#
# Frontmatter (between leading + trailing `---`) is exempt — only the body
# is scanned.
#
# Usage:
#   scripts/check-v1-caption-voice.sh <caption.md> [<caption2.md> ...]
#
# Exit codes:
#   0  no violations
#   1  one or more files have a violation
#   2  bad invocation (no files passed)

set -u

if [[ $# -eq 0 ]]; then
  echo "usage: $0 <caption.md> [<caption2.md> ...]" >&2
  exit 2
fi

VIOLATIONS=0

# ---- regex patterns ----
# Each pattern targets a specific rule from CAPTION-STYLE.md §Voice / §CTAs.
# Patterns are case-insensitive (grep -i) and use word boundaries.
#
# NOTE: the editorial-commentary regex is intentionally narrow. It catches
# the highest-frequency violation patterns surfaced in CAPTION-STYLE.md
# §Anti-pattern; it does NOT attempt to enumerate all possible negative
# adjectives. Human review (Writer in /design + /review) remains the
# load-bearing layer for tone. Widening the regex would create
# false-positive churn on legitimate observational language.

# Second person
RE_SECOND_PERSON='\b(you|your|you'\''(ll|re|ve|d))\b'
# First person (note: \bI\b is uppercase-only, distinct from "in" / "if")
RE_FIRST_PERSON_LOWER='\b(we|our|us)\b'
RE_FIRST_PERSON_UPPER='\bI\b'
# Speculation
RE_SPECULATION='\b(probably|likely|might|may|seems|appears to)\b'
# Spec/conditional language
RE_CONDITIONAL='\b(should be|could be|would be|ought to)\b'
# Editorial commentary
RE_EDITORIAL='\b(confusing|cluttered|dated|broken|janky|outdated)\b'

scan_caption() {
  local file="$1"
  local file_violations=0

  if [[ ! -f "$file" ]]; then
    echo "skip: $file not a regular file" >&2
    return 0
  fi

  # Body-only extraction. State machine: count `---` markers; emit lines after the second.
  local body
  body=$(awk '
    BEGIN { depth = 0 }
    /^---[[:space:]]*$/ {
      depth++
      next
    }
    depth >= 2 { print }
  ' "$file")

  if [[ -z "$body" ]]; then
    return 0
  fi

  # ---- Voice scan ----
  scan_pattern() {
    local pattern="$1"
    local label="$2"
    local extra_grep_flags="${3:-}"
    local hits
    # shellcheck disable=SC2086
    hits=$(echo "$body" | grep -nE $extra_grep_flags "$pattern" || true)
    if [[ -n "$hits" ]]; then
      echo "$file: $label"
      echo "$hits" | sed 's/^/  /' | head -3
      file_violations=$((file_violations + 1))
    fi
  }

  scan_pattern "$RE_SECOND_PERSON" "second-person voice forbidden (you / your / you'll …)" "-i"
  scan_pattern "$RE_FIRST_PERSON_LOWER" "first-person voice forbidden (we / our / us)" "-i"
  scan_pattern "$RE_FIRST_PERSON_UPPER" "first-person voice forbidden (I)" ""
  scan_pattern "$RE_SPECULATION" "speculation forbidden (probably / might / may / seems / appears to)" "-i"
  scan_pattern "$RE_CONDITIONAL" "conditional/spec language forbidden (should be / could be / ought to)" "-i"
  scan_pattern "$RE_EDITORIAL" "editorial commentary forbidden (confusing / cluttered / dated / broken / janky / outdated)" "-i"

  # ---- Format scan: interaction-notes bullets ----
  # Inside the "**Interaction notes:**" block, every `- ...` bullet must
  # contain the unicode arrow `→`. Block ends at first blank line OR EOF.
  local in_inote=0
  local linenum=0
  local fmt_failed=0
  while IFS= read -r line; do
    linenum=$((linenum + 1))
    if [[ "$line" =~ ^\*\*Interaction\ notes ]]; then
      in_inote=1
      continue
    fi
    if (( in_inote )); then
      # Blank line ends the block.
      if [[ -z "${line//[[:space:]]/}" ]]; then
        in_inote=0
        continue
      fi
      # Bullet line ("- …") must contain →.
      if [[ "$line" =~ ^-[[:space:]] ]]; then
        if [[ "$line" != *"→"* ]]; then
          if (( fmt_failed == 0 )); then
            echo "$file: interaction-notes bullet missing → arrow (use '<element> → <result>')"
            file_violations=$((file_violations + 1))
            fmt_failed=1
          fi
          echo "  body line $linenum: $line" | head -c 160; echo
        fi
      else
        # Non-bullet line in interaction-notes block = prose violation.
        if (( fmt_failed == 0 )); then
          echo "$file: interaction-notes block contains non-bullet line (use '- <element> → <result>' format, no prose)"
          file_violations=$((file_violations + 1))
          fmt_failed=1
        fi
        echo "  body line $linenum: $line" | head -c 160; echo
      fi
    fi
  done <<< "$body"

  # ---- Format scan: CTA quote-wrapping ----
  # Find the **CTAs visible:** line. Skip the read-only exception. Otherwise
  # split on commas; each piece must contain a `"..."` quoted run.
  local cta_line
  cta_line=$(echo "$body" | grep -m1 -E '^\*\*CTAs visible:\*\*' || true)
  if [[ -n "$cta_line" ]]; then
    # Strip the bold-key prefix and trailing period.
    local cta_payload
    cta_payload=$(echo "$cta_line" | sed -E 's/^\*\*CTAs visible:\*\*[[:space:]]+//; s/\.[[:space:]]*$//')
    # Read-only exception.
    if [[ "$cta_payload" != "none — read-only view" ]]; then
      # Split on commas (top-level — not perfect for nested structures, but
      # CTA list grammar is flat per CAPTION-STYLE.md).
      local IFS_BACKUP="$IFS"
      IFS=',' read -ra ITEMS <<< "$cta_payload"
      IFS="$IFS_BACKUP"
      local cta_failed=0
      for item in "${ITEMS[@]}"; do
        # Trim leading/trailing whitespace.
        local trimmed="${item#"${item%%[![:space:]]*}"}"
        trimmed="${trimmed%"${trimmed##*[![:space:]]}"}"
        # Item must contain at least one `"…"` quoted substring.
        if [[ ! "$trimmed" =~ \"[^\"]+\" ]]; then
          if (( cta_failed == 0 )); then
            echo "$file: CTA item not quote-wrapped (CAPTION-STYLE.md §CTAs visible — wrap labels in double quotes)"
            file_violations=$((file_violations + 1))
            cta_failed=1
          fi
          echo "  unquoted item: $trimmed"
        fi
      done
    fi
  fi

  # ---- Cross-reference link text rule ----
  # markdown links: [text](path). When path looks like a caption file
  # (matches `<NNN>-<slug>.md` with optional persona prefix),
  # text must match the canonical_id pattern `<persona>/<NNN>-<slug>`.
  local link_failed=0
  while IFS= read -r line; do
    # Extract all (text, path) tuples on this line. grep -oE for the whole
    # link, then sed to split.
    while IFS= read -r link; do
      [[ -z "$link" ]] && continue
      local text path
      text=$(echo "$link" | sed -E 's/^\[([^]]*)\]\(([^)]*)\)$/\1/')
      path=$(echo "$link" | sed -E 's/^\[([^]]*)\]\(([^)]*)\)$/\2/')
      # Is path a caption file? (matches <NNN>-<slug>.md, optional dirs.)
      if [[ "$path" =~ ^(\.\./)?([a-z-]+/)?[0-9]{3}-[a-z0-9-]+([a-z])?\.md$ ]]; then
        # Link text must match canonical_id pattern.
        if [[ ! "$text" =~ ^[a-z-]+/[0-9]{3}-[a-z0-9-]+([a-z])?$ ]]; then
          if (( link_failed == 0 )); then
            echo "$file: cross-reference link text must equal target canonical_id (e.g., 'agency-admin/016-shift-detail')"
            file_violations=$((file_violations + 1))
            link_failed=1
          fi
          echo "  bad link: [$text]($path)"
        fi
      fi
    done < <(echo "$line" | grep -oE '\[[^]]*\]\([^)]*\)' || true)
  done <<< "$body"

  return "$file_violations"
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
  echo "Caption voice/format check FAILED: $VIOLATIONS violation group(s)."
  echo "Reference: tools/v1-screenshot-catalog/CAPTION-STYLE.md"
  exit 1
fi

exit 0
