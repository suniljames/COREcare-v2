#!/usr/bin/env bash
# Tests for the issue #213 invariant: /define, /design, /implement, /review
# must abort on CLOSED issues unless --force-on-closed is passed.
#
# Three test layers:
#   1. Parser — exercise the position-independent argument parser against
#      multiple input shapes including the integer regex tightening.
#   2. Gate decision — exercise the OPEN/CLOSED × FORCE/NO-FORCE matrix
#      against a function that mirrors the gate body in the four skill
#      markdown files.
#   3. Sync — grep each of the four .claude/commands/{define,design,
#      implement,review}.md files for the canonical gate strings so we
#      catch silent drift between them.
#
# Run from repo root: bash scripts/tests/test_pipeline_state_gate.sh

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEFINE_MD="$REPO_ROOT/.claude/commands/define.md"
DESIGN_MD="$REPO_ROOT/.claude/commands/design.md"
IMPLEMENT_MD="$REPO_ROOT/.claude/commands/implement.md"
REVIEW_MD="$REPO_ROOT/.claude/commands/review.md"
CONTRIBUTING_MD="$REPO_ROOT/CONTRIBUTING.md"

PASS=0
FAIL=0

pass() { echo "  PASS — $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL — $1"; FAIL=$((FAIL + 1)); }

# ---------------------------------------------------------------------------
# Functions under test mirror the bash blocks embedded in the four skill
# markdown files. The sync tests below assert the markdown files contain the
# same key strings so this duplication can't drift silently.
# ---------------------------------------------------------------------------

# Parses positional + --force-on-closed flag from a string of arguments.
# Sets globals: ISSUE_NUMBER, FORCE_ON_CLOSED.
parse_pipeline_args() {
  local input_args="$1"
  FORCE_ON_CLOSED=false
  ISSUE_NUMBER=""
  # Empty input → both fields stay at defaults (bash 3.2 + set -u
  # errors on empty array expansion, so short-circuit).
  [[ -z "$input_args" ]] && return
  ARGS=( $input_args )
  for arg in "${ARGS[@]}"; do
    case "$arg" in
      --force-on-closed) FORCE_ON_CLOSED=true ;;
      *)
        local stripped="${arg##\#}"
        if [[ "$stripped" =~ ^[0-9]+$ ]]; then
          ISSUE_NUMBER="$stripped"
        fi
        ;;
    esac
  done
}

# Returns 0 if the gate would proceed; 1 if it would abort.
# Inputs: $1=ISSUE_STATE ("OPEN"|"CLOSED"), $2=FORCE_ON_CLOSED ("true"|"false")
evaluate_state_gate() {
  local issue_state="$1"
  local force="$2"
  if [[ "$issue_state" == "CLOSED" && "$force" == "false" ]]; then
    return 1  # abort
  fi
  return 0    # proceed
}

# ---------------------------------------------------------------------------
# Layer 1: Parser tests — covers QA test cases 1-5 and 8.
# ---------------------------------------------------------------------------

test_parser_positional_only() {
  parse_pipeline_args "213"
  if [[ "$ISSUE_NUMBER" == "213" && "$FORCE_ON_CLOSED" == "false" ]]; then
    pass "parser: '213' → ISSUE=213, FORCE=false"
  else
    fail "parser: '213' → ISSUE=$ISSUE_NUMBER, FORCE=$FORCE_ON_CLOSED"
  fi
}

test_parser_hash_prefix() {
  parse_pipeline_args "#213"
  if [[ "$ISSUE_NUMBER" == "213" && "$FORCE_ON_CLOSED" == "false" ]]; then
    pass "parser: '#213' → ISSUE=213 (hash stripped)"
  else
    fail "parser: '#213' → ISSUE=$ISSUE_NUMBER, FORCE=$FORCE_ON_CLOSED"
  fi
}

test_parser_trailing_flag() {
  parse_pipeline_args "213 --force-on-closed"
  if [[ "$ISSUE_NUMBER" == "213" && "$FORCE_ON_CLOSED" == "true" ]]; then
    pass "parser: '213 --force-on-closed' → ISSUE=213, FORCE=true"
  else
    fail "parser: trailing-flag: ISSUE=$ISSUE_NUMBER, FORCE=$FORCE_ON_CLOSED"
  fi
}

test_parser_leading_flag() {
  parse_pipeline_args "--force-on-closed 213"
  if [[ "$ISSUE_NUMBER" == "213" && "$FORCE_ON_CLOSED" == "true" ]]; then
    pass "parser: '--force-on-closed 213' → ISSUE=213, FORCE=true"
  else
    fail "parser: leading-flag: ISSUE=$ISSUE_NUMBER, FORCE=$FORCE_ON_CLOSED"
  fi
}

test_parser_flag_only() {
  parse_pipeline_args "--force-on-closed"
  if [[ "$ISSUE_NUMBER" == "" && "$FORCE_ON_CLOSED" == "true" ]]; then
    pass "parser: '--force-on-closed' → ISSUE empty (context-inferred), FORCE=true"
  else
    fail "parser: flag-only: ISSUE=$ISSUE_NUMBER, FORCE=$FORCE_ON_CLOSED"
  fi
}

test_parser_empty() {
  parse_pipeline_args ""
  if [[ "$ISSUE_NUMBER" == "" && "$FORCE_ON_CLOSED" == "false" ]]; then
    pass "parser: '' → ISSUE empty, FORCE=false"
  else
    fail "parser: empty: ISSUE=$ISSUE_NUMBER, FORCE=$FORCE_ON_CLOSED"
  fi
}

test_parser_garbage_token() {
  parse_pipeline_args "12abc"
  # Per QA case 8: regex ^[0-9]+$ rejects mixed tokens; ISSUE_NUMBER stays empty.
  if [[ "$ISSUE_NUMBER" == "" && "$FORCE_ON_CLOSED" == "false" ]]; then
    pass "parser: '12abc' → rejected by regex, ISSUE empty"
  else
    fail "parser: garbage: ISSUE=$ISSUE_NUMBER, FORCE=$FORCE_ON_CLOSED"
  fi
}

test_parser_garbage_token_with_flag() {
  parse_pipeline_args "12abc --force-on-closed"
  # Garbage rejected; flag still parsed.
  if [[ "$ISSUE_NUMBER" == "" && "$FORCE_ON_CLOSED" == "true" ]]; then
    pass "parser: '12abc --force-on-closed' → ISSUE empty, FORCE=true"
  else
    fail "parser: garbage+flag: ISSUE=$ISSUE_NUMBER, FORCE=$FORCE_ON_CLOSED"
  fi
}

test_parser_negative_token_rejected() {
  parse_pipeline_args "-5"
  # Defensive: '-5' is not a valid issue number; regex rejects.
  if [[ "$ISSUE_NUMBER" == "" ]]; then
    pass "parser: '-5' → rejected (no negative issue numbers)"
  else
    fail "parser: '-5' → unexpectedly parsed as ISSUE=$ISSUE_NUMBER"
  fi
}

# ---------------------------------------------------------------------------
# Layer 2: Gate decision tests — covers QA test cases 1-5 (decisions only).
# ---------------------------------------------------------------------------

test_gate_open_proceeds() {
  if evaluate_state_gate "OPEN" "false"; then
    pass "gate: OPEN + force=false → proceed"
  else
    fail "gate: OPEN + force=false should proceed"
  fi
}

test_gate_closed_aborts() {
  if evaluate_state_gate "CLOSED" "false"; then
    fail "gate: CLOSED + force=false should abort"
  else
    pass "gate: CLOSED + force=false → abort"
  fi
}

test_gate_closed_force_proceeds() {
  if evaluate_state_gate "CLOSED" "true"; then
    pass "gate: CLOSED + force=true → proceed (override)"
  else
    fail "gate: CLOSED + force=true should proceed"
  fi
}

test_gate_open_force_proceeds() {
  # Defensive: --force-on-closed on an open issue is a no-op, must not abort.
  if evaluate_state_gate "OPEN" "true"; then
    pass "gate: OPEN + force=true → proceed (force is no-op)"
  else
    fail "gate: OPEN + force=true should proceed"
  fi
}

# ---------------------------------------------------------------------------
# Layer 3: Sync tests — assert all four skill files contain canonical gate
# strings. Catches silent drift between the four files.
# ---------------------------------------------------------------------------

assert_skill_contains_gate() {
  local label="$1"
  local file="$2"
  local missing=0
  local needles=(
    # Heading may be prefixed (e.g. review.md uses phase-numbered headings),
    # so we don't anchor to '## ' — substring is enough to catch drift.
    "Gate: issue state"
    "Mirrors the gate in"
    "FORCE_ON_CLOSED"
    "ISSUE_NUMBER"
    "--force-on-closed"
    'closedByPullRequestsReferences'
    "see issue #213"
    "Pipeline commands abort on closed issues by default"
  )
  for needle in "${needles[@]}"; do
    if ! grep -qF -- "$needle" "$file"; then
      fail "$label missing literal: $needle"
      missing=1
    fi
  done
  [[ "$missing" -eq 0 ]] && pass "$label contains the gate"
}

test_define_md_contains_gate() {
  assert_skill_contains_gate "define.md" "$DEFINE_MD"
}

test_design_md_contains_gate() {
  assert_skill_contains_gate "design.md" "$DESIGN_MD"
}

test_implement_md_contains_gate() {
  assert_skill_contains_gate "implement.md" "$IMPLEMENT_MD"
}

test_review_md_contains_gate() {
  assert_skill_contains_gate "review.md" "$REVIEW_MD"
}

# ---------------------------------------------------------------------------
# Layer 3b: Position tests — gate must precede side-effecting steps in each
# file. We verify by line-number ordering of well-known anchors.
# ---------------------------------------------------------------------------

line_of() {
  # First-match line number for a literal needle. Empty string if missing.
  grep -nF "$1" "$2" | head -1 | cut -d: -f1
}

test_define_gate_before_label_add() {
  local gate label
  gate=$(line_of "## Gate: issue state" "$DEFINE_MD")
  label=$(line_of 'gh label create "pm-reviewed"' "$DEFINE_MD")
  if [[ -n "$gate" && -n "$label" && "$gate" -lt "$label" ]]; then
    pass "define.md: gate ($gate) precedes pm-reviewed label add ($label)"
  else
    fail "define.md: gate=$gate, label=$label (gate must precede label)"
  fi
}

test_design_gate_before_label_add() {
  local gate label
  gate=$(line_of "## Gate: issue state" "$DESIGN_MD")
  label=$(line_of 'gh label create "design-complete"' "$DESIGN_MD")
  if [[ -n "$gate" && -n "$label" && "$gate" -lt "$label" ]]; then
    pass "design.md: gate ($gate) precedes design-complete label add ($label)"
  else
    fail "design.md: gate=$gate, label=$label (gate must precede label)"
  fi
}

test_implement_gate_before_worktree() {
  local gate label worktree branch
  gate=$(line_of "## Gate: issue state" "$IMPLEMENT_MD")
  label=$(line_of 'gh label create "implementing"' "$IMPLEMENT_MD")
  worktree=$(line_of "EnterWorktree" "$IMPLEMENT_MD")
  branch=$(line_of "git fetch origin main" "$IMPLEMENT_MD")
  if [[ -n "$gate" && -n "$label" && "$gate" -lt "$label" ]]; then
    pass "implement.md: gate ($gate) precedes implementing label add ($label)"
  else
    fail "implement.md gate-vs-label: gate=$gate, label=$label"
  fi
  if [[ -n "$gate" && -n "$worktree" && "$gate" -lt "$worktree" ]]; then
    pass "implement.md: gate ($gate) precedes EnterWorktree ($worktree)"
  else
    fail "implement.md gate-vs-worktree: gate=$gate, worktree=$worktree"
  fi
  if [[ -n "$gate" && -n "$branch" && "$gate" -lt "$branch" ]]; then
    pass "implement.md: gate ($gate) precedes branch cut ($branch)"
  else
    fail "implement.md gate-vs-branch: gate=$gate, branch=$branch"
  fi
}

test_review_gate_before_make_check() {
  local gate make_check pr_create merge
  gate=$(line_of "Gate: issue state" "$REVIEW_MD")
  make_check=$(line_of "make check" "$REVIEW_MD")
  pr_create=$(line_of "gh pr create" "$REVIEW_MD")
  merge=$(line_of "gh pr merge" "$REVIEW_MD")
  if [[ -n "$gate" && -n "$make_check" && "$gate" -lt "$make_check" ]]; then
    pass "review.md: gate ($gate) precedes make check ($make_check)"
  else
    fail "review.md gate-vs-make-check: gate=$gate, make_check=$make_check"
  fi
  if [[ -n "$gate" && -n "$pr_create" && "$gate" -lt "$pr_create" ]]; then
    pass "review.md: gate ($gate) precedes gh pr create ($pr_create)"
  else
    fail "review.md gate-vs-pr-create: gate=$gate, pr_create=$pr_create"
  fi
  if [[ -n "$gate" && -n "$merge" && "$gate" -lt "$merge" ]]; then
    pass "review.md: gate ($gate) precedes gh pr merge ($merge)"
  else
    fail "review.md gate-vs-merge: gate=$gate, merge=$merge"
  fi
}

# ---------------------------------------------------------------------------
# Layer 3c: /review-specific clause — must skip silently when no issue is
# derivable (per QA case R2).
# ---------------------------------------------------------------------------

test_review_md_has_skip_silently_clause() {
  if grep -qF -- "skip this gate silently" "$REVIEW_MD"; then
    pass "review.md: contains 'skip this gate silently' clause for issue-less reviews"
  else
    fail "review.md: missing 'skip this gate silently' clause (per QA R2)"
  fi
}

# ---------------------------------------------------------------------------
# Layer 4: Documentation — CONTRIBUTING.md must reference the override.
# ---------------------------------------------------------------------------

test_contributing_documents_override() {
  if grep -qF -- "force-on-closed" "$CONTRIBUTING_MD" \
     && grep -qF -- "#213" "$CONTRIBUTING_MD"; then
    pass "CONTRIBUTING.md: documents --force-on-closed override and links #213"
  else
    fail "CONTRIBUTING.md: missing --force-on-closed override docs or #213 link"
  fi
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

echo "Running issue #213 closed-issue-gate tests..."
echo "Layer 1: parser"
test_parser_positional_only
test_parser_hash_prefix
test_parser_trailing_flag
test_parser_leading_flag
test_parser_flag_only
test_parser_empty
test_parser_garbage_token
test_parser_garbage_token_with_flag
test_parser_negative_token_rejected

echo "Layer 2: gate decision"
test_gate_open_proceeds
test_gate_closed_aborts
test_gate_closed_force_proceeds
test_gate_open_force_proceeds

echo "Layer 3: skill markdown sync"
test_define_md_contains_gate
test_design_md_contains_gate
test_implement_md_contains_gate
test_review_md_contains_gate

echo "Layer 3b: gate position (must precede side effects)"
test_define_gate_before_label_add
test_design_gate_before_label_add
test_implement_gate_before_worktree
test_review_gate_before_make_check

echo "Layer 3c: /review-specific clause"
test_review_md_has_skip_silently_clause

echo "Layer 4: CONTRIBUTING.md"
test_contributing_documents_override

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -gt 0 ]] && exit 1
exit 0
