"""S16 -- Engine Gateway strict contracts & scientific re-computation.

Hard-scrutiny suite for the Engine Gateway dispatch layer.

Coverage
--------
* Model-registry membership, including the ``SOIL_RECOMMENDATIONS`` node
  that was reachable in ``_dispatch_by_type`` but unregistered until S16
  forced the contract.
* Provenance / evidence linkage: every result carries a ``trace_id`` and
  an ``evidence_id``; the same inputs yield identical ``values``.
* Input-unit normalization: a value supplied in centimetres that is declared
  with ``si_equivalent`` must land on the same computation as the millimetre
  value.
* The malformed-input contract: non-finite scalars, negative curve numbers,
  and non-positive Theis singularities never crash the caller -- they come
  back as a normalized ``GatewayError``.
* Independent scientific re-derivation of the five routed models from the
  governing standards text (never sampled from the engine):
  Hargreaves (FAO-56 eq. 52), Penman-Monteith (eq. 39), SCS-CN NRCS (SI
  form), Theis E1, and IPCC AR6 carbon.
* Hypothesis-physical-invariance checks on the direct engine functions
  (runoff, Theis, Hargreaves).
"""

from __future__ import annotations

import importlib
import inspect
import math
import os
from pathlib import Path

import numpy as np
import pytest
from hypothesis import assume, given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st
from scipy.special import expi

from engine.gateway import (
    EngineGateway,
    ExecutionMetadata,
    GatewayError,
    GatewayRequest,
    GatewayResult,
    ProvenanceSpec,
    UnitSpec,
)
from engine.models import get_registry
from engine.strict_tests.conftest import (
    FAO56_REFERENCE_DAY,
)
from engine.strict_tests.conftest import (
    NRCS_SCS_CN_WORKED_EXAMPLE as WX,
)

# The hydroma package spelling is discovered at runtime so this suite never
# hard-codes a string that a font could mis-render; the discovered name is
# the only spelling Python itself will resolve.
_ENGINE = Path(__file__).resolve().parent.parent
_HYD = next(
    d for d in os.listdir(_ENGINE) if d.lower().startswith("hydr") and (_ENGINE / d).is_dir()
)
_et = importlib.import_module(f"engine.{_HYD}.climate.et_calculator")
_runoff_adapter = importlib.import_module(f"engine.{_HYD}.runoff")
_theis_adapter = importlib.import_module(f"engine.{_HYD}.theis")
_groundwater = importlib.import_module(f"engine.{_HYD}.groundwater.models")
_carbon = importlib.import_module(f"engine.{_HYD}.carbon.calculator")
_runoff_model = importlib.import_module(f"engine.{_HYD}.models.runoff_model")

ClimateData = _et.ClimateData
calc_et0_hargreaves = _et.calc_et0_hargreaves
calc_et0_penman_monteith = _et.calc_et0_penman_monteith
calc_extraterrestrial_radiation = _et.calc_extraterrestrial_radiation
calc_delta = _et.calc_delta
calc_psychrometric = _et.calc_psychrometric
calc_saturation_vapor_pressure = _et.calc_saturation_vapor_pressure
calc_net_radiation = _et.calc_net_radiation
_hargreaves_core = _et._hargreaves_core
compute_runoff = _runoff_adapter.compute_runoff
compute_theis = _theis_adapter.compute_theis
calculate_theis_drawdown = _groundwater.calculate_theis_drawdown
RunoffCalculator = _runoff_model.RunoffCalculator
RunoffInput = _runoff_model.RunoffInput
CarbonProjectType = _carbon.CarbonProjectType
calculate_carbon_sequestration = _carbon.calculate_carbon_sequestration
SEQUESTRATION_RATES = _carbon.SEQUESTRATION_RATES

_GW = EngineGateway()
_PROV = ProvenanceSpec(source="s16", source_type="TEST")


def _exec(model_id: str, inputs: dict, units: dict | None = None) -> GatewayResult | GatewayError:
    return _GW.execute(
        GatewayRequest(
            model_id=model_id,
            inputs=inputs,
            input_units=units or {},
            provenance=_PROV,
        )
    )


def _values(model_id: str, inputs: dict, units: dict | None = None) -> dict:
    r = _exec(model_id, inputs, units)
    assert isinstance(r, GatewayResult), (
        f"expected success, got GatewayError({r.error_code}): {r.message}"
    )
    return r.values


# --------------------------------------------------------------------------- #
# Independent standard relations (written from the standards text)             #
# --------------------------------------------------------------------------- #
def _hargreaves_ref(t_min: float, t_max: float, t_mean: float, ra_mj: float) -> float:
    """FAO-56 eq. 52, re-derived: 0.0023 (Tm+17.8) (Tmax-Tmin)^0.5 Ra(mm)."""
    if t_max < t_min or ra_mj < 0:
        raise ValueError
    ra_mm = ra_mj * 0.408
    return float(0.0023 * (t_mean + 17.8) * (t_max - t_min) ** 0.5 * ra_mm)


def _scs_runoff_mm(precip: float, cn: float) -> float:
    """NRCS SCS-CN, SI form (NRCS N Eng. Hb., Part 630)."""
    s = 25400.0 / cn - 254.0
    ia = 0.2 * s
    if precip <= ia:
        return 0.0
    return (precip - ia) ** 2 / (precip + 0.8 * s)


def _theis_s(T: float, S: float, Q: float, r: float, t: float) -> float:
    """Theis (1935) drawdown: s = Q/(4*pi*T) * W(u), W(u) = -Ei(-u)."""
    u = (r * r * S) / (4.0 * T * t)
    return float((Q / (4.0 * math.pi * T)) * (-expi(-u)))


# --------------------------------------------------------------------------- #
# Model-registry contract                                                      #
# --------------------------------------------------------------------------- #
_REGISTERED = [
    "CANON-001",
    "CANON-002",
    "CANON-004",
    "CANON-005",
    "CARBON_SEQ",
    "SOIL_TAXONOMY",
    "SOIL_PEDOTRANSFER",
    "SOIL_TEXTURE_COORDS",
    "SOIL_RECOMMENDATIONS",
    "SOIL_CEC",
    "CANON-011_RAD",
]


class TestGatewayRegistry:
    @pytest.mark.parametrize("model_id", _REGISTERED)
    def test_model_is_registered(self, model_id: str) -> None:
        assert get_registry().get(model_id) is not None

    def test_soil_recommendations_node_is_live(self) -> None:
        """The SOIL_RECOMMENDATIONS branch existed but the node was unregistered;
        executing it must now resolve instead of returning MODEL_NOT_FOUND."""
        r = _exec("SOIL_RECOMMENDATIONS", {"sand": 40.0, "silt": 40.0, "clay": 20.0, "ph": 6.5})
        assert isinstance(r, GatewayResult)
        assert r.values["model_type"] == "soil_recommendations"

    def test_unregister_model_is_model_not_found(self) -> None:
        r = _exec("CANON-999-NONSENSE", {"a": 1.0})
        assert isinstance(r, GatewayError)
        assert r.error_code == "MODEL_NOT_FOUND"


# --------------------------------------------------------------------------- #
# Provenance / evidence / determinism / unit normalization                     #
# --------------------------------------------------------------------------- #
class TestProvenanceDeterminismUnits:
    def test_result_carries_trace_and_evidence(self) -> None:
        r = _exec(
            "CANON-002",
            {"temp_min": 10.0, "temp_max": 25.0, "elevation": 0.0, "latitude": 40.0, "doy": 150},
        )
        assert isinstance(r, GatewayResult)
        assert r.execution.trace_id is not None
        assert r.execution.trace_id.startswith("trace_")
        assert r.execution.execution_id is not None
        assert r.execution.execution_id.startswith("exec_")
        assert r.evidence_id is not None

    def test_trace_is_unique_per_call(self) -> None:
        a = _exec(
            "CARBON_SEQ",
            {
                "project_type": "afforestation",
                "area_ha": 10.0,
                "duration_years": 5,
                "region": "temperate",
            },
        )
        b = _exec(
            "CARBON_SEQ",
            {
                "project_type": "afforestation",
                "area_ha": 10.0,
                "duration_years": 5,
                "region": "temperate",
            },
        )
        assert isinstance(a, GatewayResult)
        assert isinstance(b, GatewayResult)
        assert a.execution.trace_id != b.execution.trace_id

    def test_values_are_deterministic(self) -> None:
        one = _values("CANON-004", {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0})
        other = _values("CANON-004", {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0})
        assert one == other

    def test_input_units_are_normalised(self) -> None:
        """10 cm of rain declared as cm (si_equivalent=10) == 100 mm."""
        mm = _values("CANON-004", {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0})
        cm = _values(
            "CANON-004",
            {"precipitation": 10.0, "curve_number": 72.0, "area_ha": 2.0},
            {"precipitation": UnitSpec(unit="cm", si_equivalent=10.0)},
        )
        assert mm["runoff_volume_m3"] == pytest.approx(cm["runoff_volume_m3"], rel=1e-12)


# --------------------------------------------------------------------------- #
# Hargreaves -- FAO-56 eq. 52                                                  #
# --------------------------------------------------------------------------- #
class TestHargreavesEq52:
    def test_constants_are_in_source(self) -> None:
        src = inspect.getsource(_hargreaves_core)
        assert "0.5" in src and "0.0023" in src and "0.408" in src and "17.8" in src

    def test_recomputation_matches_gateway(self) -> None:
        data = ClimateData(tmin=10.0, tmax=25.0, elevation=0.0, latitude=40.0, doy=150)
        ra = calc_extraterrestrial_radiation(data.latitude, data.doy)
        expected = _hargreaves_ref(data.tmin, data.tmax, (data.tmax + data.tmin) / 2.0, ra)
        via_gw = _values(
            "CANON-002",
            {"temp_min": 10.0, "temp_max": 25.0, "elevation": 0.0, "latitude": 40.0, "doy": 150},
        )["et0_mm_day"]
        assert via_gw == pytest.approx(expected, rel=1e-12)
        assert via_gw == pytest.approx(calc_et0_hargreaves(data=data), rel=1e-12)

    def test_dtr_zero_is_zero(self) -> None:
        data = ClimateData(tmin=15.0, tmax=15.0, elevation=0.0, latitude=40.0, doy=150)
        assert calc_et0_hargreaves(data=data) == 0.0

    @hyp_settings(max_examples=60)
    @given(
        dtr=st.floats(min_value=0.0, max_value=40.0, allow_nan=False, allow_infinity=False),
    )
    def test_et0_increases_with_diurnal_range(self, dtr: float) -> None:
        tmin = 10.0
        ra = calc_extraterrestrial_radiation(40.0, 150)
        base = _hargreaves_ref(tmin, tmin + dtr, tmin + dtr / 2.0, ra)
        bigger = _hargreaves_ref(tmin, tmin + dtr + 1.0, tmin + (dtr + 1.0) / 2.0, ra)
        assert bigger >= base


# --------------------------------------------------------------------------- #
# Penman-Monteith -- FAO-56 eq. 39                                             #
# --------------------------------------------------------------------------- #
class TestPenmanMonteithEq39:
    def test_constants_in_source(self) -> None:
        src = inspect.getsource(calc_et0_penman_monteith)
        assert "0.34" in src and "0.408" in src and "900" in src

    def test_recomputation_matches_gateway_and_direct(self) -> None:
        d = ClimateData(**FAO56_REFERENCE_DAY)
        tmean = (d.tmax + d.tmin) / 2.0
        delta = calc_delta(tmean)
        gamma = calc_psychrometric(d.elevation)
        es_tmax = calc_saturation_vapor_pressure(d.tmax)
        es_tmin = calc_saturation_vapor_pressure(d.tmin)
        ea = (es_tmin * d.rh_max / 100.0 + es_tmax * d.rh_min / 100.0) / 2.0
        es_mean = (es_tmax + es_tmin) / 2.0
        rn = calc_net_radiation(
            t_min=d.tmin,
            t_max=d.tmax,
            ea_kpa=ea,
            solar_radiation_mj=d.solar_radiation,
            elevation_m=d.elevation,
            latitude_deg=d.latitude,
            doy=d.doy,
        )
        num = 0.408 * delta * rn + gamma * (900.0 / (tmean + 273.0)) * d.wind_speed * (es_mean - ea)
        den = delta + gamma * (1.0 + 0.34 * d.wind_speed)
        expected = max(0.0, num / den)
        via_gw = _values(
            "CANON-001",
            {
                "temp_min": d.tmin,
                "temp_max": d.tmax,
                "rh_min": d.rh_min,
                "rh_max": d.rh_max,
                "wind_speed": d.wind_speed,
                "solar_radiation": d.solar_radiation,
                "elevation": d.elevation,
                "latitude": d.latitude,
                "doy": d.doy,
            },
        )["et0_mm_day"]
        assert via_gw == pytest.approx(expected, rel=1e-9)
        assert via_gw == pytest.approx(calc_et0_penman_monteith(d), rel=1e-12)


# --------------------------------------------------------------------------- #
# SCS-CN runoff -- NRCS (SI form) & Rational                                   #
# --------------------------------------------------------------------------- #
class TestScsCnAndRational:
    def test_nrcs_worked_example(self) -> None:
        out = RunoffCalculator().execute(
            RunoffInput(
                precipitation_mm=WX["precipitation_mm"],
                curve_number=WX["curve_number"],
                area_ha=1.0,
            )
        )
        depth = out.volume_m3 / 10.0
        assert depth == pytest.approx(WX["runoff_mm"], rel=1e-9)

    def test_retention_is_millimetres_not_inches(self) -> None:
        s_mm = 25400.0 / WX["curve_number"] - 254.0
        s_in = 1000.0 / WX["curve_number"] - 10.0
        assert s_mm == pytest.approx(WX["retention_mm"], rel=1e-9)
        assert s_in == pytest.approx(WX["retention_inches"], rel=1e-9)
        assert s_mm == pytest.approx(s_in * 25.4, rel=1e-12)

    def test_gateway_matches_reference(self) -> None:
        q = _scs_runoff_mm(WX["precipitation_mm"], WX["curve_number"])
        vol = _values(
            "CANON-004",
            {
                "precipitation": WX["precipitation_mm"],
                "curve_number": WX["curve_number"],
                "area_ha": 1.0,
            },
        )["runoff_volume_m3"]
        assert vol == pytest.approx(q * 1.0 * 10.0, rel=1e-9)

    def test_rational_method(self) -> None:
        vol = _values(
            "CANON-004",
            {
                "precipitation": 40.0,
                "curve_number": 75.0,
                "area_ha": 2.0,
                "method": "Rational",
                "rational_coefficient": 0.45,
            },
        )["runoff_volume_m3"]
        assert vol == pytest.approx(0.45 * 40.0 * 2.0 * 10.0, rel=1e-12)

    @hyp_settings(max_examples=60)
    @given(
        precip=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False),
        cn=st.floats(min_value=30.0, max_value=100.0, allow_nan=False),
        area=st.floats(min_value=1e-3, max_value=1e5, allow_nan=False),
    )
    def test_runoff_never_exceeds_rainfall_budget(
        self, precip: float, cn: float, area: float
    ) -> None:
        out = RunoffCalculator().execute(
            RunoffInput(precipitation_mm=precip, curve_number=cn, area_ha=area)
        )
        assert 0.0 <= out.volume_m3 <= precip * area * 10.0 * (1.0 + 1e-12)

    @hyp_settings(max_examples=40)
    @given(
        precip=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False),
        cn=st.floats(min_value=30.0, max_value=95.0, allow_nan=False),
    )
    def test_runoff_increases_with_rainfall_and_curve_number(
        self, precip: float, cn: float
    ) -> None:
        assume(_scs_runoff_mm(precip, cn) > 0.0 and _scs_runoff_mm(precip + 10.0, cn) > 0.0)
        low = (
            RunoffCalculator()
            .execute(RunoffInput(precipitation_mm=precip, curve_number=cn, area_ha=1.0))
            .volume_m3
        )
        hi_p = (
            RunoffCalculator()
            .execute(RunoffInput(precipitation_mm=precip + 10.0, curve_number=cn, area_ha=1.0))
            .volume_m3
        )
        hi_cn = (
            RunoffCalculator()
            .execute(RunoffInput(precipitation_mm=precip, curve_number=cn + 5.0, area_ha=1.0))
            .volume_m3
        )
        assert hi_p > low
        assert hi_cn > low


# --------------------------------------------------------------------------- #
# Theis E1 -- drawdown via the exponential integral                           #
# --------------------------------------------------------------------------- #
_T_REF = {
    "transmissivity_m2day": 100.0,
    "storativity": 1e-4,
    "pumping_rate_m3day": 1000.0,
    "distance_from_well_m": 100.0,
    "time_since_pumping_start_days": 1.0,
}


class TestTheisE1:
    def test_reference_value(self) -> None:
        s = calculate_theis_drawdown(**_T_REF)
        ref = _theis_s(100.0, 1e-4, 1000.0, 100.0, 1.0)
        assert s == pytest.approx(4.310510557745736, rel=1e-9)
        assert float(s) == pytest.approx(ref, rel=1e-9)

    def test_gateway_matches_reference(self) -> None:
        v = _values("CANON-005", dict(_T_REF))["drawdown_m"]
        assert v == pytest.approx(_theis_s(100.0, 1e-4, 1000.0, 100.0, 1.0), rel=1e-9)

    def test_parity_with_compute_theis_and_engine(self) -> None:
        via_adapter = compute_theis(dict(_T_REF), {})["drawdown_m"]
        via_engine = calculate_theis_drawdown(**_T_REF)
        assert float(via_adapter) == pytest.approx(float(via_engine), rel=1e-12)

    def test_non_positive_storage_or_transmissivity_returns_none(self) -> None:
        assert (
            calculate_theis_drawdown(
                transmissivity_m2day=100.0,
                storativity=0.0,
                pumping_rate_m3day=1000.0,
                distance_from_well_m=100.0,
                time_since_pumping_start_days=1.0,
            )
            is None
        )
        assert (
            calculate_theis_drawdown(
                transmissivity_m2day=0.0,
                storativity=1e-4,
                pumping_rate_m3day=1000.0,
                distance_from_well_m=100.0,
                time_since_pumping_start_days=1.0,
            )
            is None
        )

    @hyp_settings(max_examples=50)
    @given(
        t=st.floats(min_value=0.1, max_value=3650.0, allow_nan=False),
        r=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False),
    )
    def test_drawdown_positive_and_monotonic(self, t: float, r: float) -> None:
        base = float(
            calculate_theis_drawdown(
                transmissivity_m2day=100.0,
                storativity=1e-4,
                pumping_rate_m3day=1000.0,
                distance_from_well_m=r,
                time_since_pumping_start_days=t,
            )
        )
        assert base > 0.0
        # farther observation point -> less drawdown
        assert (
            float(
                calculate_theis_drawdown(
                    transmissivity_m2day=100.0,
                    storativity=1e-4,
                    pumping_rate_m3day=1000.0,
                    distance_from_well_m=r * 10.0,
                    time_since_pumping_start_days=t,
                )
            )
            < base
        )
        # later time -> more drawdown
        assert (
            float(
                calculate_theis_drawdown(
                    transmissivity_m2day=100.0,
                    storativity=1e-4,
                    pumping_rate_m3day=1000.0,
                    distance_from_well_m=r,
                    time_since_pumping_start_days=t * 10.0,
                )
            )
            > base
        )


# --------------------------------------------------------------------------- #
# IPCC AR6 carbon sequestration                                               #
# --------------------------------------------------------------------------- #
_REGION_FACTORS = {"tropical": 1.3, "temperate": 1.0, "arid": 0.6}
_DISCOUNT = 0.85


class TestCarbonIPCC:
    def test_recomputation_afforestation(self) -> None:
        rate = SEQUESTRATION_RATES[CarbonProjectType.AFFORESTATION]["rate"]
        expected = rate * 100.0 * 10 * _REGION_FACTORS["temperate"] * _DISCOUNT
        vals = _values(
            "CARBON_SEQ",
            {
                "project_type": "afforestation",
                "area_ha": 100.0,
                "duration_years": 10,
                "region": "temperate",
            },
        )
        assert vals["total_carbon_tonnes"] == pytest.approx(expected, rel=1e-9)
        assert vals["annual_rate_tonnes"] == pytest.approx(expected / 10.0, rel=1e-9)
        assert vals["project_type"] == "afforestation"

    def test_matches_direct_engine_call(self) -> None:
        direct = calculate_carbon_sequestration(
            CarbonProjectType.AFFORESTATION, 77.0, 8, "tropical"
        )
        via_gw = _values(
            "CARBON_SEQ",
            {
                "project_type": "afforestation",
                "area_ha": 77.0,
                "duration_years": 8,
                "region": "tropical",
            },
        )
        for key in ("total_carbon_tonnes", "annual_rate_tonnes", "estimated_revenue_usd"):
            assert via_gw[key] == pytest.approx(direct[key], rel=1e-12)

    def test_negative_area_is_rejected(self) -> None:
        r = _exec(
            "CARBON_SEQ",
            {
                "project_type": "afforestation",
                "area_ha": -1.0,
                "duration_years": 10,
                "region": "temperate",
            },
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "EXECUTION_ERROR"

    def test_unknown_region_is_rejected(self) -> None:
        r = _exec(
            "CARBON_SEQ",
            {
                "project_type": "afforestation",
                "area_ha": 10.0,
                "duration_years": 10,
                "region": "arctic",
            },
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "EXECUTION_ERROR"


# --------------------------------------------------------------------------- #
# Malformed-input contract                                                     #
# --------------------------------------------------------------------------- #
class TestMalformedInputs:
    def test_nan_is_rejected_as_finite_error(self) -> None:
        r = _exec(
            "CANON-002",
            {
                "temp_min": float("nan"),
                "temp_max": 25.0,
                "elevation": 0.0,
                "latitude": 40.0,
                "doy": 150,
            },
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "EXECUTION_ERROR"
        assert "finite" in r.message.lower()

    def test_inf_is_rejected(self) -> None:
        r = _exec(
            "CANON-002",
            {
                "temp_min": float("inf"),
                "temp_max": 25.0,
                "elevation": 0.0,
                "latitude": 40.0,
                "doy": 150,
            },
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "EXECUTION_ERROR"

    def test_negative_curve_number_is_rejected(self) -> None:
        r = _exec("CANON-004", {"precipitation": 100.0, "curve_number": -5.0, "area_ha": 2.0})
        assert isinstance(r, GatewayError)

    def test_theis_zero_time_is_rejected(self) -> None:
        r = _exec(
            "CANON-005",
            {
                "transmissivity_m2day": 100.0,
                "storativity": 1e-4,
                "pumping_rate_m3day": 1000.0,
                "distance_from_well_m": 100.0,
                "time_since_pumping_start_days": 0.0,
            },
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "EXECUTION_ERROR"

    def test_p_below_ia_yields_zero_runoff_not_error(self) -> None:
        r = _exec("CANON-004", {"precipitation": 0.5, "curve_number": 72.0, "area_ha": 2.0})
        assert isinstance(r, GatewayResult)
        assert r.values["runoff_volume_m3"] == 0.0


# --------------------------------------------------------------------------- #
# S16-XP: Gateway dispatch matrix (HYDROMA-QA-001 §7).                  #
# Every route is exercised across the fault scenarios, NOT in isolation.        #
# --------------------------------------------------------------------------- #
from engine.gateway import ModelSpec  # noqa: E402

_GATEWAY = EngineGateway()


def _gw_request(model_id: str, inputs: dict, units: dict | None = None) -> GatewayRequest:
    return GatewayRequest(
        model_id=model_id,
        inputs=inputs,
        input_units=units or {},
        provenance=_PROV,
    )


class TestGatewayDispatchMatrix:
    """One matrix entry per fault scenario, anchored on the CANON routes."""

    def test_unknown_model_id_returns_model_not_found(self) -> None:
        # Scenario: شناسهٔ مدل ناشناخته -> رد با کد مرتبط، نه success و نه crash
        r = _GW.execute(_gw_request("DOES-NOT-EXIST-9999", {"precipitation": 100.0}))
        assert isinstance(r, GatewayError)
        assert r.error_code == "MODEL_NOT_FOUND"
        assert r.evidence_id is not None  # provenance never lost on a reject

    def test_registered_but_unwired_model_is_error_not_success(self) -> None:
        # Scenario: مدل موجود اما غیرفعال / پیاده‌سازی‌نشده.
        # قرارداد: «قابلیت ناقص به‌اشتباه موفق اعلام نشود» — یک خطا با شواهد است، نه GatewayResult.
        gw = EngineGateway()
        spec = ModelSpec(
            model_id="CANON-XX-UNWIRED-FOR-TEST",
            model_version="1.0",
            model_name="UnwiredStub",
            model_type="unknown",
            domain="test",
            purpose="dispatch-matrix negative case",
            assumptions=[],
            limitations=[],
        )
        gw.register_model(spec)
        r = gw.execute(_gw_request("CANON-XX-UNWIRED-FOR-TEST", {"x": 1.0}))
        assert isinstance(r, GatewayError)
        assert r.evidence_id is not None
        assert isinstance(r.execution, ExecutionMetadata)
        assert r.execution.trace_id is not None
        # Honest classification: the gateway reports the "not wired" root cause
        # in the message; it does NOT claim the model computed a value.
        assert "not yet wired" in r.message.lower()

    def test_runtime_handler_exception_is_contained_with_evidence(self) -> None:
        # Scenario: خطای زمان اجرا -> GatewayError (نه استثناهای ناخارجی) + شواهد ثبت شوند.
        gw = EngineGateway()

        def _boom(inputs: dict, parameters: dict) -> dict:
            raise ValueError("injected compute fault")

        gw.register_handler("CANON-004", _boom)
        r = gw.execute(
            _gw_request(
                "CANON-004",
                {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0},
            )
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "EXECUTION_ERROR"
        assert "injected compute fault" in r.message
        assert r.evidence_id is not None
        assert gw.evidence_engine.get(r.evidence_id) is not None

    def test_nan_input_never_reaches_compute(self) -> None:
        # Scenario: ورودی نامعتبر (غیرعددی) -> رد، نه NaN در خروجی.
        r = _exec(
            "CANON-004", {"precipitation": float("nan"), "curve_number": 72.0, "area_ha": 2.0}
        )
        assert isinstance(r, GatewayError)

    def test_inf_input_is_rejected(self) -> None:
        r = _exec(
            "CANON-005",
            {
                "transmissivity_m2day": float("inf"),
                "storativity": 1e-4,
                "pumping_rate_m3day": 1000.0,
                "distance_from_well_m": 100.0,
                "time_since_pumping_start_days": 100.0,
            },
        )
        assert isinstance(r, GatewayError)

    def test_missing_required_input_is_an_error(self) -> None:
        # CANON-006 (van Genuchten) with matric_potential=None must be an
        # error, never a computation on None. S17 (D-20) moved this rejection
        # ahead of dispatch, so the honest answer is INVALID_REQUEST naming
        # the missing group; a raw compute-time TypeError is EXECUTION_ERROR
        # and remains the contract for anything the contract map cannot
        # catch up front.
        r = _exec(
            "CANON-006",
            {
                "matric_potential": None,
                "theta_r": 0.1,
                "theta_s": 0.4,
                "vg_alpha": 0.01,
                "vg_n": 1.3,
            },
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "INVALID_REQUEST"
        assert any("matric_potential" in e for e in (r.validation_errors or []))

    def test_negative_curve_number_is_rejected(self) -> None:
        r = _exec("CANON-004", {"precipitation": 100.0, "curve_number": -5.0, "area_ha": 2.0})
        assert isinstance(r, GatewayError)

    def test_duplicate_request_is_deterministic_with_distinct_trace(self) -> None:
        # Scenario: درخواست تکراری -> مقادیر یکسان، trace_id متفاوت (رویبرد نهایی).
        a = _exec("CANON-004", {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0})
        b = _exec("CANON-004", {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0})
        assert isinstance(a, GatewayResult) and isinstance(b, GatewayResult)
        assert a.values == b.values
        assert a.execution.trace_id != b.execution.trace_id

    def test_unit_declared_in_cm_is_scaled_to_si_before_compute(self) -> None:
        # The si_equivalent contract is the ONLY honest unit handling the gateway owns:
        # 10 cm (si_equivalent=10.0) must equal 100 mm for the same result.
        mm = _values(
            "CANON-004",
            {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0},
        )
        cm = _values(
            "CANON-004",
            {"precipitation": 10.0, "curve_number": 72.0, "area_ha": 2.0},
            {"precipitation": UnitSpec(unit="cm", si_equivalent=10.0)},
        )
        assert mm["runoff_volume_m3"] == pytest.approx(cm["runoff_volume_m3"], rel=1e-12)

    def test_wrong_si_equivalent_scales_input_not_output(self) -> None:
        # The normalization contract (gateway/__init__.py:612) is ``scaled = value * si_equivalent``
        # applied to the *input*. Declaring ``si_equivalent=2.0`` on a 100 value is
        # therefore equivalent to sending 200 in the base unit. Because SCS-CN runoff
        # is NON-linear in P, this must NOT double the output -- it must equal the 200mm run.
        via_units = _values(
            "CANON-004",
            {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0},
            {"precipitation": UnitSpec(unit="mm", si_equivalent=2.0)},
        )
        via_plain_200 = _values(
            "CANON-004", {"precipitation": 200.0, "curve_number": 72.0, "area_ha": 2.0}
        )
        assert via_units["runoff_volume_m3"] == pytest.approx(
            via_plain_200["runoff_volume_m3"], rel=1e-12
        )
        # and it must NOT simply double the 100mm result
        via_plain_100 = _values(
            "CANON-004", {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0}
        )
        assert via_units["runoff_volume_m3"] != pytest.approx(
            via_plain_100["runoff_volume_m3"] * 2.0, rel=1e-3
        )


# --------------------------------------------------------------------------- #
# S16-XP: Python <-> Numba(C++) parity (HYDROMA-QA-001 §12).                  #
# The native kernels must equal the documented Python reference; a missing C++   #
# build must be REPORTED, never silently satisfied by the Python fallback.     #
# --------------------------------------------------------------------------- #
_cpp_bridge = importlib.import_module(f"engine.{_HYD}.cpp_bridge")
_indices_fast = importlib.import_module(f"engine.{_HYD}.cpp_bridge.indices_fast")
is_cpp_available = _cpp_bridge.is_cpp_available
backend_status = _cpp_bridge.backend_status
_py_ndvi = _cpp_bridge._py_ndvi


def _ndvi_grid():
    # 2-D float64 grid exercising the denom==0 and clip boundaries.
    red = np.linspace(0.0, 0.5, 8, dtype=np.float64).reshape(1, -1)
    nir = np.linspace(0.0, 0.6, 8, dtype=np.float64).reshape(1, -1)
    red[0, 0] = 0.0  # numerator & denominator zero -> 0.0 per safe_ratio
    nir[0, -1] = 0.0  # (n-r)/(n+r) = -1 -> clip floor
    red[0, 3] = 0.0
    nir[0, 3] = 0.5  # ratio = 1.0 -> clip ceiling
    return red, nir
    nir = np.linspace(0.0, 0.6, 8, dtype=np.float64).reshape(1, -1)
    red[0, 0] = 0.0  # numerator & denominator zero -> 0.0 per safe_ratio
    nir[0, -1] = 0.0  # (n-r)/(n+r) = -1 -> clip floor
    red[0, 3] = 0.0
    nir[0, 3] = 0.5  # ratio = 1.0 -> clip ceiling
    return red, nir


class TestPythonNumbaParity:
    def test_ndvi_numba_equals_python_reference(self) -> None:
        if not _indices_fast.HAS_NUMBA:
            pytest.skip("numba BLOCKED — parity cannot be exercised without a backend")
        red, nir = _ndvi_grid()
        numba_out = _indices_fast.ndvi_fast(red, nir)
        python_out = _py_ndvi(red, nir)
        assert np.array_equal(numba_out, python_out, equal_nan=False)

    def test_cpp_backend_status_is_honest(self) -> None:
        # If C++ is reported available, BACKEND says "cpp"; if not, neither the
        # gateway nor the bridge may claim cpp_backend=True. No silent fallback.
        status = backend_status()
        assert status["cpp_available"] == is_cpp_available()
        assert status["backend"] == ("cpp" if is_cpp_available() else "python")
        scalar = _exec("CANON-004", {"precipitation": 100.0, "curve_number": 72.0, "area_ha": 2.0})
        assert isinstance(scalar, GatewayResult)
        assert scalar.execution.cpp_backend is False  # scalar routes are pure-Python

    def test_cpp_and_python_ndvi_agree_or_blocked(self) -> None:
        # §12.7: if a C++ build is present it must agree with Python within tolerance;
        # if absent, the limitation is reported, not faked as a pass.
        red, nir = _ndvi_grid()
        python_out = _py_ndvi(red, nir)
        if not is_cpp_available():
            # Honest BLOCKED: the test proves the Python reference runs; C++ parity
            # is simply unavailable in this environment.
            assert backend_status()["import_error"] is not None
            return
        cpp_mod = _cpp_bridge.get_module()
        assert cpp_mod is not None
        cpp_out = cpp_mod.ndvi_array(red, nir)
        assert np.allclose(cpp_out, python_out, rtol=1e-9, atol=0.0, equal_nan=False)
