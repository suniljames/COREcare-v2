#!/usr/bin/env bash
# Tests for scripts/post-v1-sha-bump-diff.sh — the workflow script that
# fetches the three Family Member runbook diffs across a `V1 Reference
# Commit` SHA bump and posts a sticky PR comment.
#
# Sources the script (without running main) and exercises pure functions
# with inline fixture inputs. No real network, no real `git`/`gh` calls.
#
# Run from repo root: bash scripts/tests/test_post_v1_sha_bump_diff.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/post-v1-sha-bump-diff.sh"

PASS=0
FAIL=0

assert() {
  local description="$1"
  local condition="$2"
  if eval "$condition"; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description"
    echo "    condition: $condition"
    FAIL=$((FAIL + 1))
  fi
}

assert_contains() {
  local description="$1" haystack="$2" needle="$3"
  if printf '%s' "$haystack" | grep -qF -- "$needle"; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description"
    echo "    expected to find: $needle"
    echo "    in: $(printf '%s' "$haystack" | head -c 400)…"
    FAIL=$((FAIL + 1))
  fi
}

# Case-insensitive variant for behavioral signal matches where the comment's
# capitalization is grammatical (sentence-cap) but the spec uses lowercase.
assert_contains_ci() {
  local description="$1" haystack="$2" needle="$3"
  if printf '%s' "$haystack" | grep -qiF -- "$needle"; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description"
    echo "    expected to find (case-insensitive): $needle"
    FAIL=$((FAIL + 1))
  fi
}

assert_not_contains() {
  local description="$1" haystack="$2" needle="$3"
  if ! printf '%s' "$haystack" | grep -qF -- "$needle"; then
    echo "  PASS — $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL — $description"
    echo "    expected NOT to find: $needle"
    FAIL=$((FAIL + 1))
  fi
}

[[ -f "$SCRIPT" ]] || { echo "FAIL — script not found at $SCRIPT"; exit 1; }
# shellcheck disable=SC1090
source "$SCRIPT"

echo "== post-v1-sha-bump-diff tests =="

# --- Inline fixtures ---

# Fixture: README diff that bumps the V1 Reference Commit SHA.
readonly README_BUMP_DIFF=$'diff --git a/docs/migration/README.md b/docs/migration/README.md
index abcdef..fedcba 100644
--- a/docs/migration/README.md
+++ b/docs/migration/README.md
@@ -16,7 +16,7 @@ All facts in this docset were reconciled against:

 - **Repo:** `hcunanan79/COREcare-access`
-- **Commit SHA:** `9738412a6e41064203fc253d9dd2a5c6a9c2e231`
+- **Commit SHA:** `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
 - **Commit subject:** `feat(#1479): January annual mileage-rate verification banner (#1480)`'

# Fixture: README diff with no SHA-line change (different paragraph touched).
readonly README_NO_BUMP_DIFF=$'diff --git a/docs/migration/README.md b/docs/migration/README.md
index abcdef..fedcba 100644
--- a/docs/migration/README.md
+++ b/docs/migration/README.md
@@ -2,7 +2,7 @@

 This directory holds reference material about COREcare **v1**.

-**Audience:** engineers contributing to v2.
+**Audience:** engineers contributing to v2 — including AI agents acting on their behalf.'

# Fixture: README diff where the SHA line appears on both sides but the SHA is unchanged.
readonly README_IDENTICAL_DIFF=$'diff --git a/docs/migration/README.md b/docs/migration/README.md
index abcdef..fedcba 100644
--- a/docs/migration/README.md
+++ b/docs/migration/README.md
@@ -16,7 +16,7 @@

 - **Repo:** `hcunanan79/COREcare-access`
-- **Commit SHA:** `9738412a6e41064203fc253d9dd2a5c6a9c2e231`
+- **Commit SHA:** `9738412a6e41064203fc253d9dd2a5c6a9c2e231`
 - **Commit subject:** `feat(#1479)…`'

# Fixture: a small urls.py diff (3 routes added).
readonly URLS_DIFF=$'diff --git a/clients/urls.py b/clients/urls.py
index 1111111..2222222 100644
--- a/clients/urls.py
+++ b/clients/urls.py
@@ -10,3 +10,6 @@ urlpatterns = [
     path("clients/", views.client_list, name="client_list"),
     path("clients/<int:pk>/", views.client_detail, name="client_detail"),
+    path("family/portal/", views.family_portal, name="family_portal"),
+    path("family/clients/<int:pk>/", views.family_client_detail, name="family_client_detail"),
+    path("family/visits/", views.family_visits, name="family_visits"),
 ]'

# Fixture: clients/ diff with NO permission gate change (just template tweak).
readonly CLIENTS_DIFF_NO_GATE=$'diff --git a/clients/templates/clients/list.html b/clients/templates/clients/list.html
index 1111111..2222222 100644
--- a/clients/templates/clients/list.html
+++ b/clients/templates/clients/list.html
@@ -1,3 +1,3 @@
-<h1>Clients</h1>
+<h1>Active clients</h1>
 <ul class="client-list">'

# Fixture: clients/ diff that touches the canonical permission gate.
readonly CLIENTS_DIFF_PERMISSION=$'diff --git a/clients/permissions.py b/clients/permissions.py
index 1111111..2222222 100644
--- a/clients/permissions.py
+++ b/clients/permissions.py
@@ -3,5 +3,7 @@
 def _check_client_access(user, client):
-    return user.is_caregiver_of(client)
+    if user.is_caregiver_of(client):
+        return True
+    return user.is_family_of(client)'

# Fixture: clients/models.py diff that introduces an `is_active` column on ClientFamilyMember.
readonly MODELS_DIFF_FINGERPRINT=$'diff --git a/clients/models.py b/clients/models.py
index 1111111..2222222 100644
--- a/clients/models.py
+++ b/clients/models.py
@@ -42,6 +42,8 @@ class ClientFamilyMember(models.Model):
     client = models.ForeignKey(Client, on_delete=models.CASCADE)
     user = models.OneToOneField(User, on_delete=models.CASCADE)
     relation = models.CharField(max_length=50)
+    is_active = models.BooleanField(default=True)
+    deactivated_at = models.DateTimeField(null=True, blank=True)'

# Fixture: clients/models.py diff that does NOT touch ClientFamilyMember.
readonly MODELS_DIFF_NO_MATCH=$'diff --git a/clients/models.py b/clients/models.py
index 1111111..2222222 100644
--- a/clients/models.py
+++ b/clients/models.py
@@ -10,3 +10,4 @@ class Client(models.Model):
     name = models.CharField(max_length=200)
     dob = models.DateField(null=True, blank=True)
+    notes = models.TextField(blank=True, default="")'

readonly EMPTY_DIFF=""

# --- Assertion 1: SHA-bump detected ---

result=$(printf '%s\n' "$README_BUMP_DIFF" | extract_sha_bump)
assert \
  "1. SHA-bump detected from a fixture diff" \
  "[[ '$result' == '9738412a6e41064203fc253d9dd2a5c6a9c2e231 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' ]]"

# --- Assertion 2: no-op when no SHA line in diff ---

result=$(printf '%s\n' "$README_NO_BUMP_DIFF" | extract_sha_bump)
assert \
  "2. no-op when README diff does not touch the Commit SHA line" \
  "[[ -z '$result' ]]"

# --- Assertion 3: no-op when SHAs identical ---

result=$(printf '%s\n' "$README_IDENTICAL_DIFF" | extract_sha_bump)
assert \
  "3. no-op when old and new SHAs are identical (reformat-only)" \
  "[[ -z '$result' ]]"

# --- Assertion 4: no-op when README modified but SHA line untouched ---
# Same fixture as #2, expressed as the explicit "different paragraph changed" case.

result=$(printf '%s\n' "$README_NO_BUMP_DIFF" | extract_sha_bump)
assert \
  "4. no-op when README change is to a different paragraph" \
  "[[ -z '$result' ]]"

# --- Assertion 5: sticky-comment marker present (exactly once) ---

body=$(format_comment "9738412abcdef" "aaaaaaabcdef0" "$URLS_DIFF" "$CLIENTS_DIFF_NO_GATE" "$EMPTY_DIFF" "")
marker_count=$(printf '%s\n' "$body" | grep -c '<!-- v1-sha-bump-diff-report -->' || true)
assert \
  "5. sticky-comment marker present exactly once in body" \
  "[[ $marker_count -eq 1 ]]"

# --- Assertion 6: empty-diff branch wording ---

empty_body=$(format_comment "9738412" "aaaaaaa" "$EMPTY_DIFF" "$EMPTY_DIFF" "$EMPTY_DIFF" "")
assert_contains_ci \
  "6a. empty-diff comment contains 'all diffs empty' (case-insensitive)" \
  "$empty_body" \
  "all diffs empty"
assert_contains \
  "6b. empty-diff comment contains 'bump \`last reconciled\`'" \
  "$empty_body" \
  "bump \`last reconciled\`"

# --- Assertion 7: permission-gate branch bolds the right action ---

gate_body=$(format_comment "9738412" "aaaaaaa" "$URLS_DIFF" "$CLIENTS_DIFF_PERMISSION" "$EMPTY_DIFF" "")
assert_contains \
  "7a. permission-gate body bolds 'flag \`CUTOVER_PLAN.md\` owners'" \
  "$gate_body" \
  "**Action: re-author + flag \`CUTOVER_PLAN.md\` owners.**"
assert_contains \
  "7b. permission-gate body mutes 're-author affected rows' (other branch)" \
  "$gate_body" \
  "~~Action: re-author affected rows~~"
assert_contains \
  "7c. permission-gate body mutes 'bump \`last reconciled\` only' (other branch)" \
  "$gate_body" \
  "~~Action: bump \`last reconciled\` only~~"

# --- Assertion 8: truncation banner present + correct rerun command ---

# Build a fake "large" diff using `seq` so we don't ship a kilobyte fixture file.
# Override DIFF_CAP_BYTES to a small value so even a small fixture exceeds the cap.
big_diff=$(printf 'diff --git a/clients/urls.py b/clients/urls.py\n'; \
           for i in $(seq 1 100); do printf '+    path("family/r%d/", views.r%d, name="r%d"),\n' "$i" "$i" "$i"; done)
DIFF_CAP_BYTES=200 trunc_body=$(format_comment "9738412abc" "aaaaaaab" "$big_diff" "$EMPTY_DIFF" "$EMPTY_DIFF" "")
assert_contains \
  "8a. truncation banner present when diff exceeds DIFF_CAP_BYTES" \
  "$trunc_body" \
  "more bytes truncated. Run locally:"
assert_contains \
  "8b. truncation banner emits a copy-pasteable git diff rerun command with the pathspec" \
  "$trunc_body" \
  "git -C <v1-checkout> diff 9738412abc..aaaaaaab -- '*/urls.py'"

# --- Assertion 9: stats counts correct (files / +lines / −lines) ---

read -r urls_files urls_plus urls_minus <<<"$(format_stats_row "$URLS_DIFF")"
assert \
  "9a. urls.py fixture counts: 1 file, 3 +lines, 0 -lines" \
  "[[ '$urls_files' == '1' && '$urls_plus' == '3' && '$urls_minus' == '0' ]]"

read -r p_files p_plus p_minus <<<"$(format_stats_row "$CLIENTS_DIFF_PERMISSION")"
assert \
  "9b. permissions.py fixture counts: 1 file, 3 +lines, 1 -lines" \
  "[[ '$p_files' == '1' && '$p_plus' == '3' && '$p_minus' == '1' ]]"

read -r e_files e_plus e_minus <<<"$(format_stats_row "$EMPTY_DIFF")"
assert \
  "9c. empty-diff fixture counts: 0 files, 0 +lines, 0 -lines" \
  "[[ '$e_files' == '0' && '$e_plus' == '0' && '$e_minus' == '0' ]]"

# --- Assertion 10: hidden machine-parseable diff-stats line ---

stats_body=$(format_comment "9738412" "aaaaaaa" "$URLS_DIFF" "$CLIENTS_DIFF_PERMISSION" "$EMPTY_DIFF" "")
assert_contains \
  "10a. comment contains a machine-parseable diff-stats HTML comment" \
  "$stats_body" \
  "<!-- diff-stats: urls=1,+3,-0; clients=1,+3,-1; models=0,+0,-0 -->"

# --- Assertion 11: fingerprint-match callout on ClientFamilyMember invariant token ---

fp_body=$(format_comment "9738412" "aaaaaaa" "$EMPTY_DIFF" "$EMPTY_DIFF" "$MODELS_DIFF_FINGERPRINT" "")
assert_contains \
  "11a. fingerprint match: callout fires when models.py diff touches is_active near ClientFamilyMember" \
  "$fp_body" \
  "Baseline fingerprint match"

no_fp_body=$(format_comment "9738412" "aaaaaaa" "$EMPTY_DIFF" "$EMPTY_DIFF" "$MODELS_DIFF_NO_MATCH" "")
assert_not_contains \
  "11b. fingerprint match: no callout when models.py diff does NOT touch ClientFamilyMember" \
  "$no_fp_body" \
  "Baseline fingerprint match"

# --- Assertion 12: slice_pr_diff_to_readme isolates the README section ---
# Caught a real CI failure: `gh pr diff` does not accept `-- <path>` filtering,
# so we slice the full PR diff in the script. Regression-protect that.

readonly MULTI_FILE_PR_DIFF=$'diff --git a/Makefile b/Makefile
index 1111111..2222222 100644
--- a/Makefile
+++ b/Makefile
@@ -52,4 +52,5 @@ test-v1-docs:
 \tbash scripts/tests/test_check_v1_doc_hygiene.sh
+\tbash scripts/tests/test_post_v1_sha_bump_diff.sh
diff --git a/docs/migration/README.md b/docs/migration/README.md
index abcdef..fedcba 100644
--- a/docs/migration/README.md
+++ b/docs/migration/README.md
@@ -16,7 +16,7 @@
 - **Repo:** `hcunanan79/COREcare-access`
-- **Commit SHA:** `9738412a6e41064203fc253d9dd2a5c6a9c2e231`
+- **Commit SHA:** `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
diff --git a/scripts/post-v1-sha-bump-diff.sh b/scripts/post-v1-sha-bump-diff.sh
new file mode 100755
index 0000000..3333333
--- /dev/null
+++ b/scripts/post-v1-sha-bump-diff.sh
@@ -0,0 +1,3 @@
+#!/usr/bin/env bash
+set -uo pipefail'

readme_only=$(printf '%s\n' "$MULTI_FILE_PR_DIFF" | slice_pr_diff_to_readme)

assert_contains \
  "12a. slice extracts the README diff header" \
  "$readme_only" \
  "diff --git a/docs/migration/README.md b/docs/migration/README.md"
assert_contains \
  "12b. slice preserves the SHA-bump line" \
  "$readme_only" \
  "+- **Commit SHA:** \`aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\`"
assert_not_contains \
  "12c. slice excludes the Makefile diff header" \
  "$readme_only" \
  "diff --git a/Makefile b/Makefile"
assert_not_contains \
  "12d. slice excludes the post-v1-sha-bump-diff.sh diff header" \
  "$readme_only" \
  "diff --git a/scripts/post-v1-sha-bump-diff.sh"

# Round-trip: the sliced output should still drive extract_sha_bump correctly.
result=$(printf '%s\n' "$readme_only" | extract_sha_bump)
assert \
  "12e. sliced README section feeds extract_sha_bump correctly" \
  "[[ '$result' == '9738412a6e41064203fc253d9dd2a5c6a9c2e231 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' ]]"

# README absent from the PR → slice returns empty → main() short-circuits.
no_readme_pr_diff=$'diff --git a/Makefile b/Makefile
index 1111111..2222222 100644
--- a/Makefile
+++ b/Makefile
@@ -52,4 +52,5 @@ test-v1-docs:
+\tbash scripts/tests/test_new.sh'
empty_slice=$(printf '%s\n' "$no_readme_pr_diff" | slice_pr_diff_to_readme)
assert \
  "12f. PR diff without README → slice returns empty (script no-ops)" \
  "[[ -z '$empty_slice' ]]"

# --- Cross-cutting assertion: 'silent drift' phrase present (Writer requirement) ---

assert_contains \
  "X. comment body uses 'silent drift' as the searchable signal phrase" \
  "$stats_body" \
  "silent drift"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" == 0 ]] || exit 1
