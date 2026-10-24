"""Scenario-layer regression suite.

Pins the behaviour fixed in this change so the defects cannot silently return:

1. ``simulate_climate_change`` emits the SSP projection deltas (it used to raise
   ``AttributeError`` because ``ClimateProjection`` is a ``@dataclass``, not a
   pydantic model, and was treated as if it had ``model_dump``).
2. ``simulate_drought`` yield loss is strictly monotonic in severity, bounded in
   [0, 100], single sign across severities and flash, and soil moisture / NDVI
   actually respond to the drought trajectory (the bucket used to initialise
   every day from the same half-full value instead of carrying the balance).
3. RothC emission/sign convention (emission-positive, consistent with
   ``co2_respired_t_ha``).
4. HY-RUE wheat heat/stress direction, the misleading crop-neutral default, the
    ``lai_max`` clip, the EWSI -> f_water complement, and the seasonal (daily
    integration) mode that sums per-day biomass instead of multiplying a single
    day by ``days``.
5. DecisionEngine per-criterion threshold enforcement.
6. Gateway RECOMMEND never returns an empty success.
"""

from __future__ import annotations

import warnings
from typing import Any, cast

import numpy as np
import pytest

from engine.hydroma.models.hyrue import HYRUE, HYRUEParams
from engine.hydroma.scenarios.climate_scenarios import CLIMATE_PROJECTIONS, get_climate_projection
from engine.hydroma.simulation.contracts import MonthClimate
from engine.hydroma.simulation.runners.rothc_runner import run_rothc
from engine.hydroma.simulation_env.climate import (
    DroughtScenario,
    simulate_climate_change,
    simulate_drought,
)
from engine.tasmimyar import DecisionCriterion, DecisionEngine, DecisionOutcome

_SEVERITIES = ["mild", "moderate", "severe", "extreme"]


def _drought(severity: str, *, flash: bool = False, seed: int = 42, years: int = 5):
    return simulate_drought(
        baseline_temp_c=18.0,
        baseline_precip_mm=300.0,
        scenario=DroughtScenario(
            severity=severity, duration_years=years, flash_drought=flash
        ),
        lat=32.0,
        crop="wheat",
        seed=seed,
    )


# --------------------------------------------------------------------------- #
# 1. SSP climate-change projection                                             #
# --------------------------------------------------------------------------- #
class TestClimateChangeDeltas:
    def test_ssp245_2050_deltas(self) -> None:
        res = simulate_climate_change(
            baseline_temp_c=18.0,
            baseline_precip_mm=300.0,
            ssp="SSP2-4.5",
            target_year=2050,
            lat=32.0,
            crop="wheat",
            seed=42,
            n_ensembles=25,
        )
        # The engine's own SSP2-4.5/2050 values (verified against the
        # projection tables); no AttributeError, and the deltas are surfaced.
        summary = res["summary"]
        assert summary["delta_temp"] == 2.4
        assert summary["delta_precip"] == -8.0
        assert summary["delta_et0"] == 6.0

    def test_projection_block_matches_table(self) -> None:
        res = simulate_climate_change(
            baseline_temp_c=18.0,
            baseline_precip_mm=300.0,
            ssp="SSP2-4.5",
            target_year=2050,
            lat=32.0,
            crop="wheat",
            seed=42,
            n_ensembles=25,
        )
        dtemp, dprecip = CLIMATE_PROJECTIONS["SSP2-4.5"][2050]
        proj = res["projection"]
        assert proj["delta_temp"] == pytest.approx(dtemp)
        assert proj["delta_precip"] == pytest.approx(dprecip)
        # projected temperature applied to the baseline.
        assert res["projected_climate"]["temperature"] == pytest.approx(18.0 + dtemp)


# --------------------------------------------------------------------------- #
# 2. Drought severity ladder, bounds, and responsiveness                        #
# --------------------------------------------------------------------------- #
class TestDroughtSeverityLadder:
    def test_loss_monotonic_and_bounded(self) -> None:
        losses = [_drought(s).summary["cumulative_yield_loss_pct"] for s in _SEVERITIES]
        for loss in losses:
            assert 0.0 <= loss <= 100.0
        assert losses[0] < losses[1] < losses[2] < losses[3]

    def test_final_year_yield_monotonically_falls_with_severity(self) -> None:
        final_yields = [
            _drought(s).annual_impacts[-1].crop_yield_kg_ha for s in _SEVERITIES
        ]
        assert final_yields[0] > final_yields[1] > final_yields[2] > final_yields[3]

    def test_flash_same_sign_and_bounded(self) -> None:
        res = _drought("extreme", flash=True)
        loss = res.summary["cumulative_yield_loss_pct"]
        # Same non-negative convention as the escalating severities, and bounded.
        assert 0.0 <= loss <= 100.0

    def test_soil_moisture_and_ndvi_respond_to_trajectory(self) -> None:
        # Year 0 is unstressed (drought has not ramped); the final year is the
        # deepest drought. Soil moisture and NDVI must fall over that trajectory
        # (they used to be flat for every severity).
        res = _drought("severe")
        impacts = res.annual_impacts
        assert impacts[0].ndvi > impacts[-1].ndvi
        assert impacts[0].soil_moisture_fraction > impacts[-1].soil_moisture_fraction

    def test_ndvi_min_monotonically_falls_with_severity(self) -> None:
        minima = [_drought(s).summary["ndvi_min"] for s in _SEVERITIES]
        assert minima[0] > minima[1] > minima[2] > minima[3]

    def test_public_api_shape_stable(self) -> None:
        res = _drought("moderate")
        assert res.drought_curve  # per-year precip/temp factors
        assert res.annual_impacts[0].severity in {"mild", "moderate", "severe", "extreme"}
        for key in (
            "cumulative_yield_loss_pct",
            "ndvi_min",
            "ndvi_max",
            "final_soil_moisture_fraction",
        ):
            assert key in res.summary


# --------------------------------------------------------------------------- #
# 3. RothC emission-sign convention                                            #
# --------------------------------------------------------------------------- #
def _rothc_rows(offset: float = 0.0):
    temps = [10, 12, 15, 18, 22, 26, 28, 27, 22, 16, 12, 10]
    monthly = [
        MonthClimate(year=2024, month=m, tmean_c=t + offset, smd_mm=10.0, max_smd_mm=100.0)
        for m, t in enumerate(temps, start=1)
    ]
    return run_rothc(initial_soc_t_ha=40.0, clay_pct=25.0, monthly=monthly, years=1)


class TestRothcSignConvention:
    def test_emission_positive_and_consistent(self) -> None:
        base = _rothc_rows()
        # Soil carbon decreases (net source), so both emission-facing outputs
        # are positive and share one sign convention.
        assert base["soc_change_t_ha_yr"] < 0
        assert base["co2_respired_t_ha"] > 0
        assert base["co2e_t_ha"] > 0
        # Emission-positive means the co2e sign is OPPOSITE the carbon balance.
        assert np.sign(base["co2e_t_ha"]) == -np.sign(base["soc_change_t_ha_yr"])

    def test_no_input_net_equals_gross_scaled(self) -> None:
        base = _rothc_rows()
        # With no residue/manure input the net emission equals the gross
        # respiration expressed as CO2-equivalent.
        assert base["co2e_t_ha"] == pytest.approx(3.67 * base["co2_respired_t_ha"], rel=1e-3)

    def test_warming_increases_respiration_and_emission(self) -> None:
        base = _rothc_rows(0.0)
        warm = _rothc_rows(3.0)
        assert warm["co2_respired_t_ha"] > base["co2_respired_t_ha"]
        assert warm["co2e_t_ha"] > base["co2e_t_ha"]

    def test_respired_always_non_negative(self) -> None:
        assert _rothc_rows()["co2_respired_t_ha"] >= 0
        assert _rothc_rows(3.0)["co2_respired_t_ha"] >= 0


# --------------------------------------------------------------------------- #
# 4. HY-RUE heat/stress direction, default warning, lai_max clip, EWSI         #
# --------------------------------------------------------------------------- #
class TestHyrueWheatDirection:
    def _yield(self, temp: float) -> float:
        m = HYRUE(crop="wheat")
        return float(
            np.mean(
                m.compute(
                    par=15.0,
                    lai=np.array([3.0]),
                    ewsi=np.array([0.1]),
                    t_mean=temp,
                    days=120,
                )["yield_t_ha"]
            )
        )

    def test_wheat_yield_decreases_with_heat(self) -> None:
        y20 = self._yield(20.0)
        # Reference numbers from this change: wheat (t_opt=20) declines with
        # warming rather than increasing like the generic default would.
        assert (self._yield(22.0) - y20) / y20 == pytest.approx(-0.061, abs=5e-3)
        assert (self._yield(24.0) - y20) / y20 == pytest.approx(-0.221, abs=5e-3)
        assert (self._yield(26.0) - y20) / y20 == pytest.approx(-0.430, abs=5e-3)

    def test_generic_default_warns_about_heat_artifact(self) -> None:
        with pytest.warns(UserWarning, match="crop-neutral"):
            HYRUE()
        # Explicit params / explicit crop must not warn.
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            HYRUE(params=HYRUEParams())
            HYRUE(crop="wheat")

    def test_generic_default_heat_increases_yield_documented(self) -> None:
        # The flagged default (t_opt=25) still lets warming raise yield below 25C
        # -- the warning exists precisely so this stays documented, not trusted.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = HYRUE()
        kwargs: dict[str, Any] = {"lai": np.array([3.0]), "ewsi": np.array([0.1]), "days": 120}
        y20 = float(np.mean(m.compute(par=15.0, t_mean=20.0, **kwargs)["yield_t_ha"]))
        y26 = float(np.mean(m.compute(par=15.0, t_mean=26.0, **kwargs)["yield_t_ha"]))
        assert y26 > y20

    def test_lai_max_clips_canopy(self) -> None:
        # lai_max (default 6) caps the canopy: a LAI above it no longer increases
        # interception, and it matches the f_ipar value at the cap.
        at_cap = HYRUE.f_ipar(np.array([6.0]), 0.65, 6.0)[0]
        above = HYRUE.f_ipar(np.array([8.0]), 0.65, 6.0)[0]
        assert above == pytest.approx(at_cap)
        # The legacy two-argument call is unchanged for a sub-cap LAI.
        assert HYRUE.f_ipar(np.array([2.5]), 0.65)[0] == pytest.approx(
            1 - np.exp(-0.65 * 2.5)
        )

    def test_ewsi_complement_drives_water_stress(self) -> None:
        # EWSI in [0, 1] is a stress index (1 = severe). f_water = 1 - EWSI, so
        # higher EWSI must give lower yield (more water stress).
        m = HYRUE(crop="wheat")
        kwargs: dict[str, Any] = {"lai": np.array([3.0]), "t_mean": 20.0, "days": 120}
        y_none = float(np.mean(m.compute(par=15.0, ewsi=np.array([0.0]), **kwargs)["yield_t_ha"]))
        y_severe = float(
            np.mean(m.compute(par=15.0, ewsi=np.array([1.0]), **kwargs)["yield_t_ha"])
        )
        assert y_severe < y_none
        assert y_severe == pytest.approx(0.0)  # f_water = 0 -> no growth


# --------------------------------------------------------------------------- #
# 4b. HY-RUE seasonal (daily integration) mode                                #
# --------------------------------------------------------------------------- #
class TestHyrueSeasonalIntegration:
    """When ``par`` is an array the model integrates daily biomass (sum, not
    multiply-by-days). This resolves the yield overstatement from treating a
    peak-day figure as the whole season.
    """

    def test_seasonal_mode_sums_daily_biomass(self) -> None:
        m = HYRUE(crop="wheat")
        par = np.array([10.0, 15.0, 20.0, 20.0, 15.0])
        lai = np.array([1.0, 2.0, 3.0, 3.0, 2.0])
        ewsi = np.array([0.0, 0.0, 0.0, 0.1, 0.2])
        t = np.array([18.0, 20.0, 22.0, 22.0, 20.0])
        r = m.compute(par=par, lai=lai, ewsi=ewsi, t_mean=t)
        assert r["total_biomass_g_m2"] == pytest.approx(float(np.sum(r["daily_biomass_g_m2"])))

    def test_seasonal_mode_total_differs_from_scalar_multiple(self) -> None:
        m = HYRUE(crop="wheat")
        par_arr = np.array([10.0, 15.0, 20.0, 20.0, 15.0])
        lai_arr = np.array([1.0, 2.0, 3.0, 3.0, 2.0])
        ewsi_arr = np.array([0.0, 0.0, 0.0, 0.1, 0.2])
        t_arr = np.array([18.0, 20.0, 22.0, 22.0, 20.0])
        r_seasonal = m.compute(par=par_arr, lai=lai_arr, ewsi=ewsi_arr, t_mean=t_arr)

        # Scalar mode: single representative day * days=5
        par_scalar = float(np.mean(par_arr))
        lai_scalar = float(np.mean(lai_arr))
        ewsi_scalar = float(np.mean(ewsi_arr))
        t_scalar = float(np.mean(t_arr))
        r_scalar = m.compute(
            par=par_scalar, lai=np.array([lai_scalar]),
            ewsi=np.array([ewsi_scalar]), t_mean=t_scalar, days=5,
        )
        # The seasonal integration (varying conditions) must differ from the
        # constant-conditions multiplier. Varying LAI means peak days contribute
        # more than the mean-LAI assumption.
        assert r_seasonal["yield_t_ha"] != pytest.approx(
            float(np.mean(r_scalar["yield_t_ha"])), abs=1e-6
        )

    def test_scalar_mode_days_multiplier_still_works(self) -> None:
        m = HYRUE(crop="wheat")
        r1 = m.compute(par=15.0, lai=np.array([3.0]), ewsi=np.array([0.1]), t_mean=20.0, days=1)
        r120 = m.compute(par=15.0, lai=np.array([3.0]), ewsi=np.array([0.1]), t_mean=20.0, days=120)
        assert float(np.mean(r120["total_biomass_g_m2"])) == pytest.approx(
            float(np.mean(r1["total_biomass_g_m2"])) * 120
        )

    def test_seasonal_yield_below_scalar_multiplier(self) -> None:
        # Seasonal integration with a varying LAI trajectory must produce a
        # lower yield than the scalar multiplier mode using the same
        # representative day -- the multiplier assumes peak conditions
        # throughout, which overstates biomass.
        m = HYRUE(crop="wheat")
        par_val = 14.0
        lai_traj = np.concatenate([
            np.linspace(0.0, 2.0, 40),
            np.linspace(2.0, 4.0, 40),
        ])
        ewsi_traj = np.full(80, 0.1)
        t_traj = np.full(80, 20.0)

        r_seasonal = m.compute(
            par=np.full(80, par_val), lai=lai_traj,
            ewsi=ewsi_traj, t_mean=t_traj,
        )
        r_scalar = m.compute(
            par=par_val, lai=np.array([float(np.mean(lai_traj))]),
            ewsi=np.array([0.1]), t_mean=20.0, days=80,
        )
        seasonal_yield = float(np.mean(r_seasonal["yield_t_ha"]))
        scalar_yield = float(np.mean(r_scalar["yield_t_ha"]))
        assert seasonal_yield < scalar_yield
        assert seasonal_yield > 0.0

    def test_array_t_mean_evaluated_daily(self) -> None:
        m = HYRUE(crop="wheat")
        r = m.compute(
            par=20.0, lai=np.array([3.0, 3.0]),
            ewsi=np.array([0.1, 0.1]), t_mean=np.array([20.0, 40.0]),
        )
        # Day at t=40 exceeds t_max=35 -> f_temp=0 -> no biomass that day.
        assert float(r["daily_biomass_g_m2"][1]) == pytest.approx(0.0)
        assert float(r["daily_biomass_g_m2"][0]) > 0.0

    def test_incompatible_array_lengths_raise(self) -> None:
        m = HYRUE(crop="wheat")
        with pytest.raises(ValueError, match="broadcast"):
            m.compute(
                par=np.array([15.0, 16.0, 17.0]),
                lai=np.array([2.0, 2.5]),
                ewsi=np.array([0.1, 0.2, 0.3]),
                t_mean=np.array([20.0, 21.0, 22.0]),
            )

    def test_empty_arrays_return_zero_total(self) -> None:
        m = HYRUE(crop="wheat")
        r = m.compute(par=[], lai=[], ewsi=[], t_mean=[])
        assert r["total_biomass_g_m2"] == 0.0
        assert r["yield_t_ha"] == 0.0

    def test_scalar_broadcast_with_array_inputs(self) -> None:
        # Scalar par applied to multiple days with varying lai/ewsi/t_mean.
        # The result is per-day values (array), each multiplied by days=1 (scalar mode).
        m = HYRUE(crop="wheat")
        par_scalar = 15.0
        lai_arr = np.array([1.0, 2.0, 3.0])
        ewsi_arr = np.array([0.1, 0.1, 0.1])
        t_arr = np.array([18.0, 20.0, 22.0])
        r = m.compute(par=par_scalar, lai=lai_arr, ewsi=ewsi_arr, t_mean=t_arr)
        # Scalar par mode: total_biomass is daily_biomass * days (days=1 default).
        # Each day uses the same par=15.0.
        assert len(r["daily_biomass_g_m2"]) == 3
        assert r["total_biomass_g_m2"] == pytest.approx(r["daily_biomass_g_m2"])

    def test_seasonal_total_matches_daily_sum_three_days(self) -> None:
        # Independent verification: seasonal total must equal sum of daily.
        m = HYRUE(params=HYRUEParams(epsilon=2.2, hi=0.45, t_opt=20.0))
        par = np.array([10.0, 18.0, 16.0])
        lai = np.array([1.5, 3.2, 2.8])
        ewsi = np.array([0.0, 0.1, 0.3])
        t = np.array([18.0, 22.0, 25.0])
        r = m.compute(par=par, lai=lai, ewsi=ewsi, t_mean=t)
        expected_total = float(np.sum(r["daily_biomass_g_m2"]))
        assert r["total_biomass_g_m2"] == pytest.approx(expected_total)
        expected_yield = expected_total * 0.45 / 100
        assert r["yield_t_ha"] == pytest.approx(expected_yield)
        assert r["yield_g_m2"] == pytest.approx(r["total_biomass_g_m2"] * 0.45)

    def test_seasonal_mode_ignores_days_parameter(self) -> None:
        # In seasonal mode, days must not change the integration result.
        m = HYRUE(crop="wheat")
        par = np.array([10.0, 15.0, 20.0])
        lai = np.array([2.0, 2.5, 3.0])
        ewsi = np.array([0.1, 0.2, 0.3])
        t = np.array([20.0, 21.0, 22.0])
        r_no_days = m.compute(par=par, lai=lai, ewsi=ewsi, t_mean=t)
        r_with_days = m.compute(par=par, lai=lai, ewsi=ewsi, t_mean=t, days=120)
        assert r_no_days["yield_t_ha"] == pytest.approx(r_with_days["yield_t_ha"])
        assert r_no_days["total_biomass_g_m2"] == pytest.approx(
            r_with_days["total_biomass_g_m2"]
        )

    def test_seasonal_output_is_json_serializable(self) -> None:
        import json
        m = HYRUE(crop="wheat")
        r = m.compute(
            par=[15.0, 16.0, 17.0],
            lai=[2.0, 2.5, 3.0],
            ewsi=[0.1, 0.2, 0.3],
            t_mean=[20.0, 21.0, 22.0],
        )
        json.dumps(r)

    def test_validate_inputs_rejects_negative_par(self) -> None:
        m = HYRUE(crop="wheat")
        ok, errors = m.validate_inputs(
            par=-1.0, lai=np.array([3.0]), ewsi=np.array([0.1]), t_mean=20.0
        )
        assert not ok
        assert any("PAR" in e or "par" in e.lower() for e in errors)

    def test_validate_inputs_rejects_negative_lai(self) -> None:
        m = HYRUE(crop="wheat")
        ok, errors = m.validate_inputs(
            par=15.0, lai=np.array([-1.0]), ewsi=np.array([0.1]), t_mean=20.0
        )
        assert not ok
        assert any("LAI" in e or "lai" in e.lower() for e in errors)

    def test_validate_inputs_rejects_ewsi_out_of_range(self) -> None:
        m = HYRUE(crop="wheat")
        ok, errors = m.validate_inputs(
            par=15.0, lai=np.array([3.0]), ewsi=np.array([1.5]), t_mean=20.0
        )
        assert not ok
        assert any("EWSI" in e for e in errors)

    def test_validate_inputs_rejects_nan(self) -> None:
        m = HYRUE(crop="wheat")
        ok, errors = m.validate_inputs(
            par=15.0, lai=np.array([3.0]), ewsi=np.array([0.1]),
            t_mean=np.array([20.0, float("nan")]),
        )
        assert not ok
        assert any("finite" in e or "NaN" in e or "nan" in e.lower() for e in errors)

    def test_validate_inputs_rejects_infinity(self) -> None:
        m = HYRUE(crop="wheat")
        ok, errors = m.validate_inputs(
            par=float("inf"), lai=np.array([3.0]), ewsi=np.array([0.1]), t_mean=20.0
        )
        assert not ok

    def test_validate_inputs_rejects_empty_arrays(self) -> None:
        m = HYRUE(crop="wheat")
        ok, errors = m.validate_inputs(
            par=[], lai=[], ewsi=[], t_mean=[]
        )
        assert not ok
        assert any("empty" in e.lower() for e in errors)

    def test_validate_inputs_rejects_incompatible_array_lengths(self) -> None:
        m = HYRUE(crop="wheat")
        ok, errors = m.validate_inputs(
            par=[15.0, 16.0, 17.0],
            lai=[2.0, 2.5],
            ewsi=[0.1, 0.2, 0.3],
            t_mean=[20.0, 21.0, 22.0],
        )
        assert not ok
        assert any("does not match" in e for e in errors)

    def test_validate_inputs_accepts_valid_arrays(self) -> None:
        m = HYRUE(crop="wheat")
        ok, errors = m.validate_inputs(
            par=[15.0, 16.0, 17.0],
            lai=[2.0, 2.5, 3.0],
            ewsi=[0.1, 0.2, 0.3],
            t_mean=[20.0, 21.0, 22.0],
        )
        assert ok, errors


# --------------------------------------------------------------------------- #
# 5. DecisionEngine per-criterion threshold enforcement                        #
# --------------------------------------------------------------------------- #
# 5. DecisionEngine per-criterion threshold enforcement                        #
# --------------------------------------------------------------------------- #
class TestDecisionThresholds:
    def _engine(self) -> DecisionEngine:
        return DecisionEngine()

    def test_weighted_criterion_below_threshold_caps_at_caution(self) -> None:
        eng = self._engine()
        crit = [
            DecisionCriterion(name="evidence_quality", weight=0.4, threshold=0.6)
        ]
        # High aggregate but the weighted criterion scores below its threshold.
        assert (
            eng._determine_outcome(
                0.9, "supported", 0.9, crit, criterion_scores={"evidence_quality": 0.5}
            )
            == DecisionOutcome.CAUTION.value
        )
        # Same aggregate, criterion now above threshold -> RECOMMEND restored.
        assert (
            eng._determine_outcome(
                0.9, "supported", 0.9, crit, criterion_scores={"evidence_quality": 0.7}
            )
            == DecisionOutcome.RECOMMEND.value
        )

    def test_verdict_bands_preserved(self) -> None:
        eng = self._engine()
        crit = [
            DecisionCriterion(name="evidence_quality", weight=0.4, threshold=0.6)
        ]
        scores = {"evidence_quality": 0.9}
        assert eng._determine_outcome(0.75, "supported", 0.9, crit, scores) == "recommend"
        assert eng._determine_outcome(0.5, "supported", 0.9, crit, scores) == "caution"
        assert eng._determine_outcome(0.2, "supported", 0.9, crit, scores) == "reject"
        assert (
            eng._determine_outcome(0.9, "supported", 0.1, crit, scores)
            == DecisionOutcome.INSUFFICIENT_EVIDENCE.value
        )

    def test_zero_weight_criterion_does_not_gate(self) -> None:
        eng = self._engine()
        crit = [
            DecisionCriterion(name="evidence_quality", weight=0.0, threshold=0.6)
        ]
        assert (
            eng._determine_outcome(
                0.9, "supported", 0.9, crit, criterion_scores={"evidence_quality": 0.0}
            )
            == DecisionOutcome.RECOMMEND.value
        )

    def test_full_chain_supported_high_confidence_recommends(self) -> None:
        from engine.evidence import Evidence, EvidenceEngine, EvidenceSource
        from engine.knowledge import Claim, KnowledgeEngine

        ke = KnowledgeEngine()
        ee = EvidenceEngine(knowledge_engine=ke)
        de = DecisionEngine(knowledge_engine=ke, evidence_engine=ee)
        measurement = ee.collect(
            Evidence(source=EvidenceSource.MEASUREMENT, value=30.0, confidence=0.95)
        )
        model_ev = ee.collect(
            Evidence(
                source=EvidenceSource.MODEL,
                value={"cec": 15.0},
                confidence=0.9,
                provenance=[measurement.id],
            )
        )
        fact = ee.to_fact(model_ev.id, "CEC is high and supports fertility")
        ke.register_claim(Claim(id="claim_fert2", text="Soil is fertile"))
        decision = de.make_decision(claim_id="claim_fert2", supporting_facts=[fact])
        # Every default criterion (0.5/0.6/0.5 thresholds) is satisfied, so the
        # threshold gate must not downgrade this to CAUTION.
        assert decision.outcome == "recommend"


# --------------------------------------------------------------------------- #
# 6. Gateway RECOMMEND never returns an empty success                           #
# --------------------------------------------------------------------------- #
class TestGatewayRecommend:
    def _gw(self):
        from engine.gateway import EngineGateway

        return EngineGateway()

    def test_empty_request_raises_not_implemented(self) -> None:
        gw = self._gw()
        with pytest.raises(NotImplementedError) as err:
            gw._dispatch_by_type("RECOMMEND", "recommendation", {}, {})
        msg = str(err.value)
        assert "NOT_IMPLEMENTED" in msg
        assert "scenario_comparison" in msg and "optimization_results" in msg

    def test_execute_returns_error_not_empty_success(self) -> None:
        from engine.gateway import GatewayError, GatewayRequest

        gw = self._gw()
        resp = gw.execute(
            GatewayRequest(
                model_id="RECOMMEND",
                inputs={"context": {"project_id": "p", "note": "no dss inputs"}},
                input_units={},
                provenance=cast("Any", None),
            )
        )
        assert isinstance(resp, GatewayError)
        assert "recommendations" not in getattr(resp, "values", {})

    def test_scenario_comparison_yields_real_recommendation(self) -> None:
        from engine.gateway import GatewayRequest, GatewayResult

        gw = self._gw()
        resp = gw.execute(
            GatewayRequest(
                model_id="RECOMMEND",
                inputs={
                    "context": {
                        "scenario_comparison": {
                            "A": {"npv_irr": 5.0e6, "projected_risk_score": 0.1}
                        }
                    }
                },
                input_units={},
                provenance=cast("Any", None),
            )
        )
        assert isinstance(resp, GatewayResult)
        assert len(resp.values["recommendations"]) >= 1

    def test_projection_helper_is_consistent(self) -> None:
        # The tables the climate-change test depends on are internally consistent.
        dt, dp = CLIMATE_PROJECTIONS["SSP2-4.5"][2050]
        proj = get_climate_projection("SSP2-4.5", 2050, 18.0, 300.0, 1500.0)
        assert proj.delta_temp == pytest.approx(dt)
        assert proj.delta_et0 == pytest.approx(dt * 2.5)
