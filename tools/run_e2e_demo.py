#!/usr/bin/env python3
"""ECO-16 end-to-end chain runner with an honest ZED data gate.

Chain (spec §5.1 / §6.16):
    QC (meta.json contract) -> ET0 (Engine Gateway, CANON-001) -> SPI
    -> Water balance -> Water productivity -> Evidence -> Knowledge claim
    -> Scenario diff -> Decision -> outputs with full §5.2 provenance.

ZED rules enforced by construction:
* No live download. The runner only reads LOCAL mirrors under
  ``<data-root>/{climate,satellite,soil}`` whose files carry a validating
  ``*.meta.json`` sidecar (``engine.data.meta_contract``).
* No fabricated data. If the mirrors are missing the runner refuses,
  writes ``reports/eco-nojin/ECO-16-E2E-REPORT.md`` with
  ``status: BLOCKED_ENVIRONMENT`` and exits 2 (spec safety brake 6).
* Model execution only through the Engine Gateway (AR-06).

Scientific-validation discipline: this runner is an INTEGRATION harness. It
proves the chain is plumbed and traceable end to end; it does not, by itself,
validate any model scientifically. Independent reference benchmarks remain
the separate ``tests/reference_data`` corpus (see ``G-S6b`` in the gap
register — FAO-56 Example 18 is still xfailed).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_VERSION = "ECO-16-runner/1.0.0"

#: Categories that must be mirrored locally, with the canonical files the
#: operator is expected to provide. The gate accepts any file name inside the
#: category (all it can check offline is presence + sidecar validity); the
#: canonical names are what the BLOCKED message asks for.
REQUIRED_MIRROR: dict[str, list[str]] = {
    "climate": ["chirps_daily_precipitation.csv", "era5_land_daily.csv"],
    "satellite": ["sentinel2_sr_monthly.csv"],
    "soil": ["soilgrids_phh2o.csv"],
}

#: Indicator columns the runner knows how to read from the ERA5 CSV.
ERA5_COLUMNS = [
    "date",
    "doy",
    "latitude",
    "elevation_m",
    "temp_min",
    "temp_max",
    "rh_min",
    "rh_max",
    "wind_speed",
    "solar_radiation",
    "yield_kg_per_ha",
]

PROVENANCE_KEYS = [
    "raw_datasets",
    "indicators_calculated",
    "models_executed",
    "evidence_ids",
    "claim_ids",
    "scenario_id",
    "parameter_sets",
    "transformations",
    "uncertainty_status",
    "generated_at",
    "generator_version",
]


# --------------------------------------------------------------------------
# Data gate
# --------------------------------------------------------------------------
def check_mirror(data_root: Path) -> dict[str, Any]:
    """Check the local raw-data mirror against the §4.2 layout + §4.6 contract.

    Returns a report dict: ``ok`` is True only when every required category
    has at least one file and every file carries a sidecar that validates with
    zero blocking problems.
    """
    from engine.data.meta_contract import meta_path_for, validate_meta

    report: dict[str, Any] = {
        "data_root": str(data_root),
        "categories": {},
        "problems": [],
        "missing": [],
        "ok": False,
    }
    for category, expected in REQUIRED_MIRROR.items():
        directory = data_root / category
        found: list[str] = []
        problems: list[str] = []
        if directory.is_dir():
            for path in sorted(directory.rglob("*")):
                if not path.is_file() or path.name.endswith(".meta.json"):
                    continue
                found.append(str(path.relative_to(data_root)))
                sidecar = meta_path_for(path)
                if not sidecar.is_file():
                    problems.append(
                        f"{path.relative_to(data_root)}: missing sidecar "
                        f"{sidecar.name} (spec §4.2)"
                    )
                    continue
                try:
                    meta = json.loads(sidecar.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    problems.append(f"{sidecar}: unreadable ({exc})")
                    continue
                issues = validate_meta(meta)
                if issues:
                    problems.append(
                        f"{sidecar}: {'; '.join(issues)}"
                    )
        entry = {
            "expected_files": expected,
            "present_files": found,
            "problems": problems,
        }
        report["categories"][category] = entry
        if not found:
            report["missing"].append(
                f"{data_root}/{category}/ (one of: {', '.join(expected)})"
            )
        report["problems"].extend(f"[{category}] {p}" for p in problems)
    report["ok"] = not report["missing"] and not report["problems"]
    if report["missing"]:
        report["blocked_reason"] = (
            "local raw mirror incomplete — ZED §2.2ج forbids live download, "
            "so the chain cannot run. Provide the files listed below, each "
            "with a .meta.json sidecar that passes engine.data.meta_contract."
        )
    return report


def write_blocked_report(
    report_path: Path, gate: dict[str, Any], extra: dict[str, Any] | None = None
) -> None:
    """Write the ECO-16 report for a BLOCKED run (honest, no partial claims)."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "document_id": "ECO-16",
        "status": "BLOCKED_ENVIRONMENT",
        "generated_at": datetime.now(UTC).isoformat(),
        "generator_version": GENERATOR_VERSION,
        "gate": gate,
        "missing": gate.get("missing", []),
        "required_categories": REQUIRED_MIRROR,
        "meta_contract": (
            "Each raw file needs <file>.meta.json with the required fields of "
            "spec §4.6 (dataset_id, dataset_version, source_id, variable, "
            "unit, content_hash); see engine/data/meta_contract.py and "
            "tests/reference_data/README.md."
        ),
        "steps_to_unblock": [
            "Mirror the source files locally (no runtime download).",
            "Write a validating .meta.json sidecar next to each file.",
            "Re-run: python tools/run_e2e_demo.py --data-root data/raw",
        ],
        "scientific_claim": (
            "None. The chain has not executed, so no indicator value exists; "
            "this report claims nothing about model accuracy."
        ),
    }
    if extra:
        body.update(extra)
    report_path.write_text(
        json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(row: dict[str, str], key: str, default: float | None = None) -> float | None:
    value = row.get(key)
    if value is None or value == "":
        return default
    return float(value)


def _status_value(obj: Any) -> Any:
    """Return ``.status`` as a plain JSON-safe value (enum → its value)."""
    status = getattr(obj, "status", None)
    return getattr(status, "value", status)


# --------------------------------------------------------------------------
# Chain
# --------------------------------------------------------------------------
def run_chain(data_root: Path, out_dir: Path) -> dict[str, Any]:
    """Execute the full chain on the local mirror and write §5.2 artifacts."""
    from engine.data.meta_contract import sha256_of
    from engine.evidence import Evidence, EvidenceEngine, EvidenceSource, EvidenceType
    from engine.gateway import EngineGateway, GatewayRequest, ProvenanceSpec
    from engine.hydroma.spi_calculator import calculate_spi
    from engine.hydroma.water_balance import water_balance
    from engine.hydroma.water_productivity import water_productivity
    from engine.knowledge import Claim, Fact, KnowledgeEngine
    from engine.tasmimyar import DecisionEngine
    from scenario.engine.baseline_manager import (
        list_definitions,
        scenario_diff,
    )

    climate = sorted((data_root / "climate").glob("*.csv"))
    era5 = next((p for p in climate if "era5" in p.name.lower()), climate[0])
    chirps = next((p for p in climate if "chirps" in p.name.lower()), None)
    soil_files = sorted((data_root / "soil").glob("*"))
    satellite_files = sorted((data_root / "satellite").glob("*"))

    era5_rows = _read_rows(era5)
    if not era5_rows:
        raise ValueError(f"{era5}: no rows")

    # ---- ET0 through the Engine Gateway (AR-06) -------------------------
    gateway = EngineGateway()
    raw_datasets: list[dict[str, Any]] = []
    for label, path in (
        ("era5_land_daily", era5),
        ("chirps_daily_precipitation", chirps),
        ("soilgrids", soil_files[0] if soil_files else None),
        ("sentinel2", satellite_files[0] if satellite_files else None),
    ):
        if path is None:
            continue
        raw_datasets.append(
            {
                "dataset_id": label,
                "path": str(path.relative_to(data_root)),
                "content_hash": sha256_of(path),
            }
        )

    et0_values: list[float] = []
    inputs_used: list[dict[str, Any]] = []
    models_executed: list[dict[str, Any]] = []
    for row in era5_rows:
        payload = {
            "temp_min": _float(row, "temp_min"),
            "temp_max": _float(row, "temp_max"),
            "rh_min": _float(row, "rh_min"),
            "rh_max": _float(row, "rh_max"),
            "wind_speed": _float(row, "wind_speed"),
            "elevation": _float(row, "elevation_m", 0.0),
            "latitude": _float(row, "latitude", 0.0),
            "doy": int(_float(row, "doy", 1.0) or 1),
        }
        solar = _float(row, "solar_radiation")
        if solar is not None:
            payload["solar_radiation"] = solar
        request = GatewayRequest(
            model_id="CANON-001",
            inputs=payload,
            input_units={},
            provenance=ProvenanceSpec(
                source=f"file:{era5}",
                source_type="OBSERVATION",
                trust_level=1.0,
            ),
        )
        result = gateway.execute(request)
        error = getattr(result, "error_code", None)
        if error is not None:
            raise RuntimeError(f"gateway refused CANON-001: {error}")
        et0 = float(result.values["et0_mm_day"])
        et0_values.append(et0)
        inputs_used.append({"date": row.get("date", ""), **payload})
        models_executed.append(
            {
                "model_id": result.model.model_id,
                "model_version": result.model.model_version,
                "run_id": result.execution.execution_id,
            }
        )

    # ---- SPI ------------------------------------------------------------
    indicators: list[dict[str, Any]] = [
        {
            "indicator_id": "ENO_ET0_FAO56_001",
            "unit": "mm day-1",
            "n": len(et0_values),
            "mean": sum(et0_values) / len(et0_values),
        }
    ]
    precip_series: list[float] = []
    if chirps is not None:
        for row in _read_rows(chirps):
            value = _float(row, "precipitation_mm")
            precip_series.append(0.0 if value is None else value)
    if len(precip_series) >= 24:
        spi = calculate_spi(precip_series, scale=12)
        finite = [v for v in spi.tolist() if not math.isnan(v)]
        if finite:
            indicators.append(
                {
                    "indicator_id": "ENO_SPI_001",
                    "scale": 12,
                    "last": finite[-1],
                    "status": "COMPUTED",
                }
            )

    # ---- Water balance ---------------------------------------------------
    n = min(len(et0_values), len(precip_series)) if precip_series else len(et0_values)
    et_for_bwb = et0_values[:n]
    precipitation = (precip_series[:n] if precip_series else [0.0] * n)
    wb = water_balance(precipitation, et_for_bwb, [0.0] * n)
    indicators.append(
        {
            "indicator_id": "ENO_WB_001",
            "unit": "mm",
            "max_abs_closure": float(wb["max_abs_closure"]),
            "final_storage_mm": float(wb["storage"][-1]),
        }
    )

    # ---- Water productivity (only with an explicit yield input) ----------
    yield_column = era5_rows[0].get("yield_kg_per_ha")
    if yield_column:
        yields = [_float(r, "yield_kg_per_ha", 0.0) or 0.0 for r in era5_rows]
        wp = water_productivity(sum(yields) / len(yields), sum(et_for_bwb))
        indicators.append({"indicator_id": "ENO_WP_001", "unit": "kg m-3", "wp": wp})
        wp_status = "COMPUTED"
    else:
        wp_status = "SKIPPED_NO_INPUT (no yield_kg_per_ha column)"

    # ---- Evidence -> Knowledge ------------------------------------------
    evidence_engine = EvidenceEngine()
    knowledge_engine = KnowledgeEngine()
    evidence_ids: list[str] = []
    for indicator in indicators:
        evidence = evidence_engine.collect(
            Evidence(
                source=EvidenceSource.MODEL,
                evidence_type=EvidenceType.QUANTITATIVE,
                value=indicator,
                confidence=0.9,
                provenance=[f"ECO-16-RUN/{GENERATOR_VERSION}", f"dataset={era5.name}"],
                metadata={"synthetic_test_data": False},
            )
        )
        evidence_ids.append(evidence.id)

    fact = Fact(
        id=f"fact-{evidence_ids[0][:8]}",
        statement="ECO-16 chain produced ET0/SPI/WB from local mirrors",
        source_id="ECO-16-RUN",
        confidence=0.9,
        provenance_chain=evidence_ids,
    )
    knowledge_engine.assert_fact(fact)
    claim = Claim(
        id=f"claim-{evidence_ids[0][:8]}",
        text="Indicator chain executed with full provenance on local raw data",
        metadata={"runner": GENERATOR_VERSION},
    )
    knowledge_engine.register_claim(claim)
    evaluated = knowledge_engine.evaluate_claim(claim.id, [fact.id], [])

    # ---- Scenario diff ----------------------------------------------------
    definitions = list_definitions(REPO_ROOT / "scenario" / "definitions")
    scenario_id = None
    scenario_diff_result: dict[str, Any] = {}
    baseline_def = next(
        (d for d in definitions if d.get("baseline_id") is None), None
    )
    scenario_def = next(
        (d for d in definitions if d.get("baseline_id")), None
    )
    if baseline_def is not None and scenario_def is not None:
        scenario_id = scenario_def.get("scenario_id")
        scenario_diff_result = scenario_diff(baseline_def, scenario_def)

    # ---- Decision (fail-closed, default scientific criteria) --------------
    decision_engine = DecisionEngine(
        knowledge_engine=knowledge_engine, evidence_engine=evidence_engine
    )
    decision = decision_engine.make_decision(
        claim_id=claim.id,
        supporting_facts=[fact],
        contradicting_facts=[],
    )
    decision_record = {
        "decision_id": getattr(decision, "decision_id", None),
        "status": _status_value(decision),
    }

    # ---- Artifacts (spec §5.2 / §6.16) ------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "inputs.json").write_text(
        json.dumps(inputs_used, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "parameters.json").write_text(
        json.dumps(
            {
                "models_executed": models_executed[:1],
                "spi_scale_months": 12,
                "water_balance_storage0_mm": 0.0,
                "decision_criteria_source": (
                    "engine/tasmimyar defaults; decision/weights.yaml is the "
                    "governance record"
                ),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with (out_dir / "outputs.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "et0_mm_day", "precipitation_mm", "storage_mm"])
        for index in range(n):
            writer.writerow(
                [
                    inputs_used[index]["date"],
                    et0_values[index],
                    precipitation[index],
                    float(wb["storage"][index]),
                ]
            )
    (out_dir / "metadata.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "generator_version": GENERATOR_VERSION,
                "n_era5_rows": len(era5_rows),
                "raw_datasets": raw_datasets,
                "wp_status": wp_status,
                "gate": "PASS (local mirror validated)",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    provenance = {
        "raw_datasets": raw_datasets,
        "indicators_calculated": indicators,
        "models_executed": models_executed,
        "evidence_ids": evidence_ids,
        "claim_ids": [claim.id],
        "scenario_id": scenario_id,
        "parameter_sets": {
            "spi_scale_months": 12,
            "storage0_mm": 0.0,
            "decision_weights_source": "decision/weights.yaml",
        },
        "transformations": [
            "QC: sidecar validate_meta + sha256 content_hash",
            "ET0: EngineGateway CANON-001 (FAO-56 Penman-Monteith)",
            "SPI: engine.hydroma.spi_calculator.calculate_spi(scale=12)",
            "WB: engine.hydroma.water_balance.water_balance(P=ET+Q+dS)",
            "WP: engine.hydroma.water_productivity.water_productivity"
            if wp_status == "COMPUTED"
            else "WP: skipped (no yield input)",
            "Evidence: engine.evidence.EvidenceEngine.collect",
            "Knowledge: engine.knowledge.evaluate_claim",
            "Scenario: scenario.engine.baseline_manager.scenario_diff",
            "Decision: engine.tasmimyar.DecisionEngine.make_decision",
        ],
        "uncertainty_status": "NOT_ESTIMATED",
        "generated_at": datetime.now(UTC).isoformat(),
        "generator_version": GENERATOR_VERSION,
        "scenario_diff": scenario_diff_result,
        "decision": decision_record,
        "claim_status": _status_value(evaluated),
    }
    (out_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return provenance


def write_success_report(report_path: Path, provenance: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "document_id": "ECO-16",
        "status": "PASS_E2E_LOCAL_MIRROR",
        "generated_at": provenance["generated_at"],
        "generator_version": GENERATOR_VERSION,
        "chain": provenance["transformations"],
        "models_executed": [
            {"model_id": m["model_id"], "version": m["model_version"]}
            for m in provenance["models_executed"][:1]
        ],
        "indicators": provenance["indicators_calculated"],
        "evidence_ids": provenance["evidence_ids"],
        "claim_ids": provenance["claim_ids"],
        "scenario_id": provenance["scenario_id"],
        "uncertainty_status": provenance["uncertainty_status"],
        "scientific_claim": (
            "Integration only: the chain executed on local mirrors with full "
            "provenance. Scientific validation of each model remains the "
            "separate reference-benchmark corpus (FAO-56 Example 18 is "
            "recorded as xfailed, gap G-S6b)."
        ),
    }
    report_path.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "ECO-16 end-to-end chain runner. Refuses to download (ZED §2.2ج) "
            "and refuses to fabricate data (spec brake 6)."
        )
    )
    parser.add_argument(
        "--data-root",
        default="data/raw",
        help="local raw mirror root (spec §4.2 layout)",
    )
    parser.add_argument("--out", default="outputs/eco-nojin/e2e-demo", help="artifact directory")
    parser.add_argument(
        "--report",
        default="reports/eco-nojin/ECO-16-E2E-REPORT.md",
        help="ECO-16 report path",
    )
    args = parser.parse_args(argv)

    data_root = Path(args.data_root)
    out_dir = Path(args.out)
    report_path = Path(args.report)

    gate = check_mirror(data_root)
    if not gate["ok"]:
        write_blocked_report(report_path, gate)
        print("BLOCKED_ENVIRONMENT — the E2E chain did not run.")
        print(f"  reason: {gate.get('blocked_reason', 'local mirror incomplete')}")
        for item in gate["missing"]:
            print(f"  MISSING: {item}")
        for problem in gate["problems"]:
            print(f"  PROBLEM: {problem}")
        print(f"  report written: {report_path}")
        print("  No outputs were produced; no scientific claim is made.")
        return 2

    try:
        provenance = run_chain(data_root, out_dir)
    except Exception as exc:  # noqa: BLE001 — report, never silently pass
        write_blocked_report(
            report_path,
            gate,
            {"status": "FAILED_CHAIN", "error": f"{type(exc).__name__}: {exc}"},
        )
        print(f"FAILED_CHAIN — {type(exc).__name__}: {exc}")
        print(f"  report written: {report_path}")
        return 3

    write_success_report(report_path, provenance)
    print("PASS_E2E_LOCAL_MIRROR — chain executed on local data.")
    print(f"  indicators: {[i['indicator_id'] for i in provenance['indicators_calculated']]}")
    print(f"  evidence ids: {len(provenance['evidence_ids'])}, claim: {provenance['claim_ids']}")
    print(f"  artifacts: {out_dir}")
    print(f"  report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
