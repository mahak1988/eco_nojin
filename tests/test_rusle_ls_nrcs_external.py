"""RUSLE_LS external anchor (2nd independent source): NRCS Agronomy TN-28.

The LS factor is the *meaningful* RUSLE science (the full product
A = R*K*LS*C*P with table-supplied factors is arithmetic already covered by the
repo's product invariant). This locks the one published, independent LS value
from USDA-NRCS New Mexico Agronomy Technical Note 28 (1999), "Example Run":
an 800-ft (243.84 m) slope at 2% gives LS = 0.44 in Table 3. The engine's
AH-703/McCool form reproduces it to 2-dp.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "tests" / "reference_data" / "rusle_ls_nrcs_tn28.csv"


def test_rusle_ls_reproduces_nrcs_tn28_ls_factor() -> None:
    from engine.hydroma.cpp_bridge import ls_factor

    row = next(iter(csv.DictReader(CSV_PATH.open(encoding="utf-8"))))
    length_m = float(row["slope_length_m"])
    slope_pct = float(row["slope_percent"])
    published = float(row["published_ls_factor"])

    got = float(ls_factor(length_m, slope_pct))
    # NRCS Table 3 prints LS to two decimals; 0.44179 -> 0.44.
    assert abs(got - published) <= 0.005, (
        f"RUSLE LS {got} diverges from the NRCS TN-28 published {published} "
        f"by {abs(got - published):.4f} (tol 0.005, the source's 2-dp rounding)"
    )
