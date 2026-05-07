"""L2 — Fixture validation tests for `fixtures.py`.

Schema validation, PHI-shape regex deny, real-fixture pairing with the live
inventory doc.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from fixtures import (
    PHI_DENY_PATTERNS,
    Fixture,
    FixtureSchemaError,
    PHIInFixtureError,
    iter_repo_fixtures,
    load_fixture,
)
from inventory import PERSONAS, extract_section


def _write_fixture(tmp_path: Path, name: str, body: dict) -> Path:
    p = tmp_path / f"{name}.yaml"
    p.write_text(yaml.safe_dump(body), encoding="utf-8")
    return p


def _well_formed_body(persona: str = "family-member") -> dict:
    return {
        "persona": persona,
        "min_section_bytes": 1000,
        "questions": [
            {
                "id": "q1",
                "text": "Q1 text?",
                "expected_fact_summary": "Some fact.",
            },
            {
                "id": "q2",
                "text": "Q2 text?",
                "expected_fact_summary": "Another fact.",
            },
            {
                "id": "q3",
                "text": "Q3 text?",
                "expected_fact_summary": "Third fact.",
            },
        ],
    }


# --- happy path ---


def test_load_fixture_returns_typed_object(tmp_path: Path) -> None:
    body = _well_formed_body()
    path = _write_fixture(tmp_path, "family-member", body)
    fx = load_fixture(path)
    assert isinstance(fx, Fixture)
    assert fx.persona == "family-member"
    assert fx.min_section_bytes == 1000
    assert len(fx.questions) == 3
    assert fx.questions[0].id == "q1"
    assert fx.questions[0].text == "Q1 text?"
    assert fx.questions[0].expected_fact_summary == "Some fact."


# --- schema violations ---


def test_load_fixture_persona_not_in_whitelist(tmp_path: Path) -> None:
    body = _well_formed_body(persona="something-else")
    path = _write_fixture(tmp_path, "something-else", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "something-else" in str(exc.value)


def test_load_fixture_with_two_questions_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"] = body["questions"][:2]
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert (
        "exactly 3" in str(exc.value).lower() or "3 questions" in str(exc.value).lower()
    )


def test_load_fixture_with_four_questions_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"].append(
        {"id": "q4", "text": "extra?", "expected_fact_summary": "x"}
    )
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError):
        load_fixture(path)


def test_load_fixture_question_missing_expected_fact_summary(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][1]["expected_fact_summary"] = ""
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "expected_fact_summary" in str(exc.value)


def test_load_fixture_min_bytes_below_floor_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["min_section_bytes"] = 500
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "min_section_bytes" in str(exc.value)


def test_load_fixture_question_id_collision_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][1]["id"] = "q1"  # duplicate
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "duplicate" in str(exc.value).lower() or "unique" in str(exc.value).lower()


def test_load_fixture_filename_must_match_persona(tmp_path: Path) -> None:
    """Disk filename must equal persona slug — prevents copy-paste mismatches."""
    body = _well_formed_body(persona="family-member")
    path = _write_fixture(tmp_path, "agency-admin", body)  # mismatch
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "filename" in str(exc.value).lower()


# --- PHI deny ---


def test_load_fixture_with_email_phi_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["expected_fact_summary"] = "Contact: john.doe@example.com"
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(PHIInFixtureError) as exc:
        load_fixture(path)
    assert "email" in str(exc.value).lower()


def test_load_fixture_with_ssn_phi_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["text"] = "Patient SSN 123-45-6789?"
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(PHIInFixtureError) as exc:
        load_fixture(path)
    assert "ssn" in str(exc.value).lower()


def test_load_fixture_with_dob_phi_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["expected_fact_summary"] = "DOB 03/15/1956 visible to family"
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(PHIInFixtureError) as exc:
        load_fixture(path)
    assert "dob" in str(exc.value).lower()


def test_phi_placeholder_tokens_are_not_phi(tmp_path: Path) -> None:
    """`[CLIENT_NAME]`, `<FAMILY_MEMBER>` etc. are placeholders, not real PHI."""
    body = _well_formed_body()
    body["questions"][0][
        "expected_fact_summary"
    ] = "Family Member sees [CLIENT_NAME] and <FAMILY_MEMBER> placeholders."
    path = _write_fixture(tmp_path, "family-member", body)
    fx = load_fixture(path)
    assert fx.persona == "family-member"


def test_phi_deny_pattern_set_is_documented() -> None:
    """The deny pattern set must be exposed for documentation in the README."""
    assert PHI_DENY_PATTERNS, "PHI_DENY_PATTERNS must be a non-empty mapping"
    # Must cover at minimum the three standard shapes named in the design doc.
    assert any("email" in name for name in PHI_DENY_PATTERNS)
    assert any("ssn" in name for name in PHI_DENY_PATTERNS)
    assert any("dob" in name for name in PHI_DENY_PATTERNS)


# --- repo-fixture pairing with live inventory ---


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        if (ancestor / "docs" / "migration" / "v1-pages-inventory.md").exists():
            return ancestor
    raise RuntimeError("Could not locate repo root from test file location")


def test_repo_has_one_fixture_per_persona() -> None:
    fixtures = list(iter_repo_fixtures())
    persona_set = {fx.persona for fx in fixtures}
    assert persona_set == set(PERSONAS), (
        f"missing fixtures for: {set(PERSONAS) - persona_set}; "
        f"unexpected fixtures: {persona_set - set(PERSONAS)}"
    )


def test_repo_fixtures_pair_with_live_inventory_above_floor() -> None:
    """Every fixture's persona section in the live doc clears its min_section_bytes."""
    inv = _repo_root() / "docs" / "migration" / "v1-pages-inventory.md"
    for fx in iter_repo_fixtures():
        section = extract_section(inv, fx.persona, min_bytes=fx.min_section_bytes)
        assert len(section.encode("utf-8")) >= fx.min_section_bytes
