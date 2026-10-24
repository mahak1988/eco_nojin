"""Kirpich (CANON-015) corroboration: engine reproduces a published metric worked
example. CORROBORATION ONLY — this is NOT registered as VALIDATED_EXTERNAL.

The source (People's Science Institute training deck, cllmp.com) is an NGO
training deck, not an agency/peer-reviewed reference; it prints Tc to whole
minutes; and the register flags an unresolved divergent Kirpich sibling (G-H6)
and an unsettled coefficient (0.0195 here vs 0.01947 in NPTEL sources). This test
therefore only documents that the engine's metric 0.0195 form reproduces a
*published* worked value within that source's printing precision — a regression
anchor, not promotion evidence.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "tests" / "reference_data" / "kirpich_cllmp_worked.csv"


def test_kirpich_reproduces_cllmp_worked_example_within_printed_precision() -> None:
    from engine.hydroma.watershed.calculator import calculate_kirpich_tc

    row = next(iter(csv.DictReader(CSV_PATH.open(encoding="utf-8"))))
    got = calculate_kirpich_tc(float(row["L_m"]), float(row["S_m_m"]))
    printed = float(row["published_tc_min"])
    # cllmp prints Tc to whole minutes ("6 min"): the engine (5.9514) must land
    # within that source's own rounding.
    assert abs(got - printed) <= 0.5, (
        f"Kirpich Tc {got} min vs published {printed} min differ by "
        f"{abs(got - printed):.3f} min (beyond the source's whole-minute printing)"
    )
