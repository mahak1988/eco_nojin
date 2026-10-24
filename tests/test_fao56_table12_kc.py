"""ETc = Kc * ET0 external anchor: FAO-56 Chapter 6 Table 12 Kc_mid values.

Source: Allen, R.G., Pereira, L.S., Raes, D. and Smith, M. (1998), FAO
Irrigation and Drainage Paper 56, Chapter 6, Table 12 — single crop
coefficient (Kc) values for mid-season stage. Published at
https://www.fao.org/4/X0490E/x0490e0b.htm.

Vendored offline: ``tests/reference_data/fao56_table12_kc.csv`` (+
``.meta.json`` sidecar with sha256 checksum). The gate never fetches live.

This closes the gap on ``ENO_ETC_KC_001`` (currently PARTIAL, gap G-S6):
the Kc lookup now carries a published tabulated anchor for corn (1.20) and
wheat (1.15) mid-season Kc_mid from FAO-56 Table 12, reproduced by
``engine/hydroma/data/kc_lookup.py::get_average_kc``.

Rice is deliberately omitted: FAO-56 Table 12 lists water-management-dependent
paddy-rice Kc values, so a single scalar is not a faithful transcription.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "tests" / "reference_data" / "fao56_table12_kc.csv"


def _load_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.parametrize("crop,published_kc", [("corn/maize", 1.20), ("wheat", 1.15)])
def test_kc_lookup_reproduces_fao56_table12_kc_mid(crop: str, published_kc: float) -> None:
    """The engine's Kc lookup must reproduce FAO-56 Table 12 Kc_mid values.

    Tolerance of 0.01 honours FAO-56's two-decimal table printing.
    """
    from engine.hydroma.data.kc_lookup import get_average_kc

    crop_key = crop.split("/")[0]
    got = float(get_average_kc(crop_key))
    assert abs(got - published_kc) <= 0.01, (
        f"Kc({crop_key})={got} diverges from FAO-56 Table 12 Kc_mid={published_kc} "
        f"by {abs(got - published_kc):.4f} (tol 0.01)"
    )


def test_vendored_rows_match_csv() -> None:
    """Guard: the vendored CSV carries the expected published values."""
    rows = {r["crop_type"]: r for r in _load_rows()}
    assert rows["corn/maize"]["kc_value"] == "1.20"
    assert rows["wheat"]["kc_value"] == "1.15"
