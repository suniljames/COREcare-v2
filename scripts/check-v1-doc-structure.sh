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
#
# Usage:
#   scripts/check-v1-doc-structure.sh [--dir <docs-dir>]
#
# Default --dir is `docs/migration/` (relative to current working directory).
#
# Exit codes:
#   0  all structural invariants hold
#   1  one or more checks failed

set -u

DIR="docs/migration"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) DIR="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

INVENTORY="$DIR/v1-pages-inventory.md"
DELTA="$DIR/v1-functionality-delta.md"
INTEGRATIONS="$DIR/v1-integrations-and-exports.md"
JOURNEYS="$DIR/v1-user-journeys.md"

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
        line = $0
        while (match(line, /\(v1-pages-inventory\.md#[^)]+\)/)) {
          link = substr(line, RSTART, RLENGTH)
          # Strip "(v1-pages-inventory.md#" (length 23) and trailing ")".
          anchor = substr(link, 24, length(link) - 24)
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

if [[ "$VIOLATIONS" -gt 0 ]]; then
  echo ""
  echo "Structure check FAILED with $VIOLATIONS violation(s)."
  exit 1
fi

exit 0
