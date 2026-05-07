"""Rotation runner: per-fixture two-pass scoring + dry-run smoke + summary render.

The runner is the orchestration layer between fixtures, the inventory parser,
the Anthropic client, and the verifier. It is the single entry point used by
both the CLI (`python run.py`) and the test suite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from client import RotationCall, RotationClient, RotationResponse, Usage
from fixtures import Fixture, Question, iter_repo_fixtures
from inventory import extract_index, extract_section
from verifier import check_summary_match, verify_evidence


@dataclass(frozen=True)
class RotationFailure:
    persona: str
    question_id: str
    question_text: str
    expected_fact_summary: str
    message: str


@dataclass
class RotationResult:
    persona: str
    failures: list[RotationFailure] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)

    @property
    def passed(self) -> bool:
        return not self.failures

    def format_failure(self, failure: RotationFailure) -> str:
        return (
            f"FAILED — {failure.persona} / {failure.question_id} "
            f"({failure.question_text!r})\n"
            f"  Expected fact: {failure.expected_fact_summary.strip()}\n"
            f"  {failure.message}"
        )


@dataclass(frozen=True)
class DrySmokeSummary:
    fixtures_loaded: int
    section_bytes_above_floor: int
    errors: list[str]


def _score_question(
    fx: Fixture,
    q: Question,
    section: str,
    index: str,
    client: RotationClient,
    *,
    allow_retry: bool,
) -> tuple[RotationResponse, RotationFailure | None]:
    """Run one question; if it fails on pass A and retry is allowed, run pass B.

    Returns (last_response, failure_or_none). The caller aggregates usage from
    every response yielded along the way — this helper aggregates internally.
    """
    pass_a = client.query_rotation(
        RotationCall(
            persona=fx.persona,
            question_id=q.id,
            question_text=q.text,
            section_text=section,
            index_text=index,
            use_extended_thinking=False,
        )
    )
    failure_a = _evaluate(fx.persona, q, pass_a, section, index)
    if failure_a is None:
        return pass_a, None

    if not allow_retry:
        return pass_a, failure_a

    pass_b = client.query_rotation(
        RotationCall(
            persona=fx.persona,
            question_id=q.id,
            question_text=q.text,
            section_text=section,
            index_text=index,
            use_extended_thinking=True,
        )
    )
    failure_b = _evaluate(fx.persona, q, pass_b, section, index)
    # Aggregate usage by stuffing pass-A's usage into the response we return —
    # the caller adds pass_b.usage anyway. Trick: return a wrapper.
    combined_response = RotationResponse(
        answer=pass_b.answer,
        verbatim_evidence=pass_b.verbatim_evidence,
        confidence=pass_b.confidence,
        usage=pass_a.usage + pass_b.usage,
        used_extended_thinking=True,
    )
    return combined_response, failure_b


def _evaluate(
    persona: str,
    q: Question,
    response: RotationResponse,
    section: str,
    index: str,
) -> RotationFailure | None:
    if not response.answer.strip():
        return RotationFailure(
            persona=persona,
            question_id=q.id,
            question_text=q.text,
            expected_fact_summary=q.expected_fact_summary,
            message=(
                "model returned empty answer — section + index do not contain the load-bearing fact"
            ),
        )
    ev_check = verify_evidence(response.verbatim_evidence, section, index)
    if not ev_check.passed:
        return RotationFailure(
            persona=persona,
            question_id=q.id,
            question_text=q.text,
            expected_fact_summary=q.expected_fact_summary,
            message=ev_check.reason,
        )
    summary_check = check_summary_match(response.answer, q.expected_fact_summary)
    if not summary_check.passed:
        return RotationFailure(
            persona=persona,
            question_id=q.id,
            question_text=q.text,
            expected_fact_summary=q.expected_fact_summary,
            message=summary_check.reason,
        )
    return None


def run_rotation(
    fx: Fixture,
    *,
    section: str,
    index: str,
    client: RotationClient,
    allow_retry: bool = True,
) -> RotationResult:
    """Run all 3 questions for a fixture; aggregate failures + usage."""
    if len(section.encode("utf-8")) < fx.min_section_bytes:
        raise ValueError(
            f"section for persona {fx.persona!r} is "
            f"{len(section.encode('utf-8'))} bytes; "
            f"min_section_bytes floor is {fx.min_section_bytes}. "
            "Refusing to call the API."
        )

    result = RotationResult(persona=fx.persona)
    for q in fx.questions:
        response, failure = _score_question(fx, q, section, index, client, allow_retry=allow_retry)
        result.usage = result.usage + response.usage
        if failure is not None:
            result.failures.append(failure)
    return result


def dry_run_smoke(inventory_path: Path | None = None) -> DrySmokeSummary:
    """Validate every fixture pairs cleanly with the live inventory — no API call.

    Used by `make coldreader-local-dry` and the PR-trigger workflow path.
    Reports total fixtures loaded, count of sections above floor, and any
    errors encountered (caller decides exit code).
    """
    inv = inventory_path
    if inv is None:
        repo_root = _repo_root_from(Path(__file__))
        inv = repo_root / "docs" / "migration" / "v1-pages-inventory.md"

    errors: list[str] = []
    above_floor = 0
    loaded = 0
    for fx in iter_repo_fixtures():
        loaded += 1
        try:
            section = extract_section(inv, fx.persona, min_bytes=fx.min_section_bytes)
            if len(section.encode("utf-8")) >= fx.min_section_bytes:
                above_floor += 1
        except Exception as e:  # noqa: BLE001 - surface every parser/floor error
            errors.append(f"{fx.persona}: {type(e).__name__}: {e}")
    try:
        extract_index(inv)
    except Exception as e:  # noqa: BLE001
        errors.append(f"cross-reference index: {type(e).__name__}: {e}")
    return DrySmokeSummary(
        fixtures_loaded=loaded,
        section_bytes_above_floor=above_floor,
        errors=errors,
    )


def _repo_root_from(start: Path) -> Path:
    for ancestor in start.resolve().parents:
        if (ancestor / "docs" / "migration" / "v1-pages-inventory.md").exists():
            return ancestor
    raise RuntimeError("Could not locate repo root from runner module location")


def render_summary_markdown(
    results: list[RotationResult],
    *,
    model: str,
    run_url: str | None = None,
) -> str:
    """Render a markdown summary suitable for `$GITHUB_STEP_SUMMARY` and tracking issues."""
    total_usage = Usage()
    for r in results:
        total_usage = total_usage + r.usage

    pass_personas = [r.persona for r in results if r.passed]
    fail_personas = [r.persona for r in results if not r.passed]

    lines: list[str] = []
    lines.append("## v1 inventory cold-reader rotation")
    if run_url:
        lines.append(f"- Run: {run_url}")
    lines.append(f"- Model: `{model}`")
    lines.append(
        f"- Tokens (uncached input + output): "
        f"{total_usage.input_tokens:,} + {total_usage.output_tokens:,}"
    )
    lines.append(
        f"- Cache read tokens: {total_usage.cache_read_input_tokens:,} "
        f"(hit ratio: {total_usage.cache_hit_ratio:.0%})"
    )
    lines.append(f"- Personas checked: {len(results)}")
    lines.append(f"- PASS: {len(pass_personas)} ({', '.join(pass_personas) or '—'})")
    lines.append(f"- FAIL: {len(fail_personas)} ({', '.join(fail_personas) or '—'})")
    lines.append("")
    if fail_personas:
        lines.append("### Drift detected")
        lines.append("")
        for r in results:
            for f in r.failures:
                lines.append(r.format_failure(f))
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"
