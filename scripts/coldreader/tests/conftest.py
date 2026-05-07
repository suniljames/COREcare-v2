"""Shared test fixtures — primarily the FakeAnthropicClient stub.

Lets L3 model-interaction tests run in CI without `ANTHROPIC_API_KEY`.
Records canned tool-use responses keyed by (persona, question_id).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from client import RotationCall, RotationResponse, Usage


@dataclass
class CannedResponse:
    """A pre-recorded model response for a (persona, question_id) tuple."""

    answer: str
    verbatim_evidence: tuple[str, ...]
    confidence: str = "high"
    used_extended_thinking: bool = False
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    input_tokens: int = 100
    output_tokens: int = 200


class FakeAnthropicClient:
    """Anthropic-shaped client that returns canned responses without network calls."""

    def __init__(self, canned: dict[tuple[str, str], list[CannedResponse]] | None = None) -> None:
        self._canned = canned or {}
        self.calls: list[RotationCall] = []

    def add_response(self, persona: str, question_id: str, response: CannedResponse) -> None:
        key = (persona, question_id)
        self._canned.setdefault(key, []).append(response)

    def query_rotation(self, call: RotationCall) -> RotationResponse:
        self.calls.append(call)
        key = (call.persona, call.question_id)
        queue = self._canned.get(key)
        if not queue:
            raise AssertionError(
                f"FakeAnthropicClient has no canned response for "
                f"persona={call.persona!r} question_id={call.question_id!r} "
                f"(thinking={'on' if call.use_extended_thinking else 'off'})"
            )
        canned = queue.pop(0)
        return RotationResponse(
            answer=canned.answer,
            verbatim_evidence=tuple(canned.verbatim_evidence),
            confidence=canned.confidence,
            usage=Usage(
                input_tokens=canned.input_tokens,
                output_tokens=canned.output_tokens,
                cache_read_input_tokens=canned.cache_read_tokens,
                cache_creation_input_tokens=canned.cache_creation_tokens,
            ),
            used_extended_thinking=canned.used_extended_thinking,
        )


def iter_personas_for_test() -> Iterator[str]:
    """Convenience for parameterized tests that loop the whitelist."""
    from inventory import PERSONAS

    yield from PERSONAS
