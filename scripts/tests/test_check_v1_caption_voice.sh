#!/usr/bin/env bash
# Tests for scripts/check-v1-caption-voice.sh
# Run from repo root: bash scripts/tests/test_check_v1_caption_voice.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/check-v1-caption-voice.sh"
TEST_DIR=$(mktemp -d -t caption-voice-tests-XXXXXX)
trap 'rm -rf "$TEST_DIR"' EXIT

PASS=0
FAIL=0

assert_exit() {
  local description="$1"
  local expected_code="$2"
  shift 2
  local actual_output
  actual_output=$("$@" 2>&1)
  local actual_code=$?
  if [[ "$actual_code" == "$expected_code" ]]; then
    echo "  PASS — $description (exit $actual_code)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description (expected exit $expected_code, got $actual_code)"
    echo "    output: $actual_output"
    FAIL=$((FAIL + 1))
  fi
}

assert_output_contains() {
  local description="$1"
  local needle="$2"
  shift 2
  local actual_output
  actual_output=$("$@" 2>&1 || true)
  if echo "$actual_output" | grep -qF "$needle"; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description (output did not contain: $needle)"
    echo "    actual: $actual_output"
    FAIL=$((FAIL + 1))
  fi
}

write_clean_caption() {
  local path="$1"
  cat > "$path" <<'EOF'
---
canonical_id: agency-admin/015-shifts-list
route: /admin/todays-shifts/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-07
---
**CTAs visible:** "Filter", "Export CSV", "+ New Shift", row-level "Edit" links, row-level "Cancel" links.

**Interaction notes:**
- "Filter" button → opens a panel with date range, caregiver, and client filters.
- "Export CSV" button → downloads the current filtered list as CSV.
- Row-level "Edit" link → navigates to [agency-admin/016-shift-detail](016-shift-detail.md).
- ⚠ destructive: row-level "Cancel" link → POSTs to `/admin/shifts/<id>/cancel/`. Skipped by crawler.
EOF
}

write_caption_with_body() {
  local path="$1"
  local body="$2"
  cat > "$path" <<EOF
---
canonical_id: agency-admin/099-test
route: /admin/test/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-07
---
$body
EOF
}

echo "== check-v1-caption-voice.sh tests =="

[[ -x "$SCRIPT" ]] || { echo "FAIL — script not executable at $SCRIPT"; exit 1; }

# --- Pass cases ---

write_clean_caption "$TEST_DIR/clean.md"
assert_exit "canonical good caption passes" 0 "$SCRIPT" "$TEST_DIR/clean.md"

# Read-only page: explicit CTA-list exception
write_caption_with_body "$TEST_DIR/readonly.md" '**CTAs visible:** none — read-only view.

**Interaction notes:**
- Page → renders client demographic data.'
assert_exit "read-only CTA exception passes" 0 "$SCRIPT" "$TEST_DIR/readonly.md"

# Icon-button positional descriptor in parens (CAPTION-STYLE rule for unlabeled icons)
write_caption_with_body "$TEST_DIR/icon.md" '**CTAs visible:** "calendar icon (top-right header)", "Logout".

**Interaction notes:**
- Calendar icon → opens the calendar overlay.'
assert_exit "icon descriptor with parens passes" 0 "$SCRIPT" "$TEST_DIR/icon.md"

# --- Voice fails: second person ---
write_caption_with_body "$TEST_DIR/you1.md" '**CTAs visible:** "Filter".

**Interaction notes:**
- "Filter" → you can narrow down the list.'
assert_exit "second person ''you'' fails" 1 "$SCRIPT" "$TEST_DIR/you1.md"
assert_output_contains "second-person violation reports word" "you" "$SCRIPT" "$TEST_DIR/you1.md"

write_caption_with_body "$TEST_DIR/your.md" '**CTAs visible:** "Filter".

**Interaction notes:**
- "Filter" → narrows your results.'
assert_exit "''your'' fails" 1 "$SCRIPT" "$TEST_DIR/your.md"

write_caption_with_body "$TEST_DIR/youll.md" '**CTAs visible:** "Filter".

**Interaction notes:**
- "Filter" → you'"'"'ll see fewer results.'
assert_exit "''you'\''ll'' fails" 1 "$SCRIPT" "$TEST_DIR/youll.md"

# --- Voice fails: speculation ---
write_caption_with_body "$TEST_DIR/probably.md" '**CTAs visible:** "Save".

**Interaction notes:**
- "Save" → probably persists changes.'
assert_exit "''probably'' speculation fails" 1 "$SCRIPT" "$TEST_DIR/probably.md"

write_caption_with_body "$TEST_DIR/might.md" '**CTAs visible:** "Save".

**Interaction notes:**
- "Save" → might trigger an email.'
assert_exit "''might'' speculation fails" 1 "$SCRIPT" "$TEST_DIR/might.md"

# --- Voice fails: editorial commentary ---
write_caption_with_body "$TEST_DIR/dated.md" '**CTAs visible:** "Save".

**Interaction notes:**
- The form layout is dated and confusing.
- "Save" → persists changes.'
assert_exit "editorial ''dated'' fails" 1 "$SCRIPT" "$TEST_DIR/dated.md"

write_caption_with_body "$TEST_DIR/should_be.md" '**CTAs visible:** "Save".

**Interaction notes:**
- "Save" → persists changes. This should be replaced in v2.'
assert_exit "editorial ''should be'' fails" 1 "$SCRIPT" "$TEST_DIR/should_be.md"

# --- Voice fails: first person ---
write_caption_with_body "$TEST_DIR/we.md" '**CTAs visible:** "Save".

**Interaction notes:**
- "Save" → we believe this persists changes.'
assert_exit "first-person ''we'' fails" 1 "$SCRIPT" "$TEST_DIR/we.md"

# Bare uppercase "I" — distinct from "in" / "if". RE_FIRST_PERSON_UPPER must catch it.
write_caption_with_body "$TEST_DIR/I_alone.md" '**CTAs visible:** "Save".

**Interaction notes:**
- "Save" → I noted that this persists changes.'
assert_exit "first-person ''I'' fails" 1 "$SCRIPT" "$TEST_DIR/I_alone.md"

# Lowercase "in" / "if" must NOT trip the uppercase-I pattern.
write_caption_with_body "$TEST_DIR/in_if_safe.md" '**CTAs visible:** "Save".

**Interaction notes:**
- "Save" → persists changes if any are pending in the form.'
assert_exit "lowercase ''in''/''if'' do not trip first-person ''I'' detector" 0 "$SCRIPT" "$TEST_DIR/in_if_safe.md"

# Voice-rule words inside DOUBLE-QUOTED CTA labels are exempt — v1 buttons
# can legitimately contain "you/your" in their literal copy. The empty-state
# CTA on the CM expense list page is exactly this case.
write_caption_with_body "$TEST_DIR/literal_label_with_your.md" '**CTAs visible:** "Submit your first expense", "Logout".

**Interaction notes:**
- "Submit your first expense" empty-state link → navigates to the submission form.'
assert_exit "second-person word inside literal CTA label is exempt" 0 \
  "$SCRIPT" "$TEST_DIR/literal_label_with_your.md"

# But second-person OUTSIDE quoted labels still fails.
write_caption_with_body "$TEST_DIR/your_outside_quotes.md" '**CTAs visible:** "Save".

**Interaction notes:**
- "Save" → persists your changes.'
assert_exit "second-person OUTSIDE quoted label still fails" 1 \
  "$SCRIPT" "$TEST_DIR/your_outside_quotes.md"

# --- Format fail: interaction note missing → arrow ---
write_caption_with_body "$TEST_DIR/no_arrow.md" '**CTAs visible:** "Save".

**Interaction notes:**
- "Save" persists changes.
- "Cancel" discards changes.'
assert_exit "interaction note missing → arrow fails" 1 "$SCRIPT" "$TEST_DIR/no_arrow.md"
assert_output_contains "missing arrow violation names format" "→" "$SCRIPT" "$TEST_DIR/no_arrow.md"

# --- Format fail: prose paragraph instead of bullets ---
write_caption_with_body "$TEST_DIR/prose.md" '**CTAs visible:** "Save".

**Interaction notes:**
Clicking the Save button persists changes and reloads the page.'
assert_exit "prose paragraph in interaction notes fails" 1 "$SCRIPT" "$TEST_DIR/prose.md"

# --- Format fail: CTA item not quote-wrapped ---
write_caption_with_body "$TEST_DIR/no_quotes.md" '**CTAs visible:** Filter, Save, Cancel.

**Interaction notes:**
- "Filter" → opens panel.'
assert_exit "unquoted CTA labels fail" 1 "$SCRIPT" "$TEST_DIR/no_quotes.md"
assert_output_contains "unquoted CTA names quote rule" "quote" "$SCRIPT" "$TEST_DIR/no_quotes.md"

# Mixed: some quoted, one not
write_caption_with_body "$TEST_DIR/mixed_quotes.md" '**CTAs visible:** "Filter", Save, "Cancel".

**Interaction notes:**
- "Filter" → opens panel.'
assert_exit "one unquoted CTA among quoted fails" 1 "$SCRIPT" "$TEST_DIR/mixed_quotes.md"

# --- Cross-reference link text rule ---
# Link text must be the canonical_id (persona-slug/NNN-slug), not arbitrary
write_caption_with_body "$TEST_DIR/bad_link.md" '**CTAs visible:** "Edit".

**Interaction notes:**
- "Edit" → navigates to [Shift Detail](../agency-admin/016-shift-detail.md).'
assert_exit "non-canonical-id link text fails" 1 "$SCRIPT" "$TEST_DIR/bad_link.md"

write_caption_with_body "$TEST_DIR/bad_link2.md" '**CTAs visible:** "Edit".

**Interaction notes:**
- "Edit" → navigates to [here](../agency-admin/016-shift-detail.md).'
assert_exit "''here'' link text fails" 1 "$SCRIPT" "$TEST_DIR/bad_link2.md"

# Canonical-id link text passes
write_caption_with_body "$TEST_DIR/good_link.md" '**CTAs visible:** "Edit".

**Interaction notes:**
- "Edit" → navigates to [agency-admin/016-shift-detail](../agency-admin/016-shift-detail.md).'
assert_exit "canonical-id link text passes" 0 "$SCRIPT" "$TEST_DIR/good_link.md"

# --- Frontmatter is excluded from voice scan ---
# A caption whose body is clean must not be flagged just because frontmatter contains "you" in some hypothetical field.
# (Frontmatter has fixed keys; this test is defensive.)
write_caption_with_body "$TEST_DIR/fm_safe.md" '**CTAs visible:** "Save".

**Interaction notes:**
- "Save" → persists changes.'
assert_exit "frontmatter scan-skip works" 0 "$SCRIPT" "$TEST_DIR/fm_safe.md"

# --- Multiple files at once ---
assert_exit "multiple clean files pass" 0 "$SCRIPT" "$TEST_DIR/clean.md" "$TEST_DIR/good_link.md"
assert_exit "mixed clean + dirty fails" 1 "$SCRIPT" "$TEST_DIR/clean.md" "$TEST_DIR/you1.md"

# --- Bad invocation ---
assert_exit "no args bails" 2 "$SCRIPT"
assert_exit "non-existent file fails (handled gracefully)" 0 "$SCRIPT" "$TEST_DIR/does-not-exist.md"
# ^ Same convention as check-v1-doc-hygiene.sh — non-regular-file is a skip warn, not a violation.

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
