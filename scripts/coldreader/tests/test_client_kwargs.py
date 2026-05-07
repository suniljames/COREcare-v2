"""Test that AnthropicRotationClient builds API kwargs that don't violate
Anthropic's API contract on the Pass-B (extended-thinking) path.

Surfaced by the first live workflow run on 2026-05-07: the original
implementation combined `tool_choice: {"type": "tool", ...}` (forced),
`temperature: 0`, and `max_tokens=1024` with `thinking: {budget_tokens=4096}`
— Anthropic API rejects each of those combinations with HTTP 400.

These tests intercept the SDK call and inspect the kwargs without making
any network request.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock, patch

from client import (
    EXTENDED_THINKING_BUDGET,
    MAX_TOKENS,
    AnthropicRotationClient,
    RotationCall,
    Usage,
)


def _call(use_extended_thinking: bool) -> RotationCall:
    return RotationCall(
        persona="family-member",
        question_id="q1",
        question_text="What does X see?",
        section_text="x" * 100,
        index_text="y" * 100,
        use_extended_thinking=use_extended_thinking,
    )


def _stub_message(input_tokens: int = 100, output_tokens: int = 50) -> Any:
    """A minimal stand-in for the SDK's Message return value."""
    block = MagicMock()
    block.type = "tool_use"
    block.name = "record_rotation_answer"
    block.input = {
        "answer": "stub",
        "verbatim_evidence": ["x"],
        "confidence": "high",
    }
    msg = MagicMock()
    msg.content = [block]
    msg.usage = MagicMock(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )
    return msg


def _build_client_with_mock_sdk(create_mock: MagicMock) -> AnthropicRotationClient:
    """Construct a client whose underlying SDK is a mock — no network."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "stub-key"}, clear=False):
        # Patch anthropic.Anthropic at the *resolved* module path inside client.py
        with patch("anthropic.Anthropic") as fake_anthropic:
            fake_instance = MagicMock()
            fake_instance.messages = MagicMock()
            fake_instance.messages.create = create_mock
            fake_anthropic.return_value = fake_instance
            return AnthropicRotationClient()


def test_pass_a_uses_forced_tool_choice_and_temp_zero() -> None:
    create_mock = MagicMock(return_value=_stub_message())
    client = _build_client_with_mock_sdk(create_mock)
    client.query_rotation(_call(use_extended_thinking=False))

    kwargs = create_mock.call_args.kwargs
    assert kwargs["tool_choice"] == {"type": "tool", "name": "record_rotation_answer"}
    assert kwargs["temperature"] == 0
    assert kwargs["max_tokens"] == MAX_TOKENS
    assert "thinking" not in kwargs


def test_pass_b_uses_auto_tool_choice_and_temp_one() -> None:
    """Anthropic API rejects forced tool_choice + thinking combo. Pass B must use auto."""
    create_mock = MagicMock(return_value=_stub_message())
    client = _build_client_with_mock_sdk(create_mock)
    client.query_rotation(_call(use_extended_thinking=True))

    kwargs = create_mock.call_args.kwargs
    assert kwargs["tool_choice"] == {"type": "auto"}, (
        "Pass B must NOT force tool_choice when extended thinking is enabled — "
        "Anthropic API returns 400 invalid_request_error otherwise"
    )
    assert kwargs["temperature"] == 1, (
        "Pass B must use temperature=1 when extended thinking is enabled — "
        "Anthropic API requires it"
    )


def test_pass_b_max_tokens_exceeds_thinking_budget() -> None:
    """API contract: max_tokens must be > thinking.budget_tokens."""
    create_mock = MagicMock(return_value=_stub_message())
    client = _build_client_with_mock_sdk(create_mock)
    client.query_rotation(_call(use_extended_thinking=True))

    kwargs = create_mock.call_args.kwargs
    assert kwargs["thinking"] == {
        "type": "enabled",
        "budget_tokens": EXTENDED_THINKING_BUDGET,
    }
    assert kwargs["max_tokens"] > EXTENDED_THINKING_BUDGET
    assert kwargs["max_tokens"] == MAX_TOKENS + EXTENDED_THINKING_BUDGET


def test_pass_a_and_pass_b_produce_distinct_kwargs() -> None:
    """Sanity: the two passes really do build different kwargs."""
    create_mock = MagicMock(side_effect=[_stub_message(), _stub_message()])
    client = _build_client_with_mock_sdk(create_mock)
    client.query_rotation(_call(use_extended_thinking=False))
    client.query_rotation(_call(use_extended_thinking=True))

    pass_a_kwargs = create_mock.call_args_list[0].kwargs
    pass_b_kwargs = create_mock.call_args_list[1].kwargs
    assert pass_a_kwargs["tool_choice"] != pass_b_kwargs["tool_choice"]
    assert pass_a_kwargs["temperature"] != pass_b_kwargs["temperature"]
    assert pass_a_kwargs["max_tokens"] < pass_b_kwargs["max_tokens"]


def test_usage_returned_without_thinking_blocks() -> None:
    """When the model declines to call the tool on Pass B, answer/evidence stay empty.

    The verifier upstream treats that as a fail — which is the correct outcome
    (we'd rather a Pass-B that 'didn't engage' fail than fabricate).
    """
    text_only_block = MagicMock()
    text_only_block.type = "text"
    text_only_block.name = ""
    msg = MagicMock()
    msg.content = [text_only_block]
    msg.usage = MagicMock(
        input_tokens=10,
        output_tokens=5,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )
    create_mock = MagicMock(return_value=msg)
    client = _build_client_with_mock_sdk(create_mock)
    response = client.query_rotation(_call(use_extended_thinking=True))
    assert response.answer == ""
    assert response.verbatim_evidence == ()
    # Usage is still recorded even when the model didn't call the tool.
    assert isinstance(response.usage, Usage)
    assert response.usage.input_tokens == 10
