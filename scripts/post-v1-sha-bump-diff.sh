#!/usr/bin/env bash
# Auto-post the Family Member section diff report when a PR bumps the
# `V1 Reference Commit` SHA in docs/migration/README.md.
#
# Implements the per-section refresh runbook entry added in #121 — fetches
# the three runbook diffs (`*/urls.py`, `clients/`, `clients/models.py`)
# from the private v1 repo across the SHA bump, formats a sticky PR comment,
# and posts (or updates) it via the GitHub API.
#
# Sourced by tests for unit access to the pure functions; runs main when
# executed directly. See scripts/tests/test_post_v1_sha_bump_diff.sh.
#
# === Workflow secrets ===
# Requires repo secret `V1_REPO_READ_TOKEN`: a fine-grained PAT scoped to
# `suniljames/COREcare-access` only, `Contents: Read`, 1-year expiry.
# Rotation: re-issue the PAT, update the repo secret, document the
# rotation date in docs/migration/README.md ("Workflow secrets" section).
# Break-glass: if the gate is broken, the engineer manually runs the three
# diffs locally and ack's in the PR description; a maintainer uses
# branch-protection bypass to merge.

set -uo pipefail

# Per-diff body cap (12 KB). Total comment cap protected by the per-diff
# cap × 3 + structure overhead (~5 KB) < 60 KB << GitHub's 65,536-char
# issue-comment limit.
DIFF_CAP_BYTES=${DIFF_CAP_BYTES:-12288}

# Marker used to find an existing comment for in-place sticky update.
COMMENT_MARKER='<!-- v1-sha-bump-diff-report -->'

# slice_pr_diff_to_readme
# Reads a full PR diff from stdin (as `gh pr diff` emits, with one
# `diff --git` header per file) and emits only the section for
# docs/migration/README.md. Emits nothing when the README is not in
# the diff. Sliced separately because `gh pr diff` does not accept a
# `-- <path>` filter the way `git diff` does.
slice_pr_diff_to_readme() {
  awk '
    /^diff --git a\/docs\/migration\/README\.md / { in_section=1; print; next }
    /^diff --git / { in_section=0 }
    in_section { print }
  '
}

# extract_sha_bump
# Reads a unified diff of docs/migration/README.md from stdin.
# Emits "OLD_SHA NEW_SHA" if the `Commit SHA` line was bumped to a different
# value; emits nothing (and returns 0) otherwise. The caller distinguishes
# bump-vs-no-op by checking whether stdout is non-empty.
extract_sha_bump() {
  local diff old new
  diff=$(cat)
  old=$(printf '%s\n' "$diff" \
    | grep -E '^-\s*-\s*\*\*Commit SHA:\*\*\s*`[0-9a-f]+`' \
    | head -1 \
    | grep -oE '`[0-9a-f]+`' \
    | tr -d '`' || true)
  new=$(printf '%s\n' "$diff" \
    | grep -E '^\+\s*-\s*\*\*Commit SHA:\*\*\s*`[0-9a-f]+`' \
    | head -1 \
    | grep -oE '`[0-9a-f]+`' \
    | tr -d '`' || true)
  if [[ -n "$old" && -n "$new" && "$old" != "$new" ]]; then
    printf '%s %s\n' "$old" "$new"
  fi
}

# format_stats_row <unified-diff>
# Emits "<files> <plus> <minus>" counts for a unified diff.
format_stats_row() {
  local diff="$1"
  local files=0 plus=0 minus=0
  if [[ -n "$diff" ]]; then
    files=$(printf '%s\n' "$diff" | grep -c '^diff --git ' || true)
    plus=$(printf '%s\n' "$diff" | grep -cE '^\+[^+]|^\+$' || true)
    minus=$(printf '%s\n' "$diff" | grep -cE '^-[^-]|^-$' || true)
  fi
  printf '%s %s %s\n' "$files" "$plus" "$minus"
}

# detect_permission_gate <diff>
# Returns 0 (true) when the diff hits any of the runbook's permission-gate
# signals: the canonical helper `_check_client_access` (anywhere in the
# diff including context lines, so a body-change inside the helper is
# caught), the `is_family` body-check pattern on a +/- line, or the
# `{% if is_family %}` template-tag pattern. The runbook is explicit that
# these are example signals, not a fixed contract.
detect_permission_gate() {
  local diff="$1"
  printf '%s\n' "$diff" \
    | grep -qE '_check_client_access|^[-+].*\bis_family|\{%\s*if\s+is_family'
}

# detect_fingerprint_match <models-diff>
# Returns 0 (true) when the clients/models.py diff mentions
# `ClientFamilyMember` AND a +/- line carries one of the runbook's
# baseline-invariant tokens: is_active, deleted_at, expires_at, role,
# permission. Surfaces the row that breaks the runbook's fingerprint.
detect_fingerprint_match() {
  local diff="$1"
  if ! printf '%s\n' "$diff" | grep -q 'ClientFamilyMember'; then
    return 1
  fi
  printf '%s\n' "$diff" \
    | grep -qE '^[-+].*\b(is_active|deleted_at|expires_at|role|permission)\b'
}

# truncate_diff <diff>
# Truncates a unified diff at DIFF_CAP_BYTES and appends the runbook-
# voiced banner with a copy-pasteable local rerun command. Variables
# OLD_SHA, NEW_SHA, TRUNCATE_PATHSPEC must be set in the caller's scope.
truncate_diff() {
  local diff="$1"
  local size cut remaining
  size=${#diff}
  if (( size <= DIFF_CAP_BYTES )); then
    printf '%s' "$diff"
    return
  fi
  cut="${diff:0:DIFF_CAP_BYTES}"
  remaining=$(( size - DIFF_CAP_BYTES ))
  printf '%s\n\n… %s more bytes truncated. Run locally:\n' "$cut" "$remaining"
  printf 'git -C <v1-checkout> diff %s..%s -- %s\n' \
    "${OLD_SHA:-<old>}" "${NEW_SHA:-<new>}" "${TRUNCATE_PATHSPEC:-<pathspec>}"
}

# format_comment OLD NEW URLS_DIFF CLIENTS_DIFF MODELS_DIFF [WORKFLOW_RUN_URL]
# Emits the full PR comment body to stdout, including the sticky marker,
# the hidden machine-parseable stats line, the action call-to-action with
# only the active branch bolded, the stats table, the optional fingerprint
# callout, and three collapsed `<details>` blocks. The phrase "silent drift"
# appears at least once.
format_comment() {
  local old="$1" new="$2"
  local urls_diff="$3" clients_diff="$4" models_diff="$5"
  local run_url="${6:-}"

  local urls_stats clients_stats models_stats
  urls_stats=$(format_stats_row "$urls_diff")
  clients_stats=$(format_stats_row "$clients_diff")
  models_stats=$(format_stats_row "$models_diff")

  local urls_files urls_plus urls_minus
  read -r urls_files urls_plus urls_minus <<<"$urls_stats"
  local clients_files clients_plus clients_minus
  read -r clients_files clients_plus clients_minus <<<"$clients_stats"
  local models_files models_plus models_minus
  read -r models_files models_plus models_minus <<<"$models_stats"

  local total=$(( urls_files + clients_files + models_files ))
  local action_branch="empty"
  if (( total > 0 )); then
    if detect_permission_gate "$clients_diff"; then
      action_branch="permission"
    else
      action_branch="reauthor"
    fi
  fi

  local fingerprint_callout=""
  if detect_fingerprint_match "$models_diff"; then
    fingerprint_callout=$'\n> **Baseline fingerprint match.** The `clients/models.py` diff touches a `ClientFamilyMember` invariant token (one of `is_active`, `deleted_at`, `expires_at`, `role`, `permission`). v1 has changed a previously-stable property of the model — re-author the rows that depend on it.\n'
  fi

  local action_block
  case "$action_branch" in
    empty)
      action_block=$'**All diffs empty.** No relevant v1 changes detected for the Family Member section.\n\n**Action: bump `last reconciled` only.**\n\n~~Action: re-author affected rows~~\n~~Action: re-author + flag `CUTOVER_PLAN.md` owners~~'
      ;;
    permission)
      action_block=$'**Action: re-author + flag `CUTOVER_PLAN.md` owners.** Permission gate `_check_client_access` changed in this bump — v2 RLS may need to mirror the v1 change.\n\n~~Action: re-author affected rows~~\n~~Action: bump `last reconciled` only~~'
      ;;
    reauthor)
      action_block=$'**Action: re-author affected rows.** Update `docs/migration/v1-pages-inventory.md` Family Member rows for routes / serializers / templates surfaced below.\n\n~~Action: re-author + flag `CUTOVER_PLAN.md` owners~~\n~~Action: bump `last reconciled` only~~'
      ;;
  esac

  local short_old="${old:0:7}" short_new="${new:0:7}"

  local urls_block clients_block models_block
  OLD_SHA="$old" NEW_SHA="$new" TRUNCATE_PATHSPEC="'*/urls.py'" \
    urls_block=$(truncate_diff "$urls_diff")
  OLD_SHA="$old" NEW_SHA="$new" TRUNCATE_PATHSPEC="'clients/'" \
    clients_block=$(truncate_diff "$clients_diff")
  OLD_SHA="$old" NEW_SHA="$new" TRUNCATE_PATHSPEC="'clients/models.py'" \
    models_block=$(truncate_diff "$models_diff")

  cat <<COMMENT
$COMMENT_MARKER
<!-- diff-stats: urls=${urls_files},+${urls_plus},-${urls_minus}; clients=${clients_files},+${clients_plus},-${clients_minus}; models=${models_files},+${models_plus},-${models_minus} -->

**V1 Reference Commit bumped:** \`${short_old}..${short_new}\`. Family Member section diff report below.

This is the automated **silent drift** check from the [Family Member refresh runbook](../blob/main/docs/migration/README.md#family-member-section--extra-diff-checks-before-re-authoring).

### Action

${action_block}
${fingerprint_callout}
### Stats

| Diff target | Files | +lines | −lines |
|---|---:|---:|---:|
| \`*/urls.py\` | ${urls_files} | ${urls_plus} | ${urls_minus} |
| \`clients/\` | ${clients_files} | ${clients_plus} | ${clients_minus} |
| \`clients/models.py\` | ${models_files} | ${models_plus} | ${models_minus} |

### Diffs

<details><summary><code>git diff ${short_old}..${short_new} -- '*/urls.py'</code></summary>

\`\`\`diff
${urls_block:-(empty)}
\`\`\`

</details>

<details><summary><code>git diff ${short_old}..${short_new} -- 'clients/'</code></summary>

\`\`\`diff
${clients_block:-(empty)}
\`\`\`

</details>

<details><summary><code>git diff ${short_old}..${short_new} -- 'clients/models.py'</code></summary>

\`\`\`diff
${models_block:-(empty)}
\`\`\`

</details>

---

${run_url:+Workflow run: ${run_url}}
COMMENT
}

# fail_loud <message>
# Print a clearly-marked failure message and exit 1. Used for fail-closed
# semantics on missing secrets, fetch failures, and API errors.
fail_loud() {
  printf '\n!!! v1-sha-bump-diff-report: %s\n' "$1" >&2
  exit 1
}

# main "$@"
# Production entry point. Runs in the GitHub Actions environment with
# GITHUB_REPOSITORY, GITHUB_BASE_REF, GITHUB_TOKEN, V1_REPO_READ_TOKEN,
# and a PR number passed as the first arg (or via $PR_NUMBER).
main() {
  local pr_num="${1:-${PR_NUMBER:-}}"
  if [[ -z "$pr_num" ]]; then
    fail_loud "PR number not provided (arg or PR_NUMBER env var)."
  fi

  echo "Reading PR diff for PR #${pr_num}…"
  local pr_diff_file
  pr_diff_file=$(mktemp)
  gh pr diff "$pr_num" >"$pr_diff_file" \
    || { rm -f "$pr_diff_file"; fail_loud "Failed to read PR diff via gh."; }

  local readme_diff
  readme_diff=$(slice_pr_diff_to_readme <"$pr_diff_file")
  rm -f "$pr_diff_file"

  if [[ -z "$readme_diff" ]]; then
    echo "docs/migration/README.md unchanged in this PR — nothing to report."
    return 0
  fi

  local commit_sha_lines
  commit_sha_lines=$(printf '%s\n' "$readme_diff" \
    | grep -E '^[-+]\s*-\s*\*\*Commit SHA:\*\*' || true)
  echo "Commit SHA lines in README diff:"
  printf '  %s\n' "${commit_sha_lines:-(none)}"

  local bump
  bump=$(printf '%s\n' "$readme_diff" | extract_sha_bump)
  if [[ -z "$bump" ]]; then
    echo "no SHA bump in this PR — skipping diff report."
    return 0
  fi
  read -r OLD_SHA NEW_SHA <<<"$bump"
  echo "SHA bump: ${OLD_SHA:0:7}..${NEW_SHA:0:7}"

  if [[ -z "${V1_REPO_READ_TOKEN:-}" ]]; then
    fail_loud "V1_REPO_READ_TOKEN secret not configured. See workflow file header for setup instructions."
  fi

  local v1_dir
  v1_dir=$(mktemp -d)
  trap 'rm -rf "$v1_dir"' EXIT

  echo "Cloning v1 (filter=blob:none, no-checkout) → $v1_dir"
  echo "  git clone --filter=blob:none --no-checkout https://x-access-token:***@github.com/suniljames/COREcare-access.git"
  git clone --filter=blob:none --no-checkout --quiet \
    "https://x-access-token:${V1_REPO_READ_TOKEN}@github.com/suniljames/COREcare-access.git" \
    "$v1_dir" \
    || fail_loud "Failed to clone v1 repo. Check V1_REPO_READ_TOKEN scope and validity."

  echo "Fetching old SHA $OLD_SHA"
  git -C "$v1_dir" fetch --quiet origin "$OLD_SHA" \
    || fail_loud "Failed to fetch OLD_SHA ($OLD_SHA) from v1. Verify the SHA exists in suniljames/COREcare-access."
  echo "Fetching new SHA $NEW_SHA"
  git -C "$v1_dir" fetch --quiet origin "$NEW_SHA" \
    || fail_loud "Failed to fetch NEW_SHA ($NEW_SHA) from v1. Verify the SHA exists in suniljames/COREcare-access."

  local urls_diff clients_diff models_diff
  echo "Diffing '*/urls.py'"
  urls_diff=$(git -C "$v1_dir" diff "$OLD_SHA..$NEW_SHA" -- '*/urls.py' || true)
  echo "  $(format_stats_row "$urls_diff")"
  echo "Diffing 'clients/'"
  clients_diff=$(git -C "$v1_dir" diff "$OLD_SHA..$NEW_SHA" -- 'clients/' || true)
  echo "  $(format_stats_row "$clients_diff")"
  echo "Diffing 'clients/models.py'"
  models_diff=$(git -C "$v1_dir" diff "$OLD_SHA..$NEW_SHA" -- 'clients/models.py' || true)
  echo "  $(format_stats_row "$models_diff")"

  local run_url=""
  if [[ -n "${GITHUB_SERVER_URL:-}" && -n "${GITHUB_REPOSITORY:-}" && -n "${GITHUB_RUN_ID:-}" ]]; then
    run_url="${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"
  fi

  local body
  body=$(format_comment "$OLD_SHA" "$NEW_SHA" "$urls_diff" "$clients_diff" "$models_diff" "$run_url")

  post_or_update_comment "$pr_num" "$body"
}

# post_or_update_comment <pr-num> <body>
# Find an existing sticky comment by marker; PATCH if found, POST otherwise.
# One retry on transient failure, then fail_loud with the API error body.
post_or_update_comment() {
  local pr_num="$1" body="$2"
  local repo="${GITHUB_REPOSITORY:-}"
  if [[ -z "$repo" ]]; then
    fail_loud "GITHUB_REPOSITORY not set; cannot identify the API target."
  fi

  local existing_id
  existing_id=$(gh api "repos/${repo}/issues/${pr_num}/comments" --paginate \
    --jq ".[] | select(.body | startswith(\"${COMMENT_MARKER}\")) | .id" \
    | head -1 || true)

  local body_file
  body_file=$(mktemp)
  printf '%s' "$body" >"$body_file"

  local attempt=1
  while (( attempt <= 2 )); do
    if [[ -n "$existing_id" ]]; then
      echo "Updating existing comment $existing_id"
      if gh api -X PATCH "repos/${repo}/issues/comments/${existing_id}" \
        -F "body=@${body_file}" >/dev/null; then
        rm -f "$body_file"
        return 0
      fi
    else
      echo "Posting new comment on PR #${pr_num}"
      if gh api -X POST "repos/${repo}/issues/${pr_num}/comments" \
        -F "body=@${body_file}" >/dev/null; then
        rm -f "$body_file"
        return 0
      fi
    fi
    if (( attempt == 1 )); then
      echo "Comment-API call failed; retrying once after 5s backoff."
      sleep 5
    fi
    attempt=$(( attempt + 1 ))
  done

  rm -f "$body_file"
  fail_loud "Comment-API call failed twice. See log above for the API error body."
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
