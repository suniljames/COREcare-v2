# V1 reference-doc validation conventions

> Lives here, not in [`docs/developer/TESTING.md`](../developer/TESTING.md), because it governs v1 reference docs (the migration docset) rather than v2 application tests.

The bash + awk validators in `scripts/check-v1-doc-structure.sh` (and its sibling `scripts/check-v1-doc-hygiene.sh`) emit violation codes — short two-letter-prefix identifiers like `SL-1a`, `EL-2b`, `RR-4c` — that the test suite at `scripts/tests/test_check_v1_doc_structure.sh` exercises one at a time via fixture directories. The convention has been hardened over several issues; the rules below are the post-#196 final form.

## 1. Sub-letter when ≥2 emit branches share a code

Any code with two or more `print FILENAME ":" FNR ": <CODE>: ..."` emit branches is **sub-lettered** at the awk emit site (`SL-1a`, `SL-1b`, `SL-3a / SL-3b / SL-3c`, `EL-2a / EL-2b`, `CR-1a / CR-1b`, `GL-3a / GL-3b / GL-3c`, `RR-4a..d`). Single-emit codes (`SL-2`, `SL-4`, `EL-1`, `WF-1`, etc.) stay bare.

Canonical reference shape: `^[A-Z]{2}-[0-9]+[a-z]?$`. At most one trailing sub-letter. No dots, no underscores, no multi-letter suffixes.

## 2. Fixtures use `assert_exit_and_match` with shortest-unique substrings

Every sub-lettered code's negative fixture asserts both the exit code AND a substring of the emit message that distinguishes its branch from siblings:

```bash
assert_exit_and_match "SL-3b: severity empty when v2_status=missing fails" 1 \
  'SL-3b:.*severity is empty' \
  "$STRUCTURE" --dir "$TEST_DIR/integrations-sl3-empty"
```

Bare `assert_exit` is forbidden for any sub-lettered code. Rationale: an exit-1 from any other branch would silently pass an exit-only fixture. Positive fixtures (expecting exit 0) need no substring; their description token still uses the sub-letter so MT-1 sees the branch as covered.

## 3. MT-1 enforces per-branch parity

The meta-test at `scripts/tests/test_check_v1_doc_structure.sh:2685+` asserts that the set of distinct code references in the awk equals the set of fixture description tokens. The umbrella filter `_filter_umbrellas` drops bare `X-N` when `X-N<letter>` is also present, so umbrella mentions in headers and prose comments don't pollute parity.

A fixture for every emit branch — not just every code — is required.

## 4. MT-2 enforces canonical code shape

A second meta-test at `scripts/tests/test_check_v1_doc_structure.sh:3055+` greps the structure script for any code-shaped reference and fails if any match doesn't conform to `^[A-Z]{2}-[0-9]+[a-z]?$`. Hard trip-wire on drift forms `SL-1.1`, `SL_1a`, `SL-1ab` — they would otherwise silently disappear from MT-1's set.

## 5. Authoring inside the integrations awk block

The awk script in `scripts/check-v1-doc-structure.sh` is enclosed in BASH single quotes. Inside the awk block, **literal `'` characters in comments or strings break the bash quoting** and surface as `awk: syntax error` at runtime. To include an apostrophe in an awk string, use the escape `'\''` (see existing emit lines for the pattern). For comments, rephrase without apostrophes.

## Where the rule lives

The authoritative convention comment is at `scripts/tests/test_check_v1_doc_structure.sh:577`. This file is a navigational pointer for new contributors; the comment in the test file is the source of truth.
