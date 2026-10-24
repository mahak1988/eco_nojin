"""Gating tests for the ECO-16 end-to-end runner (tools/run_e2e_demo.py).

These are PLUMBING / integration tests. They prove that:

1. the ZED data gate refuses to run when the local mirror is incomplete,
   writes a BLOCKED_ENVIRONMENT report and produces no outputs (brake 6:
   no fabricated data, no scientific claim);
2. the chain executes end-to-end on tiny SYNTHETIC_TEST_DATA fixtures and
   emits complete spec §5.2 provenance.

Per spec safety brake 6, the synthetic fixtures used here may NOT be used for
any scientific-validation claim: they exercise the chain's plumbing only.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

_RUNNER_PATH = Path(__file__).resolve().parents[2] / "tools" / "run_e2e_demo.py"
_REQUIRED_KEYS = [
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


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_e2e_demo", _RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _with_sidecar(path: Path, dataset_id: str) -> Path:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    meta = {
        "dataset_id": dataset_id,
        "dataset_version": "1.0.0",
        "source_id": f"synthetic:{dataset_id}",
        "variable": "test",
        "unit": "n/a",
        "content_hash": digest,
        "license": "SYNTHETIC_TEST_DATA — not real data",
        "synthetic_test_data": True,
    }
    _write(
        Path(str(path) + ".meta.json"),
        json.dumps(meta, indent=2),
    )
    return path


def _make_mirror(root: Path) -> None:
    """Build a tiny SYNTHETIC_TEST_DATA mirror satisfying the §4.2 layout."""
    climate = root / "climate"
    era5_lines = [
        "date,doy,latitude,elevation_m,temp_min,temp_max,rh_min,rh_max,"
        "wind_speed,solar_radiation,yield_kg_per_ha"
    ]
    chirps_lines = ["date,precipitation_mm"]
    for i in range(36):
        era5_lines.append(
            f"2025-01-{i + 1:02d},{i + 1},41.8,142.0,"
            f"{18.0 + (i % 7) * 0.5:.2f},{28.0 + (i % 7) * 0.5:.2f},"
            f"{28 + i % 5},{52 + i % 5},{1.5 + (i % 4) * 0.2:.2f},"
            f"{18.0 + (i % 6) * 0.7:.2f},{4000 + (i % 5) * 120}"
        )
        chirps_lines.append(f"2025-01-{i + 1:02d},{20.0 + (i % 9) * 3.0:.1f}")
    _with_sidecar(
        _write(climate / "era5_land_daily.csv", "\n".join(era5_lines) + "\n"),
        "era5_land_daily",
    )
    _with_sidecar(
        _write(climate / "chirps_daily_precipitation.csv", "\n".join(chirps_lines) + "\n"),
        "chirps_daily_precipitation",
    )

    sat = root / "satellite"
    _with_sidecar(
        _write(sat / "sentinel2_sr_monthly.csv", "date,ndvi\n2025-01-01,0.42\n"),
        "sentinel2_sr_monthly",
    )
    soil = root / "soil"
    _with_sidecar(
        _write(soil / "soilgrids_phh2o.csv", "depth_cm,phh2o\n10,0.31\n"),
        "soilgrids_phh2o",
    )


# --------------------------------------------------------------------------
# Gate: refuse without data (ZED §2.2ج, brake 6)
# --------------------------------------------------------------------------
def test_missing_data_is_blocked(tmp_path: Path) -> None:
    runner = _load_runner()
    empty_root = tmp_path / "empty_raw"
    empty_root.mkdir()
    out_dir = tmp_path / "out"
    report = tmp_path / "ECO-16.md"

    code = runner.main(
        [
            "--data-root", str(empty_root),
            "--out", str(out_dir),
            "--report", str(report),
        ]
    )

    assert code == 2, "an incomplete mirror must exit 2 (BLOCKED_ENVIRONMENT)"
    body = json.loads(report.read_text(encoding="utf-8"))
    assert body["status"] == "BLOCKED_ENVIRONMENT"
    assert body["gate"]["missing"], "the report must list the missing raw files"
    assert not out_dir.exists(), "no artifacts may be produced when blocked"
    assert "None." in body["scientific_claim"], "no scientific claim may be made"


def test_no_fabrication_and_no_outputs(tmp_path: Path) -> None:
    runner = _load_runner()
    empty_root = tmp_path / "raw"
    empty_root.mkdir()
    out_dir = tmp_path / "e2e-demo"
    report = tmp_path / "ECO-16.md"

    code = runner.main(
        [
            "--data-root", str(empty_root),
            "--out", str(out_dir),
            "--report", str(report),
        ]
    )

    assert code == 2
    assert not out_dir.exists()
    assert list(tmp_path.glob("**/provenance.json")) == []
    assert list(tmp_path.glob("**/outputs.csv")) == []


# --------------------------------------------------------------------------
# Chain: plumbing only, on SYNTHETIC_TEST_DATA fixtures
# --------------------------------------------------------------------------
def test_chain_runs_on_fixtures_with_full_provenance(tmp_path: Path) -> None:
    runner = _load_runner()
    data_root = tmp_path / "raw"
    out_dir = tmp_path / "out"
    report = tmp_path / "ECO-16.md"
    _make_mirror(data_root)

    code = runner.main(
        [
            "--data-root", str(data_root),
            "--out", str(out_dir),
            "--report", str(report),
        ]
    )

    assert code == 0, f"chain must succeed on a complete local mirror (exit {code})"
    provenance = json.loads((out_dir / "provenance.json").read_text(encoding="utf-8"))
    for key in _REQUIRED_KEYS:
        assert key in provenance, f"provenance.json is missing spec §5.2 key '{key}'"

    assert provenance["models_executed"][0]["model_id"] == "CANON-001"
    indicator_ids = {i["indicator_id"] for i in provenance["indicators_calculated"]}
    assert {"ENO_ET0_FAO56_001", "ENO_WB_001", "ENO_SPI_001"} <= indicator_ids
    assert provenance["evidence_ids"] and provenance["claim_ids"]
    assert provenance["uncertainty_status"] == "NOT_ESTIMATED"
    for dataset in provenance["raw_datasets"]:
        assert set(dataset) >= {"dataset_id", "path", "content_hash"}
        assert len(dataset["content_hash"]) == 64

    for artifact in ("inputs.json", "parameters.json", "outputs.csv", "metadata.json"):
        assert (out_dir / artifact).is_file(), f"missing spec §6.16 artifact {artifact}"

    body = json.loads(report.read_text(encoding="utf-8"))
    assert body["status"] == "PASS_E2E_LOCAL_MIRROR"
    assert "Integration only" in body["scientific_claim"], "no validation claim allowed"
