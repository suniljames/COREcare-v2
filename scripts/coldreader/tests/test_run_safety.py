"""Test that run.py's top-level safety net distinguishes setup errors from drift.

Surfaced by the first live workflow run on 2026-05-07: an Anthropic API
crash propagated as an unhandled exception, exiting Python with code 1 —
the same code as `EXIT_DRIFT`. The workflow's tracking-issue step couldn't
distinguish the two and opened a false drift report.
"""

from __future__ import annotations

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

    with patch.object(run, "main", side_effect=_FakeBadRequestError("400 invalid_request_error")):
        assert _main_safe() == EXIT_SETUP_ERROR
