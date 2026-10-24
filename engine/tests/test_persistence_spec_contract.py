"""Spec-conformance tests for the SQLite PersistencePort adapter.

Covers the ECO-04 §4.5 contract as implemented by
``adapters.persistence.sqlite_persistence.SQLitePersistence``:

* round-trip fidelity for every entity,
* claim/evidence linking (relationships + weights),
* duplicate ``datasets.content_hash`` rejection,
* foreign-key enforcement for ``model_runs.model_id``,
* CHECK-constraint rejection of an unknown relationship,
* reproducibility across fresh databases.

Every test uses a temporary database (``tmp_path``) — never the
repository's ``data/`` directory.
"""

from __future__ import annotations

import sqlite3

import pytest

from adapters.persistence.sqlite_persistence import SQLitePersistence

CREATED_AT = "2026-01-02T03:04:06Z"


@pytest.fixture()
def db(tmp_path):
    """A SQLitePersistence instance backed by a throwaway database file."""
    return SQLitePersistence(str(tmp_path / "eco-nojin-test.db"))


# ── payload builders (every column populated explicitly) ────────────────────


def dataset_payload() -> dict:
    return {
        "dataset_id": "ds-chirps-2026",
        "dataset_version": "v2.1",
        "source_id": "src-chirps",
        "source_uri": "https://example.invalid/chirps/2026.tif",
        "provider": "CHG",
        "license": "CC-BY-4.0",
        "retrieved_at": "2026-01-02T03:04:05Z",
        "valid_from": "2026-01-01",
        "valid_to": "2026-12-31",
        "variable": "precipitation",
        "unit": "mm",
        "spatial_ref": "EPSG:4326",
        "temporal_resolution": "daily",
        "spatial_resolution": "0.05deg",
        "quality_flag": "OK",
        "uncertainty": 0.05,
        "processing_history": ["download", "reproject", "aggregate"],
        "content_hash": "0f1e2d3c4b5a69788796a5b4c3d2e1f0a1b2c3d4e5f60718293a4b5c6d7e8f901",
        "local_path": "raw/chirps/2026.tif",
        "created_at": CREATED_AT,
    }


def model_payload() -> dict:
    return {
        "model_id": "mdl-fao56",
        "model_version": "1.3.0",
        "name": "FAO-56 Penman-Monteith ET0",
        "domain": "hydrology",
        "purpose": "reference evapotranspiration",
        "inputs_schema": {"tmax": "degC", "tmin": "degC"},
        "outputs_schema": {"et0": "mm/day"},
        "assumptions": ["well-watered reference surface"],
        "equations": "PM-56 Eq. 6",
        "applicability_domain": "humid temperate",
        "limitations": "not for arid extremes",
        "scientific_references": ["FAO-56 (Allen et al., 1998)"],
        "calibration_status": "NONE",
        "validation_status": "VALIDATED",
        "uncertainty_method": "ensemble",
        "maturity_level": "S3",
    }


def model_run_payload() -> dict:
    return {
        "run_id": "run-0001",
        "model_id": "mdl-fao56",
        "model_version": "1.3.0",
        "executed_at": "2026-02-01T10:00:00Z",
        "parameters_json": {"kc": 1.15, "alpha": 0.23},
        "inputs_hash": "aa" * 16,
        "outputs_hash": "bb" * 16,
        "status": "SUCCESS",
        "error_message": None,
        "execution_time_ms": 1250,
        "environment_json": {"python": "3.11", "os": "windows"},
    }


def evidence_payload() -> dict:
    return {
        "evidence_id": "ev-0001",
        "evidence_type": "MEASUREMENT",
        "source_dataset_id": "ds-chirps-2026",
        "source_model_run_id": "run-0001",
        "location": {"lat": 35.7, "lon": 51.41},
        "valid_time": "2026-05-01",
        "value": 12.5,
        "unit": "mm",
        "quality_score": 0.9,
        "uncertainty": 0.02,
        "provenance_chain": [{"step": "sensor"}, {"step": "qc"}],
        "created_at": CREATED_AT,
    }


def claim_payload() -> dict:
    return {
        "claim_id": "cl-0001",
        "claim_text": "2026 seasonal rainfall stayed below the 10-year median.",
        "claim_type": "hydrological",
        "epistemic_status": "MEASUREMENT",
        "confidence_basis": "three independent gauges",
        "known_limitations": "single season only",
        "review_status": "PENDING",
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
    }


def scenario_payload() -> dict:
    return {
        "scenario_id": "sc-0001",
        "scenario_version": "1.0.0",
        "baseline_id": "baseline-2025",
        "spatial_scope": "Zayandeh-Rud basin",
        "time_horizon": "2026-2030",
        "climate_assumptions": {"ssp": "SSP2-4.5"},
        "land_management": ["contour farming"],
        "crop_plan": {"wheat": 0.6, "maize": 0.4},
        "water_allocation": {"agri": 0.7, "urban": 0.3},
        "soil_interventions": ["mulching"],
        "economic_assumptions": {"discount": 0.08},
        "social_constraints": ["groundwater cap"],
        "model_versions": {"fao56": "1.3.0"},
        "dataset_versions": {"ds-chirps-2026": "v2.1"},
        "parameter_set_versions": {"base": "1.0.0"},
        "uncertainty_settings": {"method": "monte-carlo", "n": 1000},
        "execution_status": "SUCCESS",
        "validation_status": "PENDING",
        "created_at": CREATED_AT,
    }


def decision_payload() -> dict:
    return {
        "decision_id": "dec-0001",
        "problem_definition": "allocate irrigation water for 2026 season",
        "objectives": ["maximize yield", "protect aquifer"],
        "constraints": ["groundwater cap"],
        "options_evaluated": ["do-nothing", "deficit-irrigation"],
        "scenarios_used": ["sc-0001"],
        "evidence_considered": ["ev-0001"],
        "model_outputs_used": ["run-0001"],
        "risks": ["drought recurrence"],
        "uncertainty_handling": "monte-carlo ensemble",
        "trade_offs": "-3% yield, +12% aquifer storage",
        "recommendation": "adopt deficit irrigation",
        "recommendation_basis": "evidence + model agreement",
        "monitoring_plan": "monthly piezometry",
        "limitations": "single basin, single season",
        "created_at": CREATED_AT,
    }


ALL_PAYLOADS = (
    dataset_payload(),
    model_payload(),
    model_run_payload(),
    evidence_payload(),
    claim_payload(),
    scenario_payload(),
    decision_payload(),
)


def seed(db: SQLitePersistence) -> None:
    """Save every entity in FK-safe order inside *db*."""
    for payload in ALL_PAYLOADS:
        if "model_id" in payload and "run_id" not in payload:
            db.save_model(payload)
        elif "run_id" in payload:
            db.save_model_run(payload)
        elif "dataset_id" in payload:
            db.save_dataset(payload)
        elif "evidence_id" in payload:
            db.save_evidence(payload)
        elif "claim_id" in payload:
            db.save_claim(payload)
        elif "scenario_id" in payload:
            db.save_scenario(payload)
        elif "decision_id" in payload:
            db.save_decision(payload)
        else:  # pragma: no cover - defensive
            raise AssertionError("unclassified payload")


# ── tests ───────────────────────────────────────────────────────────────────


def test_roundtrip_each_entity(db):
    seed(db)

    assert db.get_dataset("ds-chirps-2026") == dataset_payload()
    assert db.get_model_run("run-0001") == model_run_payload()
    assert db.get_evidence("ev-0001") == evidence_payload()
    assert db.get_claim("cl-0001") == claim_payload()
    assert db.get_scenario("sc-0001") == scenario_payload()
    assert db.get_decision("dec-0001") == decision_payload()


def test_roundtrip_preserves_types_and_none(db):
    seed(db)

    run = db.get_model_run("run-0001")
    assert run["execution_time_ms"] == 1250 and isinstance(run["execution_time_ms"], int)
    assert run["parameters_json"] == {"kc": 1.15, "alpha": 0.23}
    assert run["error_message"] is None

    evidence = db.get_evidence("ev-0001")
    assert evidence["value"] == 12.5 and isinstance(evidence["value"], float)
    assert evidence["provenance_chain"] == [{"step": "sensor"}, {"step": "qc"}]


def test_generated_id_is_uuid4_hex(db):
    dataset = dataset_payload()
    dataset.pop("dataset_id")
    dataset_id = db.save_dataset(dataset)

    assert len(dataset_id) == 32
    int(dataset_id, 16)  # hex-decodable
    assert db.get_dataset(dataset_id)["dataset_version"] == "v2.1"


def test_save_returns_explicit_ids(db):
    assert db.save_dataset(dataset_payload()) == "ds-chirps-2026"
    assert db.save_claim(claim_payload()) == "cl-0001"
    assert db.save_scenario(scenario_payload()) == "sc-0001"
    assert db.save_decision(decision_payload()) == "dec-0001"


def test_claim_evidence_link(db):
    seed(db)
    db.save_evidence(evidence_payload() | {"evidence_id": "ev-supports"})
    db.save_evidence(evidence_payload() | {"evidence_id": "ev-contradicts"})
    db.save_evidence(evidence_payload() | {"evidence_id": "ev-neutral"})

    db.link_evidence_to_claim("cl-0001", "ev-supports", "SUPPORTS")
    db.link_evidence_to_claim("cl-0001", "ev-contradicts", "CONTRADICTS", weight=2.5)
    db.link_evidence_to_claim("cl-0001", "ev-neutral", "NEUTRAL", weight=0.0)

    links = {(row["evidence_id"]): row for row in db.get_claim_evidence("cl-0001")}
    assert set(links) == {"ev-supports", "ev-contradicts", "ev-neutral"}

    assert links["ev-supports"]["claim_id"] == "cl-0001"
    assert links["ev-supports"]["relationship"] == "SUPPORTS"
    assert links["ev-supports"]["weight"] == pytest.approx(1.0)

    assert links["ev-contradicts"]["relationship"] == "CONTRADICTS"
    assert links["ev-contradicts"]["weight"] == pytest.approx(2.5)

    assert links["ev-neutral"]["relationship"] == "NEUTRAL"
    assert links["ev-neutral"]["weight"] == pytest.approx(0.0)

    assert db.get_claim_evidence("cl-missing") == []


def test_duplicate_content_hash_raises(db):
    db.save_dataset(dataset_payload())

    duplicate = dataset_payload()
    duplicate["dataset_id"] = "ds-chirps-2026-copy"
    with pytest.raises(ValueError) as excinfo:
        db.save_dataset(duplicate)

    assert "content_hash" in str(excinfo.value)
    assert not isinstance(excinfo.value, sqlite3.IntegrityError)


def test_fk_enforced_for_model_run(db):
    run = model_run_payload()
    run["model_id"] = "mdl-does-not-exist"

    with pytest.raises(sqlite3.IntegrityError) as excinfo:
        db.save_model_run(run)

    assert "FOREIGN KEY" in str(excinfo.value)


def test_invalid_relationship_rejected(db):
    seed(db)

    with pytest.raises(sqlite3.IntegrityError) as excinfo:
        db.link_evidence_to_claim("cl-0001", "ev-0001", "MAYBE")

    assert "CHECK" in str(excinfo.value)


def test_unknown_run_status_rejected(db):
    seed(db)
    run = model_run_payload()
    run["status"] = "MAYBE"

    with pytest.raises(sqlite3.IntegrityError):
        db.save_model_run(run)


def test_reproducibility(tmp_path):
    first = SQLitePersistence(str(tmp_path / "repro-a.db"))
    second = SQLitePersistence(str(tmp_path / "repro-b.db"))

    seed(first)
    seed(second)

    readers = {
        "run_id": (first.get_model_run, second.get_model_run),
        "model_id": (first.get_model, second.get_model),
        "dataset_id": (first.get_dataset, second.get_dataset),
        "evidence_id": (first.get_evidence, second.get_evidence),
        "claim_id": (first.get_claim, second.get_claim),
        "scenario_id": (first.get_scenario, second.get_scenario),
        "decision_id": (first.get_decision, second.get_decision),
    }

    for payload in ALL_PAYLOADS:
        for id_field, (read_first, read_second) in readers.items():
            if id_field in payload:
                assert read_first(payload[id_field]) == read_second(payload[id_field])
                break
        else:  # pragma: no cover - defensive
            raise AssertionError("unclassified payload")


def test_claim_evidence_link_is_idempotent(db):
    seed(db)

    db.link_evidence_to_claim("cl-0001", "ev-0001", "SUPPORTS", weight=0.4)
    db.link_evidence_to_claim("cl-0001", "ev-0001", "CONTRADICTS", weight=0.8)

    links = db.get_claim_evidence("cl-0001")
    assert len(links) == 1
    assert links[0]["relationship"] == "CONTRADICTS"
    assert links[0]["weight"] == pytest.approx(0.8)
