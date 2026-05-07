"""L2 — Fixture validation tests for `fixtures.py`.

Schema validation, PHI-shape regex deny, must_mention OR-group + anchoring,
and real-fixture pairing with the live inventory doc.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from fixtures import (
    PHI_DENY_PATTERNS,
    Fixture,
    FixtureSchemaError,
    PHIInFixtureError,
    anchor_must_mention,
    iter_repo_fixtures,
    load_fixture,
)
from inventory import PERSONAS, extract_index, extract_section


def _write_fixture(tmp_path: Path, name: str, body: dict[str, Any]) -> Path:
    p = tmp_path / f"{name}.yaml"
    p.write_text(yaml.safe_dump(body), encoding="utf-8")
    return p


def _well_formed_body(persona: str = "family-member") -> dict[str, Any]:
    return {
        "persona": persona,
        "min_section_bytes": 1000,
        "questions": [
            {
                "id": "q1",
                "text": "Q1 text?",
                "fact_summary": "Some fact.",
                "must_mention": [["alpha"]],
            },
            {
                "id": "q2",
                "text": "Q2 text?",
                "fact_summary": "Another fact.",
                "must_mention": [["beta"]],
            },
            {
                "id": "q3",
                "text": "Q3 text?",
                "fact_summary": "Third fact.",
                "must_mention": [["gamma"]],
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
    assert fx.questions[0].fact_summary == "Some fact."
    assert fx.questions[0].must_mention == (("alpha",),)
    assert fx.questions[0].tolerance == 0


def test_load_fixture_with_or_group_alternates(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["must_mention"] = [
        ["is_superuser", "superuser"],
        ["billing_catalogs"],
    ]
    path = _write_fixture(tmp_path, "family-member", body)
    fx = load_fixture(path)
    assert fx.questions[0].must_mention == (
        ("is_superuser", "superuser"),
        ("billing_catalogs",),
    )


def test_load_fixture_with_explicit_tolerance(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["tolerance"] = 1
    path = _write_fixture(tmp_path, "family-member", body)
    fx = load_fixture(path)
    assert fx.questions[0].tolerance == 1


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
        {"id": "q4", "text": "extra?", "fact_summary": "x", "must_mention": [["x"]]}
    )
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError):
        load_fixture(path)


def test_load_fixture_question_missing_fact_summary(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][1]["fact_summary"] = ""
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "fact_summary" in str(exc.value)


def test_load_fixture_legacy_expected_fact_summary_key_rejected(tmp_path: Path) -> None:
    """The rename to `fact_summary` is atomic; old key must hard-fail."""
    body = _well_formed_body()
    # Reintroduce the legacy key alongside the new one.
    body["questions"][0]["expected_fact_summary"] = "legacy fact"
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "expected_fact_summary" in str(exc.value)
    assert "fact_summary" in str(exc.value)


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


def test_load_fixture_must_mention_missing_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    del body["questions"][0]["must_mention"]
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "must_mention" in str(exc.value)


def test_load_fixture_must_mention_empty_list_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["must_mention"] = []
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "must_mention" in str(exc.value)


def test_load_fixture_must_mention_empty_or_group_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["must_mention"] = [[]]
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "must_mention" in str(exc.value)


def test_load_fixture_must_mention_non_string_alternate_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["must_mention"] = [[42]]
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "must_mention" in str(exc.value)


def test_load_fixture_negative_tolerance_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["tolerance"] = -1
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(FixtureSchemaError) as exc:
        load_fixture(path)
    assert "tolerance" in str(exc.value)


# --- PHI deny ---


def test_load_fixture_with_email_phi_in_fact_summary_fails(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["fact_summary"] = "Contact: john.doe@example.com"
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(PHIInFixtureError) as exc:
        load_fixture(path)
    assert "email" in str(exc.value).lower()


def test_load_fixture_with_email_phi_in_must_mention_fails(tmp_path: Path) -> None:
    """PHI-deny patterns extend to must_mention alternates."""
    body = _well_formed_body()
    body["questions"][0]["must_mention"] = [["jane.doe@gmail.com"]]
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
    body["questions"][0]["fact_summary"] = "DOB 03/15/1956 visible to family"
    path = _write_fixture(tmp_path, "family-member", body)
    with pytest.raises(PHIInFixtureError) as exc:
        load_fixture(path)
    assert "dob" in str(exc.value).lower()


def test_phi_placeholder_tokens_are_not_phi(tmp_path: Path) -> None:
    """`[CLIENT_NAME]`, `<FAMILY_MEMBER>` etc. are placeholders, not real PHI."""
    body = _well_formed_body()
    body["questions"][0][
        "fact_summary"
    ] = "Family Member sees [CLIENT_NAME] and <FAMILY_MEMBER> placeholders."
    path = _write_fixture(tmp_path, "family-member", body)
    fx = load_fixture(path)
    assert fx.persona == "family-member"


def test_phi_deny_pattern_set_is_documented() -> None:
    """The deny pattern set must be exposed for documentation in the README."""
    assert PHI_DENY_PATTERNS, "PHI_DENY_PATTERNS must be a non-empty mapping"
    assert any("email" in name for name in PHI_DENY_PATTERNS)
    assert any("ssn" in name for name in PHI_DENY_PATTERNS)
    assert any("dob" in name for name in PHI_DENY_PATTERNS)


# --- anchoring (must_mention against section ∪ index) ---


def test_anchor_must_mention_passes_when_alternates_in_section(
    tmp_path: Path,
) -> None:
    body = _well_formed_body()
    body["questions"][0]["must_mention"] = [["DASHBOARD_TOKEN"]]
    body["questions"][1]["must_mention"] = [["LINKED_CLIENT_TOKEN"]]
    body["questions"][2]["must_mention"] = [["ACTIVE_FLAG_TOKEN"]]
    path = _write_fixture(tmp_path, "family-member", body)
    fx = load_fixture(path)
    section = (
        "DASHBOARD_TOKEN, LINKED_CLIENT_TOKEN, and ACTIVE_FLAG_TOKEN appear here.\n"
    )
    anchor_must_mention(fx, section=section, index="")  # no exception


def test_anchor_must_mention_passes_when_alternate_in_index(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["must_mention"] = [["INDEX_ONLY_TOKEN"]]
    body["questions"][1]["must_mention"] = [["FOO_TOKEN"]]
    body["questions"][2]["must_mention"] = [["BAR_TOKEN"]]
    path = _write_fixture(tmp_path, "family-member", body)
    fx = load_fixture(path)
    section = "FOO_TOKEN and BAR_TOKEN appear in section."
    index = "INDEX_ONLY_TOKEN appears only in the cross-reference index."
    anchor_must_mention(fx, section=section, index=index)  # no exception


def test_anchor_must_mention_unanchored_token_raises(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["must_mention"] = [["nonexistent_xyz_token"]]
    path = _write_fixture(tmp_path, "family-member", body)
    fx = load_fixture(path)
    section = "no relevant content"
    with pytest.raises(FixtureSchemaError) as exc:
        anchor_must_mention(fx, section=section, index="")
    assert "nonexistent_xyz_token" in str(exc.value)
    assert "q1" in str(exc.value)


def test_anchor_must_mention_one_alternate_anchoring_is_sufficient(
    tmp_path: Path,
) -> None:
    """If any alternate appears in section/index, the entry is anchored."""
    body = _well_formed_body()
    body["questions"][0]["must_mention"] = [
        ["is_superuser_TOKEN", "made-up-paraphrase"]
    ]
    body["questions"][1]["must_mention"] = [["foo_TOKEN"]]
    body["questions"][2]["must_mention"] = [["bar_TOKEN"]]
    path = _write_fixture(tmp_path, "family-member", body)
    fx = load_fixture(path)
    section = "is_superuser_TOKEN, foo_TOKEN, and bar_TOKEN appear here."
    anchor_must_mention(fx, section=section, index="")  # no exception


def test_anchor_must_mention_case_insensitive(tmp_path: Path) -> None:
    body = _well_formed_body()
    body["questions"][0]["must_mention"] = [["IS_SUPERUSER_TOKEN"]]
    body["questions"][1]["must_mention"] = [["foo_TOKEN"]]
    body["questions"][2]["must_mention"] = [["bar_TOKEN"]]
    path = _write_fixture(tmp_path, "family-member", body)
    fx = load_fixture(path)
    section = "section uses is_superuser_token in lowercase. foo_TOKEN, bar_TOKEN."
    anchor_must_mention(fx, section=section, index="")


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


def test_repo_fixtures_must_mention_anchors_against_live_inventory() -> None:
    """Every must_mention entry must have ≥1 alternate appearing in section ∪ index."""
    inv = _repo_root() / "docs" / "migration" / "v1-pages-inventory.md"
    index_text = extract_index(inv)
    for fx in iter_repo_fixtures():
        section = extract_section(inv, fx.persona, min_bytes=fx.min_section_bytes)
        anchor_must_mention(fx, section=section, index=index_text)
