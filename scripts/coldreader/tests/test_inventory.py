"""L1 — Parser unit tests for `inventory.py`.

Covers section + index extraction, persona whitelist, min_section_bytes floor.
No fixtures-on-disk, no API key, no network.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from inventory import (
    PERSONAS,
    IndexNotFound,
    PersonaNotInWhitelist,
    SectionNotFound,
    SectionTooShort,
    extract_index,
    extract_section,
)


def _write_inventory(tmp_path: Path, contents: str) -> Path:
    p = tmp_path / "inventory.md"
    p.write_text(contents, encoding="utf-8")
    return p


# --- whitelist ---


def test_persona_whitelist_is_exactly_six() -> None:
    assert PERSONAS == (
        "agency-admin",
        "caregiver",
        "care-manager",
        "client",
        "family-member",
        "shared-routes",
    )


def test_extract_section_unknown_persona_raises_persona_not_in_whitelist(
    tmp_path: Path,
) -> None:
    md = _write_inventory(tmp_path, "## Family Member\nbody\n")
    with pytest.raises(PersonaNotInWhitelist) as exc:
        extract_section(md, "foobar-persona", min_bytes=0)
    assert "foobar-persona" in str(exc.value)
    # Lists every valid persona — no fuzzy match.
    for p in PERSONAS:
        assert p in str(exc.value)


# --- extract_section: heading boundaries ---


def test_extract_section_returns_body_excluding_heading_line(tmp_path: Path) -> None:
    md = _write_inventory(
        tmp_path,
        "## Family Member\n"
        "intro paragraph here\n\n"
        "### subheading is part of body\n"
        "more body content\n"
        "## Shared routes\n"
        "this is the next section, must be excluded\n",
    )
    section = extract_section(md, "family-member", min_bytes=0)
    assert "## Family Member" not in section  # heading line excluded
    assert "intro paragraph here" in section
    assert "### subheading is part of body" in section  # ### kept
    assert "more body content" in section
    assert "Shared routes" not in section  # next ## is the boundary


def test_extract_section_handles_persona_at_eof(tmp_path: Path) -> None:
    md = _write_inventory(
        tmp_path,
        "## Caregiver\nlast section, no trailing heading\n",
    )
    section = extract_section(md, "caregiver", min_bytes=0)
    assert "last section, no trailing heading" in section


def test_extract_section_two_word_personas_match(tmp_path: Path) -> None:
    md = _write_inventory(
        tmp_path,
        "## Care Manager\nbody\n## Family Member\nbody2\n",
    )
    a = extract_section(md, "care-manager", min_bytes=0)
    b = extract_section(md, "family-member", min_bytes=0)
    assert "body" in a and "body2" not in a
    assert "body2" in b and "body" not in b.replace("body2", "")


def test_extract_section_shared_routes_matches_lowercase_word(tmp_path: Path) -> None:
    md = _write_inventory(
        tmp_path,
        "## Shared routes\nshared body\n## Anything\nnope\n",
    )
    section = extract_section(md, "shared-routes", min_bytes=0)
    assert "shared body" in section


def test_extract_section_missing_heading_raises_section_not_found(
    tmp_path: Path,
) -> None:
    md = _write_inventory(
        tmp_path,
        "## Agency Admin\nonly section\n",
    )
    with pytest.raises(SectionNotFound) as exc:
        extract_section(md, "family-member", min_bytes=0)
    assert "family-member" in str(exc.value)


def test_extract_section_treats_inner_h3_as_body_not_boundary(tmp_path: Path) -> None:
    """Section spans across multiple H3 subsections within one persona."""
    md = _write_inventory(
        tmp_path,
        "## Agency Admin\n"
        "### app one\nrows\n"
        "### app two\nmore rows\n"
        "### app three\nfinal rows\n"
        "## Care Manager\nnext section\n",
    )
    section = extract_section(md, "agency-admin", min_bytes=0)
    assert "### app one" in section
    assert "### app three" in section
    assert "final rows" in section
    assert "next section" not in section


# --- extract_section: min_section_bytes floor ---


def test_extract_section_below_min_bytes_raises_section_too_short(
    tmp_path: Path,
) -> None:
    md = _write_inventory(
        tmp_path,
        "## Family Member\ntiny\n",
    )
    with pytest.raises(SectionTooShort) as exc:
        extract_section(md, "family-member", min_bytes=4000)
    msg = str(exc.value)
    assert "family-member" in msg
    # Mentions actual byte count and the floor — author needs both to debug.
    assert "4000" in msg


def test_extract_section_at_or_above_min_bytes_passes(tmp_path: Path) -> None:
    body = "x" * 4500
    md = _write_inventory(
        tmp_path,
        f"## Family Member\n{body}\n",
    )
    section = extract_section(md, "family-member", min_bytes=4000)
    assert len(section) >= 4000


# --- extract_index ---


def test_extract_index_returns_subsection_under_shared_routes_by_default(
    tmp_path: Path,
) -> None:
    """The canonical cross-ref index lives under ## Shared routes — used in rotations."""
    md = _write_inventory(
        tmp_path,
        "## Care Manager\n"
        "### Cross-reference index\ncare-manager-scoped index, not the canonical one\n"
        "## Shared routes\n"
        "### Cross-reference index\n"
        "Routes whose canonical row lives in a persona section.\n"
        "| route | primary persona |\n"
        "| /foo/ | Caregiver |\n"
        "### Routes authored here (no primary-persona section)\n"
        "this comes after the index\n",
    )
    index = extract_index(md)
    assert "Routes whose canonical row lives in a persona section." in index
    assert "/foo/" in index
    assert "this comes after the index" not in index
    assert "care-manager-scoped index, not the canonical one" not in index


def test_extract_index_missing_raises_index_not_found(tmp_path: Path) -> None:
    md = _write_inventory(
        tmp_path,
        "## Shared routes\n"
        "no index subsection here\n"
        "### Routes authored here (no primary-persona section)\n"
        "rows only\n",
    )
    with pytest.raises(IndexNotFound):
        extract_index(md)


def test_extract_index_handles_index_at_eof(tmp_path: Path) -> None:
    md = _write_inventory(
        tmp_path,
        "## Shared routes\n### Cross-reference index\ntrailing index, no following ### or ##\n",
    )
    index = extract_index(md)
    assert "trailing index" in index


def test_extract_index_stops_at_next_h2(tmp_path: Path) -> None:
    md = _write_inventory(
        tmp_path,
        "## Shared routes\n"
        "### Cross-reference index\nindex body\n"
        "## Next H2 Section\nshould not be included\n",
    )
    index = extract_index(md)
    assert "index body" in index
    assert "Next H2 Section" not in index


# --- live inventory smoke (real file from repo) ---


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        if (ancestor / "docs" / "migration" / "v1-pages-inventory.md").exists():
            return ancestor
    raise RuntimeError("Could not locate repo root from test file location")


def test_live_inventory_extract_each_persona_section() -> None:
    """Every whitelisted persona has a section in the actual repo doc."""
    inv = _repo_root() / "docs" / "migration" / "v1-pages-inventory.md"
    for persona in PERSONAS:
        section = extract_section(inv, persona, min_bytes=0)
        assert section, f"empty section for {persona}"


def test_live_inventory_extract_cross_reference_index() -> None:
    inv = _repo_root() / "docs" / "migration" / "v1-pages-inventory.md"
    index = extract_index(inv)
    assert "Routes whose canonical row lives in a persona section." in index
