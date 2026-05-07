#!/usr/bin/env bash
# Acceptance test for issue #101: Caregiver pages-inventory section.
# Asserts:
#   1. ## Caregiver contains ### caregiver_dashboard and ### charting H3
#      sub-sections, each with a one-line italicized summary.
#   2. Each H3 sub-section has at least one populated row (not the
#      placeholder).
#   3. Section lead paragraph (between ## Caregiver and the first H3)
#      mentions the actor invariant, the Visit aggregate, and the
#      ProfileCompletionMiddleware gate.
#   4. The Coverage subsection has a `### Caregiver` block with non-zero
#      numerators for both apps and a section total.
#   5. Glossary placeholder list contains 5 new Caregiver-cited terms.
#   6. Shared-routes cross-reference index entries for the 3 charting
#      Caregiver-primary routes are no longer "(pending Caregiver section)".
#   7. Every Caregiver-section row has exactly 10 columns matching the
#      schema-locked order.
#   8. Hygiene + structure scanners pass.
#
# Run from repo root: bash scripts/tests/test_issue_101_caregiver_section.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INVENTORY="$REPO_ROOT/docs/migration/v1-pages-inventory.md"
GLOSSARY="$REPO_ROOT/docs/migration/v1-glossary.md"
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

# Extract the Caregiver section body (between ## Caregiver and the next ## H2).
extract_caregiver_section() {
  awk '
    /^## Caregiver([[:space:]]|$)/ { in_section = 1; next }
    in_section && /^## / { in_section = 0 }
    in_section { print }
  ' "$INVENTORY"
}

# Extract the H3 body within Caregiver section, between `### <name>` and the
# next `### ` or `## `.
extract_h3_body() {
  local h3="$1"
  awk -v h3="$h3" '
    /^## Caregiver([[:space:]]|$)/ { in_persona = 1; next }
    in_persona && /^## / { in_persona = 0 }
    in_persona && $0 ~ "^### " h3 "$" { in_h3 = 1; next }
    in_h3 && /^### / { in_h3 = 0 }
    in_h3 && /^## / { in_h3 = 0 }
    in_h3 { print }
  ' "$INVENTORY"
}

caregiver_has_h3_caregiver_dashboard() {
  extract_caregiver_section | grep -qE '^### caregiver_dashboard$'
}

caregiver_has_h3_charting() {
  extract_caregiver_section | grep -qE '^### charting$'
}

h3_caregiver_dashboard_has_summary() {
  # Summary line `_..._` must appear within the first 6 lines of the H3
  # body (allowing for a blank-then-anchor-then-blank-then-summary pattern
  # where stable anchors are needed for cross-linking).
  extract_h3_body 'caregiver_dashboard' | head -6 | grep -qE '^_.+_$'
}

h3_charting_has_summary() {
  extract_h3_body 'charting' | head -6 | grep -qE '^_.+_$'
}

h3_caregiver_dashboard_has_rows() {
  # At least one route row (line starting with `| ` followed by a backticked
  # path beginning with `/`).
  local count
  count=$(extract_h3_body 'caregiver_dashboard' | grep -cE '^\| `/' || true)
  [[ "$count" -gt 0 ]]
}

h3_charting_has_rows() {
  local count
  count=$(extract_h3_body 'charting' | grep -cE '^\| `/' || true)
  [[ "$count" -gt 0 ]]
}

caregiver_section_lead_mentions_visit_aggregate() {
  # Lead paragraph is the body of the section before the first H3 (excluding
  # the `_last reconciled:_` line and blank lines).
  awk '
    /^## Caregiver([[:space:]]|$)/ { in_section = 1; next }
    in_section && /^### / { exit }
    in_section && /^## / { in_section = 0 }
    in_section { print }
  ' "$INVENTORY" | grep -qE 'Visit'
}

caregiver_section_lead_mentions_profile_completion_middleware() {
  awk '
    /^## Caregiver([[:space:]]|$)/ { in_section = 1; next }
    in_section && /^### / { exit }
    in_section && /^## / { in_section = 0 }
    in_section { print }
  ' "$INVENTORY" | grep -qE 'ProfileCompletionMiddleware'
}

caregiver_section_lead_mentions_actor_scope() {
  awk '
    /^## Caregiver([[:space:]]|$)/ { in_section = 1; next }
    in_section && /^### / { exit }
    in_section && /^## / { in_section = 0 }
    in_section { print }
  ' "$INVENTORY" | grep -qE 'caregiver_id = self'
}

coverage_has_caregiver_block() {
  awk '
    /^### Caregiver$/ { found = 1 }
    END { exit (found ? 0 : 1) }
  ' "$INVENTORY"
}

coverage_caregiver_dashboard_numerator_nonzero() {
  # Within the `### Caregiver` Coverage block, the row whose first cell is
  # `caregiver_dashboard` must have a non-zero numerator (4th cell).
  awk '
    /^### Caregiver$/ { in_section = 1; next }
    in_section && /^### / && !/^### Caregiver$/ { exit }
    in_section && /^\| caregiver_dashboard \|/ {
      n = split($0, cells, "|")
      gsub(/^[ \t]+|[ \t]+$/, "", cells[4])
      if (cells[4] != "0" && cells[4] != "" && cells[4] != "TBD") found = 1
      exit
    }
    END { exit (found ? 0 : 1) }
  ' "$INVENTORY"
}

coverage_caregiver_charting_numerator_nonzero() {
  awk '
    /^### Caregiver$/ { in_section = 1; next }
    in_section && /^### / && !/^### Caregiver$/ { exit }
    in_section && /^\| charting \|/ {
      n = split($0, cells, "|")
      gsub(/^[ \t]+|[ \t]+$/, "", cells[4])
      if (cells[4] != "0" && cells[4] != "" && cells[4] != "TBD") found = 1
      exit
    }
    END { exit (found ? 0 : 1) }
  ' "$INVENTORY"
}

coverage_caregiver_total_present() {
  awk '
    /^### Caregiver$/ { in_section = 1; next }
    in_section && /^### / && !/^### Caregiver$/ { exit }
    in_section && /total \(Caregiver\)/ { found = 1 }
    END { exit (found ? 0 : 1) }
  ' "$INVENTORY"
}

cross_reference_index_charting_no_pending() {
  # The cross-reference index in Shared routes had three rows pointing to
  # `(pending Caregiver section)` for the charting routes. After authoring,
  # the entries must point to the Caregiver section's `### charting` H3, not
  # to a pending placeholder.
  awk '
    /^## Shared routes/ { in_section = 1; next }
    in_section && /^## / { in_section = 0 }
    in_section && /\/charting\/visit\/.*pending Caregiver section/ { found = 1 }
    in_section && /\/charting\/medications\/.*pending Caregiver section/ { found = 1 }
    END { exit (found ? 1 : 0) }
  ' "$INVENTORY"
}

glossary_has_profile_completion_middleware() {
  grep -qE 'ProfileCompletionMiddleware' "$GLOSSARY"
}

glossary_has_shift_offer() {
  grep -qiE '\*\*.*Shift offer.*\*\*' "$GLOSSARY"
}

glossary_has_post_shift_summary() {
  grep -qiE '\*\*.*Post-shift summary.*\*\*' "$GLOSSARY"
}

glossary_has_active_shift() {
  grep -qiE '\*\*.*Active shift.*\*\*' "$GLOSSARY"
}

caregiver_rows_have_ten_columns() {
  # Every row line in the Caregiver section that starts with `| ` and a
  # backticked route must have exactly 10 columns (i.e., 11 pipes).
  local violations
  violations=$(extract_caregiver_section | awk '
    /^\| `/ {
      n = gsub(/\|/, "|")
      if (n != 11) {
        print NR ": " n " pipes (expected 11)"
      }
    }
  ')
  if [[ -z "$violations" ]]; then
    return 0
  fi
  echo "$violations"
  return 1
}

phi_rows_have_phi_prefix() {
  # Every row whose phi_displayed cell is `true` must have a `🔒 PHI · `
  # prefix in the purpose cell. The purpose cell is the 2nd column; the
  # phi_displayed cell is the 9th column. Iterate row-by-row.
  local violations
  violations=$(extract_caregiver_section | awk -F'|' '
    /^\| `/ {
      # Trim cells.
      for (i = 1; i <= NF; i++) {
        gsub(/^[ \t]+|[ \t]+$/, "", $i)
      }
      # $1 is empty (leading pipe), $2 is route, $3 is purpose, ..., $10 is phi_displayed.
      route = $2
      purpose = $3
      phi = $10
      if (phi == "true" && index(purpose, "🔒 PHI ·") == 0) {
        print "row " NR " (" route "): phi_displayed=true but no 🔒 PHI · prefix"
      }
    }
  ')
  if [[ -z "$violations" ]]; then
    return 0
  fi
  echo "$violations"
  return 1
}

dual_url_pairs_have_sibling_pointer() {
  # Six dual-URL pairs in caregiver_dashboard: add-comment, add-mileage,
  # add-reimbursement, each with a clock-out/<id>/ form and a visit/<id>/
  # form. Each row's purpose must say "Same view as `<sibling>`" pointing to
  # the other URL.
  local violations
  for verb in add-comment add-mileage add-reimbursement; do
    if ! extract_h3_body 'caregiver_dashboard' \
         | grep -E "^\| \`/caregiver/clock-out/[^ ]*${verb}/\`" \
         | grep -qE "Same view as"; then
      violations="${violations}clock-out/<id>/${verb}/ row missing 'Same view as' sibling pointer\n"
    fi
    if ! extract_h3_body 'caregiver_dashboard' \
         | grep -E "^\| \`/caregiver/visit/[^ ]*${verb}/\`" \
         | grep -qE "Same view as"; then
      violations="${violations}visit/<id>/${verb}/ row missing 'Same view as' sibling pointer\n"
    fi
  done
  if [[ -z "$violations" ]]; then
    return 0
  fi
  printf '%b' "$violations"
  return 1
}

receipt_row_has_access_control_invariant() {
  # The receipt-stream row must encode the caregiver-ownership scope and
  # the HIPAA-access-log status (preserved or v2-must-add).
  extract_h3_body 'caregiver_dashboard' \
    | grep -E '/caregiver/expenses/.*receipt' \
    | grep -qE '(caregiver ownership|caregiver-ownership|owns the parent expense)'
}

last_reconciled_updated() {
  # The `_last reconciled:_` line under ## Caregiver must reference v1
  # commit `9738412`.
  extract_caregiver_section | head -5 | grep -qE '_last reconciled:.*9738412'
}

hygiene_passes() {
  bash "$HYGIENE" "$INVENTORY" >/dev/null 2>&1
}

structure_passes() {
  bash "$STRUCTURE" --dir "$REPO_ROOT/docs/migration" >/dev/null 2>&1
}

echo "== Issue #101 acceptance tests =="

assert "Caregiver section has ### caregiver_dashboard H3" caregiver_has_h3_caregiver_dashboard
assert "Caregiver section has ### charting H3" caregiver_has_h3_charting
assert "### caregiver_dashboard has one-line summary" h3_caregiver_dashboard_has_summary
assert "### charting has one-line summary" h3_charting_has_summary
assert "### caregiver_dashboard has at least one route row" h3_caregiver_dashboard_has_rows
assert "### charting has at least one route row" h3_charting_has_rows
assert "Section lead mentions Visit aggregate" caregiver_section_lead_mentions_visit_aggregate
assert "Section lead mentions ProfileCompletionMiddleware" caregiver_section_lead_mentions_profile_completion_middleware
assert "Section lead mentions caregiver_id = self actor scope" caregiver_section_lead_mentions_actor_scope
assert "Coverage subsection has ### Caregiver block" coverage_has_caregiver_block
assert "Coverage shows non-zero numerator for caregiver_dashboard" coverage_caregiver_dashboard_numerator_nonzero
assert "Coverage shows non-zero numerator for charting" coverage_caregiver_charting_numerator_nonzero
assert "Coverage has total (Caregiver) row" coverage_caregiver_total_present
assert "Cross-reference index updated (no 'pending Caregiver section' for charting routes)" cross_reference_index_charting_no_pending
assert "Glossary contains ProfileCompletionMiddleware placeholder" glossary_has_profile_completion_middleware
assert "Glossary contains Shift offer placeholder" glossary_has_shift_offer
assert "Glossary contains Post-shift summary placeholder" glossary_has_post_shift_summary
assert "Glossary contains Active shift placeholder" glossary_has_active_shift
assert "Every Caregiver row has exactly 10 columns (11 pipes)" caregiver_rows_have_ten_columns
assert "PHI rows have 🔒 PHI · prefix in purpose" phi_rows_have_phi_prefix
assert "Six dual-URL pairs have 'Same view as' sibling pointer prose" dual_url_pairs_have_sibling_pointer
assert "Receipt-stream row encodes caregiver-ownership access-control invariant" receipt_row_has_access_control_invariant
assert "_last reconciled:_ line references v1 commit 9738412" last_reconciled_updated
assert "hygiene scanner passes over inventory" hygiene_passes
assert "structure scanner passes over docs/migration/" structure_passes

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
