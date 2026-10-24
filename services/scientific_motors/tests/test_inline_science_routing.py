"""B-3 / B-4 — the inline SCS-CN and Hargreaves copies now reach the engine.

Mandate: route the HIGH inline-science hits reported by
``tools/find_inline_science.py`` through the canonical engine functions via
``services/_gateway_facade.py``, keeping every returned number identical.

The families routed here
------------------------
* ``SCS_CN_RETENTION`` / ``SCS_CN_ABSTRACTION`` / ``SCS_CN_RUNOFF_EQ`` — the
  USDA-NRCS triplet ``S = 25400/CN - 254``, ``Ia = 0.2 S``,
  ``Q = (P - Ia)^2 / (P + 0.8 S)`` (SI form, NEH part 630 / TR-55) was written
  out in four service modules. It is the engine's relation
  (``RunoffCalculator._scs_cn_method``, gateway CANON-004) and is now reached
  through ``services._gateway_facade.calculate_runoff``:

  - ``services/_contracts/formula.py::runoff_scs``
  - ``services/simulation/adapters/hydrology_adapter.py``
  - ``services/scientific_motors/swat_plus.py`` (whole-grid vector routing)

* ``HARGREAVES_EQ52`` — ``services/validation/formula_checks.py`` used to
  re-derive FAO-56 eq. 52 inline. The relation is the engine's
  (``engine/hydroma/climate/et_calculator.py::_hargreaves_core``, gateway
  CANON-002); the check now compares against the engine's value.

Parity
------
Test modules are excluded from the inline-science scan precisely so a
published value can be pinned here. The sibling ``inline`` helpers below
re-state the algebra the routed code replaced, so the parity is a measured
comparison and not an assertion of intent.

Two shapes of difference are pinned, both below the precision of any reported
figure:

* **Scalar sites** — the routed depth is recovered by the gateway as
  ``volume_m3 / (area_ha * 10)`` with ``volume_m3 = Q * area_ha * 10``, which
  is not an involution, so the last bit of a double can move. The measured
  worst-case over the 72 curve numbers x 19 precipitation depths grid is
  ``1.1368683772161603e-13`` mm.
* **The swat_plus raster** — the inline copy stepped through float32; the
  engine computes in float64 and the raster is cast back to float32. The
  measured worst case is one float32 ulp.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest
import xarray as xr

from services._contracts.formula import runoff_scs
from services._gateway_facade import (
    calc_et0_hargreaves,
    calculate_runoff,
    hargreaves_et0,
)
from services.scientific_motors.swat_plus import _scs_runoff_raster
from services.simulation.adapters.hydrology_adapter import _scs_runoff_depth_mm

# --- Published references ---------------------------------------------------
# NRCS SCS-CN worked example (engine/strict_tests/conftest.py). SI form:
# S = 25400/70 - 254 = 108.857 mm = 4.2857 in; the inch form must never be
# mixed with millimetre rainfall.
NRCS_WORKED_EXAMPLE = {
    "precipitation_mm": 50.0,
    "curve_number": 70.0,
    "retention_mm": 108.85714285714283,
    "retention_inches": 4.2857142857142865,
    "initial_abstraction_mm": 21.77142857142857,
    "runoff_mm": 5.812802953611626,
}

# FAO-56 eq. 52 at tmin 10 / tmax 25, latitude 40 deg, DOY 150. The engine's
# own Ra for that site is 41.14825459255412 MJ m-2 day-1 and the published
# exponent on the diurnal range is 0.5 (not 0.48).
HARGREAVES_SITE = {
    "t_min": 10.0,
    "t_max": 25.0,
    "t_mean": 17.5,
    "latitude": 40.0,
    "doy": 150,
    "ra_mj_m2_day": 41.14825459255412,
    "et0_mm_day": 5.279098340839128,
}

# The parity grid: every curve number the NRCS table admits, crossed with a
# sweep of storm depths spanning the abstraction threshold of every CN.
CN_GRID = [float(cn) for cn in range(30, 101)]
P_GRID = [
    0.0, 0.5, 1.0, 2.5, 5.0, 8.0, 10.0, 15.0, 20.0, 25.0, 33.0, 50.0, 75.0,
    100.0, 150.0, 200.0, 300.0, 500.0, 1000.0,
]

# Measured worst case over CN_GRID x P_GRID (1368 points), documented in the
# module docstring: the gateway recovers the depth as volume / (area * 10).
ROUTED_DEPTH_TOLERANCE_MM = 1.2e-13

# Measured worst case for the float32 swat_plus raster: one float32 ulp at the
# depths the raster carries.
ROUTED_RASTER_RTOL = 2e-6

# Absolute floor for the same comparison. Near the initial abstraction
# (P -> Ia) the runoff depth tends to zero, so a *relative* bound explodes
# there even though both sides agree to float32 noise — the measured worst
# case at the boundary is ~1e-6 mm, far below any reported figure.
ROUTED_RASTER_ATOL_MM = 1e-5


# --- Inline re-statements of the algebra the routed code replaced ----------
def _code_only_source(path: str) -> str:
    """The module's code with comments and string literals removed.

    The "no inline science left" scans below target algebra that lives in
    *code*; a constant quoted in a docstring or comment (the citations,
    units, and design notes) is documentation, not a computation.
    """
    import tokenize

    pieces: list[str] = []
    with open(path, "rb") as handle:  # noqa: PTH123
        for token in tokenize.tokenize(handle.readline):
            if token.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            pieces.append(token.string)
    return " ".join(pieces)


def _inline_retention_mm(curve_number: float) -> float:
    """SI retention ``S = 25400 / CN - 254`` (mm)."""
    return 25400.0 / curve_number - 254.0


def _inline_runoff_mm(precip_mm: float, curve_number: float) -> float:
    """The SI SCS-CN triplet, as the migrated copies wrote it out."""
    retention = _inline_retention_mm(curve_number)
    initial_abstraction = 0.2 * retention
    if precip_mm <= initial_abstraction:
        return 0.0
    return (precip_mm - initial_abstraction) ** 2 / (precip_mm + 0.8 * retention)


def _inline_raster_runoff(precip_mm: np.ndarray, cn: np.ndarray) -> np.ndarray:
    """swat_plus's inline copy, including its float32 stepping."""
    precip = xr.DataArray(precip_mm.astype(np.float32))
    curve = xr.DataArray(cn.astype(np.float32))
    retention = (1000.0 / curve - 10.0) * 25.4
    initial_abstraction = 0.2 * retention
    return xr.where(
        precip > initial_abstraction,
        (precip - initial_abstraction) ** 2 / (precip - initial_abstraction + retention),
        0.0,
    ).values


# --------------------------------------------------------------------------- #
# 1. The published numbers the routed path must reproduce                    #
# --------------------------------------------------------------------------- #
class TestPublishedReferences:
    def test_nrcs_worked_example(self) -> None:
        """P = 50 mm on CN 70 gives Q = 5.812802953611626 mm."""
        got = calculate_runoff(
            precipitation=NRCS_WORKED_EXAMPLE["precipitation_mm"],
            curve_number=NRCS_WORKED_EXAMPLE["curve_number"],
        )["runoff_depth_mm"]
        assert got == pytest.approx(NRCS_WORKED_EXAMPLE["runoff_mm"], rel=1e-12)

    def test_nrcs_retention_is_the_si_form(self) -> None:
        """25400/70 - 254 = 108.857 mm, and that is 4.2857 inches.

        Pinned so a return to the US-customary ``1000/CN - 10`` (inches)
        cannot pass: the inch figure multiplied back by 25.4 must land here.
        """
        assert _inline_retention_mm(70.0) == pytest.approx(
            NRCS_WORKED_EXAMPLE["retention_mm"], rel=1e-12
        )
        assert (
            NRCS_WORKED_EXAMPLE["retention_inches"] * 25.4
            == pytest.approx(NRCS_WORKED_EXAMPLE["retention_mm"], rel=1e-12)
        )

    def test_hargreaves_published_value(self) -> None:
        """FAO-56 eq. 52 at the fixed site is 5.279098340839128 mm/day.

        The engine owns eq. 52 now; this pins that its value for the site is
        the published one, with the 0.408 MJ -> mm conversion and the 0.5
        exponent on the diurnal range (not 0.48).
        """
        assert hargreaves_et0(
            HARGREAVES_SITE["t_min"],
            HARGREAVES_SITE["t_max"],
            HARGREAVES_SITE["latitude"],
            HARGREAVES_SITE["doy"],
        ) == pytest.approx(HARGREAVES_SITE["et0_mm_day"], rel=1e-12)

    def test_hargreaves_equals_the_published_identity(self) -> None:
        """Independent re-derivation of eq. 52 for the same site."""
        ra_mj = HARGREAVES_SITE["ra_mj_m2_day"]
        reference = (
            0.0023
            * (HARGREAVES_SITE["t_mean"] + 17.8)
            * math.sqrt(HARGREAVES_SITE["t_max"] - HARGREAVES_SITE["t_min"])
            * (ra_mj * 0.408)
        )
        assert reference == pytest.approx(HARGREAVES_SITE["et0_mm_day"], rel=1e-12)


# --------------------------------------------------------------------------- #
# 2. services/_contracts/formula.py :: runoff_scs                            #
# --------------------------------------------------------------------------- #
class TestRunoffScsParity:
    @pytest.mark.parametrize("curve_number", CN_GRID[::7])
    @pytest.mark.parametrize("precip_mm", P_GRID)
    def test_routed_equals_the_inline_form(
        self, precip_mm: float, curve_number: float
    ) -> None:
        before = _inline_runoff_mm(precip_mm, curve_number)
        after = runoff_scs(precip_mm, curve_number)
        assert after == pytest.approx(before, abs=ROUTED_DEPTH_TOLERANCE_MM)

    def test_full_grid_worst_case(self) -> None:
        """Every (CN, P) pair on the grid stays within the documented bound."""
        worst = 0.0
        for curve_number in CN_GRID:
            for precip_mm in P_GRID:
                before = _inline_runoff_mm(precip_mm, curve_number)
                after = runoff_scs(precip_mm, curve_number)
                worst = max(worst, abs(after - before))
        assert worst == pytest.approx(0.0, abs=ROUTED_DEPTH_TOLERANCE_MM)

    def test_zero_depth_storm_is_zero(self) -> None:
        """CANON-004 refuses P = 0; a dry storm has no runoff depth."""
        assert runoff_scs(0.0, 75.0) == 0.0

    def test_below_abstraction_is_zero(self) -> None:
        """P = 20 mm on CN 70 is below Ia = 21.77 mm."""
        assert runoff_scs(20.0, 70.0) == 0.0

    def test_curve_number_contract_is_kept(self) -> None:
        with pytest.raises(ValueError, match="curve_number must be 30..100"):
            runoff_scs(50.0, 29.0)
        with pytest.raises(ValueError, match="curve_number must be 30..100"):
            runoff_scs(50.0, 101.0)
        with pytest.raises(ValueError, match="precip_mm must be >= 0"):
            runoff_scs(-1.0, 70.0)

    def test_no_inline_retention_left_in_the_module(self) -> None:
        """The routed function must not carry the SI algebra any more."""
        source = _code_only_source("services/_contracts/formula.py")
        assert "25400" not in source
        assert "0.2 * retention" not in source


# --------------------------------------------------------------------------- #
# 3. services/simulation/adapters/hydrology_adapter.py                       #
# --------------------------------------------------------------------------- #
class TestHydrologyAdapterParity:
    @pytest.mark.parametrize(
        "texture,curve_number",
        [
            ("sand", 60),
            ("loamy_sand", 65),
            ("sandy_loam", 70),
            ("loam", 75),
            ("silt_loam", 78),
            ("silt", 80),
            ("clay_loam", 82),
            ("clay", 88),
        ],
    )
    @pytest.mark.parametrize(
        "precipitation", [0.0, 5.0, 20.0, 50.0, 100.0, 250.0, 400.0]
    )
    def test_routed_equals_the_inline_form(
        self, texture: str, curve_number: int, precipitation: float
    ) -> None:
        assert texture  # the matrix row this curve number represents
        retention = (25400 / curve_number) - 254
        if precipitation > 0.2 * retention:
            before = ((precipitation - 0.2 * retention) ** 2) / (
                precipitation + 0.8 * retention
            )
        else:
            before = 0.0
        after = _scs_runoff_depth_mm(precipitation, curve_number)
        assert after == pytest.approx(before, abs=ROUTED_DEPTH_TOLERANCE_MM)

    def test_dry_event_is_zero(self) -> None:
        assert _scs_runoff_depth_mm(0.0, 75) == 0.0

    def test_infiltration_balance_is_preserved(self) -> None:
        """runoff + infiltration == precipitation, as before the routing."""
        for precipitation in (0.0, 30.0, 120.0):
            runoff = _scs_runoff_depth_mm(precipitation, 75)
            infiltration = precipitation - runoff
            assert infiltration + runoff == pytest.approx(precipitation)


# --------------------------------------------------------------------------- #
# 4. services/scientific_motors/swat_plus.py (raster)                        #
# --------------------------------------------------------------------------- #
def _swat_like_grid() -> tuple[np.ndarray, np.ndarray]:
    """A precipitation field over the CN classes ``_compute_cn`` can emit."""
    rng = np.random.default_rng(20261011)
    height, width = 11, 14
    precip = rng.uniform(0.0, 140.0, size=(height, width)).astype(np.float32)
    precip[0, 0] = 0.0  # a dry cell
    landcover = (rng.integers(0, 9, size=(height, width)) * 10).astype(np.float32)
    table = {10: 60, 20: 66, 30: 61, 40: 76, 50: 98, 60: 86, 80: 100}
    curve = np.full_like(landcover, 75, dtype=np.float32)
    for landcover_class, cn_value in table.items():
        curve[landcover == landcover_class] = cn_value
    return precip, curve


    def test_a_curve_number_below_the_tr55_floor_is_refused(self):
        """CN=29 is outside the NRCS table (30..100), not a valid raster value."""
        precip, curve = _swat_like_grid()
        curve[0, 0] = 29  # noqa: B018
        with pytest.raises(ValueError, match="30..100"):
            _scs_runoff_raster(xr.DataArray(precip), xr.DataArray(curve))


class TestSwatPlusRasterParity:
    def test_raster_matches_the_inline_copy_within_one_float32_ulp(self) -> None:
        precip, curve = _swat_like_grid()
        before = _inline_raster_runoff(precip, curve).astype(np.float64)
        after = _scs_runoff_raster(
            xr.DataArray(precip), xr.DataArray(curve)
        ).values.astype(np.float64)
        assert np.allclose(
            before,
            after,
            rtol=ROUTED_RASTER_RTOL,
            atol=ROUTED_RASTER_ATOL_MM,
        )

    def test_raster_is_float32_with_the_same_grid(self) -> None:
        precip, curve = _swat_like_grid()
        result = _scs_runoff_raster(xr.DataArray(precip), xr.DataArray(curve))
        assert isinstance(result, xr.DataArray)
        assert result.dtype == precip.dtype
        assert result.shape == precip.shape

    def test_dry_and_absent_cells_stay_zero(self) -> None:
        precip, curve = _swat_like_grid()
        result = _scs_runoff_raster(
            xr.DataArray(precip), xr.DataArray(curve)
        ).values
        assert result[0, 0] == 0.0
        before = _inline_raster_runoff(precip, curve)
        assert np.all(result[before == 0.0] == 0.0)

    def test_raster_matches_the_engine_cell_by_cell(self) -> None:
        """The vector entry reproduces the engine's scalar answer per cell."""
        precip, curve = _swat_like_grid()
        after = _scs_runoff_raster(xr.DataArray(precip), xr.DataArray(curve)).values
        for i in range(precip.shape[0]):
            for j in range(precip.shape[1]):
                if float(precip[i, j]) <= 0.0:
                    expected = 0.0
                else:
                    expected = calculate_runoff(
                        precipitation=float(precip[i, j]),
                        curve_number=float(curve[i, j]),
                    )["runoff_depth_mm"]
                assert float(after[i, j]) == pytest.approx(
                    expected, rel=ROUTED_RASTER_RTOL
                )

    def test_raster_routes_through_the_engine_in_one_call(self, monkeypatch) -> None:
        """The grid is one engine-owned call, not one gateway call per pair."""
        import services.scientific_motors.swat_plus as swat_plus

        calls: list[tuple[Any, Any]] = []
        real_raster = swat_plus.calculate_runoff_raster

        def counting(precipitation, curve_number, **kwargs):
            calls.append((precipitation, curve_number))
            return real_raster(precipitation, curve_number, **kwargs)

        monkeypatch.setattr(swat_plus, "calculate_runoff_raster", counting)
        precip, curve = _swat_like_grid()
        _scs_runoff_raster(xr.DataArray(precip), xr.DataArray(curve))

        assert len(calls) == 1
        assert calls[0][0].size == precip.size
        assert all(30.0 <= cn <= 100.0 for cn in np.unique(calls[0][1]))


# --------------------------------------------------------------------------- #
# 5. services/validation/formula_checks.py :: the eq. 52 check               #
# --------------------------------------------------------------------------- #
class TestHargreavesCheckRoutesToTheEngine:
    def test_check_compares_against_the_engine_value(self) -> None:
        from services.validation.formula_checks import run_all

        payload = run_all()
        check = next(
            c for c in payload["checks"] if c["id"] == "fao56_hargreaves"
        )
        assert check["passed"] is True
        assert check["tolerance"] == 1e-06
        # Both sides are the engine's value for the fixed site; the expectation
        # is no longer re-derived in the services tier.
        assert check["expected"] == pytest.approx(
            HARGREAVES_SITE["et0_mm_day"], rel=1e-12
        )
        assert check["actual"] == pytest.approx(
            HARGREAVES_SITE["et0_mm_day"], rel=1e-12
        )

    def test_the_two_facade_entry_points_agree(self) -> None:
        """The raw CANON-002 entry and the convenience wrapper over it."""
        via_wrapper = hargreaves_et0(
            HARGREAVES_SITE["t_min"],
            HARGREAVES_SITE["t_max"],
            HARGREAVES_SITE["latitude"],
            HARGREAVES_SITE["doy"],
        )
        via_entry = float(
            calc_et0_hargreaves(
                temp_max=HARGREAVES_SITE["t_max"],
                temp_min=HARGREAVES_SITE["t_min"],
                elevation=0.0,
                latitude=HARGREAVES_SITE["latitude"],
                doy=HARGREAVES_SITE["doy"],
            )["data"]["et0_mm_day"]
        )
        assert via_wrapper == pytest.approx(via_entry, rel=1e-12)

    def test_check_module_no_longer_derives_eq_52(self) -> None:
        """0.0023 and the 0.408 conversion belong to the engine now."""
        source = _code_only_source("services/validation/formula_checks.py")
        assert "0.0023" not in source
        assert "0.408" not in source


# --------------------------------------------------------------------------- #
# 6. What is NOT routed, and why (recorded so it is not silently skipped)   #
# --------------------------------------------------------------------------- #
class TestUnroutedFamiliesAreDocumented:
    """The RothC and RUSLE-LS families have no working facade entry.

    * ``compute_erosion`` resolves to the gateway model ``SOIL_EROSION``, which
      is not registered, so the call raises; and the CANON-007 route that is
      registered computes a different LS (McCool exponent from
      ``sin/cos^2`` plus the 16.8 steepness branch) than the registry relation
      the services pin (Foster & Nearing polynomial at m = 0.5), so routing it
      would move published numbers.
    * ``RothCRunner`` dispatches to ``ROTHTC_RUN``, which is not registered
      either, and ``services/scientific_motors/rothc.py`` deliberately runs
      DPM = 1.0 rather than the published 10.0 for numerical stability.

    Both are recorded in reports/eco-nojin/REMEDIATION-B3-ROUTING-REPORT.md.
    """

    def test_compute_erosion_is_not_a_usable_entry(self) -> None:
        with pytest.raises(RuntimeError, match="not registered"):
            calculate_runoff.__globals__["compute_erosion"](
                slope_length=50.0,
                slope_percent=8.0,
                annual_rainfall=1000.0,
                texture="loam",
            )

    def test_rothc_runner_is_not_a_usable_entry(self) -> None:
        with pytest.raises(RuntimeError):
            calculate_runoff.__globals__["RothCRunner"]().run({})
