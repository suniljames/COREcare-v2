"""Validation behavior of the `confidence` enum extractor (issue #203).

The tool's input schema declares `confidence ∈ {"high", "low"}`. The
extractor in `AnthropicRotationClient.query_rotation` defends the runtime
by coercing any out-of-enum value to `"low"` and flagging the response
with `was_confidence_malformed=True` so the runner can count the event
separately from genuine low-confidence passes.

Pins:
  - Coercion: any malformed value becomes `"low"` after extraction.
  - WARNING line: format string + level + repr() escaping of the raw value.
  - Length cap: raw value is sliced to 64 chars before repr() to bound the line.
  - Schema/runtime invariant: schema enum is derived from ALLOWED_CONFIDENCE.
"""

from __future__ import annotations

import logging
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from client import (
    ALLOWED_CONFIDENCE,
    AnthropicRotationClient,
    RotationCall,
)


def _call() -> RotationCall:
    return RotationCall(
        persona="family-member",
        question_id="q1",
        question_text="What does X see?",
        section_text="x" * 100,
        index_text="y" * 100,
        use_extended_thinking=False,
    )


def _stub_message(confidence_value: Any) -> Any:
    """Build a MagicMock Message whose tool_use payload carries the given confidence."""
    block = MagicMock()
    block.type = "tool_use"
    block.name = "record_rotation_answer"
    block.input = {
        "answer": "stub",
        "verbatim_evidence": ["x"],
        "confidence": confidence_value,
    }
    msg = MagicMock()
    msg.content = [block]
    msg.usage = MagicMock(
        input_tokens=10,
        output_tokens=5,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )
    return msg


def _build_client_with_mock_sdk(create_mock: MagicMock) -> AnthropicRotationClient:
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "stub-key"}, clear=False):
        with patch("anthropic.Anthropic") as fake_anthropic:
            fake_instance = MagicMock()
            fake_instance.messages = MagicMock()
            fake_instance.messages.create = create_mock
            fake_anthropic.return_value = fake_instance
            return AnthropicRotationClient()


# --- Case 1: malformation coerces to "low" ---


@pytest.mark.parametrize(
    "raw",
    ["medium", "Low", "low ", "HIGH", "", "true", "null"],
)
def test_malformed_confidence_coerces_to_low(raw: str) -> None:
    create_mock = MagicMock(return_value=_stub_message(raw))
    client = _build_client_with_mock_sdk(create_mock)
    response = client.query_rotation(_call())
    assert response.confidence == "low"
    assert response.was_confidence_malformed is True


def test_valid_high_passes_through_unchanged() -> None:
    create_mock = MagicMock(return_value=_stub_message("high"))
    client = _build_client_with_mock_sdk(create_mock)
    response = client.query_rotation(_call())
    assert response.confidence == "high"
    assert response.was_confidence_malformed is False


def test_valid_low_passes_through_unchanged() -> None:
    create_mock = MagicMock(return_value=_stub_message("low"))
    client = _build_client_with_mock_sdk(create_mock)
    response = client.query_rotation(_call())
    assert response.confidence == "low"
    assert response.was_confidence_malformed is False


# --- Case 2: distinct WARNING line on coercion ---


def test_malformation_emits_warning_line(caplog: pytest.LogCaptureFixture) -> None:
    create_mock = MagicMock(return_value=_stub_message("medium"))
    client = _build_client_with_mock_sdk(create_mock)
    with caplog.at_level(logging.WARNING, logger="coldreader.client"):
        client.query_rotation(_call())
    records = [r for r in caplog.records if r.name == "coldreader.client"]
    assert len(records) == 1
    rec = records[0]
    assert rec.levelno == logging.WARNING
    # Format string surfaces both raw (via %r) and coerced (via %s).
    assert rec.getMessage() == "malformed confidence value: raw='medium' coerced=low"


def test_valid_value_emits_no_warning(caplog: pytest.LogCaptureFixture) -> None:
    create_mock = MagicMock(return_value=_stub_message("high"))
    client = _build_client_with_mock_sdk(create_mock)
    with caplog.at_level(logging.WARNING, logger="coldreader.client"):
        client.query_rotation(_call())
    records = [r for r in caplog.records if r.name == "coldreader.client"]
    assert records == []


# --- Case 3: CRLF and length safety ---


def test_crlf_in_raw_value_is_escaped(caplog: pytest.LogCaptureFixture) -> None:
    """A model emitting CRLF cannot break out of the warning line.

    %r runs repr(), which escapes \\r and \\n into their literal-escape forms.
    The captured record's formatted message must NOT contain a literal newline.
    """
    create_mock = MagicMock(return_value=_stub_message("low\r\nINJECTED"))
    client = _build_client_with_mock_sdk(create_mock)
    with caplog.at_level(logging.WARNING, logger="coldreader.client"):
        client.query_rotation(_call())
    records = [r for r in caplog.records if r.name == "coldreader.client"]
    assert len(records) == 1
    formatted = records[0].getMessage()
    assert "\n" not in formatted
    assert "\r" not in formatted
    # The escaped form should be present.
    assert "\\r\\n" in formatted


def test_long_raw_value_is_truncated_before_repr(caplog: pytest.LogCaptureFixture) -> None:
    """A multi-megabyte malformed value must not produce a multi-megabyte log line."""
    raw = "x" * 200
    create_mock = MagicMock(return_value=_stub_message(raw))
    client = _build_client_with_mock_sdk(create_mock)
    with caplog.at_level(logging.WARNING, logger="coldreader.client"):
        client.query_rotation(_call())
    records = [r for r in caplog.records if r.name == "coldreader.client"]
    assert len(records) == 1
    formatted = records[0].getMessage()
    # 64-char slice + repr quoting + format-string overhead → well under 200 chars.
    # (Concretely ~110 today; the bound exists to catch regressions, not pin exact length.)
    assert len(formatted) < 200
    # The truncated repr should surface 64 x's, not 65.
    assert "x" * 64 in formatted
    assert "x" * 65 not in formatted


# --- Schema/runtime invariant ---


def test_allowed_confidence_constant_drives_schema_enum() -> None:
    """The schema enum must be derived from ALLOWED_CONFIDENCE (single source of truth)."""
    from typing import cast

    from client import _TOOL_SCHEMA

    properties = cast(dict[str, dict[str, Any]], _TOOL_SCHEMA["properties"])
    schema_enum = properties["confidence"]["enum"]
    assert schema_enum == list(ALLOWED_CONFIDENCE)
