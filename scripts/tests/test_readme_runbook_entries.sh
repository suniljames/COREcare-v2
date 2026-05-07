#!/usr/bin/env bash
# Tests for invariants of per-section refresh-runbook entries in
# docs/migration/README.md. The hygiene scanner only covers v1-*.md files,
# so README runbook entries have no automated guardrail without this script.
#
# Run from repo root: bash scripts/tests/test_readme_runbook_entries.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
README="$REPO_ROOT/docs/migration/README.md"

PASS=0
FAIL=0

assert() {
  local description="$1"
  local condition="$2"
  if eval "$condition"; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description"
    echo "    condition: $condition"
    FAIL=$((FAIL + 1))
  fi
}

echo "== README runbook-entry tests =="

[[ -f "$README" ]] || { echo "FAIL — README not found at $README"; exit 1; }

# --- Family Member section refresh entry (#121) ---

assert \
  "Family Member entry header present" \
  "grep -q '^### Family Member section' '$README'"

assert \
  "Family Member entry uses 'extra diff checks' phrase" \
  "grep -q 'extra diff checks' '$README'"

assert \
  "Family Member entry uses 'silent drift' as searchable signal" \
  "grep -q 'silent drift' '$README'"

assert \
  "Family Member entry includes cadence trigger tied to V1 Reference Commit" \
  "grep -qE 'Run these checks every time the.*V1 Reference Commit' '$README'"

assert \
  "Family Member entry references ClientFamilyMember baseline" \
  "grep -q 'ClientFamilyMember' '$README'"

# Placement: line of '### Family Member section' must fall between
# the '## Refresh runbook' header and the '## Related work' header.
runbook_line=$(grep -n '^## Refresh runbook$' "$README" | head -1 | cut -d: -f1)
related_line=$(grep -n '^## Related work$' "$README" | head -1 | cut -d: -f1)
entry_line=$(grep -n '^### Family Member section' "$README" | head -1 | cut -d: -f1)

if [[ -n "$runbook_line" && -n "$related_line" && -n "$entry_line" ]]; then
  assert \
    "Family Member entry placed inside '## Refresh runbook' section (after header, before '## Related work')" \
    "[[ $entry_line -gt $runbook_line && $entry_line -lt $related_line ]]"
else
  echo "  FAIL — placement check skipped: missing one of (runbook=$runbook_line, related=$related_line, entry=$entry_line)"
  FAIL=$((FAIL + 1))
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
