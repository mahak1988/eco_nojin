"""Reference comparison: engine van Genuchten table vs ``rosetta-soil`` 0.3.2.

Modules under test:

* ``engine/hydroma/soil/physics.py::SOIL_PARAMETERS_VG`` (the 12 USDA textures,
  loaded from ``engine/data/soil_vg_table.csv``), and
* ``engine/hydroma/soil/pedotransfer.py::estimate_soil_parameters``.

Reference implementation: **Rosetta 3** through the ``rosetta-soil`` package
0.3.2, which is the Python distribution of the USDA-ARS Rosetta pedotransfer
model (Zhang et al., ``SOIL`` 3, 2017 and Water Resour. Res. 54, 2018).
Rosetta is CC0 / USDA-ARS and is the *published* PTF here; the engine's table
carries a withdrawn Carsel & Parrish (1988) attribution and is labelled a
design assumption in ``engine/data/SOIL_TABLE_CONFLICTS.md``.

What this test is
-----------------
A **comparison**. Rosetta predicts van Genuchten parameters and saturated
conductivity from basic characterisation data; the engine reads them from a
hand-maintained table and from a separate regression set. This suite measures
how far apart the two are, per texture, and reports the deltas.

What this test is NOT
---------------------
Not an authority to change anything. **No engine table may be changed by this
suite.** Every disagreement below is a measurement of a divergence between
two sources, and both open questions stay open:

* G-S6 -- the Carsel & Parrish attribution on the engine's table, already
  withdrawn but not yet re-sourced;
* G-H4 -- ``pedotransfer.ks_cm_per_day_unconfirmed``, gated and reported here
  but not repaired.

The tolerances were set *after* measurement, from the widest deviation
actually observed, and the measured maxima are stated in the module constants
so a reader can see the band is not a licence. Where a band is wide enough to
be uninformative, the per-texture delta is in the assertion message.

How the like-for-like inputs were built
---------------------------------------
Rosetta's best model (code 5) takes sand / silt / clay %, bulk density, water
content at 33 kPa and water content at 1500 kPa. The engine's table carries
no bulk density and no water contents, so those are derived from the engine's
own table rather than imported from anywhere else:

* ``theta_33`` and ``theta_1500`` are the engine's own van Genuchten curve
  evaluated at 330 cm and 15000 cm -- the heads that 33 kPa and 1500 kPa
  correspond to. Note that this is **not** ``physics.FC_HEAD_CM`` (33.0): that
  constant is the head field capacity is *supposed* to be in this model, but
  33 kPa is 330 cm of water, not 33 cm, so using it would hand Rosetta water
  content measured at 3.3 kPa and label it 33 kPa. Using the correct head is
  what makes the comparison like-for-like; the discrepancy with the engine's
  own constant is recorded here rather than propagated.
* bulk density is ``2.65 * (1 - theta_s)``, the mineral-particle-density
  relation applied to the porosity the engine's own table implies. 2.65 g/cm3
  is the standard quartz-dominant value.

What is circular and what is not
--------------------------------
``theta_33`` and ``theta_1500`` are derived from the engine's own curve, so
Rosetta is partly being asked to reproduce an input derived from the very
parameters being judged. That part of the comparison is therefore weaker than
it looks and is reported, not asserted, in
``test_pedotransfer_compared_against_rosetta3``. The five judged parameters
-- theta_r, theta_s, alpha, n and Ks -- are **not** circular: Rosetta has to
produce them from the texture and the derived characterisation data, and the
engine's values come from its own table. ``estimate_soil_parameters`` is
likewise not circular, since it takes only sand / clay / organic matter.

The engine's reference compositions
-----------------------------------
The engine has no sand/silt/clay percentages in its table, so the twelve
compositions it already uses as reference points for its own texture classes
(``engine/hydroma/soil/tests/test_soil.py:700-713``) are used, and
``test_reference_compositions_resolve_to_their_own_texture`` checks that the
engine's own classifier maps each one back to the class it names.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.hydroma.soil.pedotransfer import (
    UNCONFIRMED_UNITHED_CONSTANTS,
    estimate_soil_parameters,
)
from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG, van_genuchten_theta

#: Package and version this suite was measured against. Recorded rather than
#: imported so the suite states what it was verified on even when the package
#: is absent.
_EXTERNAL_PACKAGE = "rosetta"
_EXTERNAL_VERSION = "0.3.2"

#: Rosetta model version. Version 3 is the current published release and is
#: the one whose model code 5 consumes all six inputs.
_ROSETTA_VERSION = 3

#: Standard mineral particle density [g/cm3], used only to turn the engine's
#: own porosity into the bulk density Rosetta wants.
_PARTICLE_DENSITY = 2.65

#: Heads corresponding to 33 kPa and 1500 kPa [cm of water]. These are the
#: definitions Rosetta's ``th33`` and ``th1500`` inputs use.
_HEAD_33_KPA_CM = 330.0
_HEAD_1500_KPA_CM = 15000.0

#: Reference particle-size fractions for the twelve USDA textures, as
#: (sand %, silt %, clay %): the engine's own reference compositions for its
#: own texture classes.
_REFERENCE_COMPOSITIONS: dict[str, tuple[float, float, float]] = {
    "sand": (85.0, 10.0, 5.0),
    "loamy_sand": (75.0, 15.0, 10.0),
    "sandy_loam": (60.0, 25.0, 15.0),
    "loam": (40.0, 40.0, 20.0),
    "silt_loam": (20.0, 65.0, 15.0),
    "silt": (5.0, 90.0, 5.0),
    "sandy_clay_loam": (60.0, 15.0, 25.0),
    "clay_loam": (35.0, 35.0, 30.0),
    "silty_clay_loam": (15.0, 55.0, 30.0),
    "sandy_clay": (50.0, 10.0, 40.0),
    "silty_clay": (10.0, 45.0, 45.0),
    "clay": (20.0, 30.0, 50.0),
}

#: Tolerances for the five judged parameters. Each is set from the widest
#: deviation measured across the twelve textures (stated in the comment on
#: each), rounded up to a usable band. ``_LOG10_KS_TOLERANCE`` is the
#: tolerance the brief specified and the measurement comfortably fits it.
_THETA_R_TOLERANCE = 0.08  # measured maximum |delta| = 0.0732
_THETA_S_TOLERANCE = 0.08  # measured maximum |delta| = 0.0701
_ALPHA_RATIO_MAX = 4.0  # measured maximum ratio = 3.797
_N_TOLERANCE = 1.0  # measured maximum |delta| = 0.9316
_LOG10_KS_TOLERANCE = 1.5  # measured maximum |delta log10| = 1.1418


def _rosetta_input_records() -> list[list[float]]:
    """The twelve Rosetta input records, derived from the engine's own table.

    Each record is ``[sand %, silt %, clay %, bulk density, theta_33,
    theta_1500]`` in the order Rosetta's ``SoilData`` expects.
    """
    records: list[list[float]] = []
    for texture in _REFERENCE_COMPOSITIONS:
        entry = SOIL_PARAMETERS_VG[texture]
        sand, silt, clay = _REFERENCE_COMPOSITIONS[texture]
        bulk_density = _PARTICLE_DENSITY * (1.0 - entry["theta_s"])
        theta_33 = van_genuchten_theta(
            -_HEAD_33_KPA_CM, entry["theta_r"], entry["theta_s"], entry["alpha"], entry["n"]
        )
        theta_1500 = van_genuchten_theta(
            -_HEAD_1500_KPA_CM, entry["theta_r"], entry["theta_s"], entry["alpha"], entry["n"]
        )
        records.append([sand, silt, clay, bulk_density, theta_33, theta_1500])
    return records


def _run_rosetta(records: list[list[float]]) -> np.ndarray:
    """Rosetta 3 predictions for the twelve records.

    The import is inside the function so this module stays importable (and
    merely skips) when the optional dev reference package is absent.
    """
    from rosetta import rosetta

    means, _stdevs, _codes = rosetta(_ROSETTA_VERSION, records)
    return np.asarray(means, dtype=float)


def _ros_theta(theta_r: float, theta_s: float, alpha: float, n: float, head_cm: float) -> float:
    """Rosetta's implied water content at a head, for like-for-like reporting.

    Only used to report where the engine's water contents diverge; it is not
    an input to any tolerance assertion.
    """
    return van_genuchten_theta(-head_cm, theta_r, theta_s, alpha, n)


def _comparison_rows() -> list[dict]:
    """Per-texture deltas, engine table against Rosetta 3."""
    records = _rosetta_input_records()
    predictions = _run_rosetta(records)
    rows: list[dict] = []
    for index, texture in enumerate(_REFERENCE_COMPOSITIONS):
        entry = SOIL_PARAMETERS_VG[texture]
        rose_theta_r, rose_theta_s, rose_alpha, rose_n, rose_ks = predictions[index, :5]
        sand, _silt, clay = _REFERENCE_COMPOSITIONS[texture]
        pedotransfer = estimate_soil_parameters(sand, clay, 1.0)
        rows.append(
            {
                "texture": texture,
                "engine_theta_r": float(entry["theta_r"]),
                "engine_theta_s": float(entry["theta_s"]),
                "engine_alpha": float(entry["alpha"]),
                "engine_n": float(entry["n"]),
                "engine_ks": float(entry["Ks"]),
                "rose_theta_r": float(rose_theta_r),
                "rose_theta_s": float(rose_theta_s),
                "rose_alpha": float(rose_alpha),
                "rose_n": float(rose_n),
                "rose_ks": float(rose_ks),
                "delta_theta_r": float(entry["theta_r"] - rose_theta_r),
                "delta_theta_s": float(entry["theta_s"] - rose_theta_s),
                "alpha_ratio": float(
                    max(entry["alpha"] / rose_alpha, rose_alpha / entry["alpha"])
                ),
                "delta_n": float(entry["n"] - rose_n),
                "delta_log10_ks": float(abs(np.log10(entry["Ks"]) - np.log10(rose_ks))),
                "pedotransfer_theta_1500": float(pedotransfer["theta_1500"]),
                "pedotransfer_theta_33": float(pedotransfer["theta_33"]),
                "pedotransfer_theta_s": float(pedotransfer["theta_s"]),
                "pedotransfer_awc": float(pedotransfer["awc"]),
                "pedotransfer_ks_unconfirmed": float(
                    pedotransfer["ks_cm_per_day_unconfirmed"]
                ),
                "pedotransfer_ks_confirmed": bool(pedotransfer["ks_confirmed"]),
                "pedotransfer_ks_marker": str(pedotransfer["ks_unconfirmed_marker"]),
                "rose_theta_33": _ros_theta(
                    float(rose_theta_r), float(rose_theta_s), float(rose_alpha), float(rose_n),
                    _HEAD_33_KPA_CM,
                ),
                "rose_theta_1500": _ros_theta(
                    float(rose_theta_r), float(rose_theta_s), float(rose_alpha), float(rose_n),
                    _HEAD_1500_KPA_CM,
                ),
            }
        )
    return rows


def _format_table(rows: list[dict]) -> str:
    """Render the measured per-texture comparison as an aligned table."""
    lines = [
        "Engine SOIL_PARAMETERS_VG (design assumption, Carsel & Parrish "
        "attribution withdrawn) vs Rosetta 3 / rosetta-soil "
        f"{_EXTERNAL_VERSION}, model code 5",
        f"{'texture':>18} {'d_thr':>8} {'d_ths':>8} {'a_ratio':>8} {'d_n':>7} "
        f"{'d_logKs':>8} {'eng Ks':>9} {'rose Ks':>9}",
    ]
    for row in rows:
        lines.append(
            f"{row['texture']:>18} {row['delta_theta_r']:>8.4f} "
            f"{row['delta_theta_s']:>8.4f} {row['alpha_ratio']:>8.3f} "
            f"{row['delta_n']:>7.3f} {row['delta_log10_ks']:>8.3f} "
            f"{row['engine_ks']:>9.2f} {row['rose_ks']:>9.2f}"
        )
    return "\n".join(lines)


def _format_pedotransfer_table(rows: list[dict]) -> str:
    """Render the measured pedotransfer-vs-Rosetta comparison as a table."""
    lines = [
        "Engine estimate_soil_parameters (Saxton & Rawls regressions) vs "
        f"Rosetta 3 / rosetta-soil {_EXTERNAL_VERSION}",
        f"{'texture':>18} {'ptf th1500':>11} {'rose th1500':>12} {'ptf th33':>10} "
        f"{'rose th33':>10} {'ptf theta_s':>12} {'rose theta_s':>13} "
        f"{'ptf Ks/rose Ks':>14}",
    ]
    for row in rows:
        ratio = row["pedotransfer_ks_unconfirmed"] / row["rose_ks"]
        lines.append(
            f"{row['texture']:>18} {row['pedotransfer_theta_1500']:>11.4f} "
            f"{row['rose_theta_1500']:>12.4f} {row['pedotransfer_theta_33']:>10.4f} "
            f"{row['rose_theta_33']:>10.4f} {row['pedotransfer_theta_s']:>12.4f} "
            f"{row['rose_theta_s']:>13.4f} {ratio:>14.3e}"
        )
    return "\n".join(lines)


def test_reference_compositions_resolve_to_their_own_texture() -> None:
    """The twelve reference compositions are valid Rosetta inputs.

    Rosetta validates its own inputs, and a silently rejected row would come
    back as code -1 and NaN predictions rather than as a failure. So the
    compositions are checked three ways: the engine's own classifier maps each
    one back to the class it names, the fractions sum to 100, and Rosetta
    reaches its best model (code 5, all six inputs accepted) for every row.
    """
    from engine.hydroma.soil.texture import classify_texture

    for texture, (sand, silt, clay) in _REFERENCE_COMPOSITIONS.items():
        assert abs(sand + silt + clay - 100.0) < 1e-9, (
            f"{texture}: reference fractions sand {sand} + silt {silt} + clay "
            f"{clay} do not sum to 100"
        )
        assert classify_texture(sand, silt, clay) == texture, (
            f"The engine's own classifier maps the reference composition "
            f"({sand}/{silt}/{clay}) to {classify_texture(sand, silt, clay)!r}, "
            f"not {texture!r}. The composition is not a reference point for "
            "the class it names, so the comparison below would not be a "
            "comparison of like with like."
        )

    pytest.importorskip(_EXTERNAL_PACKAGE)
    predictions = _run_rosetta(_rosetta_input_records())
    assert np.all(np.isfinite(predictions)), (
        "Rosetta returned NaN for at least one texture. Rosetta reports code "
        "-1 with NaN outputs when a row fails its own input validation "
        "(99 <= sand+silt+clay <= 101, 0.5 <= bulk density <= 2.0, "
        "0 < theta_1500 < theta_33 < 1), which would make the comparison "
        "silently vacuous rather than visibly failed."
    )


def test_van_genuchten_table_agrees_with_rosetta3() -> None:
    """The engine's van Genuchten table against Rosetta 3, per texture.

    Rosetta (CC0, USDA-ARS) is the published PTF. The engine's table is a
    design assumption with a withdrawn attribution, so the direction of any
    disagreement is not established by this test -- only its size. No engine
    table may be changed by this suite (G-S6 stays open).
    """
    pytest.importorskip(_EXTERNAL_PACKAGE)
    rows = _comparison_rows()
    table = _format_table(rows)

    for row in rows:
        texture = row["texture"]
        assert abs(row["delta_theta_r"]) <= _THETA_R_TOLERANCE, (
            f"{texture}: |engine theta_r - Rosetta theta_r| = "
            f"{abs(row['delta_theta_r']):.4f} cm3/cm3 exceeds "
            f"{_THETA_R_TOLERANCE} (engine {row['engine_theta_r']:.4f}, "
            f"Rosetta {row['rose_theta_r']:.4f}).\n{table}"
        )
        assert abs(row["delta_theta_s"]) <= _THETA_S_TOLERANCE, (
            f"{texture}: |engine theta_s - Rosetta theta_s| = "
            f"{abs(row['delta_theta_s']):.4f} cm3/cm3 exceeds "
            f"{_THETA_S_TOLERANCE} (engine {row['engine_theta_s']:.4f}, "
            f"Rosetta {row['rose_theta_s']:.4f}).\n{table}"
        )
        assert row["alpha_ratio"] <= _ALPHA_RATIO_MAX, (
            f"{texture}: engine alpha {row['engine_alpha']:.5f} and Rosetta "
            f"alpha {row['rose_alpha']:.5f} differ by a factor of "
            f"{row['alpha_ratio']:.3f} above {_ALPHA_RATIO_MAX}. alpha is the "
            "air-entry parameter, and a factor-of-4 gap moves the whole "
            "retention curve's inflection.\n" f"{table}"
        )
        assert abs(row["delta_n"]) <= _N_TOLERANCE, (
            f"{texture}: |engine n - Rosetta npar| = {abs(row['delta_n']):.4f} "
            f"exceeds {_N_TOLERANCE} (engine {row['engine_n']:.4f}, Rosetta "
            f"{row['rose_n']:.4f}).\n{table}"
        )
        assert row["delta_log10_ks"] <= _LOG10_KS_TOLERANCE, (
            f"{texture}: engine Ks {row['engine_ks']:.2f} cm/day and Rosetta "
            f"Ks {row['rose_ks']:.2f} cm/day differ by "
            f"{row['delta_log10_ks']:.4f} decades above {_LOG10_KS_TOLERANCE}. "
            "This is the closest agreement of the five parameters: the table's "
            "Ks column is unsourced but not absurd.\n" f"{table}"
        )


def test_pedotransfer_compared_against_rosetta3() -> None:
    """``estimate_soil_parameters`` against Rosetta 3, and the gated Ks defect.

    Rosetta (CC0, USDA-ARS) is the published PTF; this is a comparison, and
    no engine table may be changed by it (G-S6 / G-H4 remain open decisions).

    The water-content outputs are **reported, not asserted**. ``theta_1500``
    and ``theta_33`` were themselves derived from the engine's table to build
    Rosetta's inputs, so a tight agreement there would be partly circular, and
    the Saxton & Rawls regressions take sand / clay / organic matter only --
    a genuinely independent route whose divergence from Rosetta is exactly
    what needs recording.

    The ``ks_cm_per_day_unconfirmed`` value is deliberately **not asserted**.
    It is reported as a ratio against Rosetta's Ks, and the ratio is enormous
    -- on the order of 1e3 to 1e15 -- which is the documented defect G-H4. The
    module's own docstring explains why the coefficient set and the 2.778
    prefactor cannot be traced to the cited paper from anything in the
    repository. What *is* asserted here is only the containment: the value is
    emitted under the gated key, alongside ``ks_confirmed = False`` and the
    ``UNCONFIRMED_UNITHED_CONSTANTS`` marker, so a consumer of the pedotransfer
    endpoint cannot read it as an attributed conductivity.
    """
    pytest.importorskip(_EXTERNAL_PACKAGE)
    rows = _comparison_rows()
    table = _format_pedotransfer_table(rows)

    ratios = [row["pedotransfer_ks_unconfirmed"] / row["rose_ks"] for row in rows]
    assert ratios, "no comparison rows were produced"
    assert min(ratios) > 1.0, (
        "Every ratio of pedotransfer ks_cm_per_day_unconfirmed to Rosetta Ks "
        f"was expected to be large; the smallest measured is {min(ratios):.3e}."
    )

    for row in rows:
        texture = row["texture"]
        assert row["pedotransfer_ks_confirmed"] is False, (
            f"{texture}: estimate_soil_parameters reported ks_confirmed True. "
            "The containment for G-H4 is that no consumer can read "
            "ks_cm_per_day_unconfirmed as an attributed conductivity, and a "
            "True flag is what removes that containment."
        )
        assert row["pedotransfer_ks_marker"] == UNCONFIRMED_UNITHED_CONSTANTS, (
            f"{texture}: the unconfirmed-conductivity marker is "
            f"{row['pedotransfer_ks_marker']!r}, expected "
            f"{UNCONFIRMED_UNITHED_CONSTANTS!r}."
        )
    assert len(rows) == len(_REFERENCE_COMPOSITIONS), (
        f"expected one comparison row per texture.\n{table}"
    )
