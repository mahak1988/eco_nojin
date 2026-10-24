"""S20 -- Process-Simulation Validation Register: the Hydroma simulation layer
against independent scientific references.

This module validates the models reached through the engine gateway's
simulation routes (SIM_CHAIN, SIM_ORCHESTRATE, SCENARIO, CLIMATE_PROJECTION,
CLIMATE_SCENARIO, CROP_YIELD, CROP_COMPARE) against references re-derived here
from the primary sources. Following rule 3 of HYDROMA-QA-001, no expectation is
copied from the engine's own code: a green test only proves the engine matched
an *independent* law. Where a law cannot be reproduced from a source I can cite,
it is marked UNVALIDATED in the module notes rather than asserted.

Independent sources
-------------------
SCS-CN runoff         : NRCS National Engineering Handbook Part 630 / TR-55,
                        SI form S=(25400/CN)-254 [mm], Ia=0.2S,
                        Q=(P-Ia)^2/(P+0.8S) for P>Ia else 0.
RUSLE soil loss       : A = R K LS C P (Renard et al. 1997, USDA Agriculture
                        Handbook 703) -- multiplicative identity.
RUSLE LS factor       : McCool et al. (1987) slope-length/steepness form,
                        LS=(L/22.13)^m * S, m=beta/(1+beta),
                        beta=(sin(theta)/0.0896)/(3 sin(theta)^0.8 + 0.56),
                        S = 10.8 sin(theta)+0.03 (slope<9%) else 16.8 sin(theta)-0.5.
RothC temperature     : Coleman & Jenkinson (1996); Coleman, Prout & Milne
                        (2024) sec 1.6.1 eq (1) RM_Tmp=47.91/(1+e^(106.06/(T+18.27))),
                        zeroed below -5 C, normalised to 1.0 at 9.291 C.
RothC/other SOC laws  : carbon conservation (pools unbalanced only by respired
                        CO2 and residue input); monotonicity & saturation are
                        structural laws, not tuned answers.
Climate SSP ordering  : IPCC AR6 WG1 Table SPM.1 best-estimate 2081-2100 warming
                        magnitudes (relative to 1850-1900): SSP1-2.6 ~1.8,
                        SSP2-4.5 ~2.7, SSP3-7.0 ~3.6, SSP5-8.5 ~4.4 degC; the
                        monotone forcing ordering (SSP5-8.5 > SSP2-4.5 > SSP1-2.6).
Water-limited yield   : FAO AquaCrop / Stewart (Doorenbos & Kassam 1979) Ky
                        relation Ya/Ym = 1 - Ky(1 - ETa/ETm) implemented as the
                        engine's water stress multiplier.
Linearity-in-horizon  : wrapper.apply_scenario scale = min((year-2020)/30, 1.0),
                        so the SSP delta is linear in the horizon below its cap.

Honesty status of external runners
----------------------------------
SWAT+, WEAP and HEC-RAS are reported by run_chain as an explicit
``status == "not_computed"`` with a reason and ``data_source == "unavailable"``
-- never as fabricated zeros or invented arrays; these are asserted below.
AquaCrop is *not* "not computed" on this host: the ``aquacrop`` package is
installed, so the runner produces a real, provenance-labelled season result; a
test below pins that behaviour so the record is accurate rather than assumed.

Marked UNVALIDATED (no citation I can reproduce from a primary source here)
---------------------------------------------------------------------------
* The absolute SSP delta commit values in climate_scenarios (a documented
  "simplified regional" projection, not reproducible from IPCC tables verbatim);
  the structural laws that surround them (et0 sensitivity, apply arithmetic,
  forcing ordering, closest-horizon discretisation) ARE validated.
* The relative precipitation-change fractions in wrapper.apply_scenario
  (-0.05/-0.10/-0.15/-0.20); the temperature magnitudes are tied to IPCC AR6.
* The RothC *moisture* rate modifier (the in-house piecewise-linear form) against
  a golden RothC-26.3 reference output, which is not available offline; only its
  bounds and monotonicity are asserted. The temperature modifier, by contrast, is
  matched to the published equation exactly.
"""

from __future__ import annotations

import math
from typing import cast

import pytest

from engine.gateway import (
    EngineGateway,
    GatewayError,
    GatewayRequest,
    GatewayResult,
    ProvenanceSpec,
)
from engine.hydroma.scenarios.climate_scenarios import (
    apply_climate_change,
    get_climate_projection,
)
from engine.hydroma.scenarios.crop_scenarios import (
    CROP_DATABASE,
    CropParameters,
    compare_crops,
    simulate_crop_yield,
)
from engine.hydroma.simulation.contracts import MonthClimate
from engine.hydroma.simulation.runners.rothc_runner import (
    run_rothc,
    temp_factor,
    water_factor,
)
from engine.hydroma.wrapper import compute_erosion

GW = EngineGateway()
PROV = ProvenanceSpec(source="s20", source_type="TEST")

#: IPCC AR6 WG1 Table SPM.1 best-estimate 2081-2100 mean global warming (degC,
#: relative to 1850-1900) used as the independent temperature reference.
SSP_WARMING = {"ssp126": 1.8, "ssp245": 2.7, "ssp370": 3.6, "ssp585": 4.4}


def _values(model_id: str, inputs: dict) -> dict:
    r = GW.execute(
        GatewayRequest(model_id=model_id, inputs=inputs, input_units={}, provenance=PROV)
    )
    assert isinstance(r, GatewayResult), f"{model_id}: {r.error_code}: {r.message}"
    return r.values


# A complete chain-request body. use_real_weather stays False so the crop stage
# uses the runner's synthetic series and no network access is attempted.
CHAIN_BASE = {
    "site_id": "site-alpha",
    "area_ha": 12.0,
    "scenario": "Medium",
    "r_factor": 2000.0,
    "k_factor": 0.30,
    "ls_factor": 2.0,
    "c_factor_base": 0.50,
    "initial_soc_t_ha": 40.0,
    "clay_pct": 25.0,
    "residue_c_t_ha_per_month": 0.20,
    "years": 5,
    "crop": "Wheat",
    "use_real_weather": False,
}


def _chain(inputs: dict) -> dict:
    return cast("dict", _values("SIM_CHAIN", inputs)["chain"])


# ═══════════════════════════════════════════════════════════════════════════
# Honesty of the external runners + chain determinism
# ═══════════════════════════════════════════════════════════════════════════
class TestExternalRunnerHonesty:
    def test_swat_plus_reported_not_computed_with_reason(self) -> None:
        swat = _chain(CHAIN_BASE)["outputs"]["swat_plus"]
        assert swat["status"] == "not_computed"
        assert swat["data_source"] == "unavailable"
        assert swat["reason"], "an unavailable runner must give a reason"

    def test_external_runners_do_not_fabricate_numbers(self) -> None:
        swat = _chain(CHAIN_BASE)["outputs"]["swat_plus"]
        # No invented hydrology arrays/keys; the payload is a status dict only.
        for fabricated in ("runoff_mm", "runoff_m3", "water_yield_m3", "sedyld_t"):
            assert fabricated not in swat
        assert not any(isinstance(v, list) for v in swat.values())

    def test_weap_and_hecras_not_computed_and_explain_the_dependency(self) -> None:
        outs = _chain(CHAIN_BASE)["outputs"]
        for stage in ("weap", "hecras"):
            step = outs[stage]
            assert step["status"] == "not_computed"
            assert step["data_source"] == "unavailable"
            assert "SWAT" in step["reason"], step["reason"]

    def test_aquacrop_stage_is_actually_computed_on_this_host(self) -> None:
        # Contrast with the brief: AquaCrop is installed and runs. It must be a
        # real provenance-labelled number, not a "not_computed" marker.
        ac = _chain(CHAIN_BASE)["outputs"]["aquacrop"]
        assert ac.get("status") != "not_computed"
        assert ac.get("data_source") == "simulated"
        yield_kg_ha = ac.get("yield_kg_ha")
        assert yield_kg_ha is not None and math.isfinite(yield_kg_ha) and yield_kg_ha > 0.0

    def test_chain_is_deterministic_for_identical_inputs(self) -> None:
        a = _chain(CHAIN_BASE)
        b = _chain(CHAIN_BASE)
        for stage in ("swat_plus", "rusle", "rothc", "weap", "hecras"):
            assert a["outputs"][stage] == b["outputs"][stage]
        assert a["outputs"]["aquacrop"]["yield_kg_ha"] == b["outputs"]["aquacrop"]["yield_kg_ha"]

    def test_orchestrate_runs_each_requested_chain_and_marks_honesty(self) -> None:
        runs = _values(
            "SIM_ORCHESTRATE",
            {"chains": [CHAIN_BASE, dict(CHAIN_BASE, site_id="site-beta", scenario="Baseline")]},
        )
        orc = runs["orchestration"]
        assert orc["chain_count"] == 2
        assert len(orc["runs"]) == 2
        for run in orc["runs"]:
            assert run["status"] in ("ok", "partial")
            assert run["outputs"]["swat_plus"]["status"] == "not_computed"
            assert run["outputs"]["hecras"]["status"] == "not_computed"


# ═══════════════════════════════════════════════════════════════════════════
# SCS-CN runoff -- NRCS TR-55 curve-number equation (independent)          #
# ═══════════════════════════════════════════════════════════════════════════
def _scs_cn_depth(precip_mm: float, cn: float) -> float:
    """Independent NRCS TR-55 SI runoff depth [mm]."""
    s = 25400.0 / cn - 254.0
    ia = 0.2 * s
    if precip_mm <= ia:
        return 0.0
    return (precip_mm - ia) ** 2 / (precip_mm + 0.8 * s)


class TestScsCnRunoffIndependent:
    @pytest.mark.parametrize(
        "precip,cn",
        [(90.0, 70.0), (50.0, 60.0), (30.0, 85.0), (120.0, 75.0), (200.0, 65.0)],
    )
    def test_runoff_depth_matches_nrcs_equation(self, precip: float, cn: float) -> None:
        got = _values(
            "CANON-004",
            {"precipitation_mm": precip, "curve_number": cn, "area_ha": 1.0},
        )
        assert got["runoff_depth_mm"] == pytest.approx(_scs_cn_depth(precip, cn), rel=1e-9)

    def test_runoff_volume_is_depth_times_area(self) -> None:
        precip, cn, area = 90.0, 70.0, 3.0
        got = _values(
            "CANON-004",
            {"precipitation_mm": precip, "curve_number": cn, "area_ha": area},
        )
        ref_vol = _scs_cn_depth(precip, cn) * area * 10.0
        assert got["runoff_volume_m3"] == pytest.approx(ref_vol, rel=1e-9)

    def test_zero_runoff_at_or_below_initial_abstraction(self) -> None:
        cn = 70.0
        ia = 0.2 * (25400.0 / cn - 254.0)
        got = _values(
            "CANON-004", {"precipitation_mm": ia, "curve_number": cn, "area_ha": 1.0}
        )
        assert got["runoff_depth_mm"] == 0.0

    def test_runoff_monotone_in_rainfall(self) -> None:
        depths = [
            _values(
                "CANON-004",
                {"precipitation_mm": p, "curve_number": 80.0, "area_ha": 1.0},
            )["runoff_depth_mm"]
            for p in (60.0, 80.0, 100.0, 140.0, 200.0, 300.0)
        ]
        assert all(a <= b for a, b in zip(depths, depths[1:], strict=False))

    def test_runoff_monotone_in_curve_number(self) -> None:
        depths = [
            _values(
                "CANON-004",
                {"precipitation_mm": 90.0, "curve_number": cn, "area_ha": 1.0},
            )["runoff_depth_mm"]
            for cn in (50.0, 60.0, 70.0, 80.0, 90.0, 98.0)
        ]
        assert all(a <= b for a, b in zip(depths, depths[1:], strict=False))

    def test_runoff_bounded_below_rainfall(self) -> None:
        for precip, cn in ((90.0, 70.0), (60.0, 90.0), (150.0, 60.0)):
            depth = _values(
                "CANON-004",
                {"precipitation_mm": precip, "curve_number": cn, "area_ha": 1.0},
            )["runoff_depth_mm"]
            assert 0.0 <= depth < precip

    def test_chain_hydrology_is_delegated_not_computed(self) -> None:
        # run_chain has no inline SCS-CN stage: its hydrology/runoff step is the
        # external SWAT+ runner, which is reported "not_computed" here. The
        # SCS-CN equation itself is independently validated through CANON-004.
        assert _chain(CHAIN_BASE)["outputs"]["swat_plus"]["status"] == "not_computed"

    def test_scenario_cn_change_is_inert_in_chain(self) -> None:
        # DOCUMENTED GAP: ScenarioParams.cn_change is never consumed by run_chain,
        # so chains differing only in cn_change give identical results. Recorded
        # as a gap (no inline SCS-CN) rather than a validated behaviour.
        base_p = {"name": "Baseline", "c_factor_factor": 1.0, "p_factor": 1.0}
        a = _chain(dict(CHAIN_BASE, scenario={**base_p, "cn_change": 0.0}))
        b = _chain(dict(CHAIN_BASE, scenario={**base_p, "cn_change": -15.0}))
        assert a["outputs"]["rusle"] == b["outputs"]["rusle"]


# ═══════════════════════════════════════════════════════════════════════════
# RUSLE erosion -- A=R K LS C P identity and the McCool LS form            #
# ═══════════════════════════════════════════════════════════════════════════
def _mccool_ls(slope_length_m: float, slope_percent: float) -> float:
    """Independent McCool et al. (1987) LS factor."""
    theta = math.atan(slope_percent / 100.0)
    if slope_percent / 100.0 < 0.09:
        s = 10.8 * math.sin(theta) + 0.03
    else:
        s = 16.8 * math.sin(theta) - 0.5
    s = max(s, 0.0)
    sin_t = math.sin(theta)
    beta = (sin_t / 0.0896) / (3.0 * sin_t**0.8 + 0.56)
    m = beta / (1.0 + beta)
    length_factor: float = (slope_length_m / 22.13) ** m
    return length_factor * s


class TestRusleErosionIndependent:
    # Gateway scenario presets (gateway __init__ _CHAIN_SCENARIO_PRESETS).
    MEDIUM = {"c_factor_factor": 0.7, "p_factor": 0.8}
    R, K, LS, C = 2000.0, 0.30, 2.0, 0.50

    def test_erosion_before_is_rekcp_identity(self) -> None:
        rusle = _chain(CHAIN_BASE)["outputs"]["rusle"]
        ref = self.R * self.K * self.LS * self.C * 1.0
        assert rusle["erosion_before_t_ha"] == pytest.approx(ref, rel=1e-9)

    def test_erosion_after_applies_scenario_c_and_p(self) -> None:
        rusle = _chain(CHAIN_BASE)["outputs"]["rusle"]
        ref = self.R * self.K * self.LS * (self.C * 0.7) * (1.0 * 0.8)
        assert rusle["erosion_after_t_ha"] == pytest.approx(ref, rel=1e-9)

    def test_reduction_pct_is_the_identity(self) -> None:
        rusle = _chain(CHAIN_BASE)["outputs"]["rusle"]
        ref = (
            (rusle["erosion_before_t_ha"] - rusle["erosion_after_t_ha"])
            / rusle["erosion_before_t_ha"]
            * 100.0
        )
        assert rusle["reduction_pct"] == pytest.approx(ref, rel=1e-9)

    def test_baseline_scenario_does_not_change_erosion(self) -> None:
        rusle = _chain(dict(CHAIN_BASE, scenario="Baseline"))["outputs"]["rusle"]
        assert rusle["erosion_after_t_ha"] == pytest.approx(rusle["erosion_before_t_ha"])

    def test_mitigation_never_increases_soil_loss(self) -> None:
        mitigation = _chain(CHAIN_BASE)["outputs"]["rusle"]["erosion_after_t_ha"]
        baseline = _chain(dict(CHAIN_BASE, scenario="Baseline"))["outputs"]["rusle"][
            "erosion_before_t_ha"
        ]
        assert mitigation <= baseline + 1e-9

    @pytest.mark.parametrize(
        "length_m,slope_pct",
        [(22.0, 8.0), (50.0, 15.0), (100.0, 25.0), (10.0, 3.0)],
    )
    def test_ls_factor_follows_mccool_form(self, length_m: float, slope_pct: float) -> None:
        er = compute_erosion(length_m, slope_pct, 700.0)
        assert er["LS_factor"] == pytest.approx(_mccool_ls(length_m, slope_pct), abs=0.01)

    def test_rusle_identity_holds_through_wrapper(self) -> None:
        er = compute_erosion(50.0, 15.0, 700.0, "loam", 0.4, 0.7)
        ident = er["R_factor"] * er["K_factor"] * er["LS_factor"] * er["C_factor"] * er["P_factor"]
        assert er["annual_soil_loss_t_per_ha"] == pytest.approx(ident, rel=5e-3)


# ═══════════════════════════════════════════════════════════════════════════
# RothC soil-carbon -- conservation, monotonicity, saturation, temp law    #
# ═══════════════════════════════════════════════════════════════════════════
# A wet, mild reference climate: water_factor == 1.0 at every month so the
# only carbon fluxes are the fixed residue input and respired CO2.
WET = [
    MonthClimate(year=2020, month=m, tmean_c=15.0, smd_mm=0.0, max_smd_mm=60.0)
    for m in range(1, 13)
]


class TestRothcSocLaws:
    def test_carbon_ledger_is_closed(self) -> None:
        # Conservation: soc_after = soc_before + residue_carbon_in - respired_CO2.
        for res in (0.0, 0.2, 0.5, 1.0):
            r = run_rothc(40.0, 25.0, WET, res, years=5)
            total_in = 5 * 12 * res
            assert r["soc_after_t_ha"] == pytest.approx(
                40.0 + total_in - r["co2_respired_t_ha"], abs=1e-3
            )

    def test_zero_amendment_only_loses_carbon(self) -> None:
        r = run_rothc(40.0, 25.0, WET, 0.0, years=5)
        assert r["soc_after_t_ha"] < 40.0
        assert r["soc_after_t_ha"] == pytest.approx(40.0 - r["co2_respired_t_ha"], abs=1e-3)

    def test_more_amendment_never_lowers_soc(self) -> None:
        s0 = run_rothc(40.0, 25.0, WET, 0.0, years=5)["soc_after_t_ha"]
        s1 = run_rothc(40.0, 25.0, WET, 0.5, years=5)["soc_after_t_ha"]
        s2 = run_rothc(40.0, 25.0, WET, 1.0, years=5)["soc_after_t_ha"]
        assert s0 < s1 < s2

    def test_restorative_scenario_soc_non_decreasing_with_years(self) -> None:
        soc = [
            run_rothc(40.0, 25.0, WET, 1.0, years=y)["soc_after_t_ha"]
            for y in (1, 3, 5, 10, 20)
        ]
        assert all(a <= b for a, b in zip(soc, soc[1:], strict=False))
        assert soc[-1] > soc[0]

    def test_accumulation_saturates_with_diminishing_increment(self) -> None:
        s = {y: run_rothc(40.0, 25.0, WET, 1.0, years=y)["soc_after_t_ha"] for y in (1, 2, 19, 20)}
        first_step = s[2] - s[1]
        last_step = s[20] - s[19]
        assert first_step > last_step > 0.0

    def test_soc_is_bounded_above(self) -> None:
        s50 = run_rothc(40.0, 25.0, WET, 1.0, years=50)["soc_after_t_ha"]
        assert s50 < 150.0  # finite ceiling, not divergence

    def test_temp_factor_matches_published_rothc_equation(self) -> None:
        # Coleman & Jenkinson (1996) / RothC (2024 1.6.1 eq 1) tabulated points.
        for t, expect in ((-6.0, 0.0), (0.0, 0.144), (10.0, 1.099), (20.0, 2.822), (30.0, 4.791)):
            assert temp_factor(t) == pytest.approx(expect, abs=2e-3)

    def test_temp_factor_normalised_to_one_at_rothamsted(self) -> None:
        assert temp_factor(9.291) == pytest.approx(1.0, abs=2e-3)

    def test_temp_factor_is_monotone_increasing(self) -> None:
        xs = [temp_factor(t) for t in range(-4, 31, 2)]
        assert all(a <= b for a, b in zip(xs, xs[1:], strict=False))

    def test_moisture_factor_bounded_and_monotone(self) -> None:
        vals = [water_factor(s, 60.0) for s in (0, 10, 20, 30, 40, 50, 60)]
        assert all(0.2 <= v <= 1.0 for v in vals)
        assert all(a >= b for a, b in zip(vals, vals[1:], strict=False))
        assert water_factor(0.0, 60.0) == pytest.approx(1.0)
        assert water_factor(60.0, 60.0) == pytest.approx(0.2)


# ═══════════════════════════════════════════════════════════════════════════
# Climate scenarios -- climate_scenarios.py structural laws               #
# ═══════════════════════════════════════════════════════════════════════════
class TestClimateScenarios:
    def test_projection_et0_sensitivity(self) -> None:
        p = get_climate_projection("SSP2-4.5", 2050)
        assert p.delta_temp is not None
        assert p.delta_et0 is not None
        assert p.delta_et0 == pytest.approx(2.5 * p.delta_temp, rel=1e-9)
        assert 2.0 <= p.delta_et0 / p.delta_temp <= 3.0  # documented 2-3 %/degC

    def test_projection_uses_closest_discrete_horizon(self) -> None:
        # The projection is discretised to {2030,2050,2100} by nearest year; it is
        # NOT linear in the horizon (recorded as an honest observation).
        assert get_climate_projection("SSP2-4.5", 2049).time_horizon == 2050
        assert get_climate_projection("SSP2-4.5", 2051).time_horizon == 2050
        assert get_climate_projection("SSP1-2.6", 2029).time_horizon == 2030

    def test_apply_climate_change_arithmetic(self) -> None:
        p = get_climate_projection("SSP2-4.5", 2050)
        assert p.delta_temp is not None
        assert p.delta_precip is not None
        assert p.delta_et0 is not None
        app = apply_climate_change(18.0, 300.0, 1500.0, p)
        assert app["temperature"] == pytest.approx(round(18.0 + p.delta_temp, 1), abs=1e-9)
        assert app["precipitation"] == pytest.approx(
            round(300.0 * (1 + p.delta_precip / 100.0), 0), abs=1e-9
        )
        assert app["et0"] == pytest.approx(round(1500.0 * (1 + p.delta_et0 / 100.0), 0), abs=1e-9)

    def test_scenario_ordering_by_forcing(self) -> None:
        for yr in (2030, 2050, 2100):
            dt = cast("dict[str, float]", {
                s: get_climate_projection(s, yr).delta_temp
                for s in ("SSP1-2.6", "SSP2-4.5", "SSP5-8.5")
            })
            dp = cast("dict[str, float]", {
                s: get_climate_projection(s, yr).delta_precip
                for s in ("SSP1-2.6", "SSP2-4.5", "SSP5-8.5")
            })
            assert dt["SSP5-8.5"] > dt["SSP2-4.5"] > dt["SSP1-2.6"] > 0.0
            assert dp["SSP5-8.5"] < dp["SSP2-4.5"] < dp["SSP1-2.6"] <= 0.0

    def test_unknown_projection_scenario_raises(self) -> None:
        with pytest.raises(ValueError):
            get_climate_projection("SSP9-9.9", 2050)

    def test_climate_projection_route_matches_module(self) -> None:
        got = _values("CLIMATE_PROJECTION", {"rcp": "SSP5-8.5", "year": 2100})["projection"]
        p = get_climate_projection("SSP5-8.5", 2100)
        assert got["delta_temp"] == pytest.approx(p.delta_temp)
        assert got["delta_precip"] == pytest.approx(p.delta_precip)
        assert got["time_horizon"] == 2100


# ═══════════════════════════════════════════════════════════════════════════
# wrapper.apply_scenario (SCENARIO route) -- linear-in-horizon SSP scaling  #
# ═══════════════════════════════════════════════════════════════════════════
class TestWrapperScenario:
    def _scenario(self, scenario: str, target_year: int, precip: float = 300.0) -> dict:
        return cast(
            "dict",
            _values(
                "SCENARIO",
                {
                    "scenario": scenario,
                    "baseline_temp": 18.0,
                    "baseline_precip": precip,
                    "target_year": target_year,
                },
            )["scenario_impact"],
        )

    def test_baseline_year_has_zero_delta(self) -> None:
        got = self._scenario("ssp245", 2020)
        assert got["temperature_change"] == pytest.approx(0.0, abs=1e-9)
        assert got["precipitation_change_percent"] == pytest.approx(0.0, abs=1e-9)
        assert got["projected_temperature"] == pytest.approx(18.0, abs=1e-9)

    def test_temp_delta_linear_in_horizon_below_cap(self) -> None:
        inc = SSP_WARMING["ssp245"]
        got = self._scenario("ssp245", 2035)
        assert got["temperature_change"] == pytest.approx(inc * (2035 - 2020) / 30.0, abs=1e-9)

    def test_horizon_capped_at_thirty_years(self) -> None:
        at_cap = self._scenario("ssp245", 2050)
        past_cap = self._scenario("ssp245", 2100)
        assert at_cap["temperature_change"] == pytest.approx(SSP_WARMING["ssp245"], abs=1e-9)
        assert past_cap["temperature_change"] == pytest.approx(at_cap["temperature_change"])

    def test_precip_multiplier_is_consistent(self) -> None:
        got = self._scenario("ssp245", 2035, precip=400.0)
        pct = got["precipitation_change_percent"]
        assert got["projected_precipitation"] == pytest.approx(400.0 * (1 + pct / 100.0), abs=1e-9)

    def test_ssp_warming_magnitudes_match_ipcc_ar6(self) -> None:
        for ssp, inc in SSP_WARMING.items():
            got = self._scenario(ssp, 2050)
            assert got["temperature_change"] == pytest.approx(inc, abs=1e-6)

    def test_unknown_scenario_raises(self) -> None:
        r = GW.execute(
            GatewayRequest(
                model_id="SCENARIO",
                inputs={
                    "scenario": "ssp999",
                    "baseline_temp": 18.0,
                    "baseline_precip": 300.0,
                    "target_year": 2050,
                },
                input_units={},
                provenance=PROV,
            )
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "EXECUTION_ERROR"


# ═══════════════════════════════════════════════════════════════════════════
# Crop yield -- water-limited yield law (FAO AquaCrop / Ky)                #
# ═══════════════════════════════════════════════════════════════════════════
def _crop_water_requirement(crop: CropParameters) -> float:
    return crop.crop_coefficient_max * crop.growing_season_days * 3.0


def _ref_water_factor(crop: CropParameters, available_water: float) -> float:
    req = _crop_water_requirement(crop)
    if available_water >= req:
        return 1.0
    return max(0.0, 1.0 - crop.drought_sensitivity * (1.0 - available_water / req))


def _ref_temp_factor(crop: CropParameters, mean_temp: float) -> float:
    if mean_temp < crop.base_temp:
        return 0.0
    if mean_temp <= crop.optimal_temp:
        return (mean_temp - crop.base_temp) / (crop.optimal_temp - crop.base_temp)
    if mean_temp <= crop.max_temp:
        return 1.0 - 0.5 * (mean_temp - crop.optimal_temp) / (crop.max_temp - crop.optimal_temp)
    return max(0.0, 0.5 - (mean_temp - crop.max_temp) / 10.0)


def _ref_yield(
    crop: CropParameters, available_water: float, mean_temp: float, co2: float = 420.0, eff: float = 0.6
) -> float:
    req = _crop_water_requirement(crop)
    tf = _ref_temp_factor(crop, mean_temp)
    wf = _ref_water_factor(crop, available_water)
    co2f = min(1.0 + 0.05 * (co2 - 400.0) / 100.0, 1.3)
    transpiration = min(available_water, req) * eff
    potential = crop.water_productivity * transpiration
    return potential * tf * wf * co2f * 10.0


class TestCropYieldIndependent:
    def test_zero_available_water_gives_exactly_zero_yield(self) -> None:
        for crop in ("wheat", "corn", "millet"):
            assert simulate_crop_yield(crop, 0.0, 20.0)["yield_kg_per_ha"] == 0

    def test_yield_nondecreasing_in_available_water(self) -> None:
        waters = (0.0, 100.0, 200.0, 300.0, 400.0, 500.0, 594.0, 700.0, 1000.0)
        ys = [simulate_crop_yield("wheat", aw, 20.0)["yield_kg_per_ha"] for aw in waters]
        assert all(a <= b for a, b in zip(ys, ys[1:], strict=False))

    def test_water_factor_follows_ky_relation(self) -> None:
        wheat = CROP_DATABASE["wheat"]
        for aw in (0.0, 150.0, 300.0, 450.0, 600.0, 700.0):
            got = simulate_crop_yield("wheat", aw, 20.0)["water_factor"]
            assert got == pytest.approx(round(_ref_water_factor(wheat, aw), 4), abs=1e-9)

    @pytest.mark.parametrize(
        "crop,aw,temp",
        [("wheat", 400.0, 20.0), ("corn", 600.0, 18.0), ("wheat", 1200.0, 25.0),
         ("millet", 200.0, 28.0)],
    )
    def test_yield_matches_independent_reimplementation(self, crop, aw, temp) -> None:
        got = simulate_crop_yield(crop, aw, temp)["yield_kg_per_ha"]
        ref = _ref_yield(CROP_DATABASE[crop], aw, temp)
        assert got == pytest.approx(round(ref, 0), abs=1.0)

    def test_temperature_stress_endpoints(self) -> None:
        assert simulate_crop_yield("corn", 800.0, -5.0)["temp_factor"] == 0.0
        assert simulate_crop_yield("corn", 800.0, 45.0)["temp_factor"] == 0.0
        assert simulate_crop_yield("corn", 800.0, 25.0)["temp_factor"] == pytest.approx(1.0)

    def test_route_matches_direct_call(self) -> None:
        route = _values(
            "CROP_YIELD",
            {"crop_type": "wheat", "climate_data": {"available_water": 400.0, "mean_temp": 20.0}},
        )["yield"]["yield_kg_per_ha"]
        direct = simulate_crop_yield("wheat", 400.0, 20.0)["yield_kg_per_ha"]
        assert route == direct

    def test_unknown_crop_raises(self) -> None:
        with pytest.raises(ValueError):
            simulate_crop_yield("kryptonite", 300.0, 20.0)


# ═══════════════════════════════════════════════════════════════════════════
# CROP_COMPARE -- ranking consistency + drought-tolerance law              #
# ═══════════════════════════════════════════════════════════════════════════
class TestCropCompare:
    def test_ranking_sorted_by_gross_revenue_desc(self) -> None:
        res = compare_crops(300.0, 22.0)
        revenue = [(c, res["details"][c]["gross_revenue_usd_ha"]) for c in res["ranking"]]
        assert revenue == sorted(revenue, key=lambda kv: kv[1], reverse=True)

    def test_best_economic_choice_is_ranking_head(self) -> None:
        res = compare_crops(300.0, 22.0)
        assert res["best_economic_choice"] == res["ranking"][0]
        assert res["ranking"][0] in res["details"]

    def test_most_drought_tolerant_is_max_water_stress_factor(self) -> None:
        res = compare_crops(200.0, 25.0)
        best = max(res["details"].items(), key=lambda kv: kv[1]["water_stress_factor"])[0]
        assert res["most_drought_tolerant"] == best

    def test_drought_tolerance_law_under_deficit(self) -> None:
        # Millet carries the lowest drought sensitivity (0.2) and a small water
        # requirement, so under a deficit it must be retained as most tolerant.
        res = compare_crops(100.0, 25.0)
        assert res["most_drought_tolerant"] == "millet"


# ═══════════════════════════════════════════════════════════════════════════
# Regressions for the engine defects that were fixed in B5                 #
# ═══════════════════════════════════════════════════════════════════════════
class TestFixedEngineDefects:
    """Both defects were repaired; these pin the repaired behaviour.

    * the CROP_COMPARE route used to forward ``crop_a`` / ``crop_b`` /
      ``climate_data`` positionally into ``compare_crops(available_water,
      mean_temp, co2_concentration)``. A string ``available_water`` made every
      ``simulate_crop_yield`` call raise, which ``compare_crops`` swallowed, so
      the route answered with an empty ranking and
      ``best_economic_choice=None``.
    * the CLIMATE_SCENARIO route used to forward ``years_ahead`` (a duration)
      into the absolute ``time_horizon`` slot, so ``years_ahead=30`` resolved
      to the 2030 row instead of ~2050.
    """

    def test_gateway_crop_compare_returns_functional_comparison(self) -> None:
        route = _values(
            "CROP_COMPARE",
            {"crop_a": "wheat", "crop_b": "corn",
             "climate_data": {"available_water": 300.0, "mean_temp": 22.0}},
        )
        assert route["ranking"], "gateway CROP_COMPARE returned an empty ranking"
        assert route["best_economic_choice"] == route["ranking"][0]
        direct = compare_crops(300.0, 22.0)
        assert route["ranking"] == direct["ranking"]

    def test_gateway_climate_scenario_years_ahead_is_a_horizon_year(self) -> None:
        proj = _values(
            "CLIMATE_SCENARIO",
            {"rcp": "SSP2-4.5", "years_ahead": 30, "baseline_temp": 18.0,
             "baseline_precip": 300.0, "baseline_et0": 1500.0},
        )["projection"]
        # "30 years ahead" of a ~2020 baseline must not collapse to the 2030 row.
        assert proj["time_horizon"] == 2050

    def test_gateway_crop_yield_reads_the_climate_mapping(self) -> None:
        """The two scalars the route reads flat must also come from the mapping."""
        nested = _values(
            "CROP_YIELD",
            {"crop_type": "wheat",
             "climate_data": {"available_water": 300.0, "mean_temp": 22.0,
                              "irrigation_efficiency": 0.9,
                              "co2_concentration": 500.0}},
        )
        flat = _values(
            "CROP_YIELD",
            {"crop_type": "wheat", "available_water": 300.0, "mean_temp": 22.0,
             "irrigation_efficiency": 0.9, "co2_concentration": 500.0},
        )
        assert nested["yield"] == flat["yield"]
