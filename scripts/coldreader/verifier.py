"""Verbatim-evidence + soft expected_fact_summary checks.

Pure functions, no I/O. The runner composes these into the two-pass scoring
flow. Both checks are needed to call a question PASS:

1. **verify_evidence**: every verbatim_evidence string must literally appear
   in the section or index. This catches the model fabricating citations.
2. **check_summary_match**: the model's answer must mention the load-bearing
   facts named in the fixture's expected_fact_summary. This catches the
   model giving an evidenced-but-wrong answer (e.g., citing the right
   region but reaching the wrong conclusion).

A question fails if EITHER check fails on Pass A AND Pass B (with extended
thinking).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class VerifyResult:
    passed: bool
    reason: str = ""


def verify_evidence(
    evidence: tuple[str, ...],
    section: str,
    index: str,
) -> VerifyResult:
    """Each verbatim_evidence string must appear literally in section OR index.

    Returns the first missing string for inclusion in the failure message.
    Empty evidence → fail (the model didn't ground its answer).
    """
    if not evidence:
        return VerifyResult(passed=False, reason="model returned no verbatim_evidence")

    sources = (section, index)
    for s in evidence:
        # Trim whitespace at edges; the model's quoting is sometimes loose.
        needle = s.strip()
        if not needle:
            return VerifyResult(passed=False, reason="empty evidence string")
        if not any(needle in src for src in sources):
            return VerifyResult(
                passed=False,
                reason=(f"verbatim_evidence string not found in section or index: {needle!r}"),
            )
    return VerifyResult(passed=True)


_KEYWORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{4,}")


def _keywords(text: str) -> set[str]:
    """Extract reasonable keywords for soft matching (lowercase, ≥5 chars)."""
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "their",
        "have",
        "must",
        "will",
        "they",
        "what",
        "where",
        "which",
        "into",
        "should",
        "would",
        "about",
        "across",
        "section",
        "rotation",
        "answer",
        "question",
    }
    return {
        m.group(0).lower()
        for m in _KEYWORD_RE.finditer(text)
        if m.group(0).lower() not in stopwords
    }


def check_summary_match(
    answer: str,
    expected_fact_summary: str,
    *,
    threshold: float = 0.25,
) -> VerifyResult:
    """Loose keyword overlap between the answer and the fixture's summary.

    Used to catch evidenced-but-wrong answers. Threshold 0.25 means at
    least 25% of the summary's distinctive keywords must appear in the
    answer. Calibrated against the first live run on 2026-05-07 — observed
    answer overlaps for technically-correct paraphrased answers were 19–28%,
    while genuinely off answers cluster well below that. Paired with trimmed
    `expected_fact_summary` fixtures that focus on the load-bearing claim
    rather than exhaustive context.
    """
    if not answer.strip():
        return VerifyResult(passed=False, reason="empty answer")

    expected_kw = _keywords(expected_fact_summary)
    if not expected_kw:
        # Empty summary should never happen post-schema-validation, but be safe.
        return VerifyResult(passed=True)
    answer_kw = _keywords(answer)
    overlap = expected_kw & answer_kw
    ratio = len(overlap) / len(expected_kw)
    if ratio < threshold:
        missing = sorted(expected_kw - answer_kw)[:8]
        return VerifyResult(
            passed=False,
            reason=(
                f"answer covers only {ratio:.0%} of expected_fact_summary "
                f"keywords (threshold {threshold:.0%}); missing key terms: "
                f"{missing}"
            ),
        )
    return VerifyResult(passed=True)
