#!/usr/bin/env bash
# Tests for scripts/check-v1-caption-phi.sh
# Run from repo root: bash scripts/tests/test_check_v1_caption_phi.sh
#
# Body-scoped check: forbids placeholder identifiers like [CLIENT_NAME] inside
# caption BODY (between the trailing `---` and EOF). Frontmatter values are
# permitted to contain placeholder names (e.g., a route pattern); the body is
# the regulated surface per CAPTION-STYLE.md §PHI references.

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/check-v1-caption-phi.sh"
TEST_DIR=$(mktemp -d -t caption-phi-tests-XXXXXX)
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

write_caption() {
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

echo "== check-v1-caption-phi.sh tests =="

[[ -x "$SCRIPT" ]] || { echo "FAIL — script not executable at $SCRIPT"; exit 1; }

# --- Pass cases ---

# Body uses role-based language, no placeholders
write_caption "$TEST_DIR/clean.md" '**CTAs visible:** "Approve", "Reject".

**Interaction notes:**
- "Approve" → marks the assigned client'"'"'s timesheet approved.
- "Reject" → opens the rejection-reason modal.'
assert_exit "clean caption (no placeholders in body) passes" 0 "$SCRIPT" "$TEST_DIR/clean.md"

# Empty body (just frontmatter, edge case)
cat > "$TEST_DIR/just_fm.md" <<'EOF'
---
canonical_id: agency-admin/099-test
route: /admin/test/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-07
---
EOF
assert_exit "empty body passes" 0 "$SCRIPT" "$TEST_DIR/just_fm.md"

# --- Fail cases: placeholder in body ---

write_caption "$TEST_DIR/client_name.md" '**CTAs visible:** "Edit".

**Interaction notes:**
- "Edit" → opens [CLIENT_NAME]'"'"'s detail view.'
assert_exit "[CLIENT_NAME] in body fails" 1 "$SCRIPT" "$TEST_DIR/client_name.md"
assert_output_contains "violation names file" "client_name.md" "$SCRIPT" "$TEST_DIR/client_name.md"
assert_output_contains "violation names placeholder" "[CLIENT_NAME]" "$SCRIPT" "$TEST_DIR/client_name.md"

write_caption "$TEST_DIR/caregiver_name.md" '**CTAs visible:** "Approve".

**Interaction notes:**
- Row → shows the [CAREGIVER_NAME]'"'"'s shift summary.'
assert_exit "[CAREGIVER_NAME] in body fails" 1 "$SCRIPT" "$TEST_DIR/caregiver_name.md"

write_caption "$TEST_DIR/agency_name.md" '**CTAs visible:** "View".

**Interaction notes:**
- "View" → loads [AGENCY_NAME]'"'"'s settings.'
assert_exit "[AGENCY_NAME] in body fails" 1 "$SCRIPT" "$TEST_DIR/agency_name.md"

# Multiple placeholders in body (only need to flag once, but exit 1)
write_caption "$TEST_DIR/multi.md" '**CTAs visible:** "Edit", "View".

**Interaction notes:**
- "Edit" → opens [CLIENT_NAME]'"'"'s chart.
- "View" → shows [DIAGNOSIS] history.'
assert_exit "multiple placeholders in body fails" 1 "$SCRIPT" "$TEST_DIR/multi.md"

# All allowed placeholders should be detected when in body
for ph in CLIENT_NAME CLIENT_DOB CLIENT_MRN CAREGIVER_NAME AGENCY_NAME ADDRESS PHONE EMAIL DIAGNOSIS MEDICATION NOTE_TEXT SHIFT_ID VISIT_ID INVOICE_ID REDACTED; do
  write_caption "$TEST_DIR/${ph}.md" "**CTAs visible:** \"Edit\".

**Interaction notes:**
- \"Edit\" → opens [${ph}] detail."
  assert_exit "[${ph}] in body fails" 1 "$SCRIPT" "$TEST_DIR/${ph}.md"
done

# --- Frontmatter is exempt: route field with placeholder allowed ---
cat > "$TEST_DIR/fm_allows_placeholder.md" <<'EOF'
---
canonical_id: agency-admin/099-test
route: /admin/clients/[CLIENT_ID]/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-07
---
**CTAs visible:** "Edit".

**Interaction notes:**
- "Edit" → opens the assigned client's chart.
EOF
# Even though [CLIENT_ID] appears in frontmatter route, body is clean → pass.
# (CLIENT_ID isn't in the allowed-placeholder set; this test specifically asserts
# that frontmatter is exempt regardless of token.)
assert_exit "frontmatter placeholder is exempt; clean body passes" 0 \
  "$SCRIPT" "$TEST_DIR/fm_allows_placeholder.md"

# Frontmatter with a body-forbidden placeholder, but body is still clean → pass
cat > "$TEST_DIR/fm_with_client_name.md" <<'EOF'
---
canonical_id: agency-admin/099-test
route: /admin/[CLIENT_NAME]-search/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-07
---
**CTAs visible:** "Search".

**Interaction notes:**
- "Search" → returns matching clients.
EOF
assert_exit "frontmatter [CLIENT_NAME] is exempt; clean body passes" 0 \
  "$SCRIPT" "$TEST_DIR/fm_with_client_name.md"

# --- Multiple files at once ---
assert_exit "multiple clean captions pass" 0 "$SCRIPT" "$TEST_DIR/clean.md" "$TEST_DIR/just_fm.md"
assert_exit "mixed clean + dirty fails" 1 "$SCRIPT" "$TEST_DIR/clean.md" "$TEST_DIR/client_name.md"

# --- Bad invocation ---
assert_exit "no args bails" 2 "$SCRIPT"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
