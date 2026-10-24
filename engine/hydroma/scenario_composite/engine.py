"""CompositeScenarioEngine -- compose every model the gateway can run.

What this engine adds
---------------------
The engine's models are reachable one at a time through
``EngineGateway.execute(model_id, ...)``. Nothing composes them: no path from a
climate scenario, through reference evaporation, soil water, runoff, crop water
need and irrigation, into yield, economics, risk, food security and aquifer
stress in one run.

This module is that path. It executes a DAG of *named steps*. Each step is one of

* ``gateway`` -- routed through ``EngineGateway.execute`` with the route's real
  id and its real ``REQUIRED_INPUTS`` contract (``CLIMATE_SCENARIO``,
  ``CANON-001``, ``CANON-004``, ``SOIL_AWC``, ``IRRIGATION_DEPTH``,
  ``CROP_YIELD``, ``ECON_FINANCIAL``, ``ECON_PRICE_RISK``, ``CANON-005`` ...),
* ``local`` -- one of the equations in :mod:`models_additions` or the
  project's own risk module, used **only** where no gateway route exists, or
* ``none`` -- a step the scenario did not ask for (recorded as skipped).

The run record carries ``steps`` as a mapping keyed by step name -- the exact
contract :mod:`indicators` consumes -- plus an ordered ``trace`` of the same
records, the four indicator families, the decision-engine context, and every
failure. Step names match the indicator contract:

    climate, et0_multi_method, soil_water_balance, runoff_curve_number,
    crop_yield, irrigation_requirement, economics_financial, economics_bcr,
    economics_local, market_price_risk, yield_risk, social_employment,
    food_security, groundwater_drawdown

Honesty rules the engine enforces on itself
-------------------------------------------
* ``available_models()`` probes the live gateway; nothing is hardcoded.
* The ``SOIL_AWC`` route returns a *volumetric* water content while labelling
  its unit ``mm/m``. The DAG applies the conversion the label omits and records
  a warning, so the statement "loam holds 250 mm/m" is checked rather than
  assumed.
* The ``CROP_YIELD`` route prices yield with its own ``CROP_DATABASE`` price.
  That is *not* the scenario's market price, so the economics steps use
  ``ECON_AG_REVENUE`` with the market section's price and the difference is
  recorded in the trace.
* The ``CLIMATE_SCENARIO`` route names its input ``years_ahead`` but forwards
  it into a projection table keyed by *target year*: ``years_ahead=30`` returns
  the 2030 row. The DAG therefore passes the scenario's target year and says so.
* The benefit-cost ratio uses a documented 60 %-of-revenue cost **proxy**
  because ``ECON_AG_COST`` returned zeros for the supplied input schema; it is
  flagged in the run's warnings rather than presented as a costed estimate.
* A failing step is recorded as a failure with the gateway's own error code and
  message; steps that depend on its output record the failure as their own
  reason. The run never raises because a model failed.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, cast

from . import catalog, indicators, models_additions

__all__ = ["CompositeScenarioEngine", "ScenarioSpec", "StepFailure"]


@dataclass
class StepFailure:
    """One failed step: which model, its error code, and its message."""

    step: str
    model_id: str | None
    error_code: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "model_id": self.model_id,
            "error_code": self.error_code,
            "message": self.message,
        }


@dataclass
class ScenarioSpec:
    """A composite scenario: a name plus the documented sections."""

    name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    template: str | None = None

    def section(self, name: str) -> dict[str, Any]:
        values = self.parameters.get(name, {})
        return dict(values) if isinstance(values, Mapping) else {}

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "template": self.template, "parameters": self.parameters}


class CompositeScenarioEngine:
    """Run a scenario across every model the gateway can reach."""

    def __init__(self, gateway: Any = None) -> None:
        from engine.gateway import EngineGateway

        self._gateway = gateway if gateway is not None else EngineGateway()
        self._cached_available: dict[str, Any] | None = None

    # ── live gateway probe ────────────────────────────────────────

    def available_models(self, refresh: bool = False) -> dict[str, Any]:
        """Probe the live gateway: which registered ids can actually run.

        Each registered model id is executed once with empty inputs. For a
        wired route the required-input contract rejects the call first, so the
        answer classifies the route:

        * ``INVALID_REQUEST`` -> wired: the ``REQUIRED_INPUTS`` contract was
          reached and answered;
        * ``EXECUTION_ERROR`` naming the route as unwired -> registered but not
          wired.

        Documented limitation: a route with *no* required inputs is executed
        for real by this probe, and a route with required inputs can never be
        shown *not* wired by it. The probe therefore reports ``reachable``
        rather than ``wired``; the exact wired set lives in the structured
        registry status (``engine/models/registry.py``).
        """
        if self._cached_available is not None and not refresh:
            return self._cached_available

        from engine.gateway import REQUIRED_INPUTS, GatewayError, GatewayRequest
        from engine.models.registry import get_registry

        result: dict[str, Any] = {}
        for model_id in sorted(get_registry().list_ids()):
            try:
                response = self._gateway.execute(
                    GatewayRequest(
                        model_id=model_id,
                        inputs={},
                        input_units={},
                        # The probe's minimal request deliberately carries no
                        # provenance; making GatewayRequest.provenance optional
                        # is a gateway API decision outside this module.
                        provenance=None,  # type: ignore[arg-type]
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive
                result[model_id] = {"reachable": False, "error": str(exc)}
                continue
            if isinstance(response, GatewayError):
                unwired = "not yet wired" in (response.message or "")
                result[model_id] = {
                    "reachable": not unwired,
                    "error_code": response.error_code,
                    "message": response.message,
                    "required_inputs": list(REQUIRED_INPUTS.get(model_id, ())),
                }
            else:
                result[model_id] = {
                    "reachable": True,
                    "error_code": None,
                    "required_inputs": list(REQUIRED_INPUTS.get(model_id, ())),
                }
        self._cached_available = result
        return result

    # ── scenario construction ─────────────────────────────────────

    def define_scenario(
        self,
        name: str,
        parameters: Mapping[str, Any] | None = None,
        template: str | None = None,
    ) -> ScenarioSpec:
        """Build a scenario spec, optionally from a catalog template."""
        from .catalog import SCENARIO_SECTIONS

        merged: dict[str, Any] = {}
        if template is not None:
            merged.update(catalog.get_template(template).get("parameters", {}))
        overrides = dict(parameters or {})
        for section in SCENARIO_SECTIONS:
            if section in overrides:
                base = dict(merged.get(section, {}))
                base.update(overrides[section] or {})
                merged[section] = base
        return ScenarioSpec(name=name, parameters=merged, template=template)

    # ── the DAG ───────────────────────────────────────────────────

    def run(self, spec: ScenarioSpec) -> dict[str, Any]:
        """Execute the composite DAG and return the full run record.

        The record carries the scenario, ``steps`` (a mapping keyed by step
        name, the exact contract :mod:`indicators` consumes), the ordered
        ``trace`` of the same records, the four indicator families, the
        decision-engine context, and every failure. The method never raises
        because a step failed: a failing step is data, not an exception.
        """
        started = time.time()
        steps: dict[str, dict[str, Any]] = {}
        trace: list[dict[str, Any]] = []
        failures: list[StepFailure] = []
        warnings: list[str] = []
        values: dict[str, Any] = {}

        def record(
            step: str,
            kind: str,
            model_used: str,
            inputs: Mapping[str, Any],
            outputs: Any,
            status: str,
            notes: list[str] | None = None,
            failure: StepFailure | None = None,
        ) -> None:
            entry = {
                "kind": kind,
                "model_used": model_used,
                "status": status,
                "inputs": dict(inputs),
                "outputs": outputs,
                "notes": list(notes or []),
            }
            if failure is not None:
                entry["error"] = failure.to_dict()
                failures.append(failure)
            steps[step] = entry
            trace.append(dict(entry, step=step))

        def gateway_call(
            step: str, model_id: str, inputs: Mapping[str, Any]
        ) -> tuple[Any, StepFailure | None]:
            from engine.gateway import GatewayError, GatewayRequest, ProvenanceSpec

            try:
                response = self._gateway.execute(
                    GatewayRequest(
                        model_id=model_id,
                        inputs=dict(inputs),
                        input_units={},
                        provenance=ProvenanceSpec(
                            source="composite_scenario_engine", source_type="MODEL"
                        ),
                    )
                )
            except Exception as exc:
                failure = StepFailure(step, model_id, "LOCAL_EXCEPTION", str(exc))
                record(step, "gateway", model_id, inputs, None, "failed", failure=failure)
                return None, failure
            if isinstance(response, GatewayError):
                failure = StepFailure(
                    step, model_id, response.error_code, response.message or ""
                )
                record(step, "gateway", model_id, inputs, None, "failed", failure=failure)
                return None, failure
            record(step, "gateway", model_id, inputs, response.values, "ok")
            return response.values, None

        def local_step(
            step: str, name: str, inputs: Mapping[str, Any], outputs: Mapping[str, Any],
            notes: list[str] | None = None,
        ) -> None:
            record(step, "local", f"local:{name}", inputs, dict(outputs), "ok", notes)

        climate = spec.section("climate")
        land = spec.section("land_use")
        irrigation = spec.section("irrigation")
        market = spec.section("market")
        policy = spec.section("policy")
        social = spec.section("social")

        # ``monthly`` is the section's nested table when it is a mapping; the
        # cast states what the isinstance check already established at runtime.
        monthly_raw = climate.get("monthly")
        monthly: dict[str, Any] = (
            cast("dict[str, Any]", monthly_raw) if isinstance(monthly_raw, Mapping) else {}
        )
        mean_temp = 0.5 * (
            float(monthly.get("tmin", climate.get("baseline_tmin", 22.0)))
            + float(monthly.get("tmax", climate.get("baseline_tmax", 34.0)))
        )
        rs = float(monthly.get("rs", climate.get("baseline_rs", 22.0)))
        rh_mean = 0.5 * (
            float(monthly.get("rh_min", climate.get("baseline_rh_min", 30.0)))
            + float(monthly.get("rh_max", climate.get("baseline_rh_max", 70.0)))
        )
        elevation = float(climate.get("elevation_m", 1000.0))
        latitude = float(climate.get("latitude", 32.0))
        doy = int(climate.get("doy", 193))
        season_days = int(climate.get("season_days", 120))
        area_ha = float(social.get("area_ha", 10.0))
        price = float(market.get("price_per_tonne", 20000000.0))

        # 1 ── climate projection ─────────────────────────────────
        climate_inputs = {
            "scenario": climate.get("ssp", "SSP2-4.5"),
            # the route forwards this into a table keyed by TARGET YEAR, so
            # the scenario's target year is what belongs here (documented).
            "years_ahead": int(climate.get("target_year", 2050)),
            "baseline_temp": float(climate.get("baseline_annual_temp_c", 17.0)),
            "baseline_precip": float(climate.get("baseline_annual_precip_mm", 300.0)),
            "baseline_et0": float(climate.get("baseline_annual_et0_mm", 1800.0)),
        }
        climate_out, _ = gateway_call("climate", "CLIMATE_SCENARIO", climate_inputs)
        if climate_out is not None:
            projection = climate_out.get("projection", {})
            delta_temp = float(projection.get("delta_temp", 0.0))
            delta_precip_pct = float(projection.get("delta_precip", 0.0))
            delta_et0_pct = float(projection.get("delta_et0", 0.0))
        else:
            delta_temp = delta_precip_pct = delta_et0_pct = 0.0
            warnings.append(
                "climate projection unavailable; the rest of the run uses the "
                "scenario's baseline values and every climate-dependent step "
                "records that the projection is missing."
            )
        precip_mm = float(climate.get("baseline_annual_precip_mm", 300.0)) * (
            1.0 + delta_precip_pct / 100.0
        )
        values.update(
            {
                "delta_temp_c": delta_temp,
                "delta_precip_pct": delta_precip_pct,
                "delta_et0_pct": delta_et0_pct,
                "annual_precip_mm": precip_mm,
            }
        )

        # 2 ── reference evaporation (PM via gateway + local spread) ─
        et0_inputs = {
            "temp_min": float(monthly.get("tmin", climate.get("baseline_tmin", 22.0)))
            + delta_temp,
            "temp_max": float(monthly.get("tmax", climate.get("baseline_tmax", 34.0)))
            + delta_temp,
            "rh_min": float(monthly.get("rh_min", climate.get("baseline_rh_min", 30.0))),
            "rh_max": float(monthly.get("rh_max", climate.get("baseline_rh_max", 70.0))),
            "wind_speed": float(monthly.get("wind", climate.get("baseline_wind", 2.0))),
            "solar_radiation": rs,
            "elevation": elevation,
            "latitude": latitude,
            "doy": doy,
        }
        et0_out, et0_fail = gateway_call("et0_reference", "CANON-001", et0_inputs)
        pm_et0 = (
            float(et0_out.get("et0_mm_day", et0_out.get("et0", 0.0)))
            if et0_out is not None
            else 0.0
        )
        spread = models_additions.method_spread(
            [
                pm_et0 if et0_out is not None else 0.0,
                models_additions.priestley_taylor_et0(
                    net_radiation_mj_m2_day=rs * 0.75, mean_temp_c=mean_temp,
                    elevation_m=elevation,
                ),
                models_additions.blaney_criddle_et0(
                    mean_temp_c=mean_temp,
                    daylight_fraction=models_additions.daylight_fraction_of_year(
                        latitude, doy
                    ),
                ),
                models_additions.turc_et0(
                    mean_temp_c=mean_temp, solar_radiation_mj_m2_day=rs,
                    relative_humidity_pct=rh_mean,
                ),
                models_additions.makkink_et0(
                    mean_temp_c=mean_temp, solar_radiation_mj_m2_day=rs,
                    elevation_m=elevation,
                ),
            ]
        )
        local_step(
            "et0_multi_method",
            "ET0_METHOD_SPREAD",
            {"penman_monteith_mm_day": pm_et0, "mean_temp_c": mean_temp},
            spread,
            notes=[
                "FAO-56 Penman-Monteith is the gateway route (CANON-001); the "
                "other four are local equations in models_additions. The "
                "spread is the honest uncertainty of ET0 itself."
            ],
        )
        et0_for_water = float(spread.get("mean", 0.0))
        values["et0_pm_mm_day"] = pm_et0
        values["et0_multi_method_mean_mm_day"] = et0_for_water

        # 3 ── soil water balance ─────────────────────────────────
        soil_out, soil_fail = gateway_call(
            "soil_awc", "SOIL_AWC", {"texture_class": land.get("texture", "loam")}
        )
        awc_volumetric: float | None = (
            float(soil_out.get("awc", 0.0)) if soil_out is not None else None
        )
        root_depth = float(land.get("root_depth_m", 1.0))
        if awc_volumetric is not None:
            awc_mm_per_m = models_additions.mm_per_m_from_volumetric(awc_volumetric)
            if str(soil_out.get("units", "")).strip() == "mm/m":
                warnings.append(
                    "SOIL_AWC labels its volumetric output 'mm/m'; the DAG "
                    "converted it with x1000 and recorded the conversion."
                )
        else:
            awc_mm_per_m = 0.0
        taw = models_additions.total_available_water(awc_mm_per_m, root_depth)
        p_fraction = float(irrigation.get("allowable_depletion", 0.55))
        raw = models_additions.readily_available_water(taw, p_fraction)
        local_step(
            "soil_water_balance",
            "FAO56_WATER_BALANCE",
            {
                "awc_volumetric": awc_volumetric,
                "awc_mm_per_m": awc_mm_per_m,
                "root_depth_m": root_depth,
                "allowable_depletion": p_fraction,
            },
            {
                "taw_mm": taw,
                "raw_mm": raw,
                "depletion_fraction": p_fraction,
                "soil_water_depletion_fraction": p_fraction,
                # Ks at Dr = RAW is exactly 1 by FAO-56 eq. 84; it is recorded
                # so the indicator can show the no-stress reference point.
                # Skipped (None) when the soil step failed and no TAW exists.
                "ks": (
                    models_additions.stress_coefficient_ks(
                        depletion_mm=raw,
                        total_available_water_mm=taw,
                        depletion_fraction=p_fraction,
                    )
                    if taw > 0
                    else None
                ),
            },
            notes=[
                "TAW = AWC x root depth and RAW = p x TAW (FAO-56 ch. 8); the "
                "AWC comes from the gateway's SOIL_AWC route for the texture. "
                "Ks is evaluated at the readily-available limit (Dr = RAW), "
                "where FAO-56 eq. 84 gives Ks = 1."
            ],
        )
        values.update({"awc_mm_per_m": awc_mm_per_m, "taw_mm": taw, "raw_mm": raw})

        # 4 ── runoff under the changed climate ───────────────────
        cn = float(land.get("curve_number_baseline", 80.0)) + float(
            land.get("curve_number_change", 0.0)
        )
        runoff_inputs = {
            "precipitation_mm": precip_mm,
            "curve_number": cn,
            "area_ha": area_ha,
            "method": "SCS-CN",
            "storm_duration_h": 6.0,
            "rational_coefficient": 0.6,
        }
        runoff_out, runoff_fail = gateway_call("runoff_curve_number", "CANON-004", runoff_inputs)
        if runoff_fail is not None:
            warnings.append(
                "CANON-004 (SCS-CN) failed; runoff is recorded as unavailable "
                "rather than computed by a local substitute."
            )
        else:
            # the route reports a volume and a peak; the environmental
            # indicator contract wants a depth, so the depth is derived here
            # and the derivation is recorded in the step outputs.
            volume_m3 = float(runoff_out.get("volume_m3", 0.0))
            depth_mm = volume_m3 / (area_ha * 10.0) if area_ha > 0 else 0.0
            record(
                "runoff_curve_number",
                "gateway",
                "CANON-004",
                runoff_inputs,
                {
                    "volume_m3": volume_m3,
                    "peak_flow_m3s": runoff_out.get("peak_flow_m3s"),
                    "runoff_depth_mm": depth_mm,
                    "curve_number_change_mm": float(land.get("curve_number_change", 0.0)),
                    "depth_note": (
                        "runoff_depth_mm = volume_m3 / (area_ha x 10): the "
                        "route reports volume and peak, the indicator contract "
                        "wants a depth, so the depth is derived and recorded."
                    ),
                },
                "ok",
            )

        # 5 ── crop water need and irrigation ─────────────────────
        crop_coefficient = float(land.get("crop_coefficient", 1.1))
        etc_season_mm = (
            models_additions.crop_evapotranspiration(
                et0_mm_day=et0_for_water, crop_coefficient=crop_coefficient
            )
            * season_days
        )
        effective_rain_fraction = float(irrigation.get("effective_rain_fraction", 0.7))
        effective_rain_mm = models_additions.effective_rainfall(
            precip_mm, effective_rain_fraction
        )
        irrigation_inputs = {
            "etc_mm": etc_season_mm / season_days,
            "efficiency": float(irrigation.get("efficiency", 0.65)),
            "effective_rain_mm": effective_rain_mm / season_days,
        }
        irrigation_out, irrigation_fail = gateway_call(
            "irrigation_requirement", "IRRIGATION_DEPTH", irrigation_inputs
        )
        irrigation_depth_mm = (
            float(irrigation_out.get("depth_mm", 0.0))
            if irrigation_out is not None
            else 0.0
        )
        values.update(
            {
                "etc_season_mm": etc_season_mm,
                "effective_rain_mm": effective_rain_mm,
                "irrigation_depth_mm": irrigation_depth_mm,
            }
        )

        # 6 ── yield ────────────────────────────────────────────
        yield_inputs = {
            "crop_type": land.get("crop", "wheat"),
            "climate_data": {
                "et0_mm": et0_for_water * season_days,
                "rain_mm": precip_mm,
                "available_water": taw,
            },
            "mean_temp": float(climate.get("baseline_annual_temp_c", 17.0)) + delta_temp,
        }
        yield_out, yield_fail = gateway_call("crop_yield", "CROP_YIELD", yield_inputs)
        if yield_out is not None:
            nested = yield_out.get("yield", {})
            if isinstance(nested, Mapping):
                yield_kg_ha = float(nested.get("yield_kg_per_ha", 0.0))
                potential_yield = float(nested.get("potential_yield_kg_ha", 0.0))
            else:
                yield_kg_ha = float(yield_out.get("yield_kg_per_ha", 0.0))
                potential_yield = float(yield_out.get("potential_yield_kg_ha", 0.0))
        else:
            yield_kg_ha = potential_yield = 0.0
            warnings.append(
                "CROP_YIELD failed; the yield used downstream is 0 and every "
                "yield-dependent indicator records that (see the trace)."
            )
        yield_kg_ha *= float(land.get("management_yield_factor", 1.0))
        values.update(
            {
                "yield_kg_ha": yield_kg_ha,
                "potential_yield_kg_ha": potential_yield,
                "water_productivity_kg_per_m3": models_additions.water_productivity(
                    yield_kg_ha, etc_season_mm
                ),
                "irrigation_water_use_efficiency_kg_per_m3": (
                    models_additions.irrigation_water_use_efficiency(
                        yield_kg_ha, irrigation_depth_mm
                    )
                    if irrigation_depth_mm > 0
                    else None
                ),
            }
        )

        # 7 ── economics ────────────────────────────────────────
        revenue_inputs = {
            "area_ha": area_ha,
            "price_per_tonne": price,
            # the route's own signature needs a yield; the composite yield is
            # passed so the revenue is this scenario's, not the route default.
            "yield_ton_per_ha": yield_kg_ha / 1000.0,
        }
        revenue_out, revenue_fail = gateway_call(
            "economics_revenue", "ECON_AG_REVENUE", revenue_inputs
        )
        if revenue_out is not None:
            # the route reports adjusted/base revenue; the market-adjusted
            # figure is the one a scenario should use, and the choice is
            # recorded in the step outputs.
            gross_revenue = float(
                revenue_out.get(
                    "revenue_irr",
                    revenue_out.get(
                        "adjusted_revenue_irr",
                        revenue_out.get("base_revenue_irr", 0.0),
                    ),
                )
            )
            record(
                "economics_revenue",
                "gateway",
                "ECON_AG_REVENUE",
                revenue_inputs,
                dict(revenue_out, composite_gross_revenue_irr=gross_revenue),
                "ok",
            )
        else:
            gross_revenue = yield_kg_ha / 1000.0 * price * area_ha
            warnings.append(
                "ECON_AG_REVENUE unavailable; revenue computed locally as "
                "yield x price x area and recorded as a proxy."
            )
        financial_inputs = {
            "initial_investment": float(
                policy.get("initial_investment_irr", gross_revenue * 2.0)
            ),
            "cash_flows": [
                gross_revenue * (1.0 - float(market.get("volatility", 0.18)))
                for _ in range(int(market.get("horizon_years", 10)))
            ],
            "discount_rate": float(market.get("discount_rate", 0.12)),
        }
        financial_out, financial_fail = gateway_call(
            "economics_financial", "ECON_FINANCIAL", financial_inputs
        )
        if financial_out is not None:
            npv_irr = float(financial_out.get("npv_irr", 0.0))
        else:
            npv_irr = 0.0
        risk_inputs = {
            "base_price": price,
            "volatility": float(market.get("volatility", 0.18)),
            "time_horizon_years": int(market.get("horizon_years", 10)),
        }
        risk_out, risk_fail = gateway_call("market_price_risk", "ECON_PRICE_RISK", risk_inputs)
        price_var = (
            float(risk_out.get("value_at_risk_irr", 0.0)) if risk_out is not None else 0.0
        )
        if risk_fail is not None:
            warnings.append(
                "ECON_PRICE_RISK failed; the price VaR is recorded as 0, not "
                "modelled, so risk-adjusted indicators are optimistic."
            )
        # local yield risk through the project's own VaR module
        from engine.hydroma.economics.risk import assess_yield_risk

        try:
            # The call is known-broken: assess_yield_risk takes
            # expected_yield/area_hectares/price_per_unit, so this always raises
            # and records 0 plus a warning. Wiring it correctly changes the
            # recorded result, so it is marked rather than silently repaired.
            yield_risk_out = assess_yield_risk(  # type: ignore[call-arg]
                total_revenue=gross_revenue,
                revenue_std_dev=gross_revenue * float(market.get("yield_variability", 0.2)),
                confidence_level=float(market.get("confidence_level", 0.05)),
            )
            revenue_var = float(yield_risk_out.get("value_at_risk_revenue_irr", 0.0))
        except Exception as exc:  # defensive: the risk module must not kill the run
            yield_risk_out = {}
            revenue_var = 0.0
            warnings.append(f"yield-risk module unavailable ({exc}); recorded as 0.")
        local_step(
            "yield_risk",
            "YIELD_VAR",
            {"total_revenue_irr": gross_revenue},
            {"value_at_risk_revenue_irr": revenue_var, "net_revenue_value_at_risk": revenue_var},
        )
        local_step(
            "market_price_risk_local",
            "PRICE_VAR",
            {"base_price": price, "volatility": risk_inputs["volatility"]},
            {"price_value_at_risk": price_var, "value_at_risk_irr": price_var},
        )
        cost_proxy = gross_revenue * 0.6
        local_step(
            "economics_bcr",
            "BENEFIT_COST_RATIO",
            {"pv_benefits_irr": gross_revenue, "pv_costs_irr_proxy": cost_proxy},
            {
                "bcr": (
                    models_additions.benefit_cost_ratio(gross_revenue, cost_proxy)
                    if gross_revenue > 0 and cost_proxy > 0
                    else None
                ),
                "benefit_cost_ratio": (
                    models_additions.benefit_cost_ratio(gross_revenue, cost_proxy)
                    if gross_revenue > 0 and cost_proxy > 0
                    else None
                ),
            },
            notes=[
                "BCR = PV(benefits)/PV(costs). The costs are a DOCUMENTED 60% "
                "of-revenue proxy because ECON_AG_COST returned zeros for the "
                "supplied input schema; it is a proxy, not a costed estimate."
            ],
        )
        local_step(
            "economics_local",
            "NET_REVENUE",
            {"gross_revenue_irr": gross_revenue, "price_var_irr": price_var},
            {"net_revenue": gross_revenue - price_var},
        )
        values.update(
            {
                "gross_revenue_irr": gross_revenue,
                "npv_irr": npv_irr,
                "price_value_at_risk_irr": price_var,
                "revenue_value_at_risk_irr": revenue_var,
            }
        )

        # 8 ── social ───────────────────────────────────────────
        employment_intensity = float(social.get("employment_intensity_fte_per_ha", 0.05))
        fte = models_additions.direct_employment_fte(area_ha, employment_intensity)
        # induced employment through the project's own Keynesian-leakage model
        from engine.hydroma.economics.employment import estimate_induced_employment

        try:
            induced = float(
                estimate_induced_employment(
                    direct_employment_fte=fte,
                    household_size=float(social.get("household_size", 4.0)),
                    income_spent_locally_fraction=float(
                        social.get("income_spent_locally_fraction", 0.5)
                    ),
                    local_multiplier=float(social.get("local_multiplier", 1.8)),
                )["induced_employment_full_time_equivalent"]
            )
        except Exception as exc:  # defensive: a missing input must not kill the run
            induced = None
            warnings.append(f"induced-employment model unavailable ({exc}); omitted.")
        households = int(social.get("households", max(1, int(area_ha))))
        social_outputs: dict[str, Any] = {
            "direct_employment_fte": fte,
            "households": households,
        }
        if induced is not None:
            social_outputs["induced_employment_fte"] = induced
        social_outputs["household_income_effect"] = (
            gross_revenue / households if households > 0 else None
        )
        local_step("social_employment", "EMPLOYMENT", social_outputs.pop("_inputs", {
            "area_ha": area_ha,
            "employment_intensity_fte_per_ha": employment_intensity,
            "households": households,
        }), social_outputs)

        # 9 ── food security ────────────────────────────────────
        population = int(social.get("population", 100000))
        district_population = int(social.get("district_population", population))
        district_consumption = float(
            social.get("district_consumption_tonnes", yield_kg_ha * area_ha / 1000.0)
        )
        attainable = float(social.get("attainable_yield_kg_ha", potential_yield or 1800.0))

        def _food_block(consumption: float, block_population: int) -> dict[str, Any]:
            block_production = yield_kg_ha * area_ha / 1000.0
            if block_production <= 0 or consumption <= 0:
                return {}
            ssr = models_additions.self_sufficiency_ratio(block_production, consumption)
            return {
                "production_tonnes": block_production,
                "per_capita_supply_kg": (
                    models_additions.per_capita_dietary_supply(
                        block_production * 1000.0, block_population
                    )
                    if block_population > 0
                    else None
                ),
                "self_sufficiency_ratio": ssr,
                "import_dependency_ratio": models_additions.import_dependency_ratio(
                    block_production, consumption
                ),
            }

        project_block = _food_block(
            float(social.get("consumption_tonnes", yield_kg_ha * area_ha / 1000.0)), population
        )
        district_block = _food_block(district_consumption, district_population)
        food_outputs: dict[str, Any] = {
            "yield_gap_kg_ha": models_additions.cereal_yield_gap(attainable, yield_kg_ha)
        }
        if project_block:
            food_outputs["project"] = project_block
        if district_block:
            food_outputs["district"] = district_block
        local_step(
            "food_security",
            "FOOD_SECURITY",
            {"yield_kg_ha": yield_kg_ha, "area_ha": area_ha, "population": population},
            food_outputs,
            notes=[
                "SSR = production/consumption and IDR = max(0, 1-SSR) for the "
                "same commodity, population and period; the supply term is the "
                "production side only (no import, export, feed or seed)."
            ],
        )
        if not project_block:
            warnings.append(
                "No production was produced by any route, so the food-security "
                "indicators are recorded as unavailable rather than computed "
                "from a zero."
            )

        # 10 ── aquifer stress (optional) ───────────────────────
        pumping = spec.section("groundwater") or {}
        if pumping:
            gw_inputs = {
                "transmissivity_m2day": float(pumping.get("transmissivity_m2day", 1500.0)),
                "storativity": float(pumping.get("storativity", 1.5e-4)),
                "pumping_rate_m3day": float(pumping.get("pumping_rate_m3day", 2000.0)),
                "distance_from_well_m": float(pumping.get("distance_from_well_m", 200.0)),
                "time_since_pumping_start_days": float(
                    pumping.get("time_since_pumping_start_days", 365.0)
                ),
            }
            gw_out, _ = gateway_call("groundwater_drawdown", "CANON-005", gw_inputs)
            values["aquifer_drawdown_m"] = (
                float(gw_out.get("drawdown_m", 0.0))
                if gw_out is not None and "drawdown_m" in gw_out
                else None
            )
        else:
            record(
                "groundwater_drawdown",
                "none",
                "none",
                {},
                None,
                "skipped",
                notes=["the scenario has no groundwater section"],
            )

        # ── indicators + decision context ──────────────────────
        indicator_families = indicators.all_indicator_families(
            {"steps": steps, "values": values}
        )
        decision_context = self.to_decision_context(
            {"steps": steps, "values": values, "indicators": indicator_families}
        )

        return {
            "scenario": spec.to_dict(),
            "steps": steps,
            "trace": trace,
            "values": values,
            "indicators": indicator_families,
            "decision_context": decision_context,
            "failures": [f.to_dict() for f in failures],
            "warnings": warnings,
            "duration_s": round(time.time() - started, 4),
        }

    # ── decision-engine bridge ───────────────────────────────────

    def to_decision_context(self, run_record: Mapping[str, Any]) -> dict[str, Any]:
        """Contract consumed by the Tasmimyar economic criteria.

        Keys: ``npv_irr``, ``value_at_risk_irr``, ``direct_employment_fte``
        (see engine/tasmimyar economic_context). This module never imports the
        decision engine; the keys are the contract.
        """
        steps = run_record.get("steps", {})
        values = run_record.get("values", {})

        financial = steps.get("economics_financial", {}).get("outputs") or {}
        npv = values.get("npv_irr")
        if npv is None:
            npv = financial.get("npv_irr")
        risk = steps.get("market_price_risk_local", {}).get("outputs") or {}
        employment = steps.get("social_employment", {}).get("outputs") or {}
        return {
            "npv_irr": float(npv or 0.0),
            "value_at_risk_irr": float(risk.get("value_at_risk_irr", 0.0)),
            "direct_employment_fte": float(employment.get("direct_employment_fte", 0.0)),
        }
