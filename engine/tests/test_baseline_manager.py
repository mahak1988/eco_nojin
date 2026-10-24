"""Contract tests for ``scenario.engine.baseline_manager`` (ECO-12 phase 1).

These are CONTRACT tests, not scientific validation (safety-brake-6
discipline). They pin the shape of the definition layer -- loading and
validation, the structured diff, and the read-only comparison against the
recorded execution baseline -- and they assert nothing about the physical
correctness of any scenario, model, or recorded number. A green run means
the definition, versioning and comparison machinery behaves as specified;
it does not mean the drier-climate numbers are right, and it is not
evidence that any model fits the pilot area.

The comparison test reads ``engine/baseline/R18.json`` and re-reads its
bytes afterwards to prove the module left the recorded baseline alone.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]  # PyYAML ships no type hints in this env

from scenario.engine.baseline_manager import (
    compare_against_result_snapshot,
    list_definitions,
    load_scenario,
    scenario_diff,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFINITIONS_DIR = REPO_ROOT / "scenario" / "definitions"
BASELINE_PATH = DEFINITIONS_DIR / "baseline.yaml"
DRIER_PATH = DEFINITIONS_DIR / "drier_climate.yaml"
R18_PATH = REPO_ROOT / "engine" / "baseline" / "R18.json"


# ---------------------------------------------------------------------------
# Loading and validation
# ---------------------------------------------------------------------------


def test_definitions_load_and_validate() -> None:
    baseline = load_scenario(BASELINE_PATH)
    drier = load_scenario(DRIER_PATH)

    for definition in (baseline, drier):
        # ECO-12: versioned definitions, with documented assumptions.
        assert definition["scenario_version"] == "1.0.0"
        assert isinstance(definition["assumptions"], list)
        assert definition["assumptions"], "assumptions must be a non-empty list"
        assert all(entry.get("id") for entry in definition["assumptions"])
        assert all(entry.get("statement") for entry in definition["assumptions"])
        # Every undocumented section says so, rather than guessing.
        assert definition["dataset_versions"] == ["UNPROMOTED_TO_REGISTRY"]
        assert definition["uncertainty_settings"] == "NOT_ESTIMATED"
        assert definition["model_versions"], "the scenario must pin model versions"
        for key in (
            "spatial_scope",
            "time_horizon",
            "climate_assumptions",
            "land_management",
            "crop_plan",
            "water_allocation",
            "soil_interventions",
            "economic_assumptions",
            "social_constraints",
            "parameter_set_versions",
        ):
            assert key in definition

    assert baseline["scenario_id"] == "ENO_SCENARIO_BASELELINE_2025"
    assert baseline["baseline_id"] is None, "the baseline points at no other baseline"
    assert drier["scenario_id"] == "ENO_SCENARIO_DRIER_2025"


def test_list_definitions_reports_both_definitions() -> None:
    listed = list_definitions(DEFINITIONS_DIR)
    assert [definition["scenario_id"] for definition in listed] == [
        "ENO_SCENARIO_BASELELINE_2025",
        "ENO_SCENARIO_DRIER_2025",
    ]


def test_invalid_definition_rejected(tmp_path: Path) -> None:
    definition = dict(load_scenario(BASELINE_PATH))
    del definition["assumptions"]
    broken = tmp_path / "no_assumptions.yaml"
    broken.write_text(
        yaml.safe_dump(definition, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="assumptions"):
        load_scenario(broken)

    not_semver = dict(load_scenario(BASELINE_PATH))
    not_semver["scenario_version"] = "1.0"
    bad_version = tmp_path / "bad_version.yaml"
    bad_version.write_text(
        yaml.safe_dump(not_semver, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="scenario_version"):
        load_scenario(bad_version)


def test_drier_references_baseline() -> None:
    baseline = load_scenario(BASELINE_PATH)
    drier = load_scenario(DRIER_PATH)
    assert drier["baseline_id"] == baseline["scenario_id"]


# ---------------------------------------------------------------------------
# Structured diff (مقایسه با baseline)
# ---------------------------------------------------------------------------


def test_diff_detects_changes() -> None:
    diff = scenario_diff(load_scenario(BASELINE_PATH), load_scenario(DRIER_PATH))

    assert diff["changed_keys"], "the drier scenario must move something"
    assert diff["linkage"]["references_baseline"] is True

    climate = diff["fields"]["climate_assumptions"]
    assert climate["status"] == "changed"
    # The perturbations the drier scenario actually carries.
    assert "precipitation_change_pct" in climate["changed"]
    assert "temperature_change_c" in climate["changed"]
    # Each assumption is itself a mapping, so the diff walks into it and
    # names the field that moved rather than showing one opaque blob.
    precip = climate["changed"]["precipitation_change_pct"]["changed"]
    assert precip["value"] == {"baseline": 0.0, "scenario": -20.0}
    assert precip["evidence_basis"]["scenario"] == "HYPOTHESIS — no forcing dataset local yet"
    temp = climate["changed"]["temperature_change_c"]["changed"]
    assert temp["value"] == {"baseline": 0.0, "scenario": 2.0}
    # A key only the drier scenario carries is reported as added, not
    # silently merged into a changed section.
    assert "dry_spell_frequency_change_pct" in climate["added"]

    # Everything this scenario does not move must read as unchanged.
    for key in (
        "spatial_scope",
        "time_horizon",
        "land_management",
        "crop_plan",
        "water_allocation",
        "soil_interventions",
        "economic_assumptions",
        "social_constraints",
        "model_versions",
        "dataset_versions",
        "parameter_set_versions",
        "uncertainty_settings",
    ):
        assert diff["fields"][key]["status"] == "unchanged", key

    # The documented-assumption list is diffed per id, additively.
    assumptions = diff["fields"]["assumptions"]
    assert assumptions["status"] == "changed"
    assert set(assumptions["added"]) == {
        "A-008",
        "A-009",
        "A-010",
        "A-011",
        "A-012",
        "A-013",
    }
    assert set(assumptions["removed"]) == {"A-006"}


def test_diff_reports_model_versions_per_model_id() -> None:
    baseline = load_scenario(BASELINE_PATH)

    bumped = dict(baseline)
    bumped["model_versions"] = {**baseline["model_versions"], "CANON-001": "9.9.9"}
    diff = scenario_diff(baseline, bumped)

    # A nested-only comparison would bury one bumped model inside a
    # section that merely "changed"; the report must name it.
    model_versions = diff["model_versions"]
    assert model_versions["status"] == "changed"
    assert model_versions["changed"] == {
        "CANON-001": {"baseline": "1.0.0", "scenario": "9.9.9"}
    }
    assert "CANON-001" in model_versions["compared_ids"]
    assert model_versions["added"] == {} and model_versions["removed"] == {}

    identical = scenario_diff(baseline, dict(baseline))
    assert identical["summary"]["identical"] is True
    assert identical["model_versions"]["status"] == "unchanged"


# ---------------------------------------------------------------------------
# Measured snapshot vs the recorded execution baseline
# ---------------------------------------------------------------------------


def test_compare_against_snapshot_reads_R18() -> None:
    if not R18_PATH.is_file():
        pytest.skip(f"recorded execution baseline not found: {R18_PATH}")
    before = R18_PATH.read_bytes()
    try:
        recorded = json.loads(before.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        pytest.skip(f"R18.json unreadable: {exc}")

    scenario = load_scenario(BASELINE_PATH)

    # A trivial (empty) measured snapshot: nothing reproduces the record.
    empty = compare_against_result_snapshot(scenario, {"cases": {}})
    assert isinstance(empty, dict)
    assert empty["status"] == "compared"
    assert empty["stored_baseline_id"] == "R18"
    assert empty["scenario_id"] == "ENO_SCENARIO_BASELELINE_2025"
    summary = empty["summary"]
    assert summary["values_matching"] == 0
    assert summary["values_only_in_snapshot"] == 0
    assert summary["values_missing_in_snapshot"] == summary["stored_values"] > 0

    # One recorded case measured verbatim must read as a match, with a
    # per-path stored/measured delta of zero.
    group, case = "climate_et0", "penman_monteith"
    measured = {"cases": {group: {case: recorded["cases"][group][case]}}}
    result = compare_against_result_snapshot(scenario, measured)
    entry = result["cases"][group][case]
    assert entry["status"] == "match"
    assert entry["counts"]["values_differing"] == 0
    first_path = next(iter(entry["metrics"]))
    metric = entry["metrics"][first_path]
    assert metric["stored"] == metric["measured"]
    assert metric["delta"] == 0
    assert metric["within_tolerance"] is True

    # A measurement that moves one value must be reported as a delta.
    group2, case2 = "soil_retention", "awc_cm3_cm3"
    stored_case = recorded["cases"][group2][case2]
    moved = {**stored_case}
    first_key = next(iter(moved))
    moved[first_key] = moved[first_key] + 1.0
    drifted = compare_against_result_snapshot(
        scenario, {"cases": {group2: {case2: moved}}}
    )
    drift_entry = drifted["cases"][group2][case2]
    assert drift_entry["status"] == "differs"
    assert drift_entry["max_relative_delta"] is not None

    # READ-ONLY discipline: the recorded baseline is not touched.
    assert R18_PATH.read_bytes() == before


def test_compare_against_snapshot_reports_missing_record() -> None:
    scenario = load_scenario(BASELINE_PATH)
    result = compare_against_result_snapshot(
        scenario, {"cases": {}}, stored_path=REPO_ROOT / "engine" / "baseline" / "absent.json"
    )
    assert result["status"] == "stored_baseline_unavailable"
    assert result["reason"]
    assert result["cases"] == {}
