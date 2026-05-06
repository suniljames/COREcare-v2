#!/usr/bin/env bash
# Scans v1 reference documents for PHI patterns, absolute filesystem paths,
# and plausible-real-name patterns that should never be committed.
#
# Usage:
#   scripts/check-v1-doc-hygiene.sh <file1.md> [<file2.md> ...]
#
# Exit codes:
#   0  no violations
#   1  one or more files contain a violation
#
# This script is intentionally regex-based and string-only. It does not parse
# markdown structure. Designed to run in pre-commit hooks and in CI.

set -u

if [[ $# -eq 0 ]]; then
  echo "usage: $0 <file1.md> [<file2.md> ...]" >&2
  exit 2
fi

VIOLATIONS=0

# Allowed all-caps placeholder set. Names matching one of these are intentional.
ALLOWED_PLACEHOLDERS_RE='\[(CLIENT_NAME|CLIENT_DOB|CLIENT_MRN|CAREGIVER_NAME|AGENCY_NAME|ADDRESS|PHONE|EMAIL|DIAGNOSIS|MEDICATION|NOTE_TEXT|SHIFT_ID|VISIT_ID|INVOICE_ID|REDACTED)\]'

# Single-word persona-name set. These should not trip the plausible-name heuristic.
PERSONA_WORDS='Caregiver|Client|Family|Member|Agency|Admin|Care|Manager|Super'

# Common English first-words that appear before a capitalized noun in normal prose.
# When the first word of a Capitalized-Capitalized pair is one of these, the pair
# is sentence-initial determiner + noun, not a real name.
STOPWORD_FIRSTS='The|A|An|All|Some|Any|Each|Every|This|That|These|Those|His|Her|Its|Our|Their|My|Your|Such|One|Two|Three|Many|Most|Few|No|Both|Either|Neither'

scan_file() {
  local file="$1"
  local file_violations=0

  if [[ ! -f "$file" ]]; then
    echo "skip: $file not a regular file" >&2
    return 0
  fi

  # 1. SSN-like (XXX-XX-XXXX or XXXXXXXXX in obvious context)
  if grep -nE '\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b' "$file" >/dev/null; then
    echo "$file: SSN-like pattern detected"
    grep -nE '\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b' "$file" | head -3 | sed 's/^/  /'
    file_violations=$((file_violations + 1))
  fi

  # 2. DOB explicit ("DOB:" or "DOB " prefix followed by a date-shaped token)
  if grep -nEi '(^|[^A-Z_\[])DOB[: ][^]]{0,3}[0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4}' "$file" >/dev/null; then
    echo "$file: explicit DOB date pattern detected"
    grep -nEi '(^|[^A-Z_\[])DOB[: ][^]]{0,3}[0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4}' "$file" | head -3 | sed 's/^/  /'
    file_violations=$((file_violations + 1))
  fi

  # 3. US phone numbers (NNN-NNN-NNNN, (NNN) NNN-NNNN). Three-digit area code
  #    excludes route patterns like /admin/v2/123 because of explicit dash format.
  if grep -nE '\b\(?[2-9][0-9]{2}\)?[ -][0-9]{3}-[0-9]{4}\b' "$file" >/dev/null; then
    echo "$file: US phone number pattern detected"
    grep -nE '\b\(?[2-9][0-9]{2}\)?[ -][0-9]{3}-[0-9]{4}\b' "$file" | head -3 | sed 's/^/  /'
    file_violations=$((file_violations + 1))
  fi

  # 4. Absolute filesystem paths (POSIX home, /Users, Windows drive)
  if grep -nE '/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|[A-Z]:\\[A-Za-z]' "$file" >/dev/null; then
    echo "$file: absolute filesystem path detected (/Users/, /home/, or C:\\)"
    grep -nE '/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|[A-Z]:\\[A-Za-z]' "$file" | head -3 | sed 's/^/  /'
    file_violations=$((file_violations + 1))
  fi

  # 5. Plausible-real-name heuristic: two consecutive Capitalized words OUTSIDE
  #    of placeholder syntax, blockquoted strings, code fences, or links, AND
  #    not part of the known persona vocabulary.
  #
  #    The heuristic is intentionally conservative: real names like "Sarah
  #    Johnson" trip it; "Agency Admin" / "Family Member" / "Care Manager" do
  #    not because both words are in the persona vocabulary; "[CLIENT_NAME]"
  #    does not because brackets exclude the match.
  #
  #    We strip out placeholders, bracketed text, code spans, fenced code
  #    blocks, and blockquoted lines before scanning.
  local stripped
  stripped=$(awk '
    BEGIN { in_fence = 0 }
    /^```/ { in_fence = !in_fence; next }
    in_fence { next }
    /^>/ { next }
    /^#+[ ]/ { next }
    {
      gsub(/`[^`]*`/, "")
      gsub(/\[[^]]*\]/, "")
      print
    }
  ' "$file")

  # Find two-word capitalized sequences. Filter out:
  #   (a) pairs where both words are in the persona vocabulary (e.g. "Family Member")
  #   (b) pairs where the first word is a common English stopword (e.g. "The Caregiver")
  local hits
  hits=$(echo "$stripped" | grep -oE '\b[A-Z][a-z]{2,}[ ]+[A-Z][a-z]{2,}\b' | \
    grep -vE "^(${PERSONA_WORDS})[ ]+(${PERSONA_WORDS})\$" | \
    grep -vE "^(${STOPWORD_FIRSTS})[ ]+[A-Z][a-z]+\$" || true)
  if [[ -n "$hits" ]]; then
    echo "$file: plausible real-name pattern detected (two consecutive Capitalized words)"
    echo "$hits" | sort -u | head -3 | sed 's/^/  /'
    echo "  (use a placeholder from the allowed set instead)"
    file_violations=$((file_violations + 1))
  fi

  return "$file_violations"
}

for file in "$@"; do
  scan_file "$file"
  rc=$?
  if [[ "$rc" != 0 ]]; then
    VIOLATIONS=$((VIOLATIONS + rc))
  fi
done

if [[ "$VIOLATIONS" -gt 0 ]]; then
  echo ""
  echo "Hygiene check FAILED with $VIOLATIONS violation group(s) across files."
  echo "Allowed placeholders: see scripts/check-v1-doc-hygiene.sh ALLOWED_PLACEHOLDERS_RE."
  echo "Reference: docs/migration/README.md#phi-placeholder-convention"
  exit 1
fi

exit 0
