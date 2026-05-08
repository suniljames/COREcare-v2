#!/usr/bin/env bash
# Tests for scripts/check-v1-captions-authored.sh
# Run from repo root: bash scripts/tests/test_check_v1_captions_authored.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/check-v1-captions-authored.sh"
TEST_DIR=$(mktemp -d -t captions-authored-tests-XXXXXX)
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

write_caption_with_todo() {
  local path="$1"
  local cid="$2"
  cat > "$path" <<EOF
---
canonical_id: $cid
route: /admin/example/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
<!-- TODO: author CTAs + interaction notes per CAPTION-STYLE.md (Phase 3) -->
EOF
}

write_caption_authored() {
  local path="$1"
  local cid="$2"
  cat > "$path" <<EOF
---
canonical_id: $cid
route: /admin/example/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Filter", "Export CSV".

**Interaction notes:**
- "Filter" button → opens a filter panel.
- "Export CSV" button → downloads the list as CSV.
EOF
}

echo "== check-v1-captions-authored.sh tests =="

[[ -x "$SCRIPT" ]] || { echo "FAIL — script not executable at $SCRIPT"; exit 1; }

# --- Pass: empty catalog dir (no captions = vacuously authored) ---
mkdir -p "$TEST_DIR/empty-catalog"
assert_exit "empty catalog passes" 0 "$SCRIPT" --catalog "$TEST_DIR/empty-catalog"

# --- Pass: all captions authored ---
mkdir -p "$TEST_DIR/all-authored/agency-admin"
write_caption_authored "$TEST_DIR/all-authored/agency-admin/001-foo.md" "agency-admin/001-foo"
write_caption_authored "$TEST_DIR/all-authored/agency-admin/002-bar.md" "agency-admin/002-bar"
assert_exit "all captions authored passes" 0 "$SCRIPT" --catalog "$TEST_DIR/all-authored"

# --- Fail: one caption still has TODO marker ---
mkdir -p "$TEST_DIR/one-todo/agency-admin"
write_caption_authored "$TEST_DIR/one-todo/agency-admin/001-foo.md" "agency-admin/001-foo"
write_caption_with_todo "$TEST_DIR/one-todo/agency-admin/002-bar.md" "agency-admin/002-bar"
assert_exit "one TODO marker fails" 1 "$SCRIPT" --catalog "$TEST_DIR/one-todo"
assert_output_contains "failure names the file" "002-bar.md" "$SCRIPT" --catalog "$TEST_DIR/one-todo"
assert_output_contains "failure mentions TODO" "TODO" "$SCRIPT" --catalog "$TEST_DIR/one-todo"

# --- Fail: all captions still have TODO markers ---
mkdir -p "$TEST_DIR/all-todo/agency-admin"
write_caption_with_todo "$TEST_DIR/all-todo/agency-admin/001-foo.md" "agency-admin/001-foo"
write_caption_with_todo "$TEST_DIR/all-todo/agency-admin/002-bar.md" "agency-admin/002-bar"
assert_exit "all TODO markers fails" 1 "$SCRIPT" --catalog "$TEST_DIR/all-todo"

# --- Fail: TODO marker in a non-caption-body part still detected ---
# The check is grep-based across the file — the marker is the marker wherever it is.
# But the script should still locate the violating file.
mkdir -p "$TEST_DIR/odd/agency-admin"
cat > "$TEST_DIR/odd/agency-admin/001-foo.md" <<'EOF'
---
canonical_id: agency-admin/001-foo
route: /admin/foo/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Foo".

<!-- TODO: author CTAs + interaction notes per CAPTION-STYLE.md (Phase 3) -->
EOF
assert_exit "TODO marker anywhere in caption fails" 1 "$SCRIPT" --catalog "$TEST_DIR/odd"

# --- Default catalog path: scoped to docs/legacy/v1-ui-catalog by default ---
# Run from a tmpdir so the real repo catalog isn't picked up.
cd "$TEST_DIR"
mkdir -p docs/legacy/v1-ui-catalog/agency-admin
write_caption_authored docs/legacy/v1-ui-catalog/agency-admin/001-foo.md "agency-admin/001-foo"
assert_exit "default catalog path is docs/legacy/v1-ui-catalog (pass)" 0 "$SCRIPT"
write_caption_with_todo docs/legacy/v1-ui-catalog/agency-admin/002-bar.md "agency-admin/002-bar"
assert_exit "default catalog path with TODO fails" 1 "$SCRIPT"
cd "$REPO_ROOT"

# --- Bad invocation ---
assert_exit "missing catalog path arg value bails" 2 "$SCRIPT" --catalog
assert_exit "non-existent catalog dir bails" 2 "$SCRIPT" --catalog "$TEST_DIR/does-not-exist"
assert_exit "unknown arg bails" 2 "$SCRIPT" --bogus-flag

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
