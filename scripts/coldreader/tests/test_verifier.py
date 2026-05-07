"""Direct unit tests for `verifier.verify_evidence` markdown handling.

The first live workflow runs surfaced two distinct failure modes that
verify_evidence didn't cover well: (1) the model dropping `**bold**`
markers when quoting evidence (2026-05-07 family-member/q3), and (2)
zero overlap between literal-route-path answers and prose summaries
(handled separately in fixtures). This file pins the markdown-strip
normalization so the regression doesn't recur.
"""

from __future__ import annotations

from verifier import _normalize_for_evidence, verify_evidence


def test_strips_bold_double_asterisks_from_haystack_and_needle() -> None:
    section = "**v1 has no active-flag on `ClientFamilyMember`** — no soft-delete"
    # Model's quote omits the `**` bold markers.
    needle = "v1 has no active-flag on `ClientFamilyMember` — no soft-delete"
    result = verify_evidence((needle,), section, "")
    assert result.passed, (
        f"verifier should accept evidence that omits bold markers; got: {result.reason}"
    )


def test_strips_bold_double_underscores() -> None:
    section = "__some emphasized text__ continues here"
    needle = "some emphasized text continues here"
    result = verify_evidence((needle,), section, "")
    assert result.passed


def test_normalize_strips_both_marker_styles() -> None:
    assert _normalize_for_evidence("**bold** and __also bold__") == "bold and also bold"


def test_normalize_preserves_whitespace_and_case() -> None:
    """Whitespace and case carry semantic weight; only markdown markers are stripped."""
    raw = "**v1**   has\n  whitespace AND CASE preserved"
    assert _normalize_for_evidence(raw) == "v1   has\n  whitespace AND CASE preserved"


def test_normalize_leaves_single_asterisk_alone() -> None:
    """Single asterisks are too risky to strip (could collide with prose text)."""
    raw = "5 * 5 equals 25; *italic*"
    assert _normalize_for_evidence(raw) == raw


def test_evidence_still_rejects_unrelated_strings() -> None:
    """Markdown stripping must not loosen the check for genuine drift."""
    section = "**The actual content of the section**"
    needle = "this is completely unrelated text"
    result = verify_evidence((needle,), section, "")
    assert not result.passed
    assert "not found" in result.reason


def test_evidence_check_works_on_index_alone() -> None:
    section = ""
    index = "**Cross-reference index** lists shared routes."
    needle = "Cross-reference index lists shared routes."
    result = verify_evidence((needle,), section, index)
    assert result.passed
