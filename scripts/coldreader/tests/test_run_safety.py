"""Test that run.py's top-level safety net distinguishes setup errors from drift.

Surfaced by the first live workflow run on 2026-05-07: an Anthropic API
crash propagated as an unhandled exception, exiting Python with code 1 —
the same code as `EXIT_DRIFT`. The workflow's tracking-issue step couldn't
distinguish the two and opened a false drift report.
"""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

import run
from run import EXIT_DRIFT, EXIT_PASS, EXIT_SETUP_ERROR, _main_safe


def test_main_safe_returns_main_exit_code_when_main_returns_normally() -> None:
    with patch.object(run, "main", return_value=EXIT_PASS):
        assert _main_safe() == EXIT_PASS


def test_main_safe_returns_drift_when_main_returns_drift() -> None:
    with patch.object(run, "main", return_value=EXIT_DRIFT):
        assert _main_safe() == EXIT_DRIFT


def test_main_safe_converts_unhandled_exception_to_setup_error() -> None:
    """Un-anticipated crashes (network, API 4xx, runner bugs) must NOT exit 1."""
    with patch.object(run, "main", side_effect=RuntimeError("boom")):
        assert _main_safe() == EXIT_SETUP_ERROR


def test_main_safe_propagates_systemexit() -> None:
    """argparse calls sys.exit() — that should propagate, not be swallowed."""
    with patch.object(run, "main", side_effect=SystemExit(0)):
        with pytest.raises(SystemExit):
            _main_safe()


def test_main_safe_treats_anthropic_error_as_setup_error() -> None:
    """Specific regression: the original BadRequestError that surfaced live."""

    class _FakeBadRequestError(Exception):
        """Stand-in for anthropic.BadRequestError — same exit-path semantics."""

    with patch.object(
        run, "main", side_effect=_FakeBadRequestError("400 invalid_request_error")
    ):
        assert _main_safe() == EXIT_SETUP_ERROR


# --- NIT 2 (issue #142): cost-cap trip end-to-end binding ---


def test_main_returns_setup_error_when_runner_token_counts_exceed_input_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end: a runaway run that blows the input cap exits 2, not 1.

    Critical: EXIT_DRIFT (1) opens a tracking issue; EXIT_SETUP_ERROR (2)
    surfaces a setup-error message instead. Misclassifying a cost-cap trip
    as drift would file false drift issues. Pins the exit-code contract.
    """
    from client import RotationCall, RotationResponse, Usage
    from inventory import PERSONAS

    class _RunawayClient:
        def query_rotation(self, call: RotationCall) -> RotationResponse:
            # The answer + verbatim_evidence values are intentionally orthogonal to the
            # real fixture's must_mention list. This test exercises the cost-cap-trip
            # exit-code path (run.py:159-166) which short-circuits before scoring, so
            # answer/evidence correctness is irrelevant to the contract. Do NOT "fix"
            # them to match a real fixture — the test would still pass, but a future
            # reader might mistakenly believe must_mention satisfaction matters here.
            return RotationResponse(
                answer="dashboard linked-client active-flag soft-revoke",
                # Generic phrase present in every persona's section.
                verbatim_evidence=("Family Member",),
                confidence="high",
                usage=Usage(input_tokens=300_000, output_tokens=100),
            )

    monkeypatch.setattr(run, "AnthropicRotationClient", lambda: _RunawayClient())
    monkeypatch.setattr(sys, "argv", ["run.py", "--persona", PERSONAS[0]])

    rc = run.main()
    assert rc == EXIT_SETUP_ERROR, (
        f"runaway input tokens must exit EXIT_SETUP_ERROR (2); got {rc}. "
        f"If 1, the workflow would misclassify it as drift."
    )


def test_main_returns_setup_error_when_runner_token_counts_exceed_output_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Symmetric to the input case — output overage path is also covered."""
    from client import RotationCall, RotationResponse, Usage
    from inventory import PERSONAS

    class _OutputRunawayClient:
        def query_rotation(self, call: RotationCall) -> RotationResponse:
            # The answer + verbatim_evidence values are intentionally orthogonal to the
            # real fixture's must_mention list. This test exercises the cost-cap-trip
            # exit-code path (run.py:159-166) which short-circuits before scoring, so
            # answer/evidence correctness is irrelevant to the contract. Do NOT "fix"
            # them to match a real fixture — the test would still pass, but a future
            # reader might mistakenly believe must_mention satisfaction matters here.
            return RotationResponse(
                answer="dashboard linked-client active-flag soft-revoke",
                verbatim_evidence=("Family Member",),
                confidence="high",
                usage=Usage(input_tokens=100, output_tokens=50_000),
            )

    monkeypatch.setattr(run, "AnthropicRotationClient", lambda: _OutputRunawayClient())
    monkeypatch.setattr(sys, "argv", ["run.py", "--persona", PERSONAS[0]])

    rc = run.main()
    assert rc == EXIT_SETUP_ERROR
