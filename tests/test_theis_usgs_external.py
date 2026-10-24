"""CANON-005 (Theis) external anchor: reproduce a USGS published worked example.

Locked regression against a genuinely *published* drawdown (not a re-derivation),
so a future Theis change that breaks agreement with the USGS value fails here.
Reads the vendored value from ``tests/reference_data/theis_usgs_worked_example.csv``
(offline; provenance in the ``.meta.json`` sidecar) — the gate never fetches live.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "tests" / "reference_data" / "theis_usgs_worked_example.csv"


@pytest.mark.parametrize("tolerance", [1e-6])
def test_canon005_reproduces_usgs_published_drawdown(tolerance: float) -> None:
    from engine.hydroma.theis import compute_theis

    row = next(iter(csv.DictReader(CSV_PATH.open(encoding="utf-8"))))
    inputs = {
        "transmissivity_m2day": float(row["T_m2day"]),
        "storativity": float(row["storativity"]),
        "pumping_rate_m3day": float(row["Q_m3day"]),
        "distance_from_well_m": float(row["r_m"]),
        "time_since_pumping_start_days": float(row["t_days"]),
    }
    published = float(row["published_drawdown_m"])

    result = compute_theis(inputs, {})
    got = float(result["drawdown_m"])
    assert abs(got - published) <= tolerance, (
        f"Theis drawdown {got} m diverges from the USGS published {published} m "
        f"by {abs(got - published):.2e} m (tolerance {tolerance:.0e}); this is a "
        "VALIDATED_EXTERNAL anchor and must reproduce it"
    )
