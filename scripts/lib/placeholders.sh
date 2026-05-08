# Locked PHI-placeholder vocabulary.
# Single source of truth — sourced by:
#   scripts/check-v1-doc-hygiene.sh   (allowlists these in any v1 doc)
#   scripts/check-v1-caption-phi.sh   (forbids these in caption bodies)
#
# When extending the placeholder set: edit ONLY this file, then run the test
# suites for both consumers (`make test-v1-docs`).
#
# Reference: docs/migration/README.md#phi-placeholder-convention

# shellcheck disable=SC2034  # variables are sourced; consumers reference them.

# Allowlist: bracketed forms that should NOT trip the real-name heuristic.
# (Used as the negative set in scripts/check-v1-doc-hygiene.sh.)
PLACEHOLDERS_ALLOWED_RE='\[(CLIENT_NAME|CLIENT_DOB|CLIENT_MRN|CAREGIVER_NAME|AGENCY_NAME|ADDRESS|PHONE|EMAIL|DIAGNOSIS|MEDICATION|NOTE_TEXT|SHIFT_ID|VISIT_ID|INVOICE_ID|REDACTED)\]'

# Caption-body forbid: identical token set, but used positively as a "find"
# pattern in scripts/check-v1-caption-phi.sh. Same vocabulary, different
# semantic — both consumers rely on the SAME set, which is why this file
# exists.
PLACEHOLDERS_FORBID_IN_CAPTION_BODY_RE="$PLACEHOLDERS_ALLOWED_RE"
