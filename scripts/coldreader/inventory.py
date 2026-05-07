"""Section + cross-reference-index extraction for `v1-pages-inventory.md`.

Persona slug ↔ H2 heading mapping is explicit. New personas require both a
fixture file and a whitelist edit — no auto-discovery (per design issue #123,
Data Engineer review item 1).
"""

from __future__ import annotations

from pathlib import Path

PERSONAS: tuple[str, ...] = (
    "agency-admin",
    "super-admin",
    "caregiver",
    "care-manager",
    "client",
    "family-member",
    "shared-routes",
)

_PERSONA_HEADINGS: dict[str, str] = {
    "agency-admin": "## Agency Admin",
    "super-admin": "## Super-Admin",
    "caregiver": "## Caregiver",
    "care-manager": "## Care Manager",
    "client": "## Client",
    "family-member": "## Family Member",
    "shared-routes": "## Shared routes",
}

_INDEX_HEADING = "### Cross-reference index"
_INDEX_PARENT = "## Shared routes"


class PersonaNotInWhitelist(ValueError):
    """Raised when an unknown persona slug is requested."""


class SectionNotFound(ValueError):
    """Raised when the persona's H2 heading is missing from the doc."""


class SectionTooShort(ValueError):
    """Raised when a section's body is shorter than `min_bytes`."""


class IndexNotFound(ValueError):
    """Raised when the cross-reference index subsection is missing."""


def _read(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def extract_section(path: Path, persona: str, *, min_bytes: int) -> str:
    """Return the body of the persona's H2 section, exclusive of the heading line.

    Boundaries: opens at `## <Persona Heading>`, closes at the next `## ` line or EOF.
    `### subsections are part of the body. Raises if the section is missing or
    shorter than `min_bytes`.
    """
    if persona not in _PERSONA_HEADINGS:
        valid = ", ".join(PERSONAS)
        raise PersonaNotInWhitelist(
            f"persona {persona!r} not in whitelist; valid personas: {valid}"
        )

    heading = _PERSONA_HEADINGS[persona]
    lines = _read(path)
    body: list[str] = []
    in_section = False

    for line in lines:
        if not in_section:
            if line.rstrip() == heading:
                in_section = True
            continue
        # in section: stop at next H2
        if line.startswith("## "):
            break
        body.append(line)

    if not in_section:
        raise SectionNotFound(
            f"persona {persona!r} heading {heading!r} not found in {path}"
        )

    body_text = "\n".join(body)
    if len(body_text.encode("utf-8")) < min_bytes:
        raise SectionTooShort(
            f"persona {persona!r} section is "
            f"{len(body_text.encode('utf-8'))} bytes; "
            f"min_section_bytes floor is {min_bytes}. "
            "Refusing to call the API on a stub section."
        )
    return body_text


def extract_index(path: Path) -> str:
    """Return the body of the canonical `### Cross-reference index` subsection.

    Canonical = the index nested under `## Shared routes` (not the narrower
    Super-Admin one). Body excludes the heading line; closes at the next `### `
    or `## ` line, or EOF.
    """
    lines = _read(path)
    in_parent = False
    in_index = False
    body: list[str] = []

    for line in lines:
        stripped = line.rstrip()
        if not in_parent:
            if stripped == _INDEX_PARENT:
                in_parent = True
            continue
        # We're inside the parent H2.
        if not in_index:
            # Another H2 closes the parent before we found the index.
            if line.startswith("## "):
                break
            if stripped == _INDEX_HEADING:
                in_index = True
            continue
        # Inside the index subsection. Close on next H3 or H2.
        if line.startswith("## ") or line.startswith("### "):
            break
        body.append(line)

    if not in_index:
        raise IndexNotFound(
            f"`{_INDEX_HEADING}` subsection not found under `{_INDEX_PARENT}` in {path}"
        )

    return "\n".join(body)
