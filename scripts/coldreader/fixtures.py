"""Fixture loader + PHI deny + must_mention anchoring.

Each persona owns a YAML fixture under `scripts/coldreader/fixtures/<persona>.yaml`
containing 3 cold-reader rotation questions. Per question:

- `text`: the question posed to the model.
- `fact_summary`: human-readable explanation of the load-bearing facts (documentation only).
- `must_mention`: list of OR-groups; each entry is a list of acceptable surface
  forms (alternates). The model's answer must include at least one alternate
  per entry, allowing up to `tolerance` misses.
- `tolerance`: optional integer (default 0); how many `must_mention` entries
  may be missing without failing.

The loader validates schema, rejects any text that looks like real PHI
(placeholder tokens like `[CLIENT_NAME]` are allowed), and hard-fails on the
legacy `expected_fact_summary` key — the rename to `fact_summary` is atomic.

`anchor_must_mention(...)` is a separate, callable hook used by the runner
(in dry-run and live runs) to enforce that every `must_mention` entry has at
least one alternate that appears as a substring of the persona's section ∪
cross-reference index. This catches inventory drift at fixture-load time.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from inventory import PERSONAS

MIN_SECTION_BYTES_FLOOR = 1000


class FixtureSchemaError(ValueError):
    """Raised when a fixture file violates the schema contract."""


class PHIInFixtureError(ValueError):
    """Raised when a fixture's text looks like real PHI."""


# Regex deny set. Each entry's value is a *finder* — the matching substring is
# rejected unless it overlaps with one of the documented placeholder tokens.
PHI_DENY_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "dob_slash": re.compile(r"\b\d{1,2}/\d{1,2}/(?:19|20)\d{2}\b"),
    "dob_dash": re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b"),
}

# Placeholder tokens used in the live inventory doc. Matching content within
# these is allowed even if it overlaps a deny pattern.
_PLACEHOLDER_PATTERNS = (
    re.compile(r"\[[A-Z_]+\]"),  # [CLIENT_NAME], [CAREGIVER_NAME], etc.
    re.compile(r"<[A-Z_]+>"),  # <FAMILY_MEMBER>, <CLIENT_ID>, etc.
)


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    fact_summary: str
    must_mention: tuple[tuple[str, ...], ...]
    tolerance: int = 0


@dataclass(frozen=True)
class Fixture:
    persona: str
    min_section_bytes: int
    questions: tuple[Question, ...]
    source_path: Path


def _is_inside_placeholder(text: str, span: tuple[int, int]) -> bool:
    s, e = span
    for pat in _PLACEHOLDER_PATTERNS:
        for m in pat.finditer(text):
            if m.start() <= s and m.end() >= e:
                return True
    return False


def _check_phi(label: str, text: str) -> None:
    for name, pat in PHI_DENY_PATTERNS.items():
        for m in pat.finditer(text):
            if _is_inside_placeholder(text, m.span()):
                continue
            raise PHIInFixtureError(
                f"{label}: matched PHI deny pattern {name!r} on substring "
                f"{m.group()!r}. Use placeholder tokens like [CLIENT_NAME] instead."
            )


def _require(cond: object, msg: str) -> None:
    if not cond:
        raise FixtureSchemaError(msg)


def _load_must_mention(label: str, raw: object) -> tuple[tuple[str, ...], ...]:
    _require(
        isinstance(raw, list),
        f"{label}: 'must_mention' must be a list of OR-groups; got {type(raw).__name__}",
    )
    assert isinstance(raw, list)
    _require(
        len(raw) >= 1,
        f"{label}: 'must_mention' must have at least one entry — empty list "
        "would mean the answer is unconstrained, which defeats validation",
    )
    groups: list[tuple[str, ...]] = []
    for i, entry in enumerate(raw):
        _require(
            isinstance(entry, list) and len(entry) >= 1,
            f"{label}: must_mention[{i}] must be a non-empty list of alternate surface forms",
        )
        assert isinstance(entry, list)
        alts: list[str] = []
        for j, alt in enumerate(entry):
            _require(
                isinstance(alt, str) and alt.strip(),
                f"{label}: must_mention[{i}][{j}] must be a non-empty string",
            )
            assert isinstance(alt, str)
            _check_phi(f"{label}::must_mention[{i}][{j}]", alt)
            alts.append(alt)
        groups.append(tuple(alts))
    return tuple(groups)


def load_fixture(path: Path) -> Fixture:
    """Parse, validate, and PHI-check a fixture YAML file.

    Hard-fails on legacy `expected_fact_summary` key — the rename to
    `fact_summary` is atomic with the must_mention schema introduction.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(isinstance(raw, dict), f"{path}: top-level must be a mapping")
    assert isinstance(raw, dict)

    persona = raw.get("persona")
    _require(
        isinstance(persona, str) and persona in PERSONAS,
        f"{path}: 'persona' must be one of {PERSONAS}; got {persona!r}",
    )
    assert isinstance(persona, str)

    expected_filename = f"{persona}.yaml"
    _require(
        path.name == expected_filename,
        f"{path}: filename {path.name!r} must match persona slug "
        f"{expected_filename!r} — copy-paste mismatch",
    )

    min_bytes = raw.get("min_section_bytes")
    _require(
        isinstance(min_bytes, int) and min_bytes >= MIN_SECTION_BYTES_FLOOR,
        f"{path}: 'min_section_bytes' must be an int >= "
        f"{MIN_SECTION_BYTES_FLOOR}; got {min_bytes!r}",
    )
    assert isinstance(min_bytes, int)

    questions_raw = raw.get("questions")
    _require(
        isinstance(questions_raw, list) and len(questions_raw) == 3,
        f"{path}: must have exactly 3 questions; got "
        f"{len(questions_raw) if isinstance(questions_raw, list) else 'non-list'}",
    )
    assert isinstance(questions_raw, list)

    questions: list[Question] = []
    seen_ids: set[str] = set()
    for i, q_raw in enumerate(questions_raw):
        _require(isinstance(q_raw, dict), f"{path}: question[{i}] must be a mapping")
        q: dict[str, Any] = q_raw
        _require(
            "expected_fact_summary" not in q,
            f"{path}: question[{i}] uses legacy key 'expected_fact_summary'; "
            "rename to 'fact_summary' (the field is now documentation only; "
            "validation is driven by 'must_mention').",
        )
        qid = q.get("id")
        text = q.get("text")
        summary = q.get("fact_summary")
        must_mention_raw = q.get("must_mention")
        tolerance_raw = q.get("tolerance", 0)
        _require(
            isinstance(qid, str) and qid,
            f"{path}: question[{i}].id must be a non-empty string",
        )
        _require(
            isinstance(text, str) and text.strip(),
            f"{path}: question[{i}].text must be a non-empty string",
        )
        _require(
            isinstance(summary, str) and summary.strip(),
            f"{path}: question[{i}].fact_summary must be a non-empty string "
            "(documentation only; not used by the validator).",
        )
        _require(
            isinstance(tolerance_raw, int) and tolerance_raw >= 0,
            f"{path}: question[{i}].tolerance must be a non-negative int; "
            f"got {tolerance_raw!r}",
        )
        assert (
            isinstance(qid, str) and isinstance(text, str) and isinstance(summary, str)
        )
        assert isinstance(tolerance_raw, int)
        _require(
            qid not in seen_ids,
            f"{path}: duplicate question id {qid!r}; ids must be unique within a fixture",
        )
        seen_ids.add(qid)

        _check_phi(f"{path}::question[{i}].text", text)
        _check_phi(f"{path}::question[{i}].fact_summary", summary)
        must_mention = _load_must_mention(f"{path}::question[{i}]", must_mention_raw)
        questions.append(
            Question(
                id=qid,
                text=text,
                fact_summary=summary,
                must_mention=must_mention,
                tolerance=tolerance_raw,
            ),
        )

    return Fixture(
        persona=persona,
        min_section_bytes=min_bytes,
        questions=tuple(questions),
        source_path=path,
    )


def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


def iter_repo_fixtures() -> Iterator[Fixture]:
    """Yield every fixture under `scripts/coldreader/fixtures/`, sorted by persona."""
    for path in sorted(fixtures_dir().glob("*.yaml")):
        yield load_fixture(path)


def anchor_must_mention(
    fixture: Fixture,
    *,
    section: str,
    index: str,
) -> None:
    """Verify every `must_mention` entry has ≥1 alternate appearing as a
    substring of section ∪ index.

    Raises `FixtureSchemaError` naming the unanchored entries so the
    operator can fix the fixture or restore the inventory row.
    """
    haystack = (section + "\n" + index).lower()
    unanchored: list[tuple[str, str]] = []  # (qid, canonical_form)
    for q in fixture.questions:
        for entry in q.must_mention:
            if not any(alt.lower() in haystack for alt in entry):
                unanchored.append((q.id, entry[0]))
    if unanchored:
        details = ", ".join(f"{qid}:{tok!r}" for qid, tok in unanchored)
        raise FixtureSchemaError(
            f"{fixture.source_path}: {len(unanchored)} must_mention entries "
            f"have no alternate appearing in section or cross-reference index "
            f"({details}). The inventory was edited or the fixture is stale; "
            "either restore the row or update the fixture."
        )


__all__ = [
    "Fixture",
    "FixtureSchemaError",
    "MIN_SECTION_BYTES_FLOOR",
    "PHI_DENY_PATTERNS",
    "PHIInFixtureError",
    "Question",
    "anchor_must_mention",
    "fixtures_dir",
    "iter_repo_fixtures",
    "load_fixture",
]
