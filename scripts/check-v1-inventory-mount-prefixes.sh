#!/usr/bin/env bash
# Validates that every H3 italic mount-prefix declaration in
# docs/migration/v1-pages-inventory.md (a) names a prefix backed by a
# top-level mount in v1's elitecare/urls.py at the pinned commit, and
# (b) matches the first inventory row beneath the H3.
#
# Catches the #204 class of bug: silent drift between an H3's claimed
# mount prefix and the actual v1 URL conf.
#
# Source-of-truth for v1 mount prefixes is a static text fixture
# (docs/migration/fixtures/v1-elitecare-urls.txt) refreshed when the
# V1 Reference Commit SHA in docs/migration/README.md is bumped.
#
# Usage:
#   scripts/check-v1-inventory-mount-prefixes.sh
#     [--inventory <path>]   default: docs/migration/v1-pages-inventory.md
#     [--fixture <path>]     default: docs/migration/fixtures/v1-elitecare-urls.txt
#     [--readme <path>]      default: docs/migration/README.md
#
# Exit codes:
#   0  all declarations validate
#   1  one or more declarations don't validate, OR fixture is stale
#      (header SHA != README V1 Reference Commit SHA)
#   2  operator error: missing or malformed README / fixture

set -u

INVENTORY="docs/migration/v1-pages-inventory.md"
FIXTURE="docs/migration/fixtures/v1-elitecare-urls.txt"
README="docs/migration/README.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --inventory) INVENTORY="$2"; shift 2 ;;
    --fixture)   FIXTURE="$2";   shift 2 ;;
    --readme)    README="$2";    shift 2 ;;
    -h|--help)
      sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *)
      echo "unknown arg: $1" >&2
      exit 2 ;;
  esac
done

# --- Pre-flight: README V1 Reference Commit SHA --------------------------

if [[ ! -f "$README" ]]; then
  echo "$README: file not found" >&2
  exit 2
fi
README_SHA=$(grep -E '^- \*\*Commit SHA:\*\*[[:space:]]*`[0-9a-f]+`' "$README" \
  | head -1 \
  | grep -oE '`[0-9a-f]+`' \
  | tr -d '`')
if [[ -z "$README_SHA" ]]; then
  echo "$README: could not extract V1 Reference Commit SHA (expected '- **Commit SHA:** \`<sha>\`')" >&2
  exit 2
fi

# --- Pre-flight: fixture exists + has a header SHA -----------------------

if [[ ! -f "$FIXTURE" ]]; then
  echo "$FIXTURE: file not found" >&2
  exit 2
fi
FIXTURE_SHA=$(grep -E '^# v1 SHA:[[:space:]]*[0-9a-f]+' "$FIXTURE" \
  | head -1 \
  | awk '{ print $NF }')
if [[ -z "$FIXTURE_SHA" ]]; then
  echo "$FIXTURE: could not extract fixture-header SHA (expected '# v1 SHA: <sha>')" >&2
  exit 2
fi

# --- Pre-flight: fixture SHA matches README SHA --------------------------

if [[ "$FIXTURE_SHA" != "$README_SHA" ]]; then
  echo "$FIXTURE: header SHA \`$FIXTURE_SHA\` does not match $README V1 Reference Commit \`$README_SHA\`. Refresh the fixture per docs/migration/README.md#v1-mount-prefix-fixture-refresh." >&2
  exit 1
fi

# --- Build the fixture-prefix set ----------------------------------------
# Each `path("X/", ...)` line yields the prefix "X/" (trailing slash, no
# leading slash — matches v1 URL conf form). Empty-prefix mounts (the
# auth_service "" mount) are excluded so they cannot fallback-match every
# inventory declaration.

if [[ ! -f "$INVENTORY" ]]; then
  echo "$INVENTORY: file not found" >&2
  exit 2
fi

# Use comma as the inter-prefix separator. URL prefixes never contain commas
# (Django URL conf doesn't permit them), so this is unambiguous. Pass as a
# single -v var because awk -v treats literal newlines as input errors.
FIXTURE_PREFIXES=$(awk -F'"' '/^path\(/ && $2 != "" { printf "%s,", $2 }' "$FIXTURE")
FIXTURE_PREFIXES="${FIXTURE_PREFIXES%,}"

# --- Inventory walk ------------------------------------------------------

awk -v inventory="$INVENTORY" -v sha="$README_SHA" -v fixture_prefixes="$FIXTURE_PREFIXES" '
  BEGIN {
    n = split(fixture_prefixes, _arr, ",")
    fixture_n = 0
    for (i = 1; i <= n; i++) {
      if (_arr[i] != "") {
        fixture_n++
        fixture_list[fixture_n] = _arr[i]
      }
    }

    # Locked persona vocabulary (matches docs/migration/README.md). Plus
    # "Shared routes" so its H3s are walked (and naturally skipped by the
    # no-mount-at rule, since it has none).
    # MUST match scripts/check-v1-doc-structure.sh REQUIRED_PERSONAS — see #236.
    persona_set["Agency Admin"] = 1
    persona_set["Care Manager"] = 1
    persona_set["Caregiver"] = 1
    persona_set["Client"] = 1
    persona_set["Family Member"] = 1
    persona_set["Shared routes"] = 1

    in_persona = 0
    cur_h2 = ""
    cur_h3 = ""
    cur_h3_line = 0
    state = "idle"
    n_cur_prefixes = 0
    h3_invalid = 0
    fail_count = 0
  }

  # H2 — switch persona context
  /^## / {
    cur_h2 = $0
    sub(/^## +/, "", cur_h2)
    in_persona = (cur_h2 in persona_set) ? 1 : 0
    cur_h3 = ""
    cur_h3_line = 0
    state = "idle"
    next
  }

  # Horizontal rule between top-level sections
  /^---+$/ {
    state = "idle"
    in_persona = 0
    next
  }

  # H3 — start of a new sub-section
  /^### / {
    if (!in_persona) { next }
    cur_h3 = $0
    sub(/^### +/, "", cur_h3)
    cur_h3_line = NR
    state = "expecting_subhead"
    n_cur_prefixes = 0
    h3_invalid = 0
    next
  }

  # Subhead = first non-blank line after H3
  state == "expecting_subhead" && /^[[:space:]]*$/ { next }
  state == "expecting_subhead" {
    italic = $0
    if (italic ~ /^_.+_$/) {
      content = italic
      sub(/^_/, "", content)
      sub(/_$/, "", content)
      idx = index(content, "mounted at ")
      if (idx > 0) {
        s = substr(content, idx + length("mounted at "))
        # Walk a `tok` (and `tok`)* chain immediately following "mounted at "
        while (length(s) > 0) {
          if (substr(s, 1, 1) == "`") {
            close_idx = index(substr(s, 2), "`")
            if (close_idx == 0) break
            tok = substr(s, 2, close_idx - 1)
            s = substr(s, close_idx + 2)
            n_cur_prefixes++
            cur_prefixes[n_cur_prefixes] = tok
            if (substr(s, 1, 5) == " and ") {
              s = substr(s, 6)
              continue
            }
            break
          }
          break
        }

        for (i = 1; i <= n_cur_prefixes; i++) {
          tok = cur_prefixes[i]
          if (substr(tok, 1, 1) != "/") {
            print inventory ":" cur_h3_line ": " cur_h2 " > " cur_h3 ": prefix `" tok "` is missing the required leading slash (canonical form is `/X/`). Per docs/migration/README.md#h3-italic-mount-prefix-declaration-form."
            fail_count++
            h3_invalid = 1
            continue
          }
          if (substr(tok, length(tok), 1) != "/") {
            print inventory ":" cur_h3_line ": " cur_h2 " > " cur_h3 ": prefix `" tok "` is missing the required trailing slash (canonical form is `/X/`). Per docs/migration/README.md#h3-italic-mount-prefix-declaration-form."
            fail_count++
            h3_invalid = 1
            continue
          }
          stripped = substr(tok, 2)
          found = 0
          for (j = 1; j <= fixture_n; j++) {
            f = fixture_list[j]
            if (length(stripped) >= length(f) && substr(stripped, 1, length(f)) == f) {
              found = 1
              break
            }
          }
          if (!found) {
            print inventory ":" cur_h3_line ": " cur_h2 " > " cur_h3 ": declares mount at `" tok "` but no `path(\"" stripped "\", include(...))` line in v1 elitecare/urls.py at SHA " sha " covers it (see docs/migration/fixtures/v1-elitecare-urls.txt)."
            fail_count++
            h3_invalid = 1
          }
        }
      }
      state = (n_cur_prefixes > 0 && !h3_invalid) ? "expecting_first_row" : "after_first_row"
    } else {
      state = "after_first_row"
    }
    next
  }

  # First inventory row: a markdown table row whose first cell is a backticked
  # route starting with "/". Skip schema and header rows.
  state == "expecting_first_row" && /^\|[[:space:]]*`\// {
    bt1 = index($0, "`")
    if (bt1 == 0) { state = "after_first_row"; next }
    rest = substr($0, bt1 + 1)
    bt2 = index(rest, "`")
    if (bt2 == 0) { state = "after_first_row"; next }
    actual = substr(rest, 1, bt2 - 1)
    matched = 0
    for (i = 1; i <= n_cur_prefixes; i++) {
      tok = cur_prefixes[i]
      if (substr(tok, 1, 1) == "/" && substr(tok, length(tok), 1) == "/" \
          && length(actual) >= length(tok) \
          && substr(actual, 1, length(tok)) == tok) {
        matched = 1
        break
      }
    }
    if (!matched) {
      pjoin = ""
      for (i = 1; i <= n_cur_prefixes; i++) {
        if (i > 1) pjoin = pjoin " or "
        pjoin = pjoin "`" cur_prefixes[i] "`"
      }
      print inventory ":" cur_h3_line ": " cur_h2 " > " cur_h3 ": declares mount at " pjoin " but first inventory row route is `" actual "` (expected to start with one of the declared prefixes)."
      fail_count++
    }
    state = "after_first_row"
    next
  }

  END {
    exit (fail_count > 0) ? 1 : 0
  }
' "$INVENTORY"
