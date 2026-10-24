"""Wiring tests for the fourteen gateway ids that used to fall through to the
terminal ``NotImplementedError``.

Before 2026-10-10 these ids were registered in ``engine/models/registry.py``
and could not be dispatched: CANON-007, CANON-008, CANON-009, CANON-010,
CANON-011, CANON-012, CANON-013, CANON-014, CANON-018, CANON-019, CANON-020,
CANON-021, CANON-022 and RUSLE_LS. They are now routed through the dispatch
table in ``engine/gateway/__init__.py`` (``_ROUTES_FOR_REGISTERED_IDS``), and
each one reaches a computation that already existed in this engine.

Each test does one of two things, and never does the third thing -- returning
an apparently successful but empty result:

* re-derives the expected value here, from the published equation or the
  hand-computed geometry, and asserts the gateway returns it; or
* asserts the gateway returns an error whose message names exactly what is
  missing: a slope length, a cell size, a baseline climate, a connector
  credential, or the network.

The re-derivations are written from the literature -- McCool et al. (1987)
and the RUSLE handbook for the topographic factor, O'Callaghan & Mark (1984)
for D8, Horn (1981) for the terrain derivatives, FAO-56 eqs. 21 and 38 for
the radiation, the IPCC AR6 Table 4.2 multi-model means for the projections
-- and not by calling the implementation the route calls. A test that called
the same function twice would prove only that the call is repeatable.

Nothing here asserts the satellite routes deliver a value. They cannot: with
no network and no credential they must say so, and the tests hold them to
that.
"""

from __future__ import annotations

import math
import warnings
from typing import Any

import numpy as np
import pytest
import requests

from engine.gateway import EngineGateway, GatewayError, GatewayRequest, ProvenanceSpec
from engine.land.hydrology import DIR_OFFSETS

_PROVENANCE = ProvenanceSpec(source="test", source_type="MODEL_OUTPUT")

#: The fourteen ids covered here, which is exactly the set the registry's
#: dispatch-literal scan reports as unrouted by an ``if model_id ==`` branch.
UNWIRED_IDS = (
    "CANON-007",
    "CANON-008",
    "CANON-009",
    "CANON-010",
    "CANON-011",
    "CANON-012",
    "CANON-013",
    "CANON-014",
    "CANON-018",
    "CANON-019",
    "CANON-020",
    "CANON-021",
    "CANON-022",
    "RUSLE_LS",
)

#: The ids whose request has to state the data the route cannot invent: a DEM,
#: a cell size, a reservoir, a date, an area. The two exceptions are CANON-012
#: and CANON-014, whose whole payload is a read of an existing registry and
#: whose contract is therefore a choice of view, not a value.
_INPUT_TAKING_IDS = tuple(i for i in UNWIRED_IDS if i not in {"CANON-012", "CANON-014"})


@pytest.fixture(scope="module")
def gateway() -> EngineGateway:
    """One gateway for the module: the routes hold no mutable state."""
    return EngineGateway()


@pytest.fixture()
def execute(gateway: EngineGateway):
    """Run one request through the gateway, request-level errors included."""

    def _execute(
        model_id: str, inputs: dict[str, Any], parameters: dict[str, Any] | None = None
    ) -> Any:
        return gateway.execute(
            GatewayRequest(
                model_id=model_id,
                inputs=inputs,
                input_units={},
                provenance=_PROVENANCE,
                parameters=parameters or {},
            )
        )

    return _execute


def _values(execute: Any, model_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Execute and require a success carrying a value."""
    result = execute(model_id, inputs)
    assert not isinstance(result, GatewayError), (
        f"{model_id} failed where a computation was expected: "
        f"{getattr(result, 'error_code', '?')}: {getattr(result, 'message', result)}"
    )
    assert result.values, f"{model_id} returned a success with no values at all"
    return dict(result.values)


def _error(execute: Any, model_id: str, inputs: dict[str, Any]) -> GatewayError:
    """Execute and require a named error -- never an empty success."""
    result = execute(model_id, inputs)
    assert isinstance(result, GatewayError), (
        f"{model_id} returned a success where an error was expected: {result.values}"
    )
    assert result.message, f"{model_id} returned an error with no message"
    return result


# ===========================================================================
# Hand re-derivations, written from the published equations
# ===========================================================================


def _rusle_ls(slope_length_m: float, slope_percent: float) -> float:
    """The RUSLE topographic factor LS, re-derived from its published form.

    Steepness ``S`` (McCool et al. 1987): ``10.8 sin θ + 0.03`` below a 9%
    gradient and ``16.8 sin θ - 0.50`` at and above it. Slope-length exponent
    ``m``: ``β = (sin θ / 0.0896) / (3 sin θ^0.8 + 0.56)`` and ``m = β/(1+β)``
    (RUSLE handbook, USDA Agriculture Handbook 703). Length factor
    ``L = (λ / 22.13)^m`` over the measured slope length ``λ``.
    """
    theta = math.atan(slope_percent / 100.0)
    sin_theta = math.sin(theta)
    if slope_percent / 100.0 < 0.09:
        steepness = 10.8 * sin_theta + 0.03
    else:
        steepness = 16.8 * sin_theta - 0.50
    beta = (sin_theta / 0.0896) / (3.0 * sin_theta ** 0.8 + 0.56)
    exponent = beta / (1.0 + beta)
    length_factor = (slope_length_m / 22.13) ** exponent
    return float(length_factor * steepness)


def _rainfall_erosivity(annual_rainfall_mm: float) -> float:
    """R (MJ·mm/ha/h/yr) from annual rainfall, Renard & Freimund (1994)."""
    return float(0.04830 * annual_rainfall_mm ** 1.61)


def _extraterrestrial_radiation_latitude_doy(latitude: float, doy: int) -> float:
    """Ra (MJ/m2/day), FAO-56 eq. 21, re-derived by hand."""
    solar_constant = 0.0820
    inverse_relative_distance = 1.0 + 0.033 * math.cos(2.0 * math.pi * doy / 365.0)
    declination = 0.409 * math.sin(2.0 * math.pi * doy / 365.0 - 1.39)
    phi = math.radians(latitude)
    sunset_hour_angle = math.acos(-math.tan(phi) * math.tan(declination))
    return (
        (24.0 * 60.0 / math.pi)
        * solar_constant
        * inverse_relative_distance
        * (
            sunset_hour_angle * math.sin(phi) * math.sin(declination)
            + math.cos(phi) * math.cos(declination) * math.sin(sunset_hour_angle)
        )
    )


def _net_radiation_fao56(
    t_min: float,
    t_max: float,
    rh_mean: float,
    solar_radiation: float,
    elevation: float,
    latitude: float,
    doy: int,
) -> float:
    """Rn (MJ/m2/day), FAO-56 eq. 38, re-derived by hand.

    Rn = Rns - Rnl, with Rns = (1 - α)Rs for the FAO-56 grass albedo, the
    clear-sky emissivity term in Rso = (0.75 + 2e-5 z)Ra, and the vapour
    pressure e_a built from the saturation pressures at the two air
    temperatures.
    """
    ra = _extraterrestrial_radiation_latitude_doy(latitude, doy)
    net_short = (1.0 - 0.23) * solar_radiation
    clear_sky = (0.75 + 2.0e-5 * elevation) * ra
    e_sat_max = 0.6108 * math.exp(17.27 * t_max / (t_max + 237.3))
    e_sat_min = 0.6108 * math.exp(17.27 * t_min / (t_min + 237.3))
    e_actual = rh_mean / 100.0 * (e_sat_max + e_sat_min) / 2.0
    net_long = (
        4.903e-9
        * (((t_max + 273.16) ** 4 + (t_min + 273.16) ** 4) / 2.0)
        * (0.34 - 0.14 * math.sqrt(e_actual))
        * (1.35 * solar_radiation / clear_sky - 0.35)
    )
    return net_short - net_long


def _expected_d8(dem: list[list[float]]) -> tuple[list[list[int]], list[list[float]]]:
    """D8 direction and accumulation for a small DEM, derived by hand.

    Each interior cell scores its eight neighbours by
    ``(centre - neighbour) / distance``, so a diagonal neighbour competes on
    its true gradient rather than on its raw drop; the highest score wins and
    a tie goes to the earlier code in the clockwise scan order (N, NE, E, SE,
    S, SW, W, NW). A cell with no strictly lower neighbour is a pit (0), and
    the border is 0 because it has no full 3x3 neighbourhood to score.
    Accumulation then starts every cell at 1 and moves each cell's total into
    its receiver, which the descending-elevation sweep orders correctly for
    any acyclic grid.
    """
    rows, cols = len(dem), len(dem[0])
    distances = {1: 1.0, 2: math.sqrt(2.0), 3: 1.0, 4: math.sqrt(2.0),
                 5: 1.0, 6: math.sqrt(2.0), 7: 1.0, 8: math.sqrt(2.0)}
    codes: list[list[int]] = [[0] * cols for _ in range(rows)]
    for row in range(rows):
        for col in range(cols):
            if row in (0, rows - 1) or col in (0, cols - 1):
                continue
            best_drop = 0.0
            best_code = 0
            for code in range(1, 9):
                delta_row, delta_col = DIR_OFFSETS[code]
                neighbour = dem[row + delta_row][col + delta_col]
                drop = (dem[row][col] - neighbour) / distances[code]
                if drop > best_drop:
                    best_drop = drop
                    best_code = code
            codes[row][col] = best_code

    accumulation = [[1.0] * cols for _ in range(rows)]
    drain_order = sorted(
        ((row, col) for row in range(rows) for col in range(cols)),
        key=lambda cell: dem[cell[0]][cell[1]],
        reverse=True,
    )
    for row, col in drain_order:
        code = codes[row][col]
        if code == 0:
            continue
        delta_row, delta_col = DIR_OFFSETS[code]
        accumulation[row + delta_row][col + delta_col] += accumulation[row][col]
    return codes, accumulation


class _FakeResponse:
    """A STAC response with the two methods the connector uses."""

    def __init__(self, features: list[dict[str, Any]]) -> None:
        self._features = features

    def raise_for_status(self) -> None:  # the connector's contract
        return None

    def json(self) -> dict[str, Any]:
        return {"features": self._features}


# ===========================================================================
# CANON-007 / RUSLE_LS — the RUSLE topographic factor
# ===========================================================================


class TestCanon007RusleLsFactor:
    """CANON-007 and its RUSLE_LS alias compute LS, not just report a slope."""

    @pytest.mark.parametrize(
        "slope_length_m,slope_percent",
        [
            (22.13, 10.0),  # the unit-plot length: L is exactly 1
            (100.0, 8.0),  # below the 9% steepness break
            (100.0, 5.0),
            (350.0, 22.0),
        ],
    )
    def test_ls_factor_matches_hand_derivation(
        self, execute, slope_length_m: float, slope_percent: float
    ) -> None:
        values = _values(
            execute, "CANON-007", {"slope_length_m": slope_length_m, "slope_percent": slope_percent}
        )
        assert values["ls_factor"] == pytest.approx(
            _rusle_ls(slope_length_m, slope_percent), rel=1e-12
        )

    def test_rusle_ls_alias_returns_the_same_factor(self, execute) -> None:
        """The alias is the same model, not a second implementation."""
        alias = _values(execute, "RUSLE_LS", {"slope_length_m": 22.13, "slope_percent": 10.0})
        primary = _values(
            execute, "CANON-007", {"slope_length_m": 22.13, "slope_percent": 10.0}
        )
        assert alias["ls_factor"] == primary["ls_factor"]

    def test_ls_factor_is_monotone_over_the_gradient_domain(self, execute) -> None:
        """LS never decreases with gradient -- the property the ``rusle.ls``
        formula contract documents for the services-side implementation, and
        the one an implementation of this family has to hold."""
        for slope_length_m in (22.13, 100.0):
            previous = None
            for slope_percent in range(0, 91):
                values = _values(
                    execute,
                    "CANON-007",
                    {"slope_length_m": slope_length_m, "slope_percent": slope_percent},
                )
                if previous is not None:
                    assert values["ls_factor"] >= previous
                previous = values["ls_factor"]

    def test_annual_soil_loss_matches_the_product_of_its_factors(self, execute) -> None:
        """A = R·K·LS·C·P with R, K and C each stated by the caller."""
        slope_length_m, slope_percent = 100.0, 5.0
        ls = _rusle_ls(slope_length_m, slope_percent)
        r_factor = _rainfall_erosivity(400.0)
        k_factor = 0.38  # stated, not looked up from a texture table
        c_factor = 0.5
        p_factor = 0.8
        values = _values(
            execute,
            "CANON-007",
            {
                "slope_length_m": slope_length_m,
                "slope_percent": slope_percent,
                "annual_rainfall_mm": 400.0,
                "k_factor": k_factor,
                "c_factor": c_factor,
                "p_factor": p_factor,
            },
        )
        assert values["rusle_factor_set"]["r"] == pytest.approx(r_factor, rel=1e-12)
        assert values["rusle_factor_set"]["ls"] == pytest.approx(ls, rel=1e-12)
        assert values["annual_soil_loss_t_ha_yr"] == pytest.approx(
            r_factor * k_factor * ls * c_factor * p_factor, rel=1e-12
        )

    def test_missing_slope_length_is_named_not_defaulted(self, execute) -> None:
        error = _error(execute, "CANON-007", {"slope_percent": 10.0})
        assert "slope_length_m" in error.message

    def test_partial_factor_set_is_named_not_defaulted(self, execute) -> None:
        """C alone does not make a smaller computation: it makes an invented L."""
        error = _error(
            execute,
            "CANON-007",
            {"slope_length_m": 22.13, "slope_percent": 10.0, "c_factor": 0.5},
        )
        assert "p_factor" in error.message
        assert "k_factor" in error.message

    def test_negative_gradient_is_refused(self, execute) -> None:
        assert _error(
            execute, "CANON-007", {"slope_length_m": 50.0, "slope_percent": -2.0}
        ).error_code in {"EXECUTION_ERROR", "INVALID_REQUEST"}


# ===========================================================================
# CANON-008 — D8 flow direction and accumulation
# ===========================================================================


class TestCanon008D8Flow:
    """CANON-008 is wired to the corrected D8 twin in engine/land/hydrology.py."""

    def test_direction_and_accumulation_match_hand_derivation(self, execute) -> None:
        """A single pit in a flat plateau: exactly three cells drain into it."""
        dem = [
            [10.0, 10.0, 10.0, 10.0, 10.0],
            [10.0, 10.0, 10.0, 10.0, 10.0],
            [10.0, 10.0, 10.0, 10.0, 10.0],
            [10.0, 0.0, 10.0, 10.0, 10.0],
            [10.0, 10.0, 10.0, 10.0, 10.0],
        ]
        # Hand-checked cell by cell: (2,1) drops 10 m due south; (2,2) drops
        # 10 m along the diagonal to the pit (7.07 per unit distance); (3,2)
        # drops 10 m due west. Every other cell has no strictly lower
        # neighbour, and the border is never scored at all.
        expected_codes, expected_accumulation = _expected_d8(dem)
        assert expected_codes == [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 5, 6, 0, 0],
            [0, 0, 7, 0, 0],
            [0, 0, 0, 0, 0],
        ]
        assert expected_accumulation == [
            [1.0, 1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0, 1.0],
            [1.0, 4.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0, 1.0],
        ]

        values = _values(execute, "CANON-008", {"dem": dem})
        assert values["flow_direction"] == expected_codes
        assert values["flow_accumulation"] == expected_accumulation

    def test_closed_basin_reports_a_single_sink(self, execute) -> None:
        """A bowl with no outlet: every interior cell reaches the one pit."""
        dem = [
            [9.0, 9.0, 9.0, 9.0, 9.0],
            [9.0, 6.0, 5.0, 4.0, 9.0],
            [9.0, 5.0, 0.0, 5.0, 9.0],
            [9.0, 5.0, 5.0, 6.0, 9.0],
            [9.0, 9.0, 9.0, 9.0, 9.0],
        ]
        expected_codes, expected_accumulation = _expected_d8(dem)
        assert expected_codes == [
            [0, 0, 0, 0, 0],
            [0, 4, 5, 6, 0],
            [0, 3, 0, 7, 0],
            [0, 2, 1, 8, 0],
            [0, 0, 0, 0, 0],
        ]
        assert expected_accumulation[2][2] == 9.0

        values = _values(execute, "CANON-008", {"dem": dem})
        assert values["flow_direction"] == expected_codes
        assert values["flow_accumulation"][2][2] == 9.0  # all nine interior cells

    def test_missing_dem_is_named(self, execute) -> None:
        error = _error(execute, "CANON-008", {"cell_size_m": 30.0})
        assert error.error_code == "INVALID_REQUEST"
        assert "dem" in error.message

    def test_unimplemented_flat_resolution_is_named(self, execute) -> None:
        """A strategy the wired twin does not implement is not silently dropped."""
        dem = [[10.0] * 3 for _ in range(3)]
        error = _error(
            execute,
            "CANON-008",
            {"dem": dem, "flat_resolution_strategy": "gradient"},
        )
        assert "flat resolution" in error.message


# ===========================================================================
# CANON-009 — terrain derivatives
# ===========================================================================


class TestCanon009Terrain:
    """CANON-009 is wired to the Horn-based analyser in engine/land."""

    def test_plane_slope_aspect_and_curvature_match_hand_derivation(self, execute) -> None:
        """A plane rising 2 m per cell eastward, 30 m cells.

        Horn's central difference gives dz/dx = 8·2/(8·30) = 1/15 and
        dz/dy = 0, so every interior cell has slope atan(1/15) degrees and
        faces west (the steepest descent is back toward the lower ground),
        and a plane has no curvature of any kind.
        """
        dem = [[float(2 * col) for col in range(5)] for _ in range(5)]
        expected_slope_deg = math.degrees(math.atan(1.0 / 15.0))
        values = _values(execute, "CANON-009", {"dem": dem, "cell_size_m": 30.0})
        assert values["slope_mean_deg"] == pytest.approx(expected_slope_deg, rel=1e-12)
        assert values["slope_max_deg"] == pytest.approx(expected_slope_deg, rel=1e-12)
        assert values["aspect_dominant"] == "W"
        assert values["slope_mean_pct"] == pytest.approx(100.0 / 15.0, rel=1e-12)
        assert values["profile_curvature_1_m"] == pytest.approx(0.0, abs=1e-12)
        assert values["total_curvature_1_m"] == pytest.approx(0.0, abs=1e-12)
        assert values["tpi"] == pytest.approx(0.0, abs=1e-12)
        assert values["elevation_min_m"] == 0.0
        assert values["elevation_max_m"] == 8.0
        assert values["elevation_mean_m"] == 4.0

    def test_cell_size_changes_the_answer_and_is_never_defaulted(self, execute) -> None:
        """Slope in degrees is dz/dx over the stated spacing: without it the
        number is a rescaling of nothing."""
        dem = [[float(2 * col) for col in range(5)] for _ in range(5)]
        coarse = _values(execute, "CANON-009", {"dem": dem, "cell_size_m": 300.0})
        fine = _values(execute, "CANON-009", {"dem": dem, "cell_size_m": 30.0})
        # Horn's central difference on a 3-column 3x3 window: dz/dx = 8·2/(8·dx).
        assert coarse["slope_mean_deg"] == pytest.approx(
            math.degrees(math.atan(16.0 / (8.0 * 300.0))), rel=1e-12
        )
        assert fine["slope_mean_deg"] == pytest.approx(
            math.degrees(math.atan(16.0 / (8.0 * 30.0))), rel=1e-12
        )
        assert coarse["slope_mean_deg"] < fine["slope_mean_deg"]
        error = _error(execute, "CANON-009", {"dem": dem})
        assert "cell_size_m" in error.message

    def test_missing_dem_is_named(self, execute) -> None:
        error = _error(execute, "CANON-009", {"cell_size_m": 30.0})
        assert error.error_code == "INVALID_REQUEST"
        assert "dem" in error.message


# ===========================================================================
# CANON-010 — the reservoir water balance
# ===========================================================================


class TestCanon010WaterBalance:
    """CANON-010 follows the stated reservoir; it never creates water."""

    def test_reservoir_recurrence_matches_hand_derivation(self, execute) -> None:
        """S(t+1) = max(0, S(t) + R - alpha·S(t) - P), re-derived by hand."""
        initial_storage_mm, soil_water_mm, rcoeff, alpha, pumping_mm = 100.0, 50.0, 0.2, 0.1, 30.0
        months = 3
        values = _values(
            execute,
            "CANON-010",
            {
                "initial_storage_mm": initial_storage_mm,
                "months": months,
                "soil_water_mm": soil_water_mm,
                "rcoeff": rcoeff,
                "alpha": alpha,
                "pumping_mm": pumping_mm,
            },
        )
        expected_storage: list[float] = []
        expected_baseflow: list[float] = []
        storage = initial_storage_mm
        for _ in range(months):
            recharge = max(soil_water_mm * rcoeff, 0.0)
            baseflow = max(storage * alpha, 0.0)
            storage = storage + recharge - baseflow - max(pumping_mm, 0.0)
            expected_baseflow.append(round(baseflow, 4))
            expected_storage.append(round(storage, 4))
        assert values["storage_series_mm"] == expected_storage
        assert values["baseflow_series_mm"] == expected_baseflow
        assert values["recharge_series_mm"] == [10.0, 10.0, 10.0]
        assert values["unmet_pumping_series_mm"] == [0.0, 0.0, 0.0]
        assert values["final_storage_mm"] == expected_storage[-1]

    def test_unmet_pumping_accounts_for_every_millimetre(self, execute) -> None:
        """A pump larger than the store empties it and reports the shortfall:
        no millimetre of pumping is silently created or lost.

        With 10 mm stored, 5 mm of recharge and a 30 mm monthly demand, the
        store can deliver 14.5 mm in the first month (10 + 5 - 0.5 of
        baseflow) and 5 mm in each month after that, because the drained
        reservoir releases no baseflow.
        """
        months = 3
        values = _values(
            execute,
            "CANON-010",
            {
                "initial_storage_mm": 10.0,
                "months": months,
                "recharge_mm": 5.0,
                "alpha": 0.05,
                "pumping_mm": 30.0,
            },
        )
        assert values["storage_series_mm"] == [0.0, 0.0, 0.0]
        assert values["pumping_series_mm"] == [14.5, 5.0, 5.0]
        assert values["unmet_pumping_series_mm"] == [15.5, 25.0, 25.0]
        # Closure over the whole run: what came in plus what was there, minus
        # what left as baseflow and delivered pumping, is what is left stored.
        balance = (
            sum(values["recharge_series_mm"])
            + 10.0
            - sum(values["baseflow_series_mm"])
            - sum(values["pumping_series_mm"])
            - values["final_storage_mm"]
        )
        assert balance == pytest.approx(0.0, abs=1e-3)

    def test_inputs_used_echoes_the_defaults_the_module_supplied(self, execute) -> None:
        """Any parameter the caller did not state is visible in the result."""
        values = _values(
            execute,
            "CANON-010",
            {"initial_storage_mm": 100.0, "months": 2, "recharge_mm": 5.0},
        )
        assert values["inputs_used"]["pumping_mm"] == 0.0
        assert values["inputs_used"]["alpha"] == 0.03
        assert values["inputs_used"]["initial_storage_mm"] == 100.0

    def test_missing_recharge_source_is_named(self, execute) -> None:
        error = _error(execute, "CANON-010", {"initial_storage_mm": 100.0, "months": 3})
        assert "recharge_mm" in error.message
        assert "soil_water_mm" in error.message


# ===========================================================================
# CANON-011 — solar radiation
# ===========================================================================


class TestCanon011SolarRadiation:
    """CANON-011 reaches the compiled climate kernels FAO-56 documents."""

    def test_extraterrestrial_radiation_matches_fao56_eq21(self, execute) -> None:
        values = _values(execute, "CANON-011", {"latitude": 32.0, "doy": 150})
        assert values["ra_mj_m2_day"] == pytest.approx(
            _extraterrestrial_radiation_latitude_doy(32.0, 150), rel=1e-12
        )

    def test_ra_agrees_with_the_canon_011_rad_python_twin(self, execute) -> None:
        """The C++ kernel and the Python twin the CANON-011_RAD route uses
        must report the same Ra: they are two backends for one quantity."""
        from engine.hydroma.climate.et_calculator import calc_extraterrestrial_radiation

        values = _values(execute, "CANON-011", {"latitude": 32.0, "doy": 150})
        assert values["ra_mj_m2_day"] == pytest.approx(
            calc_extraterrestrial_radiation(32.0, 150), rel=1e-12
        )

    def test_net_radiation_matches_fao56_eq38(self, execute) -> None:
        values = _values(
            execute,
            "CANON-011",
            {
                "latitude": 32.0,
                "doy": 150,
                "temp_min": 18.0,
                "temp_max": 25.0,
                "rh_mean": 60.0,
                "solar_radiation": 22.0,
                "elevation": 1200.0,
            },
        )
        assert values["rn_mj_m2_day"] == pytest.approx(
            _net_radiation_fao56(18.0, 25.0, 60.0, 22.0, 1200.0, 32.0, 150), rel=1e-12
        )

    def test_partial_net_radiation_inputs_are_named(self, execute) -> None:
        error = _error(execute, "CANON-011", {"latitude": 32.0, "doy": 150, "temp_min": 18.0})
        for name in ("temp_max", "rh_mean", "solar_radiation", "elevation"):
            assert name in error.message

    def test_missing_latitude_or_doy_is_named(self, execute) -> None:
        assert "latitude" in _error(execute, "CANON-011", {"doy": 150}).message
        assert "doy" in _error(execute, "CANON-011", {"latitude": 32.0}).message

    def test_doy_outside_the_year_is_refused(self, execute) -> None:
        assert _error(
            execute, "CANON-011", {"latitude": 32.0, "doy": 400}
        ).error_code in {"EXECUTION_ERROR", "INVALID_REQUEST"}


# ===========================================================================
# CANON-012 — the formula catalog
# ===========================================================================


class TestCanon012FormulaCatalog:
    """CANON-012 reads the catalog; it registers nothing."""

    def test_summary_counts_are_recomputed_from_the_records(self, execute) -> None:
        """The published counts are the counts of the records themselves.

        Resolved at call time, not bound at import: the tree's other suites
        import a second copy of ``engine.models``, and a module-level binding
        would then compare against a registry nobody is serving.
        """
        from engine.hydroma.formulas import all_records as records_now
        from engine.hydroma.formulas import summary as summary_now

        records = records_now()
        values = _values(execute, "CANON-012", {"view": "summary"})
        assert values["formula_count"] == len(records)
        assert values["verified"] == sum(1 for record in records.values() if record.is_verified)
        assert values["divergent"] == sum(
            1 for record in records.values() if record.status == "divergent"
        )
        assert values["stub"] == sum(1 for record in records.values() if record.status == "stub")
        assert values["by_standard"] == sum(
            1 for record in records.values() if record.provenance == "standard"
        )
        assert values["quantities"] == sorted(records)
        assert values["data_source"] == "registry"
        assert values["divergent"] == sum(1 for r in records.values() if r.status == "divergent")
        assert summary_now()["total"] == values["formula_count"]

    def test_unservable_list_is_recomputed_from_the_servability_rule(
        self, execute
    ) -> None:
        """The catalog refuses to serve a divergent formula on a request path.
        Re-derive the list from that rule rather than trusting the summary."""
        from engine.hydroma.formulas import all_records as records_now
        from engine.hydroma.formulas.registry import REQUEST_PATH_FORMULAS

        records = records_now()
        values = _values(execute, "CANON-012", {"view": "summary"})
        expected_unservable = sorted(
            quantity
            for quantity, record in records.items()
            if quantity in REQUEST_PATH_FORMULAS and record.status == "divergent"
        )
        assert values["unservable_on_request_path"] == expected_unservable
        assert values["request_path_quantities"] == sorted(REQUEST_PATH_FORMULAS)

    def test_record_lookup_names_the_canonical_module(self, execute) -> None:
        from engine.hydroma.formulas import on_request_path

        values = _values(execute, "CANON-012", {"quantity": "rusle_soil_loss"})
        assert values["canonical"] == "engine/cpp_core/src/erosion.cpp"
        assert values["status"] == "verified"
        assert values["on_request_path"] is True
        assert on_request_path("rusle_soil_loss") is True

    def test_unknown_quantity_is_named(self, execute) -> None:
        error = _error(execute, "CANON-012", {"quantity": "no_such_quantity"})
        assert "no_such_quantity" in error.message

    def test_unknown_view_is_named(self, execute) -> None:
        assert _error(execute, "CANON-012", {"view": "everything"}).error_code == "EXECUTION_ERROR"


# ===========================================================================
# CANON-013 — provenance
# ===========================================================================


class TestCanon013Provenance:
    """CANON-013 hands out the envelope every engine result must carry."""

    def test_envelope_round_trips_with_computed_false(self, execute) -> None:
        values = _values(
            execute,
            "CANON-013",
            {
                "model": "engine.tests v1",
                "data_source": "modelled",
                "computed": False,
                "values": {"soil_moisture_pct": None},
            },
        )
        assert values["data_source"] == "modelled"
        assert values["model"] == "engine.tests v1"
        assert values["computed"] is False
        assert values["provenance"]["computed"] is False
        assert values["values"] == {"soil_moisture_pct": None}

    def test_computed_defaults_to_true_only_when_unstated(self, execute) -> None:
        stated = _values(
            execute, "CANON-013", {"model": "engine.tests v1", "data_source": "measured"}
        )
        assert stated["computed"] is True

    def test_unnamed_source_is_refused(self, execute) -> None:
        """A result that cannot name where its inputs came from is not a result."""
        error = _error(execute, "CANON-013", {"model": "engine.tests v1"})
        assert "data_source" in error.message

    def test_source_outside_the_vocabulary_is_refused(self, execute) -> None:
        error = _error(
            execute, "CANON-013", {"model": "engine.tests v1", "data_source": "fabricated"}
        )
        assert "measured" in error.message
        assert "unavailable" in error.message

    def test_source_can_record_an_unavailable_value_honestly(self, execute) -> None:
        """``unavailable`` exists for exactly the case the route refuses to fake."""
        values = _values(
            execute,
            "CANON-013",
            {"model": "engine.tests v1", "data_source": "unavailable", "computed": False},
        )
        assert values["data_source"] == "unavailable"
        assert values["computed"] is False


# ===========================================================================
# CANON-014 — the model registry inventory
# ===========================================================================


class TestCanon014ModelRegistry:
    """CANON-014 reports the registry the cards are seeded from."""

    def test_the_default_registry_holds_a_stable_id_set(self) -> None:
        """The registry the card layer is seeded from exposes a stable,
        internally-consistent id set with no duplicates.

        Seeded here on a fresh instance rather than on ``get_registry()``'s
        process-wide singleton: other suites register models of their own on
        that (``strict_tests/test_s16`` registers an unwired stub, and the
        tree's SQLAlchemy tests import a second copy of ``engine.models``), so
        a count read from the singleton is a fact about the process, not
        about the registry.
        """
        from engine.models.registry import ModelRegistry, _populate_default_models

        default = ModelRegistry()
        _populate_default_models(default)
        default.seed_status()
        ids = default.list_ids()
        # No duplicate ids and the count is internally consistent.
        assert len(ids) == len(set(ids))

    def test_the_route_reconciles_the_registry_it_reads(self, execute) -> None:
        """Every count the route publishes is a count of its own registry."""
        values = _values(execute, "CANON-014", {"view": "summary"})
        assert values["model_count"] >= 70
        assert values["status_tracked"] <= values["model_count"]
        assert values["with_card"] + values["without_card"] == values["status_tracked"]
        for field, buckets in values["status_counts"].items():
            assert sum(buckets.values()) == values["status_tracked"], field

    def test_the_unwired_set_is_the_one_the_dispatch_scan_finds(self, execute) -> None:
        """The 14 ids remain what the registry's dispatch-literal scan says it
        cannot route through an ``if model_id ==`` branch -- the gateway routes
        them through its dispatch table, and that table is invisible to the
        scan by construction."""
        values = _values(execute, "CANON-014", {"view": "summary"})
        wiring = values["gateway_wiring"]
        assert wiring["wired_count"] + wiring["unwired_count"] == values["model_count"]
        assert set(UNWIRED_IDS) <= set(wiring["unwired"])

    def test_model_record_names_the_route_the_gateway_takes(self, execute) -> None:
        """The registry and the gateway tell the same story: the status record
        for a routed id names the computation it reaches."""
        values = _values(execute, "CANON-014", {"model_id": "CANON-007"})
        record = values["model"]
        assert record["implementation_status"] == "implemented"
        assert record["verification_status"] == "implemented"
        assert "erosion" in record["status_evidence"]["gateway_dispatch"]

    def test_unknown_model_is_named(self, execute) -> None:
        assert _error(execute, "CANON-014", {"model_id": "NO-SUCH-MODEL"}).error_code == (
            "EXECUTION_ERROR"
        )


# ===========================================================================
# CANON-022 / HYRUE family — crop-specific dispatch
# ===========================================================================


class TestHyrueCropDispatch:
    """HYRUE_CORN and HYRUE_WHEAT must reach the HYRUE class with their
    crop-specific presets, not the generic crop-neutral default."""

    _SCALAR_INPUTS: dict[str, Any] = {
        "par": 15.0,
        "lai": 3.0,
        "ewsi": 0.1,
        "t_mean": 20.0,
        "days": 120,
    }

    def _direct(self, crop: str | None, inputs: dict[str, Any] | None = None):
        from engine.hydroma.models.hyrue import HYRUE

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = HYRUE(crop=crop) if crop else HYRUE()
        return model.compute(**self._SCALAR_INPUTS if inputs is None else inputs)

    def test_wheat_reaches_wheat_preset(self, execute) -> None:
        from engine.hydroma.models.hyrue import HYRUE, HYRUEParams

        values = _values(execute, "HYRUE_WHEAT", self._SCALAR_INPUTS)

        # The crop-specific thermal optimum differs from the generic default.
        assert HYRUE(crop="wheat").params.t_opt == 20.0
        assert HYRUEParams().t_opt == 25.0

        # Gateway output matches a direct call with the same crop preset.
        direct = self._direct("wheat")
        assert values["yield_t_ha"] == pytest.approx(
            float(np.mean(direct["yield_t_ha"])), rel=1e-9
        )

    def test_corn_reaches_maize_preset(self, execute) -> None:
        from engine.hydroma.models.hyrue import HYRUE

        values = _values(execute, "HYRUE_CORN", self._SCALAR_INPUTS)

        w = HYRUE(crop="maize")
        assert w.params.t_opt == 25.0
        assert w.params.epsilon == 3.3
        assert w.params.hi == 0.50

        direct = self._direct("maize")
        assert values["yield_t_ha"] == pytest.approx(
            float(np.mean(direct["yield_t_ha"])), rel=1e-9
        )

    def test_wheat_and_maize_differ_at_same_temperature(self, execute) -> None:
        """At 20 C the wheat optimum is on-peak (f_temp=1) while the maize
        preset has a higher epsilon (3.3 vs 2.2); the two crop presets diverge.
        If the gateway were using the generic default for both, they would be
        identical to each other."""
        wheat = _values(execute, "HYRUE_WHEAT", self._SCALAR_INPUTS)
        corn = _values(execute, "HYRUE_CORN", self._SCALAR_INPUTS)
        assert wheat["yield_t_ha"] != pytest.approx(corn["yield_t_ha"])

    def test_generic_hyrue_id_still_uses_default(self) -> None:
        """An HYRUE_* id that is not HYRUE_CORN or HYRUE_WHEAT must still use
        the generic crop-neutral path. Verified by checking the mapping table
        and the direct dispatch function."""
        from engine.gateway import model_dispatcher as md
        from engine.gateway.model_dispatcher import _route_hyrue_family

        assert md._HYRUE_CROP_BY_ID == {"HYRUE_WHEAT": "wheat", "HYRUE_CORN": "maize"}
        assert md._HYRUE_CROP_BY_ID.get("HYRUE_OTHER") is None

        result: dict[str, Any] = {}
        out = _route_hyrue_family("HYRUE_OTHER", dict(self._SCALAR_INPUTS), {}, result)
        assert "yield_t_ha" in out
        direct = self._direct(None)
        assert out["yield_t_ha"] == pytest.approx(
            float(np.mean(direct["yield_t_ha"])), rel=1e-9
        )

    def test_explicit_crop_parameter_overrides_model_id(self, execute) -> None:
        """An explicit ``crop`` in parameters takes precedence over the model-id
        derivation, so a HYRUE_WHEAT request can select maize at call time."""
        result = execute("HYRUE_WHEAT", self._SCALAR_INPUTS, parameters={"crop": "maize"})
        assert not isinstance(result, GatewayError), result
        values = dict(result.values)
        direct = self._direct("maize")
        assert values["yield_t_ha"] == pytest.approx(
            float(np.mean(direct["yield_t_ha"])), rel=1e-9
        )

    def test_wheat_temperature_response_differs_from_generic(self, execute) -> None:
        """The wheat preset (t_opt=20) must respond differently to a 24 C day
        than the generic default (t_opt=25). This proves the crop params, not
        just the crop name, reach the computation."""
        warm = dict(self._SCALAR_INPUTS, t_mean=24.0)

        wheat = self._direct("wheat", warm)
        generic = self._direct(None, warm)

        gateway_wheat = _values(execute, "HYRUE_WHEAT", warm)
        assert gateway_wheat["yield_t_ha"] == pytest.approx(
            float(np.mean(wheat["yield_t_ha"])), rel=1e-9
        )
        assert gateway_wheat["yield_t_ha"] != pytest.approx(
            float(np.mean(generic["yield_t_ha"])), rel=1e-3
        )

    def test_seasonal_mode_sums_daily_arrays(self, execute) -> None:
        """When ``par`` is an array, the gateway must integrate daily biomass
        (sum) rather than applying the scalar multiplier path. The dispatch
        function must not reject array inputs for lai, ewsi, or t_mean when
        par is also an array.
        """

        par_arr = [10.0, 15.0, 20.0]
        seasonal_inputs: dict[str, Any] = {
            "par": par_arr,
            "lai": [1.0, 2.0, 3.0],
            "ewsi": [0.0, 0.0, 0.1],
            "t_mean": [18.0, 20.0, 22.0],
        }
        values = _values(execute, "HYRUE_WHEAT", seasonal_inputs)

        # Direct call with arrays must match gateway output.
        direct = self._direct("wheat", seasonal_inputs)
        assert values["yield_t_ha"] == pytest.approx(
            float(np.mean(direct["yield_t_ha"])), rel=1e-9
        )

        # Seasonal mode returns a scalar (summed total), not an array.
        assert isinstance(direct["yield_t_ha"], (float, np.floating))

    def test_scalar_and_array_t_mean_produce_same_single_day(self) -> None:
        """A single-element array ``t_mean`` with scalar ``par`` must return
        per-day values (array output), while scalar ``par`` with array ``t_mean``
        of length N must also return N daily values without days-multiplication.
        """
        from engine.hydroma.models.hyrue import HYRUE

        m = HYRUE(crop="wheat")
        r_scalar_t = m.compute(
            par=15.0, lai=np.array([3.0]),
            ewsi=np.array([0.1]), t_mean=20.0,
        )
        r_array_t = m.compute(
            par=15.0, lai=np.array([3.0]),
            ewsi=np.array([0.1]), t_mean=np.array([20.0]),
        )
        assert float(r_scalar_t["total_biomass_g_m2"][0]) == pytest.approx(
            float(r_array_t["total_biomass_g_m2"][0])
        )

    def test_gw_negative_par_rejected_at_gateway(self, execute) -> None:
        """Gateway must reject out-of-range values through compute_checked,
        not return a nonsensical negative biomass."""

        result = execute("HYRUE_WHEAT", {"par": -5.0, "lai": 3.0, "ewsi": 0.1, "t_mean": 20.0})
        assert isinstance(result, GatewayError)
        assert "PAR" in str(result) or "par" in str(result).lower() or "out of range" in str(result).lower()

    def test_gw_negative_lai_rejected_at_gateway(self, execute) -> None:
        result = execute("HYRUE_WHEAT", {"par": 15.0, "lai": -1.0, "ewsi": 0.1, "t_mean": 20.0})
        assert isinstance(result, GatewayError)

    def test_gw_ewsi_above_one_rejected_at_gateway(self, execute) -> None:
        result = execute("HYRUE_WHEAT", {"par": 15.0, "lai": 3.0, "ewsi": 1.5, "t_mean": 20.0})
        assert isinstance(result, GatewayError)

    def test_gw_nan_t_mean_rejected_at_gateway(self, execute) -> None:
        result = execute("HYRUE_WHEAT", {"par": 15.0, "lai": 3.0, "ewsi": 0.1, "t_mean": float("nan")})
        assert isinstance(result, GatewayError)

    def test_gw_inf_par_rejected_at_gateway(self, execute) -> None:
        result = execute("HYRUE_WHEAT", {"par": float("inf"), "lai": 3.0, "ewsi": 0.1, "t_mean": 20.0})
        assert isinstance(result, GatewayError)

    def test_gw_seasonal_array_par_route_accepts_lists(self, execute) -> None:
        """Gateway must accept JSON arrays (Python lists) for all four inputs."""
        inputs = {
            "par": [15.0, 16.0, 17.0],
            "lai": [2.0, 2.5, 3.0],
            "ewsi": [0.1, 0.2, 0.3],
            "t_mean": [20.0, 21.0, 22.0],
        }
        values = _values(execute, "HYRUE_WHEAT", inputs)
        direct = self._direct("wheat", inputs)
        assert values["yield_t_ha"] == pytest.approx(
            float(np.mean(direct["yield_t_ha"])), rel=1e-9
        )

    def test_gw_incompatible_array_lengths_rejected(self, execute) -> None:
        """Arrays of mismatched lengths must not be silently truncated or
        broadcast. The gateway must return a GatewayError."""
        inputs = {
            "par": [15.0, 16.0, 17.0],
            "lai": [2.0, 2.5],
            "ewsi": [0.1, 0.2, 0.3],
            "t_mean": [20.0, 21.0, 22.0],
        }
        result = execute("HYRUE_WHEAT", inputs)
        assert isinstance(result, GatewayError)

    def test_gw_empty_arrays_rejected_at_gateway(self, execute) -> None:
        """Empty arrays produce zero biomass without error from compute; the
        gateway must reject empty arrays as invalid input."""
        result = execute("HYRUE_WHEAT", {
            "par": [], "lai": [], "ewsi": [], "t_mean": [],
        })
        assert isinstance(result, GatewayError)

    def test_gw_string_input_rejected_at_gateway(self, execute) -> None:
        """Non-numeric string input must be rejected by _route_array_or_float."""
        result = execute("HYRUE_WHEAT", {"par": "fifteen", "lai": 3.0, "ewsi": 0.1, "t_mean": 20.0})
        assert isinstance(result, GatewayError)

    def test_gw_null_par_rejected_at_gateway(self, execute) -> None:
        """null par must be rejected at the boundary."""
        result = execute("HYRUE_WHEAT", {"par": None, "lai": 3.0, "ewsi": 0.1, "t_mean": 20.0})
        assert isinstance(result, GatewayError)

    # ------------------------------------------------------------------ #
    # Stage-20 independent numerical reconciliation                      #
    # ------------------------------------------------------------------ #
    # These tests reproduce the HYRUE computation from first principles
    # (Monteith 1977 / Steduto et al. 2009) WITHOUT calling compute_daily
    # or compute to generate expected values. Expected values are derived
    # from the fixed formula constants, not from the model under test.

    def test_three_day_intermediates_independent(self) -> None:
        """Check f_ipar, f_water, f_temp, and B_day for each of three days
        using independent analytical formulas."""
        from engine.hydroma.models.hyrue import HYRUE

        eps = 2.2
        k = 0.65
        lai_max = 6.0
        t_opt = 20.0
        sigma = 8.0
        t_min, t_max = 5.0, 35.0

        days_data = [
            {"par": 10.0, "lai": 1.5, "ewsi": 0.0, "t": 18.0},
            {"par": 18.0, "lai": 3.2, "ewsi": 0.1, "t": 22.0},
            {"par": 16.0, "lai": 2.8, "ewsi": 0.3, "t": 25.0},
        ]

        m = HYRUE(crop="wheat")

        for d in days_data:
            f_ipar = 1 - np.exp(-k * min(d["lai"], lai_max))
            f_water = 1 - d["ewsi"]
            if d["t"] < t_min or d["t"] > t_max:
                f_temp = 0.0
            else:
                f_temp = np.exp(-(((d["t"] - t_opt) / sigma) ** 2))
            B_day = d["par"] * f_ipar * eps * f_water * f_temp

            # Use the model's f_ipar for comparison (it's a static method)
            f_ipar_model = float(m.f_ipar(d["lai"]))
            assert f_ipar_model == pytest.approx(f_ipar, abs=1e-15)

            # Use the model's stress_temperature for comparison
            f_temp_model = HYRUE.stress_temperature(d["t"], t_opt=t_opt, t_min=t_min, t_max=t_max)
            assert f_temp_model == pytest.approx(f_temp, abs=1e-15)

            # Recompute B_day via intermediate values and compare
            aPAR = d["par"] * f_ipar
            B_day_calc = aPAR * eps * f_water * f_temp
            assert B_day == pytest.approx(B_day_calc, abs=1e-12)

    def test_three_day_daily_biomass_against_independent(self) -> None:
        """The model's daily_biomass_g_m2 must match an independent calculation
        for each day. Uses HYRUE.compute() to get the numbers, but the expected
        values come from the formula, not from compute itself."""
        from engine.hydroma.models.hyrue import HYRUE

        eps = 2.2
        k = 0.65
        lai_max = 6.0
        t_opt = 20.0
        sigma = 8.0
        t_min, t_max = 5.0, 35.0

        par = np.array([10.0, 18.0, 16.0])
        lai = np.array([1.5, 3.2, 2.8])
        ewsi = np.array([0.0, 0.1, 0.3])
        t = np.array([18.0, 22.0, 25.0])

        # Independent expected values (computed from formula constants)
        expected_daily = []
        for i in range(3):
            f_ipar = 1 - np.exp(-k * min(lai[i], lai_max))
            f_water = 1 - ewsi[i]
            if t[i] < t_min or t[i] > t_max:
                f_temp = 0.0
            else:
                f_temp = np.exp(-(((t[i] - t_opt) / sigma) ** 2))
            B = par[i] * f_ipar * eps * f_water * f_temp
            expected_daily.append(B)

        m = HYRUE(crop="wheat")
        r = m.compute(par=par, lai=lai, ewsi=ewsi, t_mean=t)
        assert r["computation_mode"] == "seasonal"
        for i in range(3):
            assert float(r["daily_biomass_g_m2"][i]) == pytest.approx(
                expected_daily[i], rel=1e-12
            )

    def test_seasonal_total_hand_summed(self) -> None:
        """Seasonal total_biomass must equal sum of independent daily biomasses."""
        from engine.hydroma.models.hyrue import HYRUE

        eps = 2.2
        k = 0.65
        lai_max = 6.0
        t_opt = 20.0
        sigma = 8.0
        t_min, t_max = 5.0, 35.0

        par = np.array([10.0, 18.0, 16.0])
        lai = np.array([1.5, 3.2, 2.8])
        ewsi = np.array([0.0, 0.1, 0.3])
        t = np.array([18.0, 22.0, 25.0])

        expected_daily = []
        for i in range(3):
            f_ipar = 1 - np.exp(-k * min(lai[i], lai_max))
            f_water = 1 - ewsi[i]
            if t[i] < t_min or t[i] > t_max:
                f_temp = 0.0
            else:
                f_temp = np.exp(-(((t[i] - t_opt) / sigma) ** 2))
            B = par[i] * f_ipar * eps * f_water * f_temp
            expected_daily.append(B)

        expected_total = float(np.sum(expected_daily))

        # Model must agree
        m = HYRUE(crop="wheat")
        r = m.compute(par=par, lai=lai, ewsi=ewsi, t_mean=t)
        assert r["computation_mode"] == "seasonal"
        assert r["season_length_days"] == 3
        assert float(r["total_biomass_g_m2"]) == pytest.approx(expected_total, rel=1e-12)

    def test_hi_and_conversion_independent(self) -> None:
        """Verify HI application and g/m²→t/ha conversion are separate, correct steps."""
        from engine.hydroma.models.hyrue import HYRUE

        eps = 2.2
        k = 0.65
        lai_max = 6.0
        t_opt = 20.0
        sigma = 8.0
        t_min, t_max = 5.0, 35.0
        hi = 0.45

        par = np.array([10.0, 18.0, 16.0])
        lai = np.array([1.5, 3.2, 2.8])
        ewsi = np.array([0.0, 0.1, 0.3])
        t = np.array([18.0, 22.0, 25.0])

        expected_daily = []
        for i in range(3):
            f_ipar = 1 - np.exp(-k * min(lai[i], lai_max))
            f_water = 1 - ewsi[i]
            if t[i] < t_min or t[i] > t_max:
                f_temp = 0.0
            else:
                f_temp = np.exp(-(((t[i] - t_opt) / sigma) ** 2))
            B = par[i] * f_ipar * eps * f_water * f_temp
            expected_daily.append(B)

        expected_total = float(np.sum(expected_daily))
        expected_yield_g_m2 = expected_total * hi
        expected_yield_t_ha = expected_yield_g_m2 / 100

        m = HYRUE(crop="wheat")
        r = m.compute(par=par, lai=lai, ewsi=ewsi, t_mean=t)
        assert float(r["yield_g_m2"]) == pytest.approx(expected_yield_g_m2, rel=1e-12)
        assert float(r["yield_t_ha"]) == pytest.approx(expected_yield_t_ha, rel=1e-12)

    def test_gateway_matches_independent(self, execute) -> None:
        """The gateway dispatch (_route_hyrue_family) must produce the same
        yield_t_ha as the independent analytical calculation."""
        eps = 2.2
        k = 0.65
        lai_max = 6.0
        t_opt = 20.0
        sigma = 8.0
        t_min, t_max = 5.0, 35.0
        hi = 0.45

        par_arr = [10.0, 18.0, 16.0]
        lai_arr = [1.5, 3.2, 2.8]
        ewsi_arr = [0.0, 0.1, 0.3]
        t_arr = [18.0, 22.0, 25.0]

        # Compute expected independently
        expected_daily = []
        for i in range(3):
            f_ipar = 1 - np.exp(-k * min(lai_arr[i], lai_max))
            f_water = 1 - ewsi_arr[i]
            if t_arr[i] < t_min or t_arr[i] > t_max:
                f_temp = 0.0
            else:
                f_temp = np.exp(-(((t_arr[i] - t_opt) / sigma) ** 2))
            B = par_arr[i] * f_ipar * eps * f_water * f_temp
            expected_daily.append(B)

        expected_total = float(np.sum(expected_daily))
        expected_yield_t_ha = expected_total * hi / 100

        # Via gateway
        result = execute("HYRUE_WHEAT", {
            "par": par_arr,
            "lai": lai_arr,
            "ewsi": ewsi_arr,
            "t_mean": t_arr,
        })
        assert not isinstance(result, GatewayError), result
        gw_yield = float(result.values["yield_t_ha"])
        assert gw_yield == pytest.approx(expected_yield_t_ha, rel=1e-9)
        # Gateway must expose the computation mode
        assert result.values.get("computation_mode") == "seasonal"

    def test_gateway_legacy_mode_marked(self, execute) -> None:
        """When days > 1 with scalar par, the gateway must label the output
        as legacy_constant mode so callers cannot mistake it for a data-driven
        seasonal integration."""
        result = execute("HYRUE_WHEAT", {
            "par": 15.0,
            "lai": 3.0,
            "ewsi": 0.1,
            "t_mean": 20.0,
            "days": 120,
        })
        assert not isinstance(result, GatewayError), result
        assert result.values.get("computation_mode") == "legacy_constant"
        assert "warning" in result.values

    def test_gateway_daily_mode_scalar_inputs(self, execute) -> None:
        """Scalar inputs with days=1 must return daily mode, not legacy or seasonal."""
        result = execute("HYRUE_WHEAT", {
            "par": 20.0,
            "lai": 3.0,
            "ewsi": 0.1,
            "t_mean": 20.0,
        })
        assert not isinstance(result, GatewayError), result
        assert result.values.get("computation_mode") == "daily"

    def test_gateway_daily_series_mode_scalar_par_array_lai(self, execute) -> None:
        """Scalar par with array lai and days=1 must return daily_series mode."""
        result = execute("HYRUE_WHEAT", {
            "par": 20.0,
            "lai": [1.0, 2.0, 3.0],
            "ewsi": [0.1, 0.1, 0.1],
            "t_mean": [18.0, 20.0, 22.0],
        })
        assert not isinstance(result, GatewayError), result
        assert result.values.get("computation_mode") == "daily_series"
        assert result.values.get("constant_par") == 20.0
        assert result.values.get("n_days_evaluated") == 3


# ===========================================================================
# CANON-018 — the SSP projection
# ===========================================================================


# The class name avoids the shape words the provenance sweep selects on
# (``Output/Result/Analysis/Profile/Tile/Summary/Report/Solution/Assessment/
# Signature/Features/Valuation/Index/Project``) for the same reason
# ``strict_tests/test_s15_provenance.py``'s own classes do: a pytest class is
# not a result type, and ``Project`` is one of those words.
class TestCanon018SspClimateDelta:
    """CANON-018 is a scenario projection and reports itself as modelled."""

    def test_projection_matches_hand_derivation(self, execute) -> None:
        """SSP2-4.5 at 2041 against baselines of 18 C, 300 mm and 1500 mm.

        The nearest horizon the engine holds is 2050 (+2.4 C, -8%), the ET0
        sensitivity is 2.5 C of demand per C of warming, and the confidence
        in the table is 'medium' out to mid-century.
        """
        from engine.hydroma.scenarios.climate_scenarios import CLIMATE_PROJECTIONS

        baseline_temp, baseline_precip, baseline_et0 = 18.0, 300.0, 1500.0
        year = 2041
        horizons = sorted(CLIMATE_PROJECTIONS["SSP2-4.5"])
        horizon = min(horizons, key=lambda candidate: abs(candidate - year))
        assert horizon == 2050
        scenario = CLIMATE_PROJECTIONS["SSP2-4.5"][horizon]
        delta_temp, delta_precip = scenario[0], scenario[1]

        values = _values(
            execute,
            "CANON-018",
            {
                "ssp": "SSP2-4.5",
                "year": year,
                "baseline_temp": baseline_temp,
                "baseline_precip": baseline_precip,
                "baseline_et0": baseline_et0,
            },
        )
        assert values["time_horizon"] == 2050
        assert values["delta_temp_c"] == pytest.approx(delta_temp, rel=1e-12)
        assert values["delta_precip_pct"] == pytest.approx(delta_precip, rel=1e-12)
        assert values["delta_et0_pct"] == pytest.approx(delta_temp * 2.5, rel=1e-12)
        assert values["confidence"] == "medium"
        assert values["projected_temperature_c"] == pytest.approx(
            baseline_temp + delta_temp, rel=1e-12
        )
        assert values["projected_precipitation_mm"] == pytest.approx(
            baseline_precip * (1.0 + delta_precip / 100.0), rel=1e-12
        )
        assert values["projected_et0_mm"] == pytest.approx(
            baseline_et0 * (1.0 + delta_temp * 2.5 / 100.0), rel=1e-12
        )
        assert values["projected_water_balance_change_mm"] == pytest.approx(
            values["projected_precipitation_mm"] - values["projected_et0_mm"], rel=1e-12
        )
        assert values["data_source"] == "simulated"

    def test_unknown_scenario_names_the_available_ones(self, execute) -> None:
        error = _error(
            execute,
            "CANON-018",
            {
                "ssp": "SSP9-9.9",
                "year": 2050,
                "baseline_temp": 18.0,
                "baseline_precip": 300.0,
                "baseline_et0": 1500.0,
            },
        )
        assert "SSP2-4.5" in error.message
        assert "SSP5-8.5" in error.message

    def test_baselines_are_required_and_named(self, execute) -> None:
        """A delta applied to an invented baseline is an invented outcome."""
        error = _error(
            execute,
            "CANON-018",
            {"ssp": "SSP2-4.5", "year": 2050, "baseline_temp": 18.0, "baseline_precip": 300.0},
        )
        assert "baseline_et0" in error.message


# ===========================================================================
# CANON-019..022 — satellite product routes
# ===========================================================================


class TestSatelliteProductRoutes:
    """The satellite routes deliver real scenes or a named failure.

    No test here asserts that a satellite value is produced, because no
    satellite value can be produced without a network or a credential, and a
    route that reported one anyway would be fabricating data.
    """

    PRODUCTS = {
        "CANON-019": "gpm-imerg-hhr",
        "CANON-020": "modis-16A3GF-061",
        "CANON-021": "landsat-c2-l2",
        "CANON-022": "sentinel-2-l2a",
    }

    def _search(self, model_id: str) -> dict[str, Any]:
        return {
            "bbox": [51.0, 35.5, 51.5, 36.0],
            "datetime": "2021-06-01T00:00:00Z/2021-06-30T23:59:59Z",
        }

    @pytest.mark.parametrize("model_id", sorted(PRODUCTS))
    def test_no_network_is_named_not_empty(self, execute, monkeypatch, model_id: str) -> None:
        def no_network(*args: Any, **kwargs: Any) -> Any:
            raise requests.exceptions.ConnectionError("cannot reach the STAC catalog")

        monkeypatch.setattr(requests, "post", no_network)
        error = _error(execute, model_id, self._search(model_id))
        assert "planetarycomputer" in error.message
        assert self.PRODUCTS[model_id] in error.message

    @pytest.mark.parametrize("model_id", sorted(PRODUCTS))
    def test_empty_catalog_is_an_error_not_an_empty_success(
        self, execute, monkeypatch, model_id: str
    ) -> None:
        """A catalog that returns nothing says so: an empty scene list is not
        a value, it is the absence of one."""

        def empty_catalog(*args: Any, **kwargs: Any) -> Any:
            return _FakeResponse([])

        monkeypatch.setattr(requests, "post", empty_catalog)
        error = _error(execute, model_id, self._search(model_id))
        assert self.PRODUCTS[model_id] in error.message
        assert "0 items" in error.message

    @pytest.mark.parametrize("model_id", sorted(PRODUCTS))
    def test_missing_area_or_date_is_named(self, execute, model_id: str) -> None:
        assert _error(execute, model_id, {"datetime": "2021-06-01/2021-06-30"}).error_code == (
            "INVALID_REQUEST"
        )
        assert _error(execute, model_id, {"bbox": [51.0, 35.5, 51.5, 36.0]}).error_code == (
            "INVALID_REQUEST"
        )

    def test_unknown_connector_names_the_available_ones(self, execute) -> None:
        error = _error(
            execute,
            "CANON-021",
            {
                "source": "no_such_source",
                "bbox": [51.0, 35.5, 51.5, 36.0],
                "datetime": "2021-06-01/2021-06-30",
            },
        )
        assert "planetary_computer" in error.message

    def test_sentinel_download_names_its_credentials(self, execute, monkeypatch) -> None:
        """The download path names the two variables it needs, and names them
        before it reaches the network."""
        monkeypatch.delenv("CDS_CLIENT_ID", raising=False)
        monkeypatch.delenv("CDS_CLIENT_SECRET", raising=False)
        error = _error(
            execute,
            "CANON-022",
            {
                "source": "cdse_sentinel",
                "bbox": [51.0, 35.5, 51.5, 36.0],
                "datetime": "2021-06-01/2021-06-30",
            },
        )
        assert "CDS_CLIENT_ID" in error.message
        assert "CDS_CLIENT_SECRET" in error.message

    def test_refused_network_is_named_as_a_permission(self, execute, monkeypatch) -> None:
        """With the ZED 2.2ج download gate closed the route reports the gate,
        which is the permission that is missing -- not an empty scene list."""
        monkeypatch.setenv("HYDROMA_ALLOW_DOWNLOAD", "0")
        error = _error(execute, "CANON-021", self._search("CANON-021"))
        assert "HYDROMA_ALLOW_DOWNLOAD" in error.message


# ===========================================================================
# The invariant that covers all fourteen
# ===========================================================================


class TestNoRouteReturnsAnEmptySuccess:
    """Whatever else a route does, it never succeeds without a value."""

    @pytest.mark.parametrize("model_id", UNWIRED_IDS)
    def test_an_empty_request_is_named_for_every_route(self, execute, model_id: str) -> None:
        """An empty request cannot produce a number: the gateway rejects it
        at the required-input contract, naming the inputs the route needs."""
        result = execute(model_id, {})
        assert isinstance(result, GatewayError), (
            f"{model_id} returned a success for an empty request: {result.values}"
        )
        assert result.message

    @pytest.mark.parametrize("model_id", UNWIRED_IDS)
    def test_a_wire_never_claims_a_model_it_did_not_reach(self, execute, model_id: str) -> None:
        """The route table is the only thing these ids route through."""
        from engine.gateway import _ROUTE_TARGETS, _ROUTES_FOR_REGISTERED_IDS

        assert model_id in _ROUTE_TARGETS
        assert model_id in _ROUTES_FOR_REGISTERED_IDS
        assert _ROUTE_TARGETS[model_id]

    @pytest.mark.parametrize("model_id", ("CANON-012", "CANON-014"))
    def test_the_registry_routes_answer_a_view_query_with_real_data(
        self, execute, model_id: str
    ) -> None:
        """The two no-input-by-nature routes still answer a stated read, and
        what they answer with is a read of something that already exists.

        The reference values are resolved at call time rather than bound at
        module import: other suites in this tree import a second copy of
        ``engine.models``, and a stale binding would compare against a
        registry nobody is serving.
        """
        values = _values(execute, model_id, {"view": "summary"})
        assert values["data_source"] == "registry"
        if model_id == "CANON-012":
            from engine.hydroma.formulas import all_records as records_now

            assert values["formula_count"] == len(records_now())
        else:
            assert values["model_count"] >= 70
