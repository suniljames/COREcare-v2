"""L3 — Runner + verifier tests using `FakeAnthropicClient`.

No ANTHROPIC_API_KEY needed. Drives the verbatim-evidence verifier and the
two-pass retry path on synthetic responses.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
import yaml

from client import Usage
from fixtures import Fixture, Question
from runner import (
    RotationFailure,
    RotationResult,
    check_cost_caps,
    render_summary_markdown,
    run_rotation,
)
from tests.conftest import CannedResponse, FakeAnthropicClient


def _fixture(
    persona: str = "family-member",
    questions: tuple[Question, ...] | None = None,
    min_bytes: int = 100,
) -> Fixture:
    return Fixture(
        persona=persona,
        min_section_bytes=min_bytes,
        questions=questions
        or (
            Question(
                id="q1",
                text="What does X see?",
                fact_summary="They see Y on the dashboard.",
                must_mention=(("dashboard",),),
            ),
            Question(
                id="q2",
                text="Can X access Z?",
                fact_summary="No — gated by linked-client only.",
                must_mention=(("linked-client",),),
            ),
            Question(
                id="q3",
                text="Why must v2 handle revoke?",
                fact_summary="No active-flag in v1; soft-revoke needed.",
                must_mention=(("active-flag",), ("soft-revoke",)),
            ),
        ),
        source_path=Path("/tmp/fake.yaml"),
    )


def _section() -> str:
    return (
        "X sees Y on the dashboard, summarized per linked client.\n"
        "Visibility is gated linked-client only via ClientFamilyMember.\n"
        "v1 has no active-flag on the link; soft-revoke is a v2 design need.\n"
    )


def _index() -> str:
    return "Cross-reference index body — pretend this lists shared routes.\n"


# --- happy path: all 3 questions pass, no retry ---


def test_rotation_passes_when_evidence_grounded(tmp_path: Path) -> None:
    fx = _fixture()
    section = _section()
    index = _index()
    client = FakeAnthropicClient()
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="They see Y on the dashboard, per linked client.",
            verbatim_evidence=("X sees Y on the dashboard",),
        ),
    )
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="No, gated linked-client only.",
            verbatim_evidence=("linked-client only via ClientFamilyMember",),
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="v1 has no active-flag; v2 must add soft-revoke.",
            verbatim_evidence=("no active-flag on the link",),
        ),
    )

    result = run_rotation(fx, section=section, index=index, client=client, allow_retry=True)
    assert isinstance(result, RotationResult)
    assert result.passed
    assert len(result.failures) == 0
    assert len(client.calls) == 3
    # No call used extended thinking on a happy path.
    assert all(not c.use_extended_thinking for c in client.calls)


# --- evidence verification ---


def test_rotation_fails_when_verbatim_evidence_not_in_section(tmp_path: Path) -> None:
    fx = _fixture(
        questions=(
            Question(
                id="q1",
                text="?",
                fact_summary="X sees Y.",
                must_mention=(("dashboard",),),
            ),
            Question(
                id="q2",
                text="?",
                fact_summary="Y sees Z.",
                must_mention=(("Z",),),
            ),
            Question(
                id="q3",
                text="?",
                fact_summary="A sees B.",
                must_mention=(("active-flag",),),
            ),
        )
    )
    client = FakeAnthropicClient()
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="They see Y on the dashboard.",
            verbatim_evidence=("X sees Y on the dashboard",),
        ),
    )
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="They see Z.",
            verbatim_evidence=("THIS PHRASE IS NOT IN THE SECTION OR INDEX",),
        ),
    )
    # Pass-B retry on q2 also fails.
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="They see Z.",
            verbatim_evidence=("STILL NOT THERE",),
            used_extended_thinking=True,
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="They see B because v1 has no active-flag on the link.",
            verbatim_evidence=("v1 has no active-flag",),
        ),
    )

    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=True)
    assert not result.passed
    assert len(result.failures) == 1
    f = result.failures[0]
    assert isinstance(f, RotationFailure)
    assert f.question_id == "q2"
    assert "STILL NOT THERE" in f.message or "NOT IN THE SECTION" in f.message


def test_rotation_evidence_can_match_in_either_section_or_index(tmp_path: Path) -> None:
    fx = _fixture()
    client = FakeAnthropicClient()
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="They see Y on the dashboard.",
            verbatim_evidence=("X sees Y on the dashboard",),
        ),
    )
    client.add_response(
        "family-member",
        "q2",
        # Evidence string lives ONLY in the index, not the section.
        CannedResponse(
            answer="Yes, linked-client only via cross-reference index.",
            verbatim_evidence=("Cross-reference index body",),
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="v1 has no active-flag; v2 needs soft-revoke.",
            verbatim_evidence=("no active-flag on the link",),
        ),
    )
    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=False)
    assert result.passed


def test_rotation_fails_when_answer_is_null(tmp_path: Path) -> None:
    fx = _fixture()
    client = FakeAnthropicClient()
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="",  # null answer signals "I cannot answer from the section"
            verbatim_evidence=(),
        ),
    )
    # Retry is also empty.
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="",
            verbatim_evidence=(),
            used_extended_thinking=True,
        ),
    )
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="No, linked-client only.",
            verbatim_evidence=("linked-client only via ClientFamilyMember",),
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="v1 has no active-flag; v2 needs soft-revoke.",
            verbatim_evidence=("no active-flag on the link",),
        ),
    )
    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=True)
    assert not result.passed
    assert any(f.question_id == "q1" for f in result.failures)


# --- two-pass retry behavior ---


def test_rotation_retries_failing_question_with_extended_thinking(
    tmp_path: Path,
) -> None:
    fx = _fixture()
    client = FakeAnthropicClient()
    # q1 first attempt: bad evidence; retry succeeds.
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="They see Y on the dashboard.",
            verbatim_evidence=("nonsense",),
        ),
    )
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="They see Y on the dashboard.",
            verbatim_evidence=("X sees Y on the dashboard",),
            used_extended_thinking=True,
        ),
    )
    # q2/q3 happy.
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="No, linked-client only.",
            verbatim_evidence=("linked-client only via ClientFamilyMember",),
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="v1 has no active-flag; v2 needs soft-revoke.",
            verbatim_evidence=("no active-flag on the link",),
        ),
    )

    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=True)
    assert result.passed, "second-pass retry should rescue q1"
    # The retry call has use_extended_thinking=True
    retry_calls = [c for c in client.calls if c.use_extended_thinking]
    assert len(retry_calls) == 1
    assert retry_calls[0].question_id == "q1"


def test_rotation_skips_retry_when_disabled(tmp_path: Path) -> None:
    """allow_retry=False = single-pass mode (used in dry-run / fast checks)."""
    fx = _fixture()
    client = FakeAnthropicClient()
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="They see Y on the dashboard.",
            verbatim_evidence=("nonsense",),
        ),
    )
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="No, linked-client only.",
            verbatim_evidence=("linked-client only via ClientFamilyMember",),
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="v1 has no active-flag; v2 needs soft-revoke.",
            verbatim_evidence=("no active-flag on the link",),
        ),
    )
    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=False)
    assert not result.passed
    # No retry call recorded
    assert all(not c.use_extended_thinking for c in client.calls)


# --- usage aggregation ---


_KEYWORD_RICH_ANSWERS = {
    "q1": (
        "They see Y on the dashboard, per linked client.",
        "X sees Y on the dashboard",
    ),
    "q2": (
        "No, gated linked-client only.",
        "linked-client only via ClientFamilyMember",
    ),
    "q3": (
        "v1 has no active-flag; v2 needs soft-revoke.",
        "no active-flag on the link",
    ),
}


def test_rotation_aggregates_token_usage(tmp_path: Path) -> None:
    fx = _fixture()
    client = FakeAnthropicClient()
    for qid in ("q1", "q2", "q3"):
        answer, evidence = _KEYWORD_RICH_ANSWERS[qid]
        client.add_response(
            "family-member",
            qid,
            CannedResponse(
                answer=answer,
                verbatim_evidence=(evidence,),
                input_tokens=100,
                output_tokens=200,
                cache_read_tokens=2000,
                cache_creation_tokens=500,
            ),
        )
    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=False)
    assert result.usage.input_tokens == 300
    assert result.usage.output_tokens == 600
    assert result.usage.cache_read_input_tokens == 6000
    assert result.usage.cache_creation_input_tokens == 1500


def test_rotation_cache_hit_ratio_helper() -> None:
    fx = _fixture()
    client = FakeAnthropicClient()
    for qid in ("q1", "q2", "q3"):
        answer, evidence = _KEYWORD_RICH_ANSWERS[qid]
        client.add_response(
            "family-member",
            qid,
            CannedResponse(
                answer=answer,
                verbatim_evidence=(evidence,),
                input_tokens=100,
                cache_read_tokens=900,
            ),
        )
    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=False)
    # 900 cached vs 100 uncached input per call → ratio 0.9
    assert abs(result.usage.cache_hit_ratio - 0.9) < 1e-6


# --- min_section_bytes still enforced before any model call ---


def test_rotation_aborts_before_api_when_section_below_floor(tmp_path: Path) -> None:
    fx = _fixture(min_bytes=10_000)
    short_section = "way too short to be a real section"
    client = FakeAnthropicClient()
    with pytest.raises(ValueError) as exc:
        run_rotation(
            fx,
            section=short_section,
            index=_index(),
            client=client,
            allow_retry=True,
        )
    assert "min_section_bytes" in str(exc.value) or "10000" in str(exc.value)
    # No API call should have been made.
    assert client.calls == []


# --- structured failure rendering for tracking-issue body ---


def test_failure_message_includes_persona_question_text_and_missing_evidence(
    tmp_path: Path,
) -> None:
    fx = _fixture()
    client = FakeAnthropicClient()
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="something",
            verbatim_evidence=("UNFINDABLE_PHRASE_XYZ",),
        ),
    )
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="something",
            verbatim_evidence=("STILL_UNFINDABLE",),
            used_extended_thinking=True,
        ),
    )
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="No, gated linked-client only.",
            verbatim_evidence=("linked-client only via ClientFamilyMember",),
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="v1 has no active-flag; v2 needs soft-revoke.",
            verbatim_evidence=("no active-flag on the link",),
        ),
    )
    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=True)
    assert not result.passed
    f = result.failures[0]
    msg = result.format_failure(f)
    assert "family-member" in msg
    assert "q1" in msg or "What does X see?" in msg
    assert "STILL_UNFINDABLE" in msg


# --- fixture loading from real repo: dry-run smoke (no API call) ---


def test_dry_run_smoke_loads_every_fixture_against_live_inventory(
    tmp_path: Path,
) -> None:
    """Reuses the real repo fixtures + inventory; verifies parser+fixture pair end-to-end."""
    from runner import dry_run_smoke

    # No client passed; dry_run_smoke must not require one.
    summary = dry_run_smoke()
    assert summary.fixtures_loaded == 7
    assert summary.section_bytes_above_floor == 7
    assert summary.errors == []


# --- format_failure with model_answer (Security + QA review) ---


def test_format_failure_includes_model_answer_when_present(tmp_path: Path) -> None:
    """The model's answer surfaces in the rendered failure for triage."""
    from runner import RotationFailure, RotationResult

    failure = RotationFailure(
        persona="agency-admin",
        question_id="q1",
        question_text="What screens does an Agency Admin see for billing?",
        fact_summary="Billing apps...",
        message="answer missing 1 of 5 must_mention entries",
        model_answer="The Agency Admin sees the billing dashboard with invoice management.",
    )
    result = RotationResult(persona="agency-admin", failures=[failure])
    rendered = result.format_failure(failure)
    assert "Model answer:" in rendered
    assert "billing dashboard" in rendered


def test_format_failure_omits_model_answer_block_when_empty(tmp_path: Path) -> None:
    """No `Model answer:` line when the field is empty (default)."""
    from runner import RotationFailure, RotationResult

    failure = RotationFailure(
        persona="agency-admin",
        question_id="q1",
        question_text="?",
        fact_summary="...",
        message="empty evidence string",
        # model_answer defaults to ""
    )
    result = RotationResult(persona="agency-admin", failures=[failure])
    rendered = result.format_failure(failure)
    assert "Model answer:" not in rendered


def test_format_failure_truncates_long_model_answer(tmp_path: Path) -> None:
    """Long model answers are bounded to TEXT_BLOCK_TRUNCATE_CHARS."""
    from runner import TEXT_BLOCK_TRUNCATE_CHARS, RotationFailure, RotationResult

    long_answer = "X" * (TEXT_BLOCK_TRUNCATE_CHARS + 200)
    failure = RotationFailure(
        persona="x",
        question_id="q1",
        question_text="?",
        fact_summary="...",
        message="...",
        model_answer=long_answer,
    )
    result = RotationResult(persona="x", failures=[failure])
    rendered = result.format_failure(failure)
    # The full untruncated tail must NOT appear.
    assert "X" * (TEXT_BLOCK_TRUNCATE_CHARS + 50) not in rendered


def test_format_failure_phi_scrubs_model_answer(tmp_path: Path) -> None:
    """PHI-shaped substrings in `model_answer` are scrubbed before rendering.

    Defense-in-depth: PHI-deny is enforced at fixture load, so this should be
    unreachable in practice. But the rendered output lands in the public
    auto-issue body, so scrub-on-render mirrors the Pass-B text-block path.
    """
    from runner import RotationFailure, RotationResult

    failure = RotationFailure(
        persona="x",
        question_id="q1",
        question_text="?",
        fact_summary="...",
        message="...",
        model_answer="The model would normally cite jane.doe@example.com here.",
    )
    result = RotationResult(persona="x", failures=[failure])
    rendered = result.format_failure(failure)
    assert "jane.doe@example.com" not in rendered
    assert "PHI-REDACTED" in rendered


# --- YAML round-trip sanity ---


def test_fake_client_records_calls_in_order(tmp_path: Path) -> None:
    """Sanity check on the fake — order matters for usage aggregation tests."""
    fx = _fixture()
    client = FakeAnthropicClient()
    for qid in ("q1", "q2", "q3"):
        answer, evidence = _KEYWORD_RICH_ANSWERS[qid]
        client.add_response(
            "family-member",
            qid,
            CannedResponse(answer=answer, verbatim_evidence=(evidence,)),
        )
    run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=False)
    assert [c.question_id for c in client.calls] == ["q1", "q2", "q3"]


# --- tracking-issue body builder ---


def test_render_tracking_issue_body_for_failures(tmp_path: Path) -> None:
    """The runner exposes a helper that renders a markdown-friendly summary."""
    from runner import render_summary_markdown

    fx = _fixture()
    client = FakeAnthropicClient()
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="They see Y on the dashboard.",
            verbatim_evidence=("X sees Y on the dashboard",),
        ),
    )
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(answer="No, gated linked-client only.", verbatim_evidence=("not there",)),
    )
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="No, gated linked-client only.",
            verbatim_evidence=("still not there",),
            used_extended_thinking=True,
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="v1 has no active-flag; v2 needs soft-revoke.",
            verbatim_evidence=("v1 has no active-flag",),
        ),
    )
    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=True)
    md = render_summary_markdown([result], model="claude-haiku-4-5-20251001")
    assert "claude-haiku-4-5-20251001" in md
    assert "FAIL" in md or "fail" in md
    assert "family-member" in md
    assert "q2" in md or "Can X access Z?" in md


# --- Pass-B tool-refusal: empty answer + text block surfaces as SETUP error ---


def test_pass_b_tool_refusal_surfaces_text_block_as_setup_failure(
    tmp_path: Path,
) -> None:
    """When Pass-B returns empty answer + a text block, classify as SETUP error."""
    from runner import FAILURE_CLASS_SETUP

    fx = _fixture()
    client = FakeAnthropicClient()
    # q1 Pass-A: empty answer, no text → CONTENT failure on Pass-A.
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(answer="", verbatim_evidence=()),
    )
    # q1 Pass-B: empty answer + a text block (model declined to call the tool).
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="",
            verbatim_evidence=(),
            used_extended_thinking=True,
            text_block_content="I am not sure I can answer this from the section alone.",
        ),
    )
    # q2/q3 happy.
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="No, gated linked-client only.",
            verbatim_evidence=("linked-client only via ClientFamilyMember",),
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="v1 has no active-flag; v2 needs soft-revoke.",
            verbatim_evidence=("no active-flag on the link",),
        ),
    )

    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=True)
    assert not result.passed
    assert result.has_setup_error
    f = result.failures[0]
    assert f.failure_class == FAILURE_CLASS_SETUP
    assert "declined to call" in f.message.lower() or "tool" in f.message.lower()
    assert "I am not sure" in f.message


def test_text_block_content_truncated_in_failure_message(tmp_path: Path) -> None:
    """Long text-block content is truncated to bound the auto-issue body."""
    from runner import TEXT_BLOCK_TRUNCATE_CHARS

    fx = _fixture()
    long_text = "X" * (TEXT_BLOCK_TRUNCATE_CHARS + 200)
    client = FakeAnthropicClient()
    client.add_response("family-member", "q1", CannedResponse(answer="", verbatim_evidence=()))
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="",
            verbatim_evidence=(),
            used_extended_thinking=True,
            text_block_content=long_text,
        ),
    )
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="No, gated linked-client only.",
            verbatim_evidence=("linked-client only via ClientFamilyMember",),
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="v1 has no active-flag; v2 needs soft-revoke.",
            verbatim_evidence=("no active-flag on the link",),
        ),
    )

    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=True)
    f = result.failures[0]
    # Truncated to bound; no full-length echo.
    assert "X" * (TEXT_BLOCK_TRUNCATE_CHARS + 50) not in f.message


def test_text_block_phi_scrubbed_in_failure_message(tmp_path: Path) -> None:
    """PHI-shaped strings in text-block content are scrubbed before logging."""
    fx = _fixture()
    client = FakeAnthropicClient()
    client.add_response("family-member", "q1", CannedResponse(answer="", verbatim_evidence=()))
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="",
            verbatim_evidence=(),
            used_extended_thinking=True,
            text_block_content=("I would normally cite jane.doe@example.com but cannot here."),
        ),
    )
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="No, gated linked-client only.",
            verbatim_evidence=("linked-client only via ClientFamilyMember",),
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="v1 has no active-flag; v2 needs soft-revoke.",
            verbatim_evidence=("no active-flag on the link",),
        ),
    )

    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=True)
    f = result.failures[0]
    assert "jane.doe@example.com" not in f.message
    assert "PHI-REDACTED" in f.message


# --- per-question hit-count telemetry rendered in summary markdown ---


def test_render_summary_includes_per_question_hit_counts(tmp_path: Path) -> None:
    """Step summary must show hit counts on every question, PASS or FAIL."""
    from runner import render_summary_markdown

    fx = _fixture()
    client = FakeAnthropicClient()
    for qid in ("q1", "q2", "q3"):
        answer, evidence = _KEYWORD_RICH_ANSWERS[qid]
        client.add_response(
            "family-member",
            qid,
            CannedResponse(answer=answer, verbatim_evidence=(evidence,)),
        )
    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=False)
    md = render_summary_markdown([result], model="claude-haiku-4-5-20251001")
    # Each question line shows N of M hit counts.
    assert "q1: 1 of 1" in md
    assert "q2: 1 of 1" in md
    # q3 has must_mention=(("active-flag",), ("soft-revoke",)) — answer contains both.
    assert "q3: 2 of 2" in md


def test_rotation_records_telemetry_for_passing_questions(tmp_path: Path) -> None:
    """Telemetry list is populated for PASS questions, not just failures."""
    fx = _fixture()
    client = FakeAnthropicClient()
    for qid in ("q1", "q2", "q3"):
        answer, evidence = _KEYWORD_RICH_ANSWERS[qid]
        client.add_response(
            "family-member",
            qid,
            CannedResponse(answer=answer, verbatim_evidence=(evidence,)),
        )
    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=False)
    assert result.passed
    assert len(result.telemetry) == 3
    # All entries report the actual N-of-M, regardless of pass status.
    assert all(t.total >= 1 for t in result.telemetry)


# --- prevent stale yaml from confusing tests ---


def test_yaml_round_trip_smoke(tmp_path: Path) -> None:
    body = {
        "persona": "family-member",
        "min_section_bytes": 1500,
        "questions": [
            {
                "id": f"q{i}",
                "text": f"q{i}?",
                "fact_summary": f"fact{i}",
                "must_mention": [["alpha"]],
            }
            for i in range(1, 4)
        ],
    }
    p = tmp_path / "family-member.yaml"
    p.write_text(yaml.safe_dump(body), encoding="utf-8")
    assert yaml.safe_load(p.read_text(encoding="utf-8"))["persona"] == "family-member"


# --- NIT 1 (issue #142): low-confidence telemetry ---


def _all_three_pass_with_confidence(
    client: FakeAnthropicClient, *, q1: str, q2: str, q3: str
) -> None:
    """Queue 3 canned answers that satisfy the default fixture's must_mention.

    Confidence values per question come from the kwargs.
    """
    payloads = {
        "q1": (
            "They see Y on the dashboard, per linked client.",
            "X sees Y on the dashboard",
        ),
        "q2": (
            "No, gated linked-client only.",
            "linked-client only via ClientFamilyMember",
        ),
        "q3": (
            "v1 has no active-flag; v2 needs soft-revoke.",
            "no active-flag on the link",
        ),
    }
    for qid, conf in (("q1", q1), ("q2", q2), ("q3", q3)):
        ans, ev = payloads[qid]
        client.add_response(
            "family-member",
            qid,
            CannedResponse(answer=ans, verbatim_evidence=(ev,), confidence=conf),
        )


def test_low_confidence_pass_emits_warning_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fx = _fixture()
    client = FakeAnthropicClient()
    _all_three_pass_with_confidence(client, q1="high", q2="low", q3="high")

    with caplog.at_level(logging.WARNING, logger="coldreader"):
        result = run_rotation(
            fx, section=_section(), index=_index(), client=client, allow_retry=True
        )

    assert result.passed
    assert result.failures == []
    assert result.low_confidence_count == 1

    warnings = [
        r for r in caplog.records if r.name == "coldreader" and r.levelno == logging.WARNING
    ]
    assert len(warnings) == 1
    msg = warnings[0].getMessage()
    assert "family-member" in msg
    assert "q2" in msg
    assert "low" in msg.lower()
    # Security MUST-FIX (#142): never log answer/evidence text.
    assert "linked-client only via ClientFamilyMember" not in msg
    assert "No, gated linked-client only" not in msg


def test_high_confidence_pass_emits_no_warning_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fx = _fixture()
    client = FakeAnthropicClient()
    _all_three_pass_with_confidence(client, q1="high", q2="high", q3="high")

    with caplog.at_level(logging.WARNING, logger="coldreader"):
        result = run_rotation(
            fx, section=_section(), index=_index(), client=client, allow_retry=True
        )

    assert result.passed
    assert result.low_confidence_count == 0
    warnings = [
        r for r in caplog.records if r.name == "coldreader" and r.levelno == logging.WARNING
    ]
    assert warnings == []


def test_low_confidence_failure_does_not_double_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failing question with confidence='low' must NOT emit the warning.

    The warning is for *passing* low-confidence answers — a failure already
    speaks for itself via the failure path, no need to double-log.
    """
    fx = _fixture()
    client = FakeAnthropicClient()
    # q1 fails Pass A on evidence, retries on Pass B (still bad), confidence=low.
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="They see Y on the dashboard.",
            verbatim_evidence=("UNFINDABLE_PHRASE_A",),
            confidence="low",
        ),
    )
    client.add_response(
        "family-member",
        "q1",
        CannedResponse(
            answer="They see Y on the dashboard.",
            verbatim_evidence=("UNFINDABLE_PHRASE_B",),
            confidence="low",
            used_extended_thinking=True,
        ),
    )
    # q2/q3 pass with confidence=high.
    client.add_response(
        "family-member",
        "q2",
        CannedResponse(
            answer="No, gated linked-client only.",
            verbatim_evidence=("linked-client only via ClientFamilyMember",),
            confidence="high",
        ),
    )
    client.add_response(
        "family-member",
        "q3",
        CannedResponse(
            answer="v1 has no active-flag; v2 needs soft-revoke.",
            verbatim_evidence=("no active-flag on the link",),
            confidence="high",
        ),
    )

    with caplog.at_level(logging.WARNING, logger="coldreader"):
        result = run_rotation(
            fx, section=_section(), index=_index(), client=client, allow_retry=True
        )

    assert not result.passed
    assert result.low_confidence_count == 0
    warnings = [
        r for r in caplog.records if r.name == "coldreader" and r.levelno == logging.WARNING
    ]
    assert warnings == []


def test_render_summary_includes_low_confidence_count_when_nonzero() -> None:
    fx = _fixture()
    client = FakeAnthropicClient()
    _all_three_pass_with_confidence(client, q1="low", q2="low", q3="high")
    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=False)
    md = render_summary_markdown([result], model="claude-haiku-4-5-20251001")
    assert "Low-confidence passes: 2" in md


def test_render_summary_omits_low_confidence_line_when_zero() -> None:
    fx = _fixture()
    client = FakeAnthropicClient()
    _all_three_pass_with_confidence(client, q1="high", q2="high", q3="high")
    result = run_rotation(fx, section=_section(), index=_index(), client=client, allow_retry=False)
    md = render_summary_markdown([result], model="claude-haiku-4-5-20251001")
    assert "Low-confidence" not in md


# --- NIT 2 (issue #142): cost-cap helper testability ---


def test_check_cost_caps_returns_none_when_under_caps() -> None:
    assert (
        check_cost_caps(
            Usage(input_tokens=100, output_tokens=200),
            input_cap=200_000,
            output_cap=30_000,
        )
        is None
    )


def test_check_cost_caps_trips_on_input_overage() -> None:
    reason = check_cost_caps(
        Usage(input_tokens=300_000, output_tokens=200),
        input_cap=200_000,
        output_cap=30_000,
    )
    assert reason is not None
    assert "input" in reason.lower()
    assert "300000" in reason or "300,000" in reason


def test_check_cost_caps_trips_on_output_overage() -> None:
    reason = check_cost_caps(
        Usage(input_tokens=100, output_tokens=50_000),
        input_cap=200_000,
        output_cap=30_000,
    )
    assert reason is not None
    assert "output" in reason.lower()


def test_check_cost_caps_input_takes_precedence_when_both_trip() -> None:
    """Deterministic ordering: input-trip beats output-trip for log clarity."""
    reason = check_cost_caps(
        Usage(input_tokens=300_000, output_tokens=50_000),
        input_cap=200_000,
        output_cap=30_000,
    )
    assert reason is not None
    assert "input" in reason.lower()
    assert "output" not in reason.lower()


def test_check_cost_caps_at_boundary_does_not_trip() -> None:
    """Exactly at the cap is acceptable; only > cap trips."""
    assert (
        check_cost_caps(
            Usage(input_tokens=200_000, output_tokens=30_000),
            input_cap=200_000,
            output_cap=30_000,
        )
        is None
    )
