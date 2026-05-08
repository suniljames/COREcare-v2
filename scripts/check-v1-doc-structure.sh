#!/usr/bin/env bash
# Validates structural invariants of the v1 reference document set:
#   1. v1-pages-inventory.md has an H2 section for each of the six personas.
#   2. v1-functionality-delta.md has the cross-reference header
#      "For collaborators without v1 access" as its first H2.
#   3. v1-functionality-delta.md contains no "needs confirmation" residue.
#   4. v1-pages-inventory.md's "## Shared routes" section, if present, is
#      populated — no "_(pending content authoring)_" placeholder, and it
#      contains at least one route row (markdown table row whose first cell
#      starts with a backtick — the route slug).
#   5. v1-pages-inventory.md's "## Family Member" section: every authored
#      route row (table row whose first cell is a backticked route slug)
#      must (a) contain the literal substring `linked-client only`, (b)
#      contain exactly one of the two literal audit-posture phrases —
#      `HIPAA-access-logged in v1` OR
#      `v1 has no audit on this route — v2 design must add` — and (c)
#      begin its `purpose` cell (second cell) with the `🔒 PHI · ` prefix.
#      Issue #103 visibility-scope discipline.
#   6. v1-integrations-and-exports.md, if present, has the locked five-H2 set
#      and the locked six-H3 set under "## External integrations" (CL-1, CL-2),
#      every entry-table header matches the locked schema (SL-1), every
#      v2_status / severity / direction_and_sync cell carries a valid token
#      (SL-2, SL-3, SL-4), and every surfaces_at_routes inventory link
#      resolves against an existing inventory anchor (EL-1, EL-2). Issue #98.
#   7. v1-user-journeys.md, if present, has the **Status:** header form, the
#      six persona H2s, and (when AUTHORED) the per-persona journey-count
#      minimums, the Route trace + Side effects sub-blocks under each H3, and
#      no placeholder / filler residue (JL-1..JL-6). Every anchor citation to
#      v1-pages-inventory.md — whether written as a relative path, an absolute
#      GitHub URL, or a `../blob/<branch>/...` form — resolves to a real
#      heading or <a id> in the inventory (JL-7). Issues #104, #134.
#   8. v1-pages-inventory.md cross-reference index sub-sections (any "###
#      Cross-reference index" heading) keep their mirrored flag values in
#      sync with the canonical persona-section row they link to. Triggers
#      only when the index table header contains BOTH `phi_displayed` and
#      `row location` columns (header-intersection rule — the same machinery
#      picks up future mirrored columns automatically when they appear in
#      both headers). Violation codes:
#        CR-1  route from index not found at the linked anchor (or the row
#              location cell carries no `(#anchor)` link).
#        CR-2  route slug is duplicated under the linked anchor — canonical
#              lookup is ambiguous.
#        CR-3  `phi_displayed` value disagreement between index row and
#              canonical row.
#        CR-4  `phi_displayed` value outside `{true, false}` on either side.
#        CR-5  Cross-reference index header contains a canonical-row column
#              other than `route` (the join key) or `phi_displayed` (the only
#              currently-handled mirrored column). Tripwire — fires before
#              CR-1..CR-4 evaluation and points the developer at #145's design.
#              Issue #212 — guarantees the deferred N-column generalization
#              (#145) gets executed when its trigger condition is met.
#      Issue #124 — drift in this column would silently mis-scope v2's
#      operator-portal HIPAA-minimum-necessary controls.
#   9. docs/migration/README.md `## Refresh runbook` section invariants.
#      Locks the operational shape of the runbook so per-persona override
#      blocks don't silently lose load-bearing instructions. Violation codes:
#        RR-1  `## Refresh runbook` H2 missing.
#        RR-2  `### Refresh order — Agency Admin first` H3 missing or placed
#              outside the Refresh runbook section.
#        RR-3  Persona-section override H3 placed outside the section, OR
#              a near-miss H3 inside the section uses a persona name not in
#              the locked $REQUIRED_PERSONAS set (e.g. "Family Members").
#        RR-4a Persona-section body missing literal `V1 Reference Commit`.
#        RR-4b Persona-section body missing literal
#              `Baseline at the currently-pinned SHA:`.
#        RR-4c Persona-section body missing one or both branching outcome
#              literals (`If any diff is non-empty:` / `If all diffs are empty:`).
#        RR-4d Persona-section body missing literal `'*/urls.py'` or has
#              fewer than 3 distinct `git diff <old>..<new> --` invocations.
#        RR-5  Markdown intra-file anchor link `](#<anchor>)` does not resolve
#              to a heading or `<a id>` in the same README.
#      Issue #132 — extends the structure check to cover the README itself,
#      replacing the standalone `scripts/tests/test_readme_runbook_entries.sh`
#      prototype added in PR #130.
#  10. docs/migration/README.md `.github/workflows/*.yml` path resolution.
#      Locks the workflow filename references in the README so a rename in
#      `.github/workflows/` cannot silently desync the runbook. Violation code:
#        WF-1  Backticked reference of the form `.github/workflows/<name>.yml`
#              in `docs/migration/README.md` does not point to a file on disk
#              (resolved relative to --repo-root, default CWD). One violation
#              emitted per cite-site so multiple stale references in the same
#              README all surface in one CI run.
#      Issue #169 — generalizes the path-drift check QA flagged on #146 beyond
#      a single sentence; fires for every backticked workflow citation.
#
# Usage:
#   scripts/check-v1-doc-structure.sh [--dir <docs-dir>] [--repo-root <path>]
#
# Default --dir is `docs/migration/` (relative to current working directory).
# Default --repo-root is `.` (current working directory) — the production
# invocation runs from the repo root, so workflow paths cited as
# `.github/workflows/<name>.yml` in the README resolve against the real
# `.github/workflows/` directory. Tests override --repo-root to isolate
# fixture-tree resolution.
#
# Exit codes:
#   0  all structural invariants hold
#   1  one or more checks failed

set -u

DIR="docs/migration"
REPO_ROOT="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) DIR="$2"; shift 2 ;;
    --repo-root) REPO_ROOT="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

INVENTORY="$DIR/v1-pages-inventory.md"
DELTA="$DIR/v1-functionality-delta.md"
INTEGRATIONS="$DIR/v1-integrations-and-exports.md"
JOURNEYS="$DIR/v1-user-journeys.md"
GLOSSARY="$DIR/v1-glossary.md"
README="$DIR/README.md"

REQUIRED_PERSONAS=(
  "Super-Admin"
  "Agency Admin"
  "Care Manager"
  "Caregiver"
  "Client"
  "Family Member"
)

VIOLATIONS=0
fail() { echo "FAIL: $1"; VIOLATIONS=$((VIOLATIONS + 1)); }

# --- File presence ---
if [[ ! -f "$INVENTORY" ]]; then
  fail "$INVENTORY does not exist"
fi
if [[ ! -f "$DELTA" ]]; then
  fail "$DELTA does not exist"
fi

# --- Inventory: six persona H2 sections ---
if [[ -f "$INVENTORY" ]]; then
  for persona in "${REQUIRED_PERSONAS[@]}"; do
    # Match line starting with "## " followed by the exact persona string.
    # Anchor with end-of-line OR whitespace so "Care Manager" doesn't match
    # "Care Manager Exec" or similar.
    if ! grep -qE "^## ${persona}([[:space:]]|$)" "$INVENTORY"; then
      fail "$INVENTORY missing H2 section for persona: $persona"
    fi
  done
fi

# --- Inventory: Shared routes section, if present, is populated ---
# The shared-routes section gathers dual-role / portal-switching routes that
# multiple personas reach. While the docset is being authored, the section
# carries a "_(pending content authoring)_" placeholder. Once authored, the
# placeholder must be gone AND the section must contain at least one route
# row — a markdown table row whose first non-pipe character is a backtick
# (the route slug, e.g. `| \`/switch-role/\` |`).
if [[ -f "$INVENTORY" ]]; then
  shared_section=$(awk '
    /^## Shared routes([[:space:]]|$)/ { in_section = 1; next }
    in_section && /^## / { in_section = 0 }
    in_section { print }
  ' "$INVENTORY")
  if [[ -n "$shared_section" ]]; then
    if echo "$shared_section" | grep -qE '_\(pending content authoring\)_'; then
      fail "$INVENTORY '## Shared routes' still has '_(pending content authoring)_' placeholder"
    fi
    if ! echo "$shared_section" | grep -qE '^\|[[:space:]]*`'; then
      fail "$INVENTORY '## Shared routes' contains no route rows (no table row whose first cell is a backticked route slug)"
    fi
  fi
fi

# --- Delta: cross-ref header is the FIRST H2-or-deeper section ---
if [[ -f "$DELTA" ]]; then
  # Find the first heading line at H2 or deeper.
  first_section_heading=$(grep -nE '^##+ ' "$DELTA" | head -1 | cut -d: -f2-)
  if [[ -z "$first_section_heading" ]]; then
    fail "$DELTA contains no H2-or-deeper headings"
  elif ! echo "$first_section_heading" | grep -qE '^## For collaborators without v1 access'; then
    fail "$DELTA first H2 is not 'For collaborators without v1 access'"
    echo "  actual first H2: $first_section_heading"
  fi
fi

# --- Delta: no "needs confirmation" residue, scoped to content body ---
# The intro / legend before the first `---` separator is allowed to mention
# the marker as a convention. Any occurrence after the first separator is
# unresolved residue.
if [[ -f "$DELTA" ]]; then
  body_after_first_separator=$(awk '
    BEGIN { past_separator = 0 }
    /^---[[:space:]]*$/ && !past_separator { past_separator = 1; next }
    past_separator { print }
  ' "$DELTA")
  if echo "$body_after_first_separator" | grep -niE 'needs confirmation' >/dev/null; then
    fail "$DELTA still contains 'needs confirmation' residue (in body, past intro)"
    echo "$body_after_first_separator" | grep -niE 'needs confirmation' | head -3 | sed 's/^/  /'
  fi
fi

# --- Inventory: Family Member rows enforce visibility-scope + audit-posture phrasing (#103) ---
# Each authored route row under `## Family Member` (a markdown table row whose
# first cell is a backticked route slug) must:
#   (a) contain the literal substring `linked-client only`
#   (b) contain exactly one of the two literal audit-posture phrases:
#         `HIPAA-access-logged in v1`
#         `v1 has no audit on this route — v2 design must add`
#   (c) begin its second cell (purpose) with the `🔒 PHI · ` prefix
#
# The two audit-posture phrases are exhaustive — no third option. Forces the
# author to verify the v1 view's audit posture explicitly per row.
if [[ -f "$INVENTORY" ]]; then
  family_section=$(awk '
    /^## Family Member([[:space:]]|$)/ { in_section = 1; next }
    in_section && /^## / { in_section = 0 }
    in_section { print }
  ' "$INVENTORY")
  if [[ -n "$family_section" ]]; then
    # Iterate over each authored row (route slug in backticks as first cell).
    while IFS= read -r row; do
      [[ -z "$row" ]] && continue
      # Extract route slug for error messages: between first pair of backticks.
      route_slug=$(echo "$row" | sed -n 's/^|[[:space:]]*`\([^`]*\)`.*/\1/p')
      [[ -z "$route_slug" ]] && route_slug="<unparseable>"
      # (a) `linked-client only` literal
      if ! echo "$row" | grep -qF 'linked-client only'; then
        fail "$INVENTORY '## Family Member' row '$route_slug' missing literal phrase 'linked-client only'"
      fi
      # (b) exactly one of the two audit-posture phrases
      audit_logged=$(echo "$row" | grep -cF 'HIPAA-access-logged in v1')
      audit_missing=$(echo "$row" | grep -cF 'v1 has no audit on this route — v2 design must add')
      audit_count=$((audit_logged + audit_missing))
      if [[ "$audit_count" -ne 1 ]]; then
        fail "$INVENTORY '## Family Member' row '$route_slug' must contain EXACTLY one of the two audit-posture phrases (found $audit_count: HIPAA-access-logged=$audit_logged, no-audit=$audit_missing)"
      fi
      # (c) purpose cell (second cell) begins with `🔒 PHI · `
      # The first cell is the route; the second is purpose. Extract second cell.
      purpose_cell=$(echo "$row" | awk -F'|' '{ gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3); print $3 }')
      if [[ "$purpose_cell" != "🔒 PHI · "* ]]; then
        fail "$INVENTORY '## Family Member' row '$route_slug' purpose cell must begin with '🔒 PHI · ' prefix (got: '${purpose_cell:0:40}…')"
      fi
    done < <(echo "$family_section" | grep -E '^\|[[:space:]]*`')
  fi
fi

# --- Integrations-and-exports doc: structure + cell-token + anchor checks (#98) ---
# CL-1 locks the H2 set; CL-2 locks the H3 set under "## External integrations".
# SL-1..SL-4 lock entry-table column order and per-cell token validity.
# EL-1..EL-2 confirm every surfaces_at_routes inventory link resolves to a real
# heading anchor in v1-pages-inventory.md (or a literal "no UI surface" marker).
INTEGRATIONS_REQUIRED_H2S=(
  "## Schema"
  "## External integrations"
  "## Internal notification and email backend"
  "## Customer-facing exports"
  "## Cross-references"
)
INTEGRATIONS_EXTERNAL_H3S=(
  "### Billing and payments"
  "### Payroll"
  "### Accounting"
  "### Messaging and notifications (third-party)"
  "### Identity, auth, and SSO (third-party)"
  "### Other"
)
INTEGRATIONS_SCHEMA_HEADER='| name | vendor_or_internal | trigger | direction_and_sync | surfaces_at_routes | customer_visibility | v2_status | severity |'

if [[ -f "$INTEGRATIONS" ]]; then
  # CL-1: exact set of H2s. Sort both sides so order doesn't matter.
  actual_h2s=$(grep -E '^## ' "$INTEGRATIONS" | sed -E 's/[[:space:]]+$//' | sort)
  expected_h2s=$(printf '%s\n' "${INTEGRATIONS_REQUIRED_H2S[@]}" | sort)
  if [[ "$actual_h2s" != "$expected_h2s" ]]; then
    fail "$INTEGRATIONS H2 sections do not match locked set (CL-1)"
    diff <(echo "$expected_h2s") <(echo "$actual_h2s") | sed 's/^/  /'
  fi

  # CL-2: exact set of H3s under "## External integrations".
  external_section=$(awk '
    /^## External integrations[[:space:]]*$/ { in_section = 1; next }
    in_section && /^## / { in_section = 0 }
    in_section { print }
  ' "$INTEGRATIONS")
  external_h3s=$(echo "$external_section" | grep -E '^### ' | sed -E 's/[[:space:]]+$//' | sort)
  expected_h3s=$(printf '%s\n' "${INTEGRATIONS_EXTERNAL_H3S[@]}" | sort)
  if [[ "$external_h3s" != "$expected_h3s" ]]; then
    fail "$INTEGRATIONS '## External integrations' H3 sub-sections do not match locked set (CL-2)"
    diff <(echo "$expected_h3s") <(echo "$external_h3s") | sed 's/^/  /'
  fi

  # SL-1, SL-2, SL-3, SL-4, EL-1, EL-2 — single awk pass that
  # (1) builds an anchor-set from the inventory file, then
  # (2) walks entry tables in the integrations doc and emits a violation per
  #     bad cell, prefixed with file:line.
  if [[ -f "$INVENTORY" ]]; then
    awk_violations=$(awk -v EXPECTED_HEADER="$INTEGRATIONS_SCHEMA_HEADER" '
      function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
      # GFM-style anchor approximation: lowercase, spaces -> "-", drop chars
      # outside [a-z0-9_-]. Matches GitHub auto-anchors for the heading shapes
      # used in v1-pages-inventory.md (verified against #agency-admin,
      # #top-level-elitecareurlspy, #auth_service, etc.).
      function to_anchor(s,   a) {
        a = tolower(s)
        gsub(/[ \t]+/, "-", a)
        gsub(/[^a-z0-9_-]/, "", a)
        return a
      }

      # Pass 1: inventory -> anchor set.
      NR == FNR {
        if ($0 ~ /^## /) {
          ANCHORS[to_anchor(substr($0, 4))] = 1
        } else if ($0 ~ /^### /) {
          ANCHORS[to_anchor(substr($0, 5))] = 1
        }
        # Explicit anchor tags: <a id="..."></a>
        line = $0
        while (match(line, /<a id="[^"]+"/)) {
          a = substr(line, RSTART + 7, RLENGTH - 8)
          ANCHORS[a] = 1
          line = substr(line, RSTART + RLENGTH)
        }
        next
      }

      # Pass 2: integrations doc.
      {
        # Detect entry-table header (contains the v2_status column name).
        if ($0 ~ /\| *v2_status *\|/) {
          in_entry_table = 1
          entry_row_seen = 0
          if ($0 != EXPECTED_HEADER) {
            print FILENAME ":" FNR ": SL-1: entry-table header does not match locked schema"
            print "  expected: " EXPECTED_HEADER
            print "  actual:   " $0
          }
          next
        }
        if (in_entry_table) {
          # Leaving the table? (blank line or non-pipe)
          if ($0 !~ /^\|/) {
            in_entry_table = 0
            next
          }
          # Separator row immediately after header.
          if (entry_row_seen == 0 && $0 ~ /^\|[- :|]+\|[[:space:]]*$/) {
            entry_row_seen = 1
            next
          }
          # Data row.
          n = split($0, cells, /\|/)
          # cells[1] is empty (before first pipe); cells[n] is empty (after last).
          # Real cells live in cells[2..n-1]. Locked schema has 8 columns.
          if (n - 2 != 8) {
            print FILENAME ":" FNR ": SL-1: data row has " (n - 2) " cells, expected 8"
            next
          }
          name      = trim(cells[2])
          vendor    = trim(cells[3])
          trigger   = trim(cells[4])
          direction = trim(cells[5])
          surfaces  = trim(cells[6])
          visibility= trim(cells[7])
          v2_status = trim(cells[8])
          severity  = trim(cells[9])

          # SL-2: v2_status token validity.
          if (v2_status !~ /^(implemented|scaffolded|missing)$/) {
            print FILENAME ":" FNR ": SL-2: v2_status='\''" v2_status "'\'' not in {implemented, scaffolded, missing}"
          }
          # SL-3: severity token validity, conditional on v2_status.
          if (severity != "" && severity !~ /^(H|M|L|D)$/) {
            print FILENAME ":" FNR ": SL-3: severity='\''" severity "'\'' not in {H, M, L, D, empty}"
          }
          if (severity == "" && v2_status == "missing") {
            print FILENAME ":" FNR ": SL-3: severity is empty but v2_status='\''missing'\'' (severity required)"
          }
          if (severity != "" && v2_status != "missing") {
            print FILENAME ":" FNR ": SL-3: severity='\''" severity "'\'' set but v2_status='\''" v2_status "'\'' (severity allowed only when v2_status=missing)"
          }
          # SL-4: direction_and_sync regex.
          if (direction !~ /^(inbound|outbound|bidirectional);[ \t]*(sync|async)$/) {
            print FILENAME ":" FNR ": SL-4: direction_and_sync='\''" direction "'\'' does not match (inbound|outbound|bidirectional); (sync|async)"
          }
          # EL-2: surfaces_at_routes content rule.
          if (surfaces == "") {
            print FILENAME ":" FNR ": EL-2: surfaces_at_routes is empty"
          } else if (surfaces ~ /_no UI surface/) {
            # Operator-only / orphan marker; pass.
          } else {
            tmp = surfaces
            found_link = 0
            while (match(tmp, /\(v1-pages-inventory\.md#[^)]+\)/)) {
              link = substr(tmp, RSTART, RLENGTH)
              # Strip the "(v1-pages-inventory.md#" prefix and closing ")".
              anchor = substr(link, 24, length(link) - 24)
              found_link = 1
              if (!(anchor in ANCHORS)) {
                print FILENAME ":" FNR ": EL-1: anchor '\''" anchor "'\'' not found in v1-pages-inventory.md"
              }
              tmp = substr(tmp, RSTART + RLENGTH)
            }
            if (!found_link) {
              print FILENAME ":" FNR ": EL-2: surfaces_at_routes has no inventory link and no '\''_no UI surface_'\'' marker"
            }
          }
        }
      }
    ' "$INVENTORY" "$INTEGRATIONS")
    if [[ -n "$awk_violations" ]]; then
      while IFS= read -r line; do
        # Each awk line that begins with "<file>:<line>: " is a primary
        # violation; lines that don't match are continuation context.
        if [[ "$line" =~ ^[^:]+:[0-9]+:[[:space:]] ]]; then
          fail "$line"
        else
          echo "$line"
        fi
      done <<< "$awk_violations"
    fi
  fi
fi

# --- v1-user-journeys.md (#104) ---
# Validates the journeys doc once it has been authored. Until the status header
# flips from SCAFFOLDED to AUTHORED, journey-block checks are skipped (the
# scaffold's "_pending content authoring_" placeholders would otherwise produce
# noisy violations during partial drafts). The status-header form itself, the
# six persona H2s, and link integrity are validated in every state.
#
# JL-1: status header is "AUTHORED. Last reconciled: YYYY-MM-DD against
#       v1 commit `<sha>`." once authoring is complete.
# JL-2: six persona H2 sections present (always).
# JL-3: per-persona journey count meets locked minimums (Super-Admin ≥2,
#       Agency Admin ≥5, Care Manager ≥2, Caregiver ≥4, Client ≥2,
#       Family Member ≥3) — gated on AUTHORED.
# JL-4: no "_pending content authoring_" placeholder remains — gated on
#       AUTHORED.
# JL-5: no "**Failure-mode UX:** None" filler — gated on AUTHORED.
# JL-6: every H3 under a persona section carries both a "**Route trace:**"
#       and a "**Side effects:**" sub-block — gated on AUTHORED.
# JL-7: every link to v1-pages-inventory.md#<anchor> resolves against an
#       existing heading or explicit <a id> in the inventory (always).
if [[ -f "$JOURNEYS" ]]; then
  # JL-1: status header form (only enforced once flipped).
  status_line=$(grep -E '^\*\*Status:\*\*' "$JOURNEYS" | head -1)
  if [[ -z "$status_line" ]]; then
    fail "$JOURNEYS missing **Status:** header line"
    JOURNEYS_AUTHORED=0
  elif echo "$status_line" | grep -qE '^\*\*Status:\*\* SCAFFOLDED'; then
    JOURNEYS_AUTHORED=0
  elif echo "$status_line" | grep -qE '^\*\*Status:\*\* AUTHORED\. Last reconciled: [0-9]{4}-[0-9]{2}-[0-9]{2} against v1 commit `[0-9a-f]{7,40}`\.[[:space:]]*$'; then
    JOURNEYS_AUTHORED=1
  else
    fail "$JOURNEYS **Status:** header malformed; expected exactly 'SCAFFOLDED.' or 'AUTHORED. Last reconciled: YYYY-MM-DD against v1 commit \`<sha>\`.' (got: $status_line)"
    JOURNEYS_AUTHORED=0
  fi

  # JL-2: persona H2 sections (always).
  for persona in "${REQUIRED_PERSONAS[@]}"; do
    if ! grep -qE "^## ${persona}([[:space:]]|$)" "$JOURNEYS"; then
      fail "$JOURNEYS missing H2 section for persona: $persona"
    fi
  done

  if [[ "${JOURNEYS_AUTHORED:-0}" == "1" ]]; then
    # JL-3: per-persona journey count minimums.
    # Pipe-separated "persona|min" pairs (no associative arrays — bash 3.2).
    JL3_PAIRS=(
      "Super-Admin|2"
      "Agency Admin|5"
      "Care Manager|2"
      "Caregiver|4"
      "Client|2"
      "Family Member|3"
    )
    for pair in "${JL3_PAIRS[@]}"; do
      persona="${pair%|*}"
      min="${pair##*|}"
      count=$(awk -v p="$persona" '
        $0 ~ ("^## " p "([[:space:]]|$)") { in_section = 1; next }
        in_section && /^## / { in_section = 0 }
        in_section && /^### / { c++ }
        END { print (c+0) }
      ' "$JOURNEYS")
      if (( count < min )); then
        fail "$JOURNEYS persona '$persona' has $count journey H3s; minimum is $min"
      fi
    done

    # JL-4: no _pending content authoring_ placeholder.
    if grep -q "_pending content authoring_" "$JOURNEYS"; then
      fail "$JOURNEYS still contains '_pending content authoring_' placeholder"
    fi

    # JL-5: no "**Failure-mode UX:** None" filler.
    if grep -qE '\*\*Failure-mode UX:\*\* (None|none|N/A|n/a)\b' "$JOURNEYS"; then
      fail "$JOURNEYS contains '**Failure-mode UX:** None|none|N/A' filler — omit the line entirely instead"
    fi

    # JL-6: each H3 inside a persona H2 carries Route trace + Side effects.
    jl6_violations=$(awk '
      BEGIN {
        personas[1] = "Super-Admin"
        personas[2] = "Agency Admin"
        personas[3] = "Care Manager"
        personas[4] = "Caregiver"
        personas[5] = "Client"
        personas[6] = "Family Member"
      }
      function flush_block() {
        if (in_h3) {
          if (!seen_route_trace) {
            print FILENAME ":" h3_line ": JL-6: journey \"" h3_title "\" missing **Route trace:** sub-block"
          }
          if (!seen_side_effects) {
            print FILENAME ":" h3_line ": JL-6: journey \"" h3_title "\" missing **Side effects:** sub-block"
          }
        }
      }
      /^## / {
        flush_block()
        in_h3 = 0
        in_persona = 0
        for (i = 1; i <= 6; i++) {
          pat = "^## " personas[i] "([[:space:]]|$)"
          if ($0 ~ pat) { in_persona = 1; break }
        }
        next
      }
      /^### / {
        flush_block()
        if (in_persona) {
          in_h3 = 1
          h3_title = substr($0, 5)
          sub(/[[:space:]]+$/, "", h3_title)
          h3_line = NR
          seen_route_trace = 0
          seen_side_effects = 0
        } else {
          in_h3 = 0
        }
        next
      }
      in_h3 && /\*\*Route trace:\*\*/ { seen_route_trace = 1 }
      in_h3 && /\*\*Side effects:\*\*/ { seen_side_effects = 1 }
      END { flush_block() }
    ' "$JOURNEYS")
    if [[ -n "$jl6_violations" ]]; then
      while IFS= read -r line; do fail "$line"; done <<< "$jl6_violations"
    fi
  fi

  # JL-7: anchor-resolution against inventory (always — also catches scaffold drift).
  if [[ -f "$INVENTORY" ]]; then
    jl7_violations=$(awk '
      function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
      function to_anchor(s,   a) {
        a = tolower(s)
        gsub(/[ \t]+/, "-", a)
        gsub(/[^a-z0-9_-]/, "", a)
        return a
      }
      NR == FNR {
        if ($0 ~ /^#+ /) {
          h = $0
          sub(/^#+[[:space:]]*/, "", h)
          ANCHORS[to_anchor(trim(h))] = 1
        }
        line = $0
        while (match(line, /<a id="[^"]+"/)) {
          a = substr(line, RSTART + 7, RLENGTH - 8)
          ANCHORS[a] = 1
          line = substr(line, RSTART + RLENGTH)
        }
        next
      }
      {
        # `[^()]*` permits any non-paren prefix between the opening `(` and the
        # literal `v1-pages-inventory.md#`, covering all three target forms:
        #   - relative:                (v1-pages-inventory.md#anchor)
        #   - absolute GitHub URL:     (https://github.com/<o>/<r>/blob/<b>/docs/migration/v1-pages-inventory.md#anchor)
        #   - sibling-blob form:       (../blob/<branch>/docs/migration/v1-pages-inventory.md#anchor)
        # Note: `[^()]*v1-pages-inventory.md` would also match a hypothetical
        # `*-v1-pages-inventory.md` sibling file. No such file exists in the
        # docset today; this is a known collateral-match shape.
        line = $0
        while (match(line, /\([^()]*v1-pages-inventory\.md#[^)]+\)/)) {
          link = substr(line, RSTART, RLENGTH)
          # Find the literal marker inside the captured link and slice the
          # anchor from immediately after it to immediately before the closing ")".
          # `index()` does not mutate RSTART/RLENGTH (only `match()` does).
          marker_pos = index(link, "v1-pages-inventory.md#")
          anchor_start = marker_pos + 22   # length of "v1-pages-inventory.md#"
          anchor = substr(link, anchor_start, length(link) - anchor_start)
          if (!(anchor in ANCHORS)) {
            print FILENAME ":" FNR ": JL-7: anchor \"" anchor "\" not found in v1-pages-inventory.md"
          }
          line = substr(line, RSTART + RLENGTH)
        }
      }
    ' "$INVENTORY" "$JOURNEYS")
    if [[ -n "$jl7_violations" ]]; then
      while IFS= read -r line; do fail "$line"; done <<< "$jl7_violations"
    fi
  fi
fi

# --- v1-glossary.md (#105) ---
# Validates the glossary doc once it has been authored. The status header
# gates block-level checks: a SCAFFOLDED prefix skips them (so the in-flight
# scaffold doesn't emit noisy violations during partial drafts); the
# AUTHORED form turns them on. Anchor resolution against the inventory,
# journeys, and integrations docs is always-on, mirroring JL-7.
#
# GL-1: status header is "**Status:** SCAFFOLDED..." (any trailing prose)
#       OR "**Status:** AUTHORED. Last reconciled: YYYY-MM-DD against
#       v1 commit `<sha>`." (exact form). Missing or malformed fails.
# GL-2: when AUTHORED, no placeholder markers remain — `_(pending)_`,
#       `_(definitions pending)_`, `_(definitions pending content authoring`,
#       `_(pending content authoring)_`. Anything that announces itself
#       as not-yet-authored.
# GL-3: every link from the glossary to v1-pages-inventory.md#anchor,
#       v1-user-journeys.md#anchor, or v1-integrations-and-exports.md#anchor
#       resolves against an existing heading or explicit <a id> in the
#       target doc. Always-on. If a target doc is absent on disk, links
#       into it are reported as orphan (the glossary cannot point at a
#       doc the docset omits).
if [[ -f "$GLOSSARY" ]]; then
  # GL-1: status header form (always enforced).
  glossary_status_line=$(grep -E '^\*\*Status:\*\*' "$GLOSSARY" | head -1)
  if [[ -z "$glossary_status_line" ]]; then
    fail "$GLOSSARY missing **Status:** header line"
    GLOSSARY_AUTHORED=0
  elif echo "$glossary_status_line" | grep -qE '^\*\*Status:\*\* SCAFFOLDED'; then
    GLOSSARY_AUTHORED=0
  elif echo "$glossary_status_line" | grep -qE '^\*\*Status:\*\* AUTHORED\. Last reconciled: [0-9]{4}-[0-9]{2}-[0-9]{2} against v1 commit `[0-9a-f]{7,40}`\.[[:space:]]*$'; then
    GLOSSARY_AUTHORED=1
  else
    fail "$GLOSSARY **Status:** header malformed; expected exactly 'SCAFFOLDED.' or 'AUTHORED. Last reconciled: YYYY-MM-DD against v1 commit \`<sha>\`.' (got: $glossary_status_line)"
    GLOSSARY_AUTHORED=0
  fi

  if [[ "${GLOSSARY_AUTHORED:-0}" == "1" ]]; then
    # GL-2: no placeholder/pending markers.
    GL2_PATTERNS=(
      '_(pending)_'
      '_(definitions pending)_'
      '_(definitions pending content authoring'
      '_(pending content authoring)_'
    )
    for pat in "${GL2_PATTERNS[@]}"; do
      if grep -qF "$pat" "$GLOSSARY"; then
        fail "$GLOSSARY still contains placeholder marker '$pat'"
      fi
    done
  fi

  # GL-3: anchor resolution against inventory, journeys, integrations (always).
  # Build per-target anchor sets, then walk the glossary and emit a violation
  # per orphan link. Mirrors JL-7's awk pattern but keyed on three target docs.
  # If a target doc is absent on disk, its anchor set stays empty — links
  # into it will report as orphan, which is the desired behavior (the
  # glossary cannot point at a doc the docset omits).
  gl3_target_files=()
  [[ -f "$INVENTORY" ]]    && gl3_target_files+=("$INVENTORY")
  [[ -f "$JOURNEYS" ]]     && gl3_target_files+=("$JOURNEYS")
  [[ -f "$INTEGRATIONS" ]] && gl3_target_files+=("$INTEGRATIONS")
  gl3_violations=$(awk '
    function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
    function to_anchor(s,   a) {
      a = tolower(s)
      gsub(/[ \t]+/, "-", a)
      gsub(/[^a-z0-9_-]/, "", a)
      return a
    }
    # Pass 1..3: collect anchors per target file. FILENAME tracks which file
    # is currently being read; we tag anchors with a target prefix.
    FNR == 1 {
      f = FILENAME
      if (f ~ /v1-pages-inventory\.md$/)            { TARGET = "INV" }
      else if (f ~ /v1-user-journeys\.md$/)         { TARGET = "JRN" }
      else if (f ~ /v1-integrations-and-exports\.md$/) { TARGET = "ITG" }
      else if (f ~ /v1-glossary\.md$/)              { TARGET = "GLS" }
      else                                           { TARGET = "OTHER" }
    }
    # Pre-glossary passes: collect anchors.
    TARGET != "GLS" {
      if ($0 ~ /^#+ /) {
        h = $0
        sub(/^#+[[:space:]]*/, "", h)
        ANCHORS[TARGET, to_anchor(trim(h))] = 1
      }
      line = $0
      while (match(line, /<a id="[^"]+"/)) {
        a = substr(line, RSTART + 7, RLENGTH - 8)
        ANCHORS[TARGET, a] = 1
        line = substr(line, RSTART + RLENGTH)
      }
      next
    }
    # Glossary pass: resolve outbound links.
    TARGET == "GLS" {
      line = $0
      while (match(line, /\(v1-pages-inventory\.md#[^)]+\)/)) {
        link = substr(line, RSTART, RLENGTH)
        anchor = substr(link, 24, length(link) - 24)
        if (!(("INV", anchor) in ANCHORS)) {
          print FILENAME ":" FNR ": GL-3: anchor \"" anchor "\" not found in v1-pages-inventory.md"
        }
        line = substr(line, RSTART + RLENGTH)
      }
      line = $0
      while (match(line, /\(v1-user-journeys\.md#[^)]+\)/)) {
        link = substr(line, RSTART, RLENGTH)
        # "(v1-user-journeys.md#" is 21 chars; anchor starts at char 22.
        anchor = substr(link, 22, length(link) - 22)
        if (!(("JRN", anchor) in ANCHORS)) {
          print FILENAME ":" FNR ": GL-3: anchor \"" anchor "\" not found in v1-user-journeys.md"
        }
        line = substr(line, RSTART + RLENGTH)
      }
      line = $0
      while (match(line, /\(v1-integrations-and-exports\.md#[^)]+\)/)) {
        link = substr(line, RSTART, RLENGTH)
        # "(v1-integrations-and-exports.md#" is 32 chars; anchor starts at char 33.
        anchor = substr(link, 33, length(link) - 33)
        if (!(("ITG", anchor) in ANCHORS)) {
          print FILENAME ":" FNR ": GL-3: anchor \"" anchor "\" not found in v1-integrations-and-exports.md"
        }
        line = substr(line, RSTART + RLENGTH)
      }
    }
  ' "${gl3_target_files[@]}" "$GLOSSARY")
  if [[ -n "$gl3_violations" ]]; then
    while IFS= read -r line; do fail "$line"; done <<< "$gl3_violations"
  fi
fi

# --- Inventory: cross-reference index ↔ canonical row consistency (#124) ---
# Two-pass awk over v1-pages-inventory.md. Pass 1 builds a map keyed by
# (anchor, route_slug) → "<line>|<phi_displayed>" by walking persona-section
# tables; cross-reference index sub-sections are explicitly skipped during
# this pass so their mirrored rows do not pollute the canonical map. Pass 2
# walks every "### Cross-reference index" sub-section and, for indexes whose
# header contains both `phi_displayed` and `row location`, compares each row's
# mirrored flag against the canonical row found via the linked anchor.
#
# Anchors track BOTH explicit `<a id="...">` standalone-line declarations
# (which apply to the immediately-following heading, e.g. line 211 in the
# real inventory) AND GFM-derived anchors from heading text. Canonical rows
# are recorded under every anchor that points at their containing H2/H3, so
# a link using either form resolves.
if [[ -f "$INVENTORY" ]]; then
  xref_violations=$(awk '
    function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
    function to_anchor(s,   a) {
      a = tolower(s)
      gsub(/[ \t]+/, "-", a)
      gsub(/[^a-z0-9_-]/, "", a)
      return a
    }
    function clear(arr,   k) { for (k in arr) delete arr[k] }

    # ---- Pass 1: build CANONICAL[anchor SUBSEP slug] = "<line>|<phi>" ----
    NR == FNR {
      # Standalone explicit anchor — applies to next heading.
      if ($0 ~ /^<a id="[^"]+"><\/a>[[:space:]]*$/) {
        match($0, /id="[^"]+"/)
        pending_anchor = substr($0, RSTART + 4, RLENGTH - 5)
        next
      }

      # H3 heading — reset to just this H3'\''s anchors.
      if ($0 ~ /^### /) {
        n_anchors = 0
        clear(header_cols)
        in_canon_table = 0
        if (pending_anchor != "") {
          current_anchors[++n_anchors] = pending_anchor
          pending_anchor = ""
        }
        heading_text = trim(substr($0, 5))
        current_anchors[++n_anchors] = to_anchor(heading_text)
        # Cross-reference index sub-sections hold mirrored rows, not canonical.
        if (heading_text == "Cross-reference index") {
          in_xref_skip = 1
        } else {
          in_xref_skip = 0
        }
        next
      }
      # H2 heading — reset to just this H2'\''s anchors.
      if ($0 ~ /^## /) {
        n_anchors = 0
        clear(header_cols)
        in_canon_table = 0
        in_xref_skip = 0
        if (pending_anchor != "") {
          current_anchors[++n_anchors] = pending_anchor
          pending_anchor = ""
        }
        heading_text = trim(substr($0, 4))
        current_anchors[++n_anchors] = to_anchor(heading_text)
        next
      }

      if (in_xref_skip) next
      if (n_anchors == 0) next

      # Markdown table line.
      if ($0 ~ /^\|/) {
        n_cells = split($0, cells, /\|/)
        first_cell = trim(cells[2])
        # Header row — first cell content is literally "route".
        if (first_cell == "route") {
          clear(header_cols)
          for (i = 2; i < n_cells; i++) {
            col = trim(cells[i])
            header_cols[col] = i
            # Global accumulator across all canonical-table headers — feeds
            # the CR-5 tripwire in pass 2 (issue #212).
            CANONICAL_COL_NAMES[col] = 1
          }
          in_canon_table = 1
          next
        }
        if (!in_canon_table) next
        # Separator row — skip.
        if ($0 ~ /^\|[- :|]+\|[[:space:]]*$/) next
        # Data row — first cell should be a backticked route slug.
        if (first_cell ~ /^`[^`]+`/) {
          slug = first_cell
          sub(/^`/, "", slug)
          sub(/`.*/, "", slug)
          phi_col = ("phi_displayed" in header_cols) ? header_cols["phi_displayed"] : 0
          if (phi_col != 0) {
            phi_val = trim(cells[phi_col])
            for (a = 1; a <= n_anchors; a++) {
              key = current_anchors[a] SUBSEP slug
              if (key in CANONICAL) {
                CANONICAL_DUP[key] = 1
              }
              CANONICAL[key] = FNR "|" phi_val
            }
          }
        }
        next
      }
      # Non-table line inside the section — leave canonical-table state.
      in_canon_table = 0
      next
    }

    # ---- Pass 2: walk "### Cross-reference index" sub-sections ----
    {
      if ($0 ~ /^### Cross-reference index[[:space:]]*$/) {
        in_xref = 1
        xref_phi_col = 0
        xref_loc_col = 0
        xref_table_started = 0
        xref_header_seen = 0
        next
      }
      if ($0 ~ /^## / || $0 ~ /^### /) {
        in_xref = 0
        next
      }
      if (!in_xref) next
      if ($0 !~ /^\|/) next

      n_cells = split($0, cells, /\|/)
      if (!xref_header_seen) {
        # CR-5 tripwire (#212): collect any canonical-row column other than
        # the join key (route) or the only currently-handled mirrored column
        # (phi_displayed). The comparator below only handles phi_displayed;
        # any other mirrored column would silently truncate on '\''|'\'' in its
        # value. Fail loud and point the developer at #145.
        extras = ""
        for (i = 2; i < n_cells; i++) {
          col = trim(cells[i])
          if (col == "phi_displayed") xref_phi_col = i
          if (col == "row location") xref_loc_col = i
          if ((col in CANONICAL_COL_NAMES) && col != "route" && col != "phi_displayed") {
            if (extras == "") {
              extras = "'\''" col "'\''"
            } else {
              extras = extras ", '\''" col "'\''"
            }
          }
        }
        xref_header_seen = 1
        if (extras != "") {
          print FILENAME ":" FNR ": CR-5: cross-reference index now mirrors column(s) " extras " beyond phi_displayed. The comparator currently only handles phi_displayed correctly; values containing '\''|'\'' in any other mirrored column would be silently truncated. Generalize the comparator per the design in #145 (https://github.com/suniljames/COREcare-v2/issues/145) before adding this column to the index."
        }
        # Header-intersection rule: only fire CR-1..CR-4 when both columns are present.
        if (xref_phi_col == 0 || xref_loc_col == 0) {
          in_xref = 0
        }
        next
      }
      if (!xref_table_started && $0 ~ /^\|[- :|]+\|[[:space:]]*$/) {
        xref_table_started = 1
        next
      }
      first_cell = trim(cells[2])
      if (first_cell !~ /^`[^`]+`/) next
      slug = first_cell
      sub(/^`/, "", slug)
      sub(/`.*/, "", slug)
      idx_phi = trim(cells[xref_phi_col])
      loc_cell = trim(cells[xref_loc_col])

      # Extract the first markdown anchor link in the row-location cell.
      if (match(loc_cell, /\(#[^)]+\)/)) {
        anchor = substr(loc_cell, RSTART + 2, RLENGTH - 3)
      } else {
        print FILENAME ":" FNR ": CR-1: route '\''" slug "'\'' from cross-reference index has no anchor link in row location cell"
        next
      }

      key = anchor SUBSEP slug
      if (!(key in CANONICAL)) {
        print FILENAME ":" FNR ": CR-1: route '\''" slug "'\'' from cross-reference index not found at anchor '\''" anchor "'\''"
        next
      }
      if (key in CANONICAL_DUP) {
        print FILENAME ":" FNR ": CR-2: route '\''" slug "'\'' has multiple canonical rows under anchor '\''" anchor "'\'' — disambiguate the link target"
        next
      }

      split(CANONICAL[key], parts, "|")
      canon_line = parts[1]
      canon_phi = parts[2]

      # CR-4: vocabulary check — emit on the offending side, do not proceed to CR-3.
      if (idx_phi != "true" && idx_phi != "false") {
        print FILENAME ":" FNR ": CR-4: phi_displayed='\''" idx_phi "'\'' is not in {true, false}"
        next
      }
      if (canon_phi != "true" && canon_phi != "false") {
        print FILENAME ":" canon_line ": CR-4: phi_displayed='\''" canon_phi "'\'' is not in {true, false}"
        next
      }

      # CR-3: equality.
      if (idx_phi != canon_phi) {
        print FILENAME ":" FNR ": CR-3: phi_displayed disagreement between index and canonical row. Index has '\''" idx_phi "'\'' (here); canonical row at " FILENAME ":" canon_line " has '\''" canon_phi "'\'' (route '\''" slug "'\''). Reconfirm v1'\''s PHI exposure at this route in the source repo, then update whichever side is incorrect. Do not align the index to the canonical (or vice-versa) without source verification — that re-introduces the silent-drift risk this check is preventing."
      }
    }
  ' "$INVENTORY" "$INVENTORY")
  if [[ -n "$xref_violations" ]]; then
    while IFS= read -r line; do
      if [[ "$line" =~ ^[^:]+:[0-9]+:[[:space:]] ]]; then
        fail "$line"
      else
        echo "$line"
      fi
    done <<< "$xref_violations"
  fi
fi

# --- README Refresh runbook rule group (RR-1..RR-5) — Issue #132 ---
# Locks the operational invariants of the `## Refresh runbook` section in
# `docs/migration/README.md`. The hygiene scanner only covers `v1-*.md` files,
# so the README's runbook section had no automated guardrail until now.
#
#   RR-1  `## Refresh runbook` H2 exists.
#   RR-2  `### Refresh order — Agency Admin first` H3 exists, placed inside
#         the Refresh runbook section (between the H2 and the next `## ` H2).
#   RR-3  Each persona-section override H3 — `^### <Persona> section( —.*)?$`
#         where <Persona> is in the locked $REQUIRED_PERSONAS set — is placed
#         inside the Refresh runbook section. Typo'd persona names (e.g.
#         "Family Members") inside the section are flagged so the override
#         doesn't silently bypass RR-4 body validation.
#   RR-4  Each persona-section override body must contain:
#           a. literal `V1 Reference Commit` (cadence trigger anchor)
#           b. literal `Baseline at the currently-pinned SHA:` (fingerprint anchor)
#           c. BOTH `If any diff is non-empty:` AND `If all diffs are empty:`
#              (lock both branching outcomes — empty-diff branch enforces the
#              "still bump `last reconciled`" discipline)
#           d. literal `'*/urls.py'` (Security: resists narrowing back to
#              `dashboard/urls.py`) AND ≥3 distinct `git diff <old>..<new> --`
#              invocations (count check; specific paths beyond `'*/urls.py'`
#              may evolve when v1 reorganizes).
#   RR-5  Every markdown intra-file anchor link `](#<anchor>)` in the README
#         resolves to a heading or explicit `<a id>` in the same README.
#         Protects the `## Workflow secrets / Break-glass` deep-link.
if [[ -f "$README" ]]; then
  # Locate the Refresh runbook section bounds. End of section = next `## ` H2
  # or EOF; section content lives strictly between (start, end).
  rr_runbook_start=$(grep -nE '^## Refresh runbook[[:space:]]*$' "$README" | head -1 | cut -d: -f1)
  if [[ -z "$rr_runbook_start" ]]; then
    fail "$README missing '## Refresh runbook' H2 (RR-1)"
  else
    rr_runbook_end=$(awk -v s="$rr_runbook_start" 'NR > s && /^## / { print NR; exit }' "$README")
    if [[ -z "$rr_runbook_end" ]]; then
      rr_runbook_end=$(($(wc -l < "$README") + 1))
    fi

    # RR-2: Agency-Admin-first H3 must exist AND sit inside the section.
    rr_aa_lines=$(grep -nE '^### Refresh order — Agency Admin first[[:space:]]*$' "$README" | cut -d: -f1)
    if [[ -z "$rr_aa_lines" ]]; then
      fail "$README missing '### Refresh order — Agency Admin first' H3 (RR-2)"
    else
      rr_aa_in_section=0
      while IFS= read -r aa_line; do
        [[ -z "$aa_line" ]] && continue
        if (( aa_line > rr_runbook_start && aa_line < rr_runbook_end )); then
          rr_aa_in_section=1
        else
          fail "$README '### Refresh order — Agency Admin first' H3 at line $aa_line is outside '## Refresh runbook' section (RR-2)"
        fi
      done <<< "$rr_aa_lines"
      if [[ "$rr_aa_in_section" -eq 0 ]]; then
        fail "$README '### Refresh order — Agency Admin first' H3 not placed inside '## Refresh runbook' section (RR-2)"
      fi
    fi

    # Build the locked persona-section regex from $REQUIRED_PERSONAS.
    rr_persona_alt=$(IFS='|'; echo "${REQUIRED_PERSONAS[*]}")
    rr_persona_re="^### (${rr_persona_alt}) section( —.*)?[[:space:]]*\$"

    # RR-3 (placement): every locked persona-section H3 in the file must sit
    # inside the runbook section.
    while IFS=: read -r h3_line h3_text; do
      [[ -z "$h3_line" ]] && continue
      if (( h3_line < rr_runbook_start || h3_line >= rr_runbook_end )); then
        fail "$README persona-section H3 '$h3_text' (line $h3_line) placed outside '## Refresh runbook' section (RR-3)"
      fi
    done < <(grep -nE "$rr_persona_re" "$README" || true)

    # RR-3 (typo): any H3 inside the runbook section ending in ` section`
    # (with optional ` — …` tail) that does NOT match the locked persona regex
    # is flagged. Catches `### Family Members section` and similar near-misses
    # that would otherwise silently bypass RR-4 body validation.
    while IFS=: read -r h3_line h3_text; do
      [[ -z "$h3_line" ]] && continue
      # Skip H3s that DO match the locked persona regex.
      if echo "$h3_text" | grep -qE "$rr_persona_re"; then continue; fi
      # Flag anything else whose heading text ends in ` section` (or ` section — …`).
      if echo "$h3_text" | grep -qE '^### .+ section( —.*)?[[:space:]]*$'; then
        fail "$README runbook H3 '$h3_text' (line $h3_line) does not match locked persona name from \${REQUIRED_PERSONAS[*]} (RR-3)"
      fi
    done < <(awk -v s="$rr_runbook_start" -v e="$rr_runbook_end" 'NR > s && NR < e && /^### / { print NR ":" $0 }' "$README")

    # RR-4: validate the body of each persona-section H3 inside the runbook
    # section. Body = lines from this H3 to the next H3-or-H2 (whichever first)
    # OR to the end of the runbook section.
    rr4_violations=$(awk -v s="$rr_runbook_start" -v e="$rr_runbook_end" -v re="$rr_persona_re" '
      function flush(   diff_count, body_copy, p) {
        if (cur_h3 == "") return
        if (!index(body, "V1 Reference Commit")) {
          print FILENAME ":" h3_line ": RR-4a: persona-section H3 \"" cur_h3 "\" body missing literal `V1 Reference Commit` (cadence trigger)"
        }
        if (!index(body, "Baseline at the currently-pinned SHA:")) {
          print FILENAME ":" h3_line ": RR-4b: persona-section H3 \"" cur_h3 "\" body missing literal `Baseline at the currently-pinned SHA:` (fingerprint anchor)"
        }
        if (!index(body, "If any diff is non-empty:")) {
          print FILENAME ":" h3_line ": RR-4c: persona-section H3 \"" cur_h3 "\" body missing branch literal `If any diff is non-empty:`"
        }
        if (!index(body, "If all diffs are empty:")) {
          print FILENAME ":" h3_line ": RR-4c: persona-section H3 \"" cur_h3 "\" body missing branch literal `If all diffs are empty:` (locks the still-bump-`last reconciled` discipline)"
        }
        if (!index(body, "\x27*/urls.py\x27")) {
          print FILENAME ":" h3_line ": RR-4d: persona-section H3 \"" cur_h3 "\" body missing literal `\x27*/urls.py\x27` (Security: resists narrowing back to `dashboard/urls.py`)"
        }
        diff_count = 0
        body_copy = body
        while ((p = index(body_copy, "git diff <old>..<new> --")) > 0) {
          diff_count++
          body_copy = substr(body_copy, p + 24)
        }
        if (diff_count < 3) {
          print FILENAME ":" h3_line ": RR-4d: persona-section H3 \"" cur_h3 "\" body has " diff_count " `git diff <old>..<new> --` invocations, minimum 3"
        }
        cur_h3 = ""
        body = ""
      }
      NR > s && NR < e {
        if ($0 ~ re) {
          flush()
          cur_h3 = $0
          h3_line = NR
          body = ""
          next
        }
        if (cur_h3 != "" && ($0 ~ /^### / || $0 ~ /^## /)) {
          flush()
          next
        }
        if (cur_h3 != "") {
          body = body "\n" $0
        }
      }
      END { flush() }
    ' "$README")
    if [[ -n "$rr4_violations" ]]; then
      while IFS= read -r line; do
        if [[ "$line" =~ ^[^:]+:[0-9]+:[[:space:]] ]]; then
          fail "$line"
        else
          echo "$line"
        fi
      done <<< "$rr4_violations"
    fi
  fi

  # RR-5: anchor-resolution within the README itself.
  # Build a heading anchor set (GFM-derived from headings + explicit <a id>)
  # in pass 1, then walk markdown intra-file links `](#<anchor>)` in pass 2.
  # Pattern `\]\(#[^)]+\)` requires the closing `]` of a markdown link text
  # immediately before `(` so we don't false-match issue refs like ` (#131)`
  # in plain prose (which are NOT anchor links and need not resolve).
  rr5_violations=$(awk '
    function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
    function to_anchor(s,   a) {
      a = tolower(s)
      gsub(/[ \t]+/, "-", a)
      gsub(/[^a-z0-9_-]/, "", a)
      return a
    }
    NR == FNR {
      if ($0 ~ /^#+ /) {
        h = $0
        sub(/^#+[[:space:]]*/, "", h)
        ANCHORS[to_anchor(trim(h))] = 1
      }
      line = $0
      while (match(line, /<a id="[^"]+"/)) {
        a = substr(line, RSTART + 7, RLENGTH - 8)
        ANCHORS[a] = 1
        line = substr(line, RSTART + RLENGTH)
      }
      next
    }
    {
      line = $0
      while (match(line, /\]\(#[^)]+\)/)) {
        link = substr(line, RSTART, RLENGTH)
        # link starts with "](#" (3 chars) and ends with ")" (1 char).
        anchor = substr(link, 4, length(link) - 4)
        if (!(anchor in ANCHORS)) {
          print FILENAME ":" FNR ": RR-5: anchor \"" anchor "\" not found in same README"
        }
        line = substr(line, RSTART + RLENGTH)
      }
    }
  ' "$README" "$README")
  if [[ -n "$rr5_violations" ]]; then
    while IFS= read -r line; do fail "$line"; done <<< "$rr5_violations"
  fi
fi

# --- WF-1: workflow path resolution from README — Issue #169 ---
# Every backticked reference in `docs/migration/README.md` matching the form
# `.github/workflows/<name>.yml` must point to a file that exists on disk.
# Resolution is relative to $REPO_ROOT (default CWD).
#
# Character class `[A-Za-z0-9._-]` (no `/`, no shell metacharacters): excludes
# nested-subdir paths and shell-injection vectors by construction. If a future
# workflow lives at `.github/workflows/<subdir>/foo.yml`, the regex must be
# updated deliberately — a hard trip-wire, not a silent miss.
#
# Backtick-fenced match: prose mentions, markdown link forms, and HTML comments
# are out of scope per the issue's "only backticked refs count" rule.
#
# One violation emitted per cite-site (no dedup) so multiple stale references
# in the same README all surface in one CI run.
if [[ -f "$README" ]]; then
  wf1_paths=$(awk '
    {
      line = $0
      while (match(line, /`\.github\/workflows\/[A-Za-z0-9._-]+\.yml`/)) {
        token = substr(line, RSTART, RLENGTH)
        # Strip the leading and trailing backticks.
        path = substr(token, 2, length(token) - 2)
        print FNR "\t" path
        line = substr(line, RSTART + RLENGTH)
      }
    }
  ' "$README")
  if [[ -n "$wf1_paths" ]]; then
    while IFS=$'\t' read -r wf_line wf_path; do
      [[ -z "$wf_line" ]] && continue
      if [[ ! -f "$REPO_ROOT/$wf_path" ]]; then
        fail "$README:$wf_line: WF-1: workflow path '$wf_path' not found on disk"
      fi
    done <<< "$wf1_paths"
  fi
fi

if [[ "$VIOLATIONS" -gt 0 ]]; then
  echo ""
  echo "Structure check FAILED with $VIOLATIONS violation(s)."
  exit 1
fi

exit 0
