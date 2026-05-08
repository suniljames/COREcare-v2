"""Anthropic API client wrapper.

Defines the `RotationCall`/`RotationResponse` shape used by the runner and
the real `AnthropicRotationClient` implementation that calls Claude Haiku
with prompt caching + structured tool-use. Tests use a separate
`FakeAnthropicClient` (in `tests/conftest.py`) implementing the same shape.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, Protocol

if TYPE_CHECKING:
    from anthropic import Anthropic

_log = logging.getLogger("coldreader.client")

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
EXTENDED_THINKING_BUDGET = 4096

# Confidence enum — single source of truth for both the tool input schema
# we send to Anthropic AND the runtime guard in the extractor. Issue #203:
# the schema enum and the comparison at runner.py must not drift.
ConfidenceLevel = Literal["high", "low"]
ALLOWED_CONFIDENCE: Final[tuple[ConfidenceLevel, ...]] = ("high", "low")

# Cap the raw malformed value before repr() so a runaway model output
# cannot produce an unbounded warning line. Issue #203 (Security).
_MALFORMED_CONFIDENCE_LOG_MAX = 64

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
            "enum": list(ALLOWED_CONFIDENCE),
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
    """Output of a single model call after structured-output extraction.

    `text_block_content` carries any prose the model emitted in a `text`
    block alongside (or instead of) the structured tool call. Used by the
    runner to detect Pass-B tool refusals and surface them as SETUP errors.

    `was_confidence_malformed` is True when the extractor coerced an
    out-of-enum confidence value to "low" (issue #203). The runner uses
    this flag to keep `RotationResult.malformed_confidence_count` distinct
    from `low_confidence_count` — schema drift and genuine low confidence
    are different drift classes.
    """

    answer: str
    verbatim_evidence: tuple[str, ...]
    confidence: ConfidenceLevel
    usage: Usage = field(default_factory=Usage)
    used_extended_thinking: bool = False
    text_block_content: str = ""
    was_confidence_malformed: bool = False


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
        # Two cached blocks: the cross-reference index (reused across all 6
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
        # Anthropic API rejects `thinking: enabled` combined with a forced
        # `tool_choice: {"type": "tool", ...}` (HTTP 400). On Pass B (extended
        # thinking), drop to `tool_choice: "auto"` and rely on the system
        # prompt's explicit instruction to call the tool. If the model
        # declines, the response has no tool_use block and `answer` stays
        # empty — which the verifier correctly treats as a failure.
        tool_choice: dict[str, Any] = (
            {"type": "auto"} if call.use_extended_thinking else {"type": "tool", "name": _TOOL_NAME}
        )
        # When extended thinking is enabled, max_tokens must be > budget_tokens
        # per the Anthropic API contract; budget tokens are *additional* output.
        max_tokens = (
            MAX_TOKENS + EXTENDED_THINKING_BUDGET if call.use_extended_thinking else MAX_TOKENS
        )
        # Anthropic API forbids temperature != 1 when extended thinking is on.
        temperature = 1 if call.use_extended_thinking else 0
        kwargs: dict[str, Any] = {
            "model": MODEL,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": self._build_system(),
            "messages": self._build_messages(call),
            "tools": [
                {
                    "name": _TOOL_NAME,
                    "description": ("Record the rotation answer with verbatim evidence."),
                    "input_schema": _TOOL_SCHEMA,
                }
            ],
            "tool_choice": tool_choice,
        }
        if call.use_extended_thinking:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": EXTENDED_THINKING_BUDGET,
            }
        message = self._client.messages.create(**kwargs)

        answer = ""
        evidence: tuple[str, ...] = ()
        confidence: ConfidenceLevel = "low"
        was_confidence_malformed = False
        text_block_parts: list[str] = []
        for block in message.content:
            block_type = getattr(block, "type", None)
            if block_type == "tool_use" and block.name == _TOOL_NAME:
                payload = block.input
                if isinstance(payload, str):
                    payload = json.loads(payload)
                if isinstance(payload, dict):
                    answer = str(payload.get("answer", ""))
                    raw_ev = payload.get("verbatim_evidence", [])
                    if isinstance(raw_ev, list):
                        evidence = tuple(str(x) for x in raw_ev)
                    raw_conf = str(payload.get("confidence", "low"))
                    if raw_conf in ALLOWED_CONFIDENCE:
                        # mypy narrows raw_conf to ConfidenceLevel via the membership check.
                        confidence = raw_conf
                    else:
                        # Schema enum is server-validated under nominal operation,
                        # but a model rev or an edge case could slip a non-enum
                        # value past it. Coerce to "low" (defensive default —
                        # malformation is itself a small drift signal) and emit
                        # a distinct warning so the runner can count it separately.
                        # %r escapes CRLF; slice caps log-line length.
                        coerced: ConfidenceLevel = "low"
                        _log.warning(
                            "malformed confidence value: raw=%r coerced=%s",
                            raw_conf[:_MALFORMED_CONFIDENCE_LOG_MAX],
                            coerced,
                        )
                        confidence = coerced
                        was_confidence_malformed = True
            elif block_type == "text":
                text = getattr(block, "text", "")
                if isinstance(text, str) and text.strip():
                    text_block_parts.append(text)

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
            text_block_content="\n".join(text_block_parts),
            was_confidence_malformed=was_confidence_malformed,
        )
