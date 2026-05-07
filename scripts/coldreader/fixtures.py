"""Fixture loader + PHI deny.

Each persona owns a YAML fixture under `scripts/coldreader/fixtures/<persona>.yaml`
containing 3 cold-reader rotation questions and the load-bearing facts each
question's answer must cover. The loader validates schema and rejects any text
that looks like real PHI — placeholder tokens (`[CLIENT_NAME]` etc.) are allowed.
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
    expected_fact_summary: str


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


def load_fixture(path: Path) -> Fixture:
    """Parse, validate, and PHI-check a fixture YAML file."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(isinstance(raw, dict), f"{path}: top-level must be a mapping")
    assert isinstance(raw, dict)  # for type-checker

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
        qid = q.get("id")
        text = q.get("text")
        summary = q.get("expected_fact_summary")
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
            f"{path}: question[{i}].expected_fact_summary must be a non-empty "
            "string — it grounds the soft-compare check during scoring",
        )
        assert isinstance(qid, str) and isinstance(text, str) and isinstance(summary, str)
        _require(
            qid not in seen_ids,
            f"{path}: duplicate question id {qid!r}; ids must be unique within a fixture",
        )
        seen_ids.add(qid)

        _check_phi(f"{path}::question[{i}].text", text)
        _check_phi(f"{path}::question[{i}].expected_fact_summary", summary)
        questions.append(
            Question(id=qid, text=text, expected_fact_summary=summary),
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
