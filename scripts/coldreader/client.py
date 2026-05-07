"""Anthropic API client wrapper.

Defines the `RotationCall`/`RotationResponse` shape used by the runner and
the real `AnthropicRotationClient` implementation that calls Claude Haiku
with prompt caching + structured tool-use. Tests use a separate
`FakeAnthropicClient` (in `tests/conftest.py`) implementing the same shape.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from anthropic import Anthropic

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
EXTENDED_THINKING_BUDGET = 4096

_TOOL_NAME = "record_rotation_answer"
_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "description": (
                "Concise answer grounded ONLY in the provided "
                "<inventory_section> and <cross_reference_index> blocks. "
                "Empty string if you cannot answer from those alone."
            ),
        },
        "verbatim_evidence": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "List of verbatim substrings copied EXACTLY from the "
                "provided <inventory_section> or <cross_reference_index> "
                "that ground the answer. Each string MUST appear character-"
                "for-character in the source. Empty list if answer is empty."
            ),
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "low"],
            "description": (
                "'high' if the section + index clearly answer the question; "
                "'low' if the answer required interpretation."
            ),
        },
    },
    "required": ["answer", "verbatim_evidence", "confidence"],
}


@dataclass(frozen=True)
class RotationCall:
    """Inputs to a single model call."""

    persona: str
    question_id: str
    question_text: str
    section_text: str
    index_text: str
    use_extended_thinking: bool = False


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_read_input_tokens=(self.cache_read_input_tokens + other.cache_read_input_tokens),
            cache_creation_input_tokens=(
                self.cache_creation_input_tokens + other.cache_creation_input_tokens
            ),
        )

    @property
    def cache_hit_ratio(self) -> float:
        total_input = self.input_tokens + self.cache_read_input_tokens
        if total_input == 0:
            return 0.0
        return self.cache_read_input_tokens / total_input


@dataclass(frozen=True)
class RotationResponse:
    """Output of a single model call after structured-output extraction."""

    answer: str
    verbatim_evidence: tuple[str, ...]
    confidence: str
    usage: Usage = field(default_factory=Usage)
    used_extended_thinking: bool = False


class RotationClient(Protocol):
    """The minimal interface the runner consumes — implemented by real + fake."""

    def query_rotation(self, call: RotationCall) -> RotationResponse: ...


def load_prompt_template() -> str:
    p = Path(__file__).resolve().parent / "prompts" / "rotation.md"
    return p.read_text(encoding="utf-8")


class AnthropicRotationClient:
    """Real client. Wraps the Anthropic SDK; never logs request/response bodies."""

    def __init__(self, api_key: str | None = None) -> None:
        from anthropic import Anthropic  # imported lazily so dry-run doesn't need it

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. The runner will not start a live "
                "rotation without a key. Use --dry-run for parser/fixture validation."
            )
        self._client: Anthropic = Anthropic(api_key=key)
        self._template = load_prompt_template()

    def _build_system(self) -> str:
        return self._template

    def _build_messages(self, call: RotationCall) -> list[dict[str, Any]]:
        # Two cached blocks: the cross-reference index (reused across all 7
        # personas in a single run) and the persona section (reused across
        # the 3 questions for that persona). Question text is the uncached
        # suffix.
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"<cross_reference_index>\n{call.index_text}\n</cross_reference_index>"
                        ),
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": (
                            f'<inventory_section persona="{call.persona}">\n'
                            f"{call.section_text}\n"
                            "</inventory_section>"
                        ),
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Rotation question (id={call.question_id}): "
                            f"{call.question_text}\n\n"
                            f"Call the {_TOOL_NAME} tool with your answer and "
                            "verbatim_evidence drawn ONLY from the section + "
                            "cross-reference-index blocks above."
                        ),
                    },
                ],
            }
        ]

    def query_rotation(self, call: RotationCall) -> RotationResponse:
        kwargs: dict[str, Any] = {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "temperature": 0,
            "system": self._build_system(),
            "messages": self._build_messages(call),
            "tools": [
                {
                    "name": _TOOL_NAME,
                    "description": ("Record the rotation answer with verbatim evidence."),
                    "input_schema": _TOOL_SCHEMA,
                }
            ],
            "tool_choice": {"type": "tool", "name": _TOOL_NAME},
        }
        if call.use_extended_thinking:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": EXTENDED_THINKING_BUDGET,
            }
        message = self._client.messages.create(**kwargs)

        answer = ""
        evidence: tuple[str, ...] = ()
        confidence = "low"
        for block in message.content:
            if getattr(block, "type", None) == "tool_use" and block.name == _TOOL_NAME:
                payload = block.input
                if isinstance(payload, str):
                    payload = json.loads(payload)
                if isinstance(payload, dict):
                    answer = str(payload.get("answer", ""))
                    raw_ev = payload.get("verbatim_evidence", [])
                    if isinstance(raw_ev, list):
                        evidence = tuple(str(x) for x in raw_ev)
                    confidence = str(payload.get("confidence", "low"))
                break

        u = message.usage
        return RotationResponse(
            answer=answer,
            verbatim_evidence=evidence,
            confidence=confidence,
            usage=Usage(
                input_tokens=getattr(u, "input_tokens", 0),
                output_tokens=getattr(u, "output_tokens", 0),
                cache_read_input_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
                cache_creation_input_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
            ),
            used_extended_thinking=call.use_extended_thinking,
        )
