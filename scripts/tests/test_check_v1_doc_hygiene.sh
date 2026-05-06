#!/usr/bin/env bash
# Tests for scripts/check-v1-doc-hygiene.sh
# Run from repo root: bash scripts/tests/test_check_v1_doc_hygiene.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HYGIENE="$REPO_ROOT/scripts/check-v1-doc-hygiene.sh"
FIXTURES="$SCRIPT_DIR/fixtures"

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

echo "== check-v1-doc-hygiene.sh tests =="

[[ -x "$HYGIENE" ]] || { echo "FAIL — hygiene script not executable at $HYGIENE"; exit 1; }

# Clean state
rm -f "$FIXTURES"/*.md

# --- Pass cases ---

cat > "$FIXTURES/clean.md" <<'EOF'
# Clean v1 reference doc

This documents `[CLIENT_NAME]` and `[CAREGIVER_NAME]` interactions.
Reference v1 source: `suniljames/COREcare-access`.
The route `/admin/clients/<id>/` is for `Agency Admin`.
EOF

assert_exit "clean doc with placeholders passes" 0 "$HYGIENE" "$FIXTURES/clean.md"

cat > "$FIXTURES/empty.md" <<'EOF'
EOF
assert_exit "empty file passes" 0 "$HYGIENE" "$FIXTURES/empty.md"

# --- PHI pattern fail cases ---

cat > "$FIXTURES/ssn.md" <<'EOF'
# Doc with SSN-like pattern
Patient SSN: 123-45-6789 (this should never be committed).
EOF
assert_exit "SSN pattern blocks" 1 "$HYGIENE" "$FIXTURES/ssn.md"
assert_output_contains "SSN failure mentions SSN" "SSN" "$HYGIENE" "$FIXTURES/ssn.md"

cat > "$FIXTURES/dob_explicit.md" <<'EOF'
# Doc with DOB
DOB: 03/15/1942
EOF
assert_exit "explicit DOB pattern blocks" 1 "$HYGIENE" "$FIXTURES/dob_explicit.md"

cat > "$FIXTURES/phone.md" <<'EOF'
# Doc with phone
Contact: 555-123-4567
EOF
assert_exit "US phone pattern blocks" 1 "$HYGIENE" "$FIXTURES/phone.md"

# --- Path fail cases ---

cat > "$FIXTURES/users_path.md" <<'EOF'
# Doc with /Users/
v1 source at /Users/suniljames/Code/COREcare-access/
EOF
assert_exit "/Users/ path blocks" 1 "$HYGIENE" "$FIXTURES/users_path.md"
assert_output_contains "users path failure mentions /Users" "/Users/" "$HYGIENE" "$FIXTURES/users_path.md"

cat > "$FIXTURES/home_path.md" <<'EOF'
# Doc with /home/
Local install at /home/sunil/v1.
EOF
assert_exit "/home/ path blocks" 1 "$HYGIENE" "$FIXTURES/home_path.md"

cat > "$FIXTURES/win_path.md" <<'EOF'
# Doc with C:\
Windows install at C:\Users\sunil\v1.
EOF
assert_exit "C:\\ path blocks" 1 "$HYGIENE" "$FIXTURES/win_path.md"

# --- Plausible-name heuristic (simple uppercase-name pattern, two-word) ---
cat > "$FIXTURES/plausible_name.md" <<'EOF'
# Doc with plausible name
Caregiver Sarah Johnson submitted the chart note.
EOF
assert_exit "plausible two-word capitalized name blocks" 1 "$HYGIENE" "$FIXTURES/plausible_name.md"

# Single-word capitalized terms (persona names like "Caregiver") should NOT trip.
cat > "$FIXTURES/persona_only.md" <<'EOF'
# Doc with persona names only
The Caregiver clocks in. The Agency Admin reviews.
A Family Member views recent visit notes.
EOF
assert_exit "persona names alone do not trip name heuristic" 0 "$HYGIENE" "$FIXTURES/persona_only.md"

# Headings can have title-case noun phrases like "Reference Commit" without tripping.
cat > "$FIXTURES/title_case_headings.md" <<'EOF'
# V1 Reference Documentation Set

## V1 Reference Commit

### PHI Placeholder Convention

Some prose follows.
EOF
assert_exit "title-case multi-word headings do not trip name heuristic" 0 "$HYGIENE" "$FIXTURES/title_case_headings.md"

# But PHI patterns inside a heading still block (defense in depth).
cat > "$FIXTURES/phi_in_heading.md" <<'EOF'
# Patient SSN: 123-45-6789

Some prose.
EOF
assert_exit "PHI pattern in heading still blocks" 1 "$HYGIENE" "$FIXTURES/phi_in_heading.md"

# Code-spanned fake names (used as illustrative examples in docs) do not trip.
cat > "$FIXTURES/code_spanned_examples.md" <<'EOF'
# Doc teaching the placeholder convention

Never use plausible-looking fake names like `Jane Doe` or `Sarah Johnson` — use the placeholder set instead.
EOF
assert_exit "code-spanned fake-name examples do not trip name heuristic" 0 "$HYGIENE" "$FIXTURES/code_spanned_examples.md"

# --- Multiple files at once ---
cat > "$FIXTURES/clean2.md" <<'EOF'
# Another clean doc
Uses `[CLIENT_DOB]` and `[MEDICATION]`.
EOF
assert_exit "multiple clean files pass" 0 "$HYGIENE" "$FIXTURES/clean.md" "$FIXTURES/clean2.md"
assert_exit "mixed clean + dirty fails" 1 "$HYGIENE" "$FIXTURES/clean.md" "$FIXTURES/ssn.md"

# --- Cleanup ---
rm -f "$FIXTURES"/*.md

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
