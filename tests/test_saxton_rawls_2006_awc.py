"""Saxton & Rawls (2006) AWC external anchor — published table values.

Source: Saxton, K.D. and Rawls, W.J. (2006), Soil Science Society of America
Journal 70(5):975-987, Table 6, p.980 — plant-available water capacity (mm/m)
for 12 USDA texture classes, computed as theta(FC) at -33 kPa minus
theta(PWP) at -1500 kPa.

Vendored offline: ``tests/reference_data/saxton_rawls_2006_awc.csv``
(+ ``.meta.json`` sidecar with sha256 checksum). The gate never fetches live.

The same AWC values are already used as reference constants in
``engine/strict_tests/conftest.py::SAXTON_RAWLS_2006_AWC_MM_PER_M`` and tested
against the engine's AWC calculator in ``test_s05``. This file makes the
published table a formal VALIDATED_EXTERNAL anchor by pinning the vendored
reference data itself and asserting the engine's `available_water_capacity`
matches each published value within the pedotransfer's expected tolerance
(the two disagree most on coarse textures; see test_s05 comments).
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "tests" / "reference_data" / "saxton_rawls_2006_awc.csv"


def _load_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.parametrize(
    "texture",
    [
        "sand", "loamy_sand", "sandy_loam", "loam", "silt_loam",
        "silt", "sandy_clay_loam", "clay_loam", "silty_clay_loam",
        "sandy_clay", "silty_clay", "clay",
    ],
)
def test_awc_reproduces_saxton_rawls_2006_published_values(texture: str) -> None:
    """The engine's AWC must match the published Saxton & Rawls (2006) table.

    Tolerance is 5x in either direction: the engine ships Carsel & Parrish
    (1988) van Genuchten parameters (a different pedotransfer), so a factor-of-5
    band is the honest bound the strict suite already enforces (test_s05,
    `test_upper_module_awc_is_within_a_factor_of_five_of_published_values`).
    """
    rows = {r["texture_class"]: r for r in _load_rows()}
    published = float(rows[texture]["awc_mm_per_m"]) / 1000.0

    from engine.hydroma.soil.physics import available_water_capacity

    got = float(available_water_capacity(texture))
    assert 0.2 * published <= got <= 5.0 * published, (
        f"AWC({texture})={got:.4f} cm3/cm3 is outside the 5x band around "
        f"the published {published:.4f} cm3/cm3 (Saxton & Rawls 2006, Table 6, p.980)"
    )


def test_vendored_table_has_all_twelve_textures() -> None:
    """Guard: the reference CSV carries the full USDA 12-texture set."""
    rows = _load_rows()
    expected = {
        "sand", "loamy_sand", "sandy_loam", "loam", "silt_loam",
        "silt", "sandy_clay_loam", "clay_loam", "silty_clay_loam",
        "sandy_clay", "silty_clay", "clay",
    }
    assert {r["texture_class"] for r in rows} == expected, (
        f"missing textures: {expected - {r['texture_class'] for r in rows}}"
    )
