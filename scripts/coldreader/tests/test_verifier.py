"""L1 — verifier unit tests.

`verify_evidence` checks verbatim evidence appears in section/index (preserved).
`check_must_mention` checks the model's answer mentions an explicit list of
load-bearing tokens, with OR-group semantics and miss-tolerance.
"""

from __future__ import annotations

from verifier import VerifyResult, check_must_mention, verify_evidence

# --- check_must_mention ---


def test_must_mention_single_token_in_answer_passes() -> None:
    result = check_must_mention(
        answer="The is_superuser flag grants access.",
        must_mention=[["is_superuser"]],
    )
    assert result.passed
    assert result.hits == 1
    assert result.total == 1


def test_must_mention_or_group_alternate_match_passes() -> None:
    """Any one alternate in the OR-group satisfies the entry."""
    result = check_must_mention(
        answer="The superuser flag grants access.",
        must_mention=[["is_superuser", "superuser"]],
    )
    assert result.passed
    assert result.hits == 1


def test_must_mention_case_insensitive_substring_match() -> None:
    """Match is case-insensitive; both directions."""
    assert check_must_mention(
        answer="The IS_SUPERUSER flag grants access.",
        must_mention=[["is_superuser"]],
    ).passed
    assert check_must_mention(
        answer="The is_superuser flag grants access.",
        must_mention=[["IS_SUPERUSER"]],
    ).passed


def test_must_mention_substring_match_not_tokenized() -> None:
    """Literal substring; does not tokenize. `phi_displayed=true` must appear as a substring."""
    # Tokenization-style 'PHI ... displayed' should NOT match the canonical form.
    result = check_must_mention(
        answer="The rows where PHI is displayed in the table.",
        must_mention=[["phi_displayed=true"]],
    )
    assert not result.passed
    assert "phi_displayed=true" in result.reason


def test_must_mention_strict_one_of_two_missing_fails() -> None:
    result = check_must_mention(
        answer="Mentions only alpha here.",
        must_mention=[["alpha"], ["BETA_TOKEN"]],
        tolerance=0,
    )
    assert not result.passed
    assert result.hits == 1
    assert result.total == 2
    assert "BETA_TOKEN" in result.reason


def test_must_mention_tolerance_allows_n_misses() -> None:
    result = check_must_mention(
        answer="ZZA1, ZZB2, ZZC3, ZZD4 — covers four of five.",
        must_mention=[["ZZA1"], ["ZZB2"], ["ZZC3"], ["ZZD4"], ["ZZE5"]],
        tolerance=1,
    )
    assert result.passed
    assert result.hits == 4
    assert result.total == 5


def test_must_mention_tolerance_exceeded_fails() -> None:
    result = check_must_mention(
        answer="ZZA1 only here.",
        must_mention=[["ZZA1"], ["ZZB2"], ["ZZC3"]],
        tolerance=1,
    )
    assert not result.passed
    assert result.hits == 1
    assert result.total == 3


def test_must_mention_empty_answer_fails() -> None:
    result = check_must_mention(
        answer="",
        must_mention=[["alpha"]],
    )
    assert not result.passed
    assert "empty" in result.reason.lower()


def test_must_mention_failure_reason_names_canonical_form() -> None:
    """Missing OR-groups show their first alternate as the canonical form."""
    result = check_must_mention(
        answer="Nothing here.",
        must_mention=[
            ["is_superuser", "superuser"],
            ["billing_catalogs"],
        ],
    )
    assert not result.passed
    assert "is_superuser" in result.reason
    assert "billing_catalogs" in result.reason
    # Alternate forms should not be listed as missing entries
    # (canonical = the OR-group's first alternate).
    assert "superuser" not in result.reason.replace("is_superuser", "")


def test_must_mention_or_group_one_alternate_sufficient() -> None:
    """If any alternate appears, the entry is satisfied."""
    result = check_must_mention(
        answer="Uses the @staff_member_required decorator.",
        must_mention=[["@staff_member_required", "staff_member_required", "staff-required"]],
    )
    assert result.passed
    assert result.hits == 1


def test_must_mention_no_entries_passes_trivially() -> None:
    """Empty must_mention list = no constraints = pass."""
    result = check_must_mention(answer="anything", must_mention=[])
    assert result.passed
    assert result.hits == 0
    assert result.total == 0


def test_must_mention_returns_verify_result_dataclass() -> None:
    """API contract: returns a VerifyResult with passed/reason/hits/total."""
    result = check_must_mention(answer="alpha", must_mention=[["alpha"]])
    assert isinstance(result, VerifyResult)
    assert hasattr(result, "passed")
    assert hasattr(result, "reason")
    assert hasattr(result, "hits")
    assert hasattr(result, "total")


# --- verify_evidence (regression — existing behavior preserved) ---


def test_verify_evidence_passes_when_string_in_section() -> None:
    result = verify_evidence(
        evidence=("hello world",),
        section="this section contains hello world inline",
        index="",
    )
    assert result.passed


def test_verify_evidence_passes_when_string_in_index() -> None:
    result = verify_evidence(
        evidence=("from-the-index",),
        section="",
        index="cross-ref includes from-the-index entry",
    )
    assert result.passed


def test_verify_evidence_fails_on_empty_evidence() -> None:
    result = verify_evidence(evidence=(), section="anything", index="anything")
    assert not result.passed
    assert "no verbatim_evidence" in result.reason


def test_verify_evidence_fails_when_string_missing() -> None:
    result = verify_evidence(
        evidence=("not present anywhere",),
        section="this section",
        index="this index",
    )
    assert not result.passed
    assert "not present anywhere" in result.reason
