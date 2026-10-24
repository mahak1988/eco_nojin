"""FAO-56 Chapter 7 irrigation interval external anchor.

Source: Allen, R.G., Pereira, L.S., Raes, D. and Smith, M. (1998),
FAO Irrigation and Drainage Paper 56, Chapter 7 "Irrigation scheduling",
Section 7.2: I = (TAW * p) / ETc. Published at
https://www.fao.org/4/X0490E/x0490e0c.htm.

Vendored offline: ``tests/reference_data/fao56_ch7_irrigation.csv``
(+ ``.meta.json`` sidecar with sha256 checksum). The gate never fetches live.

The published worked example: a silt loam wheat field with TAW = 100 mm,
p = 0.55 (55 %), peak ETc = 6 mm/day gives I = (100 * 0.55) / 6 = 9.17,
rounded to 9 days. This same example is cited in
``engine/strict_tests/test_s08_irrigation.py:139`` as "the FAO-56 worked
example". This file formalizes it as a VALIDATED_EXTERNAL anchor.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "tests" / "reference_data" / "fao56_ch7_irrigation.csv"


def _load_row() -> dict[str, str]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1, f"expected one irrigation example row, found {len(rows)}"
    return rows[0]


def test_interval_reproduces_fao56_ch7_worked_example() -> None:
    """calculate_interval(ETc=6, TAW=100, p=0.55) must give 9 days.

    FAO-56 Ch.7: I = (TAW * p) / ETc = (100 * 0.55) / 6 = 9.17, rounded to 9.
    The engine floors at 1 day and rounds to the nearest integer.
    """
    row = _load_row()
    etc = float(row["etc_mm_per_day"])
    taw = float(row["taw_mm"])
    depletion = float(row["allowable_depletion"])
    published = int(row["etc_published_interval_days"])

    from engine.hydroma.irrigation.scheduler import calculate_interval

    got = calculate_interval(etc, taw, depletion)
    assert got == published, (
        f"irrigation interval {got} days diverges from the FAO-56 Ch.7 published "
        f"{published} days (ETc={etc}, TAW={taw}, p={depletion})"
    )
