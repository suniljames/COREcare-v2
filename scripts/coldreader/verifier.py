"""Verbatim-evidence + must_mention checks.

Pure functions, no I/O. The runner composes these into per-question scoring.
Both checks are needed to call a question PASS:

1. **verify_evidence**: every verbatim_evidence string must literally appear
   in the section or index. This catches the model fabricating citations.
2. **check_must_mention**: the model's answer must contain each load-bearing
   token from the fixture's `must_mention` list. Each entry is an OR-group
   (a list of acceptable surface forms); the answer satisfies the entry if
   any one alternate appears as a case-insensitive substring. A per-question
   `tolerance` (default 0) controls how many entries may be missing.

This replaces the prior `check_summary_match` keyword-overlap heuristic, which
conflated load-bearing facts with prose connective tissue and over-flagged
correct paraphrased answers.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class VerifyResult:
    passed: bool
    reason: str = ""
    hits: int = 0
    total: int = 0


def _normalize_for_evidence(text: str) -> str:
    """Strip surface markdown markers before comparing evidence strings.

    The model occasionally drops bold/italic markers (`**`, `__`, `*`, `_`)
    from a quoted span when it copies "verbatim" — the substance is identical
    but a literal substring check rejects it. Normalizing both haystack and
    needle the same way makes the check robust to that.

    Whitespace and case are left alone — those carry semantic weight.
    """
    out = text
    for marker in ("**", "__"):
        out = out.replace(marker, "")
    # Single-char emphasis markers are riskier (they collide with text), so
    # only strip them when adjacent to alphanumeric chars on both sides — i.e.
    # likely emphasis, not punctuation. Skipped for now; the double-marker
    # strip alone covers every observed case.
    return out


def verify_evidence(
    evidence: tuple[str, ...],
    section: str,
    index: str,
) -> VerifyResult:
    """Each verbatim_evidence string must appear literally in section OR index.

    Returns the first missing string for inclusion in the failure message.
    Empty evidence → fail (the model didn't ground its answer).

    Both haystack and needle are normalized to strip bold-markdown markers
    (`**`, `__`) — the model sometimes drops these when quoting a bolded
    span. Whitespace and casing are preserved.
    """
    if not evidence:
        return VerifyResult(passed=False, reason="model returned no verbatim_evidence")

    sources = (_normalize_for_evidence(section), _normalize_for_evidence(index))
    for s in evidence:
        # Trim whitespace at edges; the model's quoting is sometimes loose.
        needle = _normalize_for_evidence(s.strip())
        if not needle:
            return VerifyResult(passed=False, reason="empty evidence string")
        if not any(needle in src for src in sources):
            return VerifyResult(
                passed=False,
                reason=(f"verbatim_evidence string not found in section or index: {needle!r}"),
            )
    return VerifyResult(passed=True)


def check_must_mention(
    answer: str,
    must_mention: Sequence[Sequence[str]],
    *,
    tolerance: int = 0,
) -> VerifyResult:
    """Each entry in `must_mention` is an OR-group; at least one alternate must
    appear as a case-insensitive substring of the answer. The answer may miss
    up to `tolerance` entries (default 0). Empty `must_mention` is a trivial
    pass.
    """
    total = len(must_mention)
    if total == 0:
        return VerifyResult(passed=True, hits=0, total=0)

    if not answer.strip():
        return VerifyResult(passed=False, reason="empty answer", hits=0, total=total)

    answer_lc = answer.lower()
    missing_canonical: list[str] = []
    hits = 0
    for entry in must_mention:
        if any(alt.lower() in answer_lc for alt in entry):
            hits += 1
        else:
            # Canonical form = first alternate in the OR-group.
            missing_canonical.append(entry[0])

    misses = total - hits
    if misses > tolerance:
        return VerifyResult(
            passed=False,
            reason=(
                f"answer missing {misses} of {total} must_mention entries "
                f"(tolerance {tolerance}); missing: {missing_canonical}"
            ),
            hits=hits,
            total=total,
        )
    return VerifyResult(passed=True, hits=hits, total=total)
