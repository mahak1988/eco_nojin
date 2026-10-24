"""S17 -- Gateway route repair: the 17 broken dispatch paths, honest input
validation, and the Hargreaves scientific reference.

Every test in this module is written **before** its fix. Each one failed on
commit ``d6fac05`` + the working-tree fixes, and each one names the defect it
pins (see ``reports/HYDROMA-STAGE1-DIAGNOSTIC-2026-10-09.md``, sections 3.3,
4.4 and 5).

Acceptance criteria
-------------------
* A wired route must return a ``GatewayResult`` with the numeric outputs of
  the function it dispatches to -- never ``EXECUTION_ERROR`` for correct
  inputs. Where a published or independent reference exists, the equality
  is asserted at ``rel=1e-9``.
* Missing required inputs must produce ``INVALID_REQUEST`` naming the
  missing keys, never a raw ``TypeError`` surfaced as ``EXECUTION_ERROR``.
* ``calc_et0_hargreaves`` must implement FAO-56 eq. 52 **as published**,
  i.e. ``(Tmax - Tmin)^0.5`` -- the exponent 0.48 the engine carried
  contradicts the official text (fao.org/3/x0490e/x0490e07.htm) and the
  published equation is the acceptance reference.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

from engine.gateway import (
    EngineGateway,
    GatewayError,
    GatewayRequest,
    GatewayResult,
    ProvenanceSpec,
)

GW = EngineGateway()
PROV = ProvenanceSpec(source="s17", source_type="TEST")

FAO_REF_DAY = {
    "tmin": 22.6,
    "tmax": 30.5,
    "rh_min": 62.0,
    "rh_max": 82.0,
    "wind_speed": 1.7,
    "solar_radiation": 28.4,
    "elevation": 100.0,
    "latitude": 41.9,
    "doy": 193,
}

# One synthetic but deterministic electrical signal for the plant-neuro route.
_SIGNAL = list(np.random.default_rng(11).normal(0.0, 5.0, size=200).round(6))


def _exec(model_id: str, inputs: dict[str, Any]) -> GatewayResult | GatewayError:
    return GW.execute(
        GatewayRequest(model_id=model_id, inputs=inputs, input_units={}, provenance=PROV)
    )


def _values(model_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    r = _exec(model_id, inputs)
    assert isinstance(r, GatewayResult), (
        f"{model_id}: expected GatewayResult, got GatewayError({r.error_code}): {r.message}"
    )
    return r.values


# --------------------------------------------------------------------------- #
# 1. The 17 broken routes: correct inputs must dispatch to real computation    #
# --------------------------------------------------------------------------- #
class TestBrokenRoutesCompute:
    """Defect D-01..D-17: wiring/signature mismatches in the gateway.

    Each case supplies the inputs the route's own contract requires and
    asserts the dispatched function's numeric output, not merely the
    absence of an error.
    """

    def test_canon_016_climate_kernel_matches_python_penman_monteith(self) -> None:
        """CANON-016 must dispatch to the compiled PM kernel.

        Acceptance: bit-level agreement with the Python CANON-001
        Penman-Monteith implementation when ``rh_min == rh_max``, which is
        the convention under which the single-RH native binding and the
        Python eq. 17 computation coincide (documented in S11's
        ``test_cpp_backend_matches_the_published_equations``).
        """
        inputs = {
            "temp_min": FAO_REF_DAY["tmin"],
            "temp_max": FAO_REF_DAY["tmax"],
            "rh_min": 72.0,
            "rh_max": 72.0,
            "wind_speed": FAO_REF_DAY["wind_speed"],
            "solar_radiation": FAO_REF_DAY["solar_radiation"],
            "elevation": FAO_REF_DAY["elevation"],
            "latitude": FAO_REF_DAY["latitude"],
            "doy": FAO_REF_DAY["doy"],
        }
        got = _values("CANON-016", inputs)
        assert "et0_mm_day" in got, f"missing kernel output, got {sorted(got)}"
        py = _values("CANON-001", dict(inputs))
        assert got["et0_mm_day"] == pytest.approx(py["et0_mm_day"], rel=1e-12), (
            f"native PM {got['et0_mm_day']} != python PM {py['et0_mm_day']}"
        )

    def test_canon_017_soil_kernel_matches_python_van_genuchten(self) -> None:
        """CANON-017 must dispatch to the compiled soil kernel.

        Acceptance: exact agreement with Python ``van_genuchten_theta`` for
        the Carsel & Parrish (1988) loam parameters the kernel embeds.
        """
        from engine.hydroma.soil.physics import van_genuchten_theta
        from engine.hydroma.soil.water_retention import get_vg_parameters

        params = get_vg_parameters("loam")
        heads = [-10.0, -100.0, -330.0]
        got = _values(
            "CANON-017",
            {"pressure_head_cm": heads, "texture": "loam"},
        )
        assert "theta" in got, f"missing kernel output, got {sorted(got)}"
        assert len(got["theta"]) == len(heads)
        for h, theta in zip(heads, got["theta"], strict=True):
            expected = van_genuchten_theta(
                h, params["theta_r"], params["theta_s"], params["alpha"], params["n"]
            )
            assert theta == pytest.approx(expected, rel=1e-12), f"h={h}"
        # Physical law: retention decreases as the soil dries.
        assert got["theta"] == sorted(got["theta"], reverse=True)

    def test_climate_projection_dispatches_with_scenario_and_horizon(self) -> None:
        """D-04: the gateway passed (lat, lon, rcp, year) to a function whose
        signature is (scenario, time_horizon, ...)."""
        got = _values(
            "CLIMATE_PROJECTION",
            {
                "rcp": "SSP2-4.5",
                "year": 2050,
                "baseline_temp": 18.0,
                "baseline_precip": 300.0,
                "baseline_et0": 1500.0,
            },
        )
        projection = got.get("projection")
        assert isinstance(projection, dict), f"expected projection dict, got {sorted(got)}"
        assert projection["scenario"] == "SSP2-4.5"
        assert projection["time_horizon"] == 2050
        assert projection["delta_temp"] > 0, "SSP2-4.5 at 2050 must warm the baseline"

    def test_climate_scenario_applies_projection_to_baseline(self) -> None:
        """D-03: ``apply_climate_change`` was called with 3 of 4 arguments."""
        got = _values(
            "CLIMATE_SCENARIO",
            {
                "rcp": "SSP5-8.5",
                "years_ahead": 30,
                "baseline_temp": 18.0,
                "baseline_precip": 300.0,
                "baseline_et0": 1500.0,
            },
        )
        projected = got.get("climate_change")
        assert isinstance(projected, dict), f"expected projected dict, got {sorted(got)}"
        assert projected["temperature"] > 18.0, "warming scenario must raise temperature"
        assert projected["precipitation"] < 300.0, "SSP5-8.5 projects drier conditions"

    def test_crop_yield_simulates_water_limited_yield(self) -> None:
        """D-05: dicts were passed where the adapter expects floats."""
        got = _values(
            "CROP_YIELD",
            {
                "crop_type": "wheat",
                "climate_data": {
                    "mean_temp": 18.0,
                    "available_water": 300.0,
                    "growing_season_precip": 250.0,
                },
                "irrigation_efficiency": 0.6,
                "co2_concentration": 420.0,
            },
        )
        yield_result = got.get("yield")
        assert isinstance(yield_result, dict), f"expected yield dict, got {sorted(got)}"
        assert yield_result["yield_kg_per_ha"] > 0.0
        dry = _values(
            "CROP_YIELD",
            {
                "crop_type": "wheat",
                "climate_data": {"mean_temp": 18.0, "available_water": 0.0},
            },
        )
        assert dry["yield"]["yield_kg_per_ha"] == 0.0, "no water must mean no yield"

    def test_scenario_route_applies_ssp_to_baseline(self) -> None:
        """D-06: ``apply_scenario`` was called with 2 of 4 arguments."""
        got = _values(
            "SCENARIO",
            {
                "baseline_temp": 18.0,
                "baseline_precip": 300.0,
                "scenario": "SSP2-4.5",
                "target_year": 2050,
            },
        )
        impact = got.get("scenario_impact")
        assert isinstance(impact, dict), f"expected impact dict, got {sorted(got)}"
        assert impact["projected_temperature"] > 18.0
        assert "projected_temperature" in impact and "projected_precipitation" in impact

    def test_data_pipeline_returns_connector_by_name(self) -> None:
        """D-07: ``get_pipeline()`` takes no arguments; the route must
        resolve a named connector from the singleton it returns."""
        got = _values("DATA_PIPELINE", {"name": "gbif"})
        pipeline = got.get("pipeline")
        assert isinstance(pipeline, dict), f"expected pipeline dict, got {sorted(got)}"
        assert pipeline["name"] == "gbif"
        assert "gbif" in pipeline["available_connectors"]
        assert pipeline["connector_class"], "connector class must be reported"

    def test_sim_chain_runs_the_orchestrator_with_a_chain_inputs(self) -> None:
        """D-08: ``run_chain`` takes (ChainInputs, progress_cb); the route
        passed (steps, inputs)."""
        got = _values(
            "SIM_CHAIN",
            {
                "site_id": "s17-site",
                "area_ha": 10.0,
                "scenario": {
                    "name": "Medium",
                    "cn_change": -5.0,
                    "c_factor_factor": 0.7,
                    "p_factor": 0.8,
                },
                "r_factor": 600.0,
                "k_factor": 0.3,
                "ls_factor": 1.5,
                "c_factor_base": 0.4,
                "crop": "Wheat",
                "soil_type": "SiltLoam",
                "initial_soc_t_ha": 40.0,
                "clay_pct": 25.0,
                "years": 1,
            },
        )
        chain = got.get("chain")
        assert isinstance(chain, dict), f"expected chain dict, got {sorted(got)}"
        assert chain["site_id"] == "s17-site"
        assert chain["status"] == "ok"
        assert isinstance(chain["outputs"], dict)

    def test_sim_orchestrate_runs_every_requested_chain(self) -> None:
        """D-09: the route imported ``SimulationOrchestrator``, a class the
        orchestrator module does not define. Orchestration is the module's
        ``run_chain`` applied per requested chain."""
        chain_inputs = {
            "site_id": "s17-orch",
            "area_ha": 5.0,
            "scenario": {
                "name": "Baseline",
                "cn_change": 0.0,
                "c_factor_factor": 1.0,
                "p_factor": 1.0,
            },
            "r_factor": 600.0,
            "k_factor": 0.3,
            "ls_factor": 1.5,
            "c_factor_base": 0.4,
            "crop": "Wheat",
            "soil_type": "SiltLoam",
            "initial_soc_t_ha": 40.0,
            "clay_pct": 25.0,
            "years": 1,
        }
        got = _values(
            "SIM_ORCHESTRATE",
            {"chains": [chain_inputs, dict(chain_inputs, site_id="s17-orch-2")]},
        )
        orchestration = got.get("orchestration")
        assert isinstance(orchestration, dict), f"expected dict, got {sorted(got)}"
        runs = orchestration["runs"]
        assert len(runs) == 2
        assert all(r["status"] == "ok" for r in runs)
        assert {r["site_id"] for r in runs} == {"s17-orch", "s17-orch-2"}

    def test_mrv_metrics_computes_soc_and_rusle(self) -> None:
        """D-10: the route imported ``MRVMetrics``, a class the module does
        not define (its functions exist). The route must compose them."""
        got = _values(
            "MRV_METRICS",
            {
                "site_id": "s17-mrv",
                "soc_pct": 1.5,
                "depth_m": 0.3,
                "bulk_density_g_cm3": 1.3,
                "rainfall_mm": 600.0,
                "slope_length_m": 22.0,
                "slope_percent": 8.0,
            },
        )
        mrv = got.get("mrv")
        assert isinstance(mrv, dict), f"expected metrics dict, got {sorted(got)}"
        assert mrv["soc_stock_tha"] == pytest.approx(58.5, rel=1e-9)
        assert mrv["rusle_annual_loss_tha"] == pytest.approx(193.81, rel=1e-9)

    def test_mrv_validate_sat_accepts_index_and_value(self) -> None:
        """D-11: ``validate_satellite_index`` expects (index, value)."""
        got = _values("MRV_VALIDATE_SAT", {"index": "NDVI", "value": 0.45})
        # The route follows the existing gateway convention of spreading the
        # QA report into the result (see MRV_VALIDATE).
        assert got["qa_status"] == "ok"
        assert "NDVI" in got["message"]
        # A single-entry index_data mapping is the same request.
        alt = _values("MRV_VALIDATE_SAT", {"index_data": {"NDVI": 0.45}})
        assert alt["qa_status"] == "ok"
        # Out-of-physical-range readings are rejected, not silently passed.
        bad = _values("MRV_VALIDATE_SAT", {"index": "NDVI", "value": 3.0})
        assert bad["qa_status"] == "rejected"

    def test_plant_neuro_analyzes_electrical_signal(self) -> None:
        """D-12: the route called ``PlantNeuroEngine.detect_stress``, which
        does not exist; the engine's real API is ``analyze_from_signals``."""
        got = _values("PLANT_NEURO", {"signal_mv": _SIGNAL})
        neuro = got.get("neuro")
        assert isinstance(neuro, dict), f"expected assessment dict, got {sorted(got)}"
        assert neuro["computed"] is True
        assert 0.0 <= neuro["electrical_confidence"] <= 1.0
        assert neuro["integrated_stress_level"] in {
            "healthy",
            "mild",
            "moderate",
            "severe",
        }

    def test_econ_ag_cost_maps_every_cost_component(self) -> None:
        """D-13: four of eight required arguments were dropped."""
        got = _values(
            "ECON_AG_COST",
            {
                "area_ha": 10.0,
                "crop_type": "wheat",
                "input_costs": {
                    "labor_hours_per_hectare": 120.0,
                    "labor_cost_per_hour": 5.0,
                    "seed_cost_per_hectare": 200.0,
                    "fertilizer_cost_per_hectare": 150.0,
                    "machinery_cost_per_hectare": 300.0,
                },
            },
        )
        # 10 ha x (120 h x 5 + 200 + 150 + 300) IRR/ha = 12500 IRR.
        assert got["total_cost_irr"] == pytest.approx(12500.0, rel=1e-9)
        assert got["cost_per_hectare_irr"] == pytest.approx(1250.0, rel=1e-9)

    def test_econ_ag_revenue_passes_yield_in_the_yield_slot(self) -> None:
        """D-14: ``crop_type`` (a string) was passed where the second
        positional parameter is ``yield_ton_per_ha`` (a float)."""
        got = _values(
            "ECON_AG_REVENUE",
            {
                "area_ha": 10.0,
                "crop_type": "wheat",
                "yield_ton_per_ha": 5.0,
                "price_per_tonne": 200.0,
            },
        )
        assert got["adjusted_revenue_irr"] == pytest.approx(10000.0, rel=1e-9)
        # A total-yield input must convert to per-hectare before dispatch.
        total = _values(
            "ECON_AG_REVENUE",
            {
                "area_ha": 10.0,
                "crop_type": "wheat",
                "yield_tonnes": 50.0,
                "price_per_tonne": 200.0,
            },
        )
        assert total["adjusted_revenue_irr"] == pytest.approx(10000.0, rel=1e-9)

    def test_econ_financial_maps_lifetime_and_salvage(self) -> None:
        """D-15: ``terminal_value`` was landing in ``project_lifetime_years``
        and ``salvage_value`` was dropped."""
        got = _values(
            "ECON_FINANCIAL",
            {
                "initial_investment": 1000.0,
                "cash_flows": [300.0, 400.0, 500.0],
                "discount_rate": 0.1,
                "project_lifetime_years": 3,
                "terminal_value": 50.0,
            },
        )
        assert got["project_lifetime_years"] == 3
        assert got["salvage_value_irr"] == 50.0
        # NPV of [-1000, 300, 400, 500] at 10 % is -21.0368; the salvage
        # value recovered in year 3 adds 50 / 1.1^3 = 37.5657, so the
        # project NPV including salvage is 16.5289.
        assert got["npv_irr"] == pytest.approx(
            -21.0368144252443 + 50.0 / 1.1**3, rel=1e-9
        )
        # Simple ROI counts the 50.0 salvage value among inflows:
        # (1200 + 50 - 1000) / 1000 = 25 %.
        assert got["roi_simple_percentage"] == pytest.approx(25.0, rel=1e-9)

    def test_econ_price_risk_uses_base_price_and_volatility(self) -> None:
        """D-16: only ``price_history`` was forwarded to a function that
        needs a price level and a volatility."""
        got = _values(
            "ECON_PRICE_RISK",
            {"base_price": 200.0, "volatility": 0.15, "time_horizon_years": 1},
        )
        assert got["base_price_irr"] == pytest.approx(200.0)
        assert got["value_at_risk_irr"] > 0.0
        assert got["expected_worst_case_price_irr"] < got["base_price_irr"]

    def test_econ_yield_risk_uses_all_four_factors(self) -> None:
        """D-17: two of four required arguments were dropped."""
        got = _values(
            "ECON_YIELD_RISK",
            {
                "expected_yield": 4.2,
                "yield_std_dev": 0.5,
                "area_hectares": 10.0,
                "price_per_unit": 200.0,
            },
        )
        assert got["expected_total_revenue_irr"] == pytest.approx(8400.0, rel=1e-9)
        assert got["value_at_risk_revenue_irr"] > 0.0


# --------------------------------------------------------------------------- #
# 2. Honest rejection of incomplete inputs (defect D-20)                      #
# --------------------------------------------------------------------------- #
class TestMissingRequiredInputsRejected:
    """A wired route must reject a request that omits required inputs with
    ``INVALID_REQUEST`` naming the missing keys -- never a raw TypeError
    surfaced as ``EXECUTION_ERROR``.
    """

    CASES = [
        ("CANON-004", {"curve_number": 70.0, "area_ha": 10.0}, "precipitation_mm"),
        ("CANON-005", {"pumping_rate_m3day": 760.0}, "transmissivity_m2day"),
        ("ECON_YIELD_RISK", {"expected_yield": 4.2, "yield_std_dev": 0.5}, "area_hectares"),
        ("ECON_AG_REVENUE", {"area_ha": 10.0, "crop_type": "wheat"}, "price_per_tonne"),
        ("CLIMATE_PROJECTION", {"rcp": "SSP2-4.5"}, "year"),
    ]

    @pytest.mark.parametrize(
        "model_id,inputs,missing",
        CASES,
        ids=[c[0] for c in CASES],
    )
    def test_missing_key_is_rejected_with_invalid_request(
        self, model_id: str, inputs: dict[str, Any], missing: str
    ) -> None:
        r = _exec(model_id, inputs)
        assert isinstance(r, GatewayError), f"{model_id} accepted {inputs}"
        assert r.error_code == "INVALID_REQUEST", (
            f"{model_id}: raw computation error escaped as {r.error_code}: {r.message}"
        )
        assert missing in r.message or missing in (r.validation_errors or []), (
            f"{model_id}: error does not name the missing key {missing!r}: {r.message}"
        )

    def test_none_for_required_key_is_rejected(self) -> None:
        r = _exec("CLIMATE_PROJECTION", {"rcp": "SSP2-4.5", "year": None})
        assert isinstance(r, GatewayError)
        assert r.error_code == "INVALID_REQUEST"
        assert "year" in r.message

    def test_penman_monteith_rejects_missing_humidity_up_front(self) -> None:
        """CANON-001 without humidity/wind/radiation used to fail inside the
        PM equation with an EXECUTION_ERROR; the contract now names the
        missing groups first (S17 review finding R-1)."""
        r = _exec(
            "CANON-001",
            {"temp_min": 15.0, "temp_max": 28.0, "elevation": 100.0, "latitude": 32.0, "doy": 150},
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "INVALID_REQUEST"
        assert r.validation_errors is not None
        assert any("rh_min" in e for e in r.validation_errors)
        assert any("wind_speed" in e for e in r.validation_errors)

    def test_crop_yield_accepts_the_flat_scalar_form(self) -> None:
        """The handler supports flat scalars as well as the nested climate
        mapping, so the contract must not reject the flat form
        (S17 review finding R-2)."""
        got = _values(
            "CROP_YIELD",
            {"crop_type": "wheat", "available_water": 200.0, "mean_temp": 15.0},
        )
        assert got["yield"]["yield_kg_per_ha"] > 0.0
        nested = _values(
            "CROP_YIELD",
            {
                "crop_type": "wheat",
                "climate_data": {"mean_temp": 15.0, "available_water": 200.0},
            },
        )
        assert nested["yield"]["yield_kg_per_ha"] == pytest.approx(
            got["yield"]["yield_kg_per_ha"]
        )

    def test_plant_neuro_rejects_a_signal_too_short_to_smooth(self) -> None:
        """A 3-sample signal used to leak a scipy padlen error; the route now
        names the real minimum (S17 review finding R-3)."""
        r = _exec("PLANT_NEURO", {"signal_mv": [1.0, 2.0, 3.0]})
        assert isinstance(r, GatewayError)
        assert "at least 16" in r.message


# --------------------------------------------------------------------------- #
# 3. Hargreaves: FAO-56 eq. 52 as published (defect D-18)                     #
# --------------------------------------------------------------------------- #
class TestHargreavesFAO56PublishedExponent:
    """FAO-56 (Allen et al. 1998) eq. 52, verbatim from the official text at
    https://www.fao.org/3/x0490e/x0490e07.htm :

        ET0 = 0.0023 (Tmean + 17.8) (Tmax - Tmin)^0.5 Ra

    with Ra converted to mm/day by the 0.408 factor (eq. 40). The engine
    carried exponent 0.48 with a comment asserting FAO publishes 0.48; the
    official document publishes 0.5, and 0.5 is the acceptance reference.
    """

    def _reference(self, t_min: float, t_max: float, t_mean: float, ra_mj: float) -> float:
        ra_mm = ra_mj * 0.408
        return float(0.0023 * (t_mean + 17.8) * (t_max - t_min) ** 0.5 * ra_mm)

    @pytest.mark.parametrize(
        "t_min,t_max,ra",
        [(10.0, 25.0, 20.0), (5.0, 30.0, 30.0), (-2.0, 18.0, 12.0), (0.0, 40.0, 35.0)],
    )
    def test_core_matches_published_exponent(
        self, t_min: float, t_max: float, ra: float
    ) -> None:
        from engine.hydroma.climate.et_calculator import calc_et0_hargreaves

        t_mean = (t_min + t_max) / 2.0
        reference = self._reference(t_min, t_max, t_mean, ra)
        got = calc_et0_hargreaves(t_min=t_min, t_max=t_max, ra_mj=ra)
        assert got == pytest.approx(reference, rel=1e-9), (
            f"Hargreaves {got:.6f} != FAO-56 eq.52 published {reference:.6f} "
            f"(dT={t_max - t_min})"
        )

    def test_gateway_canon_002_matches_published_exponent(self) -> None:
        from engine.hydroma.climate.et_calculator import (
            calc_extraterrestrial_radiation,
        )

        d = FAO_REF_DAY
        ra_mj = calc_extraterrestrial_radiation(d["latitude"], int(d["doy"]))
        reference = self._reference(
            d["tmin"], d["tmax"], (d["tmin"] + d["tmax"]) / 2.0, ra_mj
        )
        got = _values(
            "CANON-002",
            {
                "temp_min": d["tmin"],
                "temp_max": d["tmax"],
                "elevation": d["elevation"],
                "latitude": d["latitude"],
                "doy": d["doy"],
            },
        )
        assert got["et0_mm_day"] == pytest.approx(reference, rel=1e-9), (
            f"CANON-002 {got['et0_mm_day']:.6f} != FAO-56 eq.52 {reference:.6f}"
        )

    def test_documented_deviation_quantified(self) -> None:
        """The audit day (Tmin 15, Tmax 28, lat 32, doy 150): the published
        equation gives 5.4457 mm/day; the 0.48 exponent gave 5.1734."""
        from engine.hydroma.climate.et_calculator import (
            calc_et0_hargreaves,
            calc_extraterrestrial_radiation,
        )

        t_min, t_max, lat, doy = 15.0, 28.0, 32.0, 150
        ra_mj = calc_extraterrestrial_radiation(lat, doy)
        reference = self._reference(t_min, t_max, (t_min + t_max) / 2.0, ra_mj)
        assert math.isclose(reference, 5.4457, rel_tol=1e-3), (
            f"independent reference moved: {reference}"
        )
        got = calc_et0_hargreaves(t_min=t_min, t_max=t_max, ra_mj=ra_mj)
        assert got == pytest.approx(reference, rel=1e-9)

    def test_every_local_copy_delegates_to_the_core(self) -> None:
        """The four satellite copies must stay delegates, so one correction
        cannot leave a divergent exponent behind."""
        import importlib
        import inspect

        from engine.hydroma.climate import et_calculator
        core_src = inspect.getsource(et_calculator._hargreaves_core)
        assert "** 0.48" not in core_src, (
            "core must no longer carry the unjustified 0.48 exponent"
        )
        assert "** 0.5" in core_src, "core must carry the published exponent 0.5"
        for module_name, function_name in [
            ("engine.hydroma.simulation.weather_source", "hargreaves_et0"),
            ("engine.hydroma.simulation_env.weather", "hargreaves_et0"),
        ]:
            module = importlib.import_module(module_name)
            src = inspect.getsource(getattr(module, function_name))
            assert "calc_et0_hargreaves" in src, (
                f"{module_name}.{function_name} no longer delegates to the core"
            )

# --------------------------------------------------------------------------- #
# 4. Honest classification of import failures (defect T-02)                   #
# --------------------------------------------------------------------------- #
class TestImportFailureClassification:
    """T-02: the gateway used to answer every ImportError with "Install
    required packages", which is wrong -- and misleading -- when the named
    implementation module or symbol simply does not exist in this engine.
    A missing third-party dependency is an availability problem; a missing
    internal symbol is an unimplemented route, and the two must be told
    apart.
    """

    def test_missing_internal_symbol_is_not_a_install_problem(self) -> None:
        from engine.gateway import _import_failure_message

        err = ImportError(
            "cannot import name 'MRVMetrics' from 'engine.hydroma.mrv.metrics'"
        )
        message = _import_failure_message("MRV_METRICS", err)
        assert "not implemented" in message
        assert "Install required packages" not in message

    def test_missing_internal_module_is_not_an_install_problem(self) -> None:
        from engine.gateway import _import_failure_message

        err = ModuleNotFoundError("No module named 'engine.hydroma.gone'")
        err.name = "engine.hydroma.gone"
        message = _import_failure_message("SOME_ROUTE", err)
        assert "not implemented" in message
        assert "Install required packages" not in message

    def test_import_error_reaches_caller_as_not_implemented(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fault-injected on the real dispatch path of a registered model:
        an ImportError from the by-type dispatcher must surface as
        NotImplementedError carrying the honest "not implemented" wording,
        never as "Install required packages"."""
        from engine.gateway import EngineGateway

        gw = EngineGateway()
        model = gw._model_registry.get("CANON-004")

        def broken_dispatch(
            model_id: str,
            model_type: str,
            inputs: dict[str, Any],
            parameters: dict[str, Any],
        ) -> dict[str, Any]:
            raise ImportError(
                "cannot import name 'Nope' from 'engine.hydroma.mrv.metrics'"
            )

        monkeypatch.setattr(gw, "_dispatch_by_type", broken_dispatch)
        with pytest.raises(NotImplementedError) as excinfo:
            # Deliberately loosened internal call: ``model`` is a dropped-model
            # class and ``{}`` is not an ``ErrorModelSpec``; the point is the
            # not-implemented fallback a surfaced route must reach, so the public
            # ``ModelSpec``/``ErrorModelSpec`` types do not apply at this seam.
            gw._dispatch_to_model(model, {}, {})  # type: ignore[arg-type]
        assert "not implemented" in str(excinfo.value)
        assert "Install required packages" not in str(excinfo.value)

    def test_missing_third_party_package_stays_a_dependency_problem(self) -> None:
        from engine.gateway import _import_failure_message

        err = ModuleNotFoundError("No module named 'numpy'")
        err.name = "numpy"
        message = _import_failure_message("SOME_ROUTE", err)
        assert "requires dependencies that are not available" in message
        assert "not implemented" not in message


# --------------------------------------------------------------------------- #
# 5. Payback convention (T-01 re-classification)                              #
# --------------------------------------------------------------------------- #
class TestPaybackConvention:
    """T-01 was reported as an off-by-one against a t=0-investment reading.
    The module's own published contract
    (``services/validation/formula_checks.py`` "payback_convention", note
    "engine counts full periods") defines the cumulative-cash, full-period
    convention instead, so the numbers are correct for that contract. This
    test pins the documented convention so the two readings cannot be
    silently conflated again.
    """

    @pytest.mark.parametrize(
        "cashflows,expected",
        [
            ([-100.0, 50.0, 50.0, 50.0], 3.0),
            ([-1000.0, 250.0, 250.0, 250.0, 250.0], 5.0),
            ([-100.0, 30.0, 40.0, 50.0], 4.0),
        ],
    )
    def test_full_period_convention(self, cashflows: list[float], expected: float) -> None:
        from engine.hydroma.economics.analysis import calculate_payback

        assert float(calculate_payback(cashflows)) == expected

    def test_convention_is_documented_in_the_docstring(self) -> None:
        import inspect

        from engine.hydroma.economics.analysis import calculate_payback

        doc = inspect.getdoc(calculate_payback) or ""
        assert "cumulative-cash convention" in doc
        assert "full periods" in doc

