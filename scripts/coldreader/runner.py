"""Rotation runner: per-fixture must_mention scoring + dry-run smoke + summary render.

The runner is the orchestration layer between fixtures, the inventory parser,
the Anthropic client, and the verifier. It is the single entry point used by
both the CLI (`python run.py`) and the test suite.

A question PASSes when (1) verbatim_evidence verifies AND (2) the answer
satisfies the fixture's must_mention list within the question's tolerance.
Pass-B (extended thinking) is invoked once on a failing question; if Pass-B
returns no tool block but the response carried a text block, the runner
records the text-block content as a SETUP-ERROR (not drift) — this surfaces
the model declining to use the tool rather than masking it as content drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from client import RotationCall, RotationClient, RotationResponse, Usage
from fixtures import Fixture, Question, anchor_must_mention, iter_repo_fixtures
from inventory import extract_index, extract_section
from verifier import check_must_mention, verify_evidence

# Failure-class tags. `CONTENT` failures mean the answer is wrong (drift).
# `SETUP` failures mean the validator could not score this question at all
# (Pass-B tool refusal, evidence verification gone sideways) — they exit
# `EXIT_SETUP_ERROR` so the workflow does not raise a false drift alarm.
FAILURE_CLASS_CONTENT = "CONTENT"
FAILURE_CLASS_SETUP = "SETUP"

# Cap text-block content surfaced from a Pass-B tool refusal so a runaway
# model output cannot blow up the auto-issue body or the step summary.
TEXT_BLOCK_TRUNCATE_CHARS = 500


@dataclass(frozen=True)
class RotationFailure:
    persona: str
    question_id: str
    question_text: str
    fact_summary: str
    message: str
    failure_class: str = FAILURE_CLASS_CONTENT
    model_answer: str = ""


@dataclass(frozen=True)
class QuestionTelemetry:
    """Per-question hit-count signal recorded for every question, PASS or FAIL."""

    question_id: str
    hits: int
    total: int


@dataclass
class RotationResult:
    persona: str
    failures: list[RotationFailure] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    telemetry: list[QuestionTelemetry] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures

    @property
    def has_setup_error(self) -> bool:
        return any(f.failure_class == FAILURE_CLASS_SETUP for f in self.failures)

    def format_failure(self, failure: RotationFailure) -> str:
        # The model's actual answer is the load-bearing detail when triaging
        # whether a failure is real drift, a fixture-vocabulary mismatch, or
        # a question the model finds intractable. Scrub through the same
        # bounded + PHI-deny pass as Pass-B text-block content for parity —
        # this output lands in the public auto-issue body.
        answer_block = (
            f"\n  Model answer: {_truncate_phi_scrub(failure.model_answer.strip())}"
            if failure.model_answer
            else ""
        )
        return (
            f"FAILED [{failure.failure_class}] — {failure.persona} / "
            f"{failure.question_id} ({failure.question_text!r})\n"
            f"  Fact summary: {failure.fact_summary.strip()}\n"
            f"  {failure.message}{answer_block}"
        )


@dataclass(frozen=True)
class DrySmokeSummary:
    fixtures_loaded: int
    section_bytes_above_floor: int
    errors: list[str]


def _truncate_phi_scrub(text: str) -> str:
    """Truncate to bound and scrub PHI-shaped substrings before logging.

    Belt-and-suspenders: the model is grounded in a non-PHI inventory doc, so
    real PHI in a text-block would be a fixture/inventory authoring error
    (already caught by load-time PHI-deny). This pass scrubs anyway, since
    text-block content surfaces in the public auto-issue body.
    """
    from fixtures import PHI_DENY_PATTERNS

    truncated = text[:TEXT_BLOCK_TRUNCATE_CHARS]
    if len(text) > TEXT_BLOCK_TRUNCATE_CHARS:
        truncated += "…"
    scrubbed = truncated
    for _name, pat in PHI_DENY_PATTERNS.items():
        scrubbed = pat.sub("[PHI-REDACTED]", scrubbed)
    return scrubbed


def _score_question(
    fx: Fixture,
    q: Question,
    section: str,
    index: str,
    client: RotationClient,
    *,
    allow_retry: bool,
) -> tuple[RotationResponse, RotationFailure | None, QuestionTelemetry]:
    """Run one question; if it fails on pass A and retry is allowed, run pass B.

    Returns (last_response, failure_or_none, telemetry). The caller aggregates
    usage from every response yielded along the way — this helper aggregates
    internally.
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
    failure_a, telemetry_a = _evaluate(fx.persona, q, pass_a, section, index)
    if failure_a is None:
        return pass_a, None, telemetry_a

    if not allow_retry:
        return pass_a, failure_a, telemetry_a

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
    failure_b, telemetry_b = _evaluate(fx.persona, q, pass_b, section, index)
    combined_response = RotationResponse(
        answer=pass_b.answer,
        verbatim_evidence=pass_b.verbatim_evidence,
        confidence=pass_b.confidence,
        usage=pass_a.usage + pass_b.usage,
        used_extended_thinking=True,
        text_block_content=pass_b.text_block_content,
    )
    return combined_response, failure_b, telemetry_b


def _evaluate(
    persona: str,
    q: Question,
    response: RotationResponse,
    section: str,
    index: str,
) -> tuple[RotationFailure | None, QuestionTelemetry]:
    # Empty answer special case — distinguish two sub-cases:
    #   1) text_block_content present → Pass-B tool refusal (SETUP error)
    #   2) text_block_content absent → genuine "no answer" (CONTENT)
    if not response.answer.strip():
        if response.text_block_content and response.text_block_content.strip():
            scrubbed = _truncate_phi_scrub(response.text_block_content.strip())
            return (
                RotationFailure(
                    persona=persona,
                    question_id=q.id,
                    question_text=q.text,
                    fact_summary=q.fact_summary,
                    message=(
                        "model declined to call the rotation tool and emitted "
                        f"prose instead: {scrubbed!r}"
                    ),
                    failure_class=FAILURE_CLASS_SETUP,
                ),
                QuestionTelemetry(question_id=q.id, hits=0, total=len(q.must_mention)),
            )
        return (
            RotationFailure(
                persona=persona,
                question_id=q.id,
                question_text=q.text,
                fact_summary=q.fact_summary,
                message=(
                    "model returned empty answer — section + index do not "
                    "contain the load-bearing fact"
                ),
            ),
            QuestionTelemetry(question_id=q.id, hits=0, total=len(q.must_mention)),
        )

    ev_check = verify_evidence(response.verbatim_evidence, section, index)
    if not ev_check.passed:
        return (
            RotationFailure(
                persona=persona,
                question_id=q.id,
                question_text=q.text,
                fact_summary=q.fact_summary,
                message=ev_check.reason,
                model_answer=response.answer,
            ),
            QuestionTelemetry(question_id=q.id, hits=0, total=len(q.must_mention)),
        )

    mention_check = check_must_mention(response.answer, q.must_mention, tolerance=q.tolerance)
    telemetry = QuestionTelemetry(
        question_id=q.id, hits=mention_check.hits, total=mention_check.total
    )
    if not mention_check.passed:
        return (
            RotationFailure(
                persona=persona,
                question_id=q.id,
                question_text=q.text,
                fact_summary=q.fact_summary,
                message=mention_check.reason,
                model_answer=response.answer,
            ),
            telemetry,
        )
    return None, telemetry


def run_rotation(
    fx: Fixture,
    *,
    section: str,
    index: str,
    client: RotationClient,
    allow_retry: bool = True,
) -> RotationResult:
    """Run all 3 questions for a fixture; aggregate failures + usage + telemetry."""
    if len(section.encode("utf-8")) < fx.min_section_bytes:
        raise ValueError(
            f"section for persona {fx.persona!r} is "
            f"{len(section.encode('utf-8'))} bytes; "
            f"min_section_bytes floor is {fx.min_section_bytes}. "
            "Refusing to call the API."
        )

    # Anchoring guard before any API call — surfaces inventory drift as a
    # FixtureSchemaError, which the CLI converts to EXIT_SETUP_ERROR.
    anchor_must_mention(fx, section=section, index=index)

    result = RotationResult(persona=fx.persona)
    for q in fx.questions:
        response, failure, telemetry = _score_question(
            fx, q, section, index, client, allow_retry=allow_retry
        )
        result.usage = result.usage + response.usage
        result.telemetry.append(telemetry)
        if failure is not None:
            result.failures.append(failure)
    return result


def dry_run_smoke(inventory_path: Path | None = None) -> DrySmokeSummary:
    """Validate every fixture pairs cleanly with the live inventory — no API call.

    Used by `make coldreader-local-dry` and the PR-trigger workflow path.
    Reports total fixtures loaded, count of sections above floor, and any
    errors encountered (caller decides exit code). Anchoring is enforced —
    a stale must_mention token surfaces here, not at first live API call.
    """
    inv = inventory_path
    if inv is None:
        repo_root = _repo_root_from(Path(__file__))
        inv = repo_root / "docs" / "migration" / "v1-pages-inventory.md"

    errors: list[str] = []
    above_floor = 0
    loaded = 0
    try:
        index_text = extract_index(inv)
    except Exception as e:  # noqa: BLE001
        errors.append(f"cross-reference index: {type(e).__name__}: {e}")
        index_text = ""

    for fx in iter_repo_fixtures():
        loaded += 1
        try:
            section = extract_section(inv, fx.persona, min_bytes=fx.min_section_bytes)
            if len(section.encode("utf-8")) >= fx.min_section_bytes:
                above_floor += 1
            anchor_must_mention(fx, section=section, index=index_text)
        except Exception as e:  # noqa: BLE001 - surface every parser/floor/anchor error
            errors.append(f"{fx.persona}: {type(e).__name__}: {e}")
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
    """Render a markdown summary suitable for `$GITHUB_STEP_SUMMARY` and tracking issues.

    Always logs per-question must_mention hit counts (PASS or FAIL) so that
    drift in answer quality is observable before it crosses the failure
    threshold.
    """
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
    # Telemetry section: per-question hit counts across all personas, PASS or FAIL.
    lines.append("### Per-question must_mention coverage")
    lines.append("")
    for r in results:
        for t in r.telemetry:
            lines.append(f"- {r.persona} / {t.question_id}: {t.hits} of {t.total}")
    lines.append("")
    if fail_personas:
        lines.append("### Drift detected")
        lines.append("")
        for r in results:
            for f in r.failures:
                lines.append(r.format_failure(f))
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "FAILURE_CLASS_CONTENT",
    "FAILURE_CLASS_SETUP",
    "DrySmokeSummary",
    "QuestionTelemetry",
    "RotationFailure",
    "RotationResult",
    "TEXT_BLOCK_TRUNCATE_CHARS",
    "dry_run_smoke",
    "iter_repo_fixtures",
    "render_summary_markdown",
    "run_rotation",
]
