#!/usr/bin/env bash
# Acceptance test for issue #100: pages-inventory rows for Care Manager
# persona. Asserts the Definition of Done from the issue body:
#   1. ## Care Manager has exactly one ### care_manager H3 (no ### charting).
#   2. ### care_manager has 6 populated route rows.
#   3. All 6 rows are PHI-prefixed (🔒 PHI · ).
#   4. Lead paragraph carries the four required tokens (CareManagerProfile,
#      is_staff=False, @staff_member_required, proxy_chart_view).
#   5. Lead paragraph cross-refs the Agency Admin charting anchor.
#   6. Receipt row's purpose includes the audit-gap phrase + IDOR boundary.
#   7. Coverage subsection has a ### Care Manager block.
#   8. Cross-reference index has the new receipt-route entry.
#   9. _last reconciled:_ line is updated to 2026-05-07 + commit 9738412.
#  10. No "supervising nurse" / "supervising-nurse" leakage in section prose.
#  11. Hygiene + structure scanners pass.
#
# Run from repo root: bash scripts/tests/test_issue_100_care_manager.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INVENTORY="$REPO_ROOT/docs/migration/v1-pages-inventory.md"
HYGIENE="$REPO_ROOT/scripts/check-v1-doc-hygiene.sh"
STRUCTURE="$REPO_ROOT/scripts/check-v1-doc-structure.sh"

PASS=0
FAIL=0

assert() {
  local description="$1"; shift
  if "$@"; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description"
    FAIL=$((FAIL + 1))
  fi
}

# Print lines between (exclusive) two H2 headings — used to scope checks
# to the Care Manager section.
care_manager_section() {
  awk '
    /^## Care Manager$/ { in_section = 1; next }
    in_section && /^## / { in_section = 0 }
    in_section { print }
  ' "$INVENTORY"
}

# Print lines under ### care_manager (exclusive of the H3 line itself,
# stopping at next H3 or H2).
care_manager_h3_block() {
  awk '
    /^### care_manager$/ { in_block = 1; next }
    in_block && /^### / { exit }
    in_block && /^## / { exit }
    in_block { print }
  ' "$INVENTORY"
}

# Print lines under ### Care Manager (Coverage block) — exclusive of the
# H3 line itself, stopping at next H3 or H2.
coverage_care_manager_block() {
  awk '
    /^### Care Manager$/ { in_block = 1; next }
    in_block && /^### / { exit }
    in_block && /^## / { exit }
    in_block { print }
  ' "$INVENTORY"
}

# 1. ## Care Manager has exactly one ### care_manager H3.
care_manager_has_one_h3_care_manager() {
  local count
  count=$(care_manager_section | grep -cE '^### care_manager$' || true)
  [[ "$count" -eq 1 ]]
}

# 2. ## Care Manager does NOT have a ### charting H3 (anchor-stability rule).
care_manager_has_no_h3_charting() {
  ! care_manager_section | grep -qE '^### charting$'
}

# 3. ### care_manager has exactly 6 route rows (lines starting with `| `).
care_manager_h3_has_six_rows() {
  local count
  count=$(care_manager_h3_block | grep -cE '^\| `/care-manager/' || true)
  [[ "$count" -eq 6 ]]
}

# 4. Every route row in ### care_manager has 🔒 PHI · prefix in purpose.
care_manager_rows_phi_prefixed() {
  # All 6 rows expected; if fewer rows have the prefix, fail.
  local prefixed
  prefixed=$(care_manager_h3_block | grep -cE '^\| `/care-manager/.*\| 🔒 PHI · ' || true)
  [[ "$prefixed" -eq 6 ]]
}

# 5a. Lead paragraph contains CareManagerProfile token.
lead_has_caremanagerprofile() {
  care_manager_section | grep -qE 'CareManagerProfile'
}

# 5b. Lead paragraph contains is_staff=False token.
lead_has_is_staff_false() {
  care_manager_section | grep -qE 'is_staff=False'
}

# 5c. Lead paragraph contains @staff_member_required token.
lead_has_staff_member_required() {
  care_manager_section | grep -qE '@staff_member_required'
}

# 5d. Lead paragraph references proxy_chart_view.
lead_has_proxy_chart_view() {
  care_manager_section | grep -qE 'proxy_chart_view'
}

# 6. Lead paragraph contains a markdown link to Agency Admin charting anchor.
lead_links_to_charting_anchor() {
  care_manager_section | grep -qE '\(#charting\)'
}

# 7a. Receipt row contains the verbatim audit-gap phrase.
receipt_row_has_audit_gap_phrase() {
  care_manager_h3_block \
    | grep -E '^\| `/care-manager/expenses/<int:expense_id>/receipt/' \
    | grep -q 'v1 has no audit on this route'
}

# 7b. Receipt row mentions IDOR boundary.
receipt_row_mentions_idor() {
  care_manager_h3_block \
    | grep -E '^\| `/care-manager/expenses/<int:expense_id>/receipt/' \
    | grep -qE 'IDOR'
}

# 7c. Receipt row notes the is_staff short-circuit boundary.
receipt_row_notes_is_staff_boundary() {
  care_manager_h3_block \
    | grep -E '^\| `/care-manager/expenses/<int:expense_id>/receipt/' \
    | grep -qE 'is_staff'
}

# 8. Coverage subsection has a ### Care Manager block.
coverage_has_care_manager_block() {
  awk '
    /^## Coverage/ { in_section = 1; next }
    in_section && /^## / { exit }
    in_section && /^### Care Manager$/ { found = 1; exit }
    END { exit (found ? 0 : 1) }
  ' "$INVENTORY"
}

# 8b. Coverage Care Manager block has care_manager row with 6/6 numerator.
coverage_care_manager_row_complete() {
  coverage_care_manager_block | grep -qE '^\| care_manager \| 6 \| 6 \|'
}

# 9. Cross-reference index has the new receipt-route entry.
xref_index_has_receipt_route() {
  awk '
    /^### Cross-reference index/ { in_section = 1; next }
    in_section && /^### / { exit }
    in_section && /^## / { exit }
    in_section && /\/care-manager\/expenses\/<int:expense_id>\/receipt\/<int:receipt_id>\// { found = 1 }
    END { exit (found ? 0 : 1) }
  ' "$INVENTORY"
}

# 9b. The new entry's primary persona is Care Manager and also-reachable mentions Agency Admin via is_staff.
xref_index_receipt_route_attributes() {
  awk '
    /^### Cross-reference index/ { in_section = 1; next }
    in_section && /^### / { exit }
    in_section && /^## / { exit }
    in_section && /\/care-manager\/expenses\/<int:expense_id>\/receipt\/<int:receipt_id>\// {
      if ($0 ~ /Care Manager/ && $0 ~ /Agency Admin/ && $0 ~ /is_staff/) { found = 1 }
      exit
    }
    END { exit (found ? 0 : 1) }
  ' "$INVENTORY"
}

# 10. _last reconciled:_ line under ## Care Manager has 2026-05-07 + 9738412.
care_manager_last_reconciled_updated() {
  care_manager_section | head -3 | grep -qE '_last reconciled: 2026-05-07 against v1 commit `9738412`_'
}

# 11. No "supervising nurse" leakage in the section's prose.
no_supervising_nurse_leak() {
  ! care_manager_section | grep -qiE 'supervising[ -]?nurse'
}

# 12. Hygiene scanner passes over the inventory.
hygiene_passes() {
  bash "$HYGIENE" "$INVENTORY" >/dev/null 2>&1
}

# 13. Structure scanner passes over docs/migration/.
structure_passes() {
  bash "$STRUCTURE" --dir "$REPO_ROOT/docs/migration" >/dev/null 2>&1
}

echo "== Issue #100 acceptance tests =="

assert "## Care Manager has exactly one ### care_manager H3" care_manager_has_one_h3_care_manager
assert "## Care Manager has NO ### charting H3 (anchor-stability)" care_manager_has_no_h3_charting
assert "### care_manager has 6 route rows" care_manager_h3_has_six_rows
assert "all 6 ### care_manager rows are 🔒 PHI · prefixed" care_manager_rows_phi_prefixed
assert "lead paragraph cites CareManagerProfile" lead_has_caremanagerprofile
assert "lead paragraph cites is_staff=False" lead_has_is_staff_false
assert "lead paragraph cites @staff_member_required" lead_has_staff_member_required
assert "lead paragraph references proxy_chart_view" lead_has_proxy_chart_view
assert "lead paragraph links to (#charting)" lead_links_to_charting_anchor
assert "receipt row contains audit-gap phrase verbatim" receipt_row_has_audit_gap_phrase
assert "receipt row mentions IDOR boundary" receipt_row_mentions_idor
assert "receipt row notes is_staff short-circuit" receipt_row_notes_is_staff_boundary
assert "Coverage subsection has ### Care Manager block" coverage_has_care_manager_block
assert "Coverage care_manager row shows 6/6" coverage_care_manager_row_complete
assert "Cross-reference index has the new receipt-route entry" xref_index_has_receipt_route
assert "Cross-ref index entry: Care Manager primary, Agency Admin via is_staff" xref_index_receipt_route_attributes
assert "_last reconciled:_ updated to 2026-05-07 + 9738412" care_manager_last_reconciled_updated
assert "no 'supervising nurse' / 'supervising-nurse' leak in section" no_supervising_nurse_leak
assert "hygiene scanner passes over inventory" hygiene_passes
assert "structure scanner passes over docs/migration/" structure_passes

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
