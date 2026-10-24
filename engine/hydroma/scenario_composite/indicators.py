"""Composite indicator families produced by a scenario run.

Every indicator is a record with an explicit unit, a ``source`` label from a
three-value vocabulary, a ``formula`` note and a ``provenance`` mapping naming
the DAG steps (and therefore the gateway routes or local equations) it came
from. The vocabulary is deliberately small:

``measured``
    Comes from an observation (a gauge, a farm record, a price quotation). A
    scenario run normally has none of these: the engine is not fed by
    instruments, so an indicator labelled ``measured`` would be a lie.
``modelled``
    Comes from a scientific model dispatched through the gateway
    (``CANON-001``, ``IRRIGATION_DEPTH``, ``ECON_FINANCIAL``, ...).
``proxy``
    Comes from a planning ratio, a published default or a scenario assumption
    that is not a model of the physical or economic process -- the effective
    rainfall fraction, the attainable-yield reference, the management yield
    factor.

An indicator never carries a value without its source, and no consumer of this
package has to guess which of the two it is reading.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .models_additions import water_productivity

__all__ = [
    "INDICATOR_SOURCES",
    "Indicator",
    "environmental_indicators",
    "economic_indicators",
    "social_indicators",
    "food_security_indicators",
    "all_indicator_families",
    "flatten_indicators",
    "water_productivity_cross_check",
]


#: The only three values an indicator's ``source`` may carry.
INDICATOR_SOURCES: tuple[str, ...] = ("measured", "modelled", "proxy")


@dataclass
class Indicator:
    """One indicator value with its unit, source and provenance."""

    name: str
    value: float
    unit: str
    source: str
    formula: str
    family: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.source not in INDICATOR_SOURCES:
            raise ValueError(
                f"indicator {self.name!r} source must be one of {INDICATOR_SOURCES}, "
                f"got {self.source!r}"
            )
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError(
                f"indicator {self.name!r} value must be a number, got {self.value!r}"
            )
        if not math.isfinite(float(self.value)):
            raise ValueError(f"indicator {self.name!r} value must be finite (got {self.value!r})")

    def as_dict(self) -> dict[str, Any]:
        """The machine-readable form of this indicator."""
        return {
            "name": self.name,
            "value": float(self.value),
            "unit": self.unit,
            "source": self.source,
            "formula": self.formula,
            "family": self.family,
            "provenance": dict(self.provenance),
        }


# --------------------------------------------------------------------------- #
# run-mapping helpers                                                          #
# --------------------------------------------------------------------------- #


def _steps(run: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """The step records of a run, tolerating a missing key."""
    steps = run.get("steps")
    if not isinstance(steps, Mapping):
        return {}
    return {str(name): dict(record) for name, record in steps.items()}


def _values(run: Mapping[str, Any], step: str) -> dict[str, Any]:
    """The extracted outputs of one step, or an empty mapping."""
    record = _steps(run).get(step)
    if not record or record.get("status") != "ok":
        return {}
    outputs = record.get("outputs")
    return dict(outputs) if isinstance(outputs, Mapping) else {}


def _require(run: Mapping[str, Any], step: str, key: str) -> float:
    """A finite scalar from one step's outputs, or a ``KeyError`` naming it."""
    values = _values(run, step)
    if key not in values:
        raise KeyError(f"step {step!r} has no output {key!r} (status " f"{_steps(run).get(step, {}).get('status')!r})")
    number = values[key]
    if isinstance(number, bool) or not isinstance(number, (int, float)):
        raise ValueError(f"step {step!r} output {key!r} is not a number: {number!r}")
    scalar = float(number)
    if not math.isfinite(scalar):
        raise ValueError(f"step {step!r} output {key!r} is not finite: {number!r}")
    return scalar


def _step_ids(run: Mapping[str, Any], *names: str) -> list[str]:
    """``model_id`` of each named step, for provenance records."""
    provenance: list[str] = []
    for name in names:
        record = _steps(run).get(name)
        model_id = (record or {}).get("model_id")
        provenance.append(f"{name}:{model_id}" if model_id else f"{name}:absent")
    return provenance


def _gateway_or_local(run: Mapping[str, Any], step: str) -> str:
    """'modelled' when the step ran through the gateway, else 'proxy'.

    A step routed through a gateway model is a model output; a step computed by
    a local ratio that no registered model covers is a proxy.
    """
    record = _steps(run).get(step) or {}
    return "modelled" if record.get("kind") == "gateway" else "proxy"


# --------------------------------------------------------------------------- #
# Environmental                                                                #
# --------------------------------------------------------------------------- #


def environmental_indicators(run: Mapping[str, Any]) -> dict[str, Indicator]:
    """Environmental indicators: evaporation, soil water, runoff, aquifer.

    The ET0 multi-method spread is the headline: it is the honest statement of
    how much the reference evaporation itself is uncertain, and every water
    requirement downstream of it inherits that uncertainty.
    """
    indicators: dict[str, Indicator] = {}

    spread = _values(run, "et0_multi_method")
    if spread:
        indicators["et0_multi_method_mean_mm_day"] = Indicator(
            name="et0_multi_method_mean_mm_day",
            value=float(spread["mean"]),
            unit="mm/day",
            source=_gateway_or_local(run, "et0_multi_method"),
            formula="mean of the Penman-Monteith, Hargreaves, Priestley-Taylor, "
            "Blaney-Criddle, Turc and Makkink ET0 estimates",
            family="environmental",
            provenance={"steps": _step_ids(
                run,
                "et0_reference_pm",
                "et0_cross_check_hargreaves",
                "et0_local_methods",
                "et0_multi_method",
            )},
        )
        indicators["et0_multi_method_spread_mm_day"] = Indicator(
            name="et0_multi_method_spread_mm_day",
            value=float(spread["range"]),
            unit="mm/day",
            source=_gateway_or_local(run, "et0_multi_method"),
            formula="max(ET0 methods) - min(ET0 methods) over the same weather day",
            family="environmental",
            provenance={"steps": _step_ids(run, "et0_multi_method")},
        )

    balances = _values(run, "soil_water_balance")
    if balances and balances.get("ks") is not None:
        indicators["soil_water_depletion_fraction"] = Indicator(
            name="soil_water_depletion_fraction",
            value=float(balances["depletion_fraction"]),
            unit="fraction of TAW",
            source=_gateway_or_local(run, "soil_water_balance"),
            formula="Dr / TAW with TAW = 1000 (theta_FC - theta_WP) Zr (FAO-56 eq. 87)",
            family="environmental",
            provenance={"steps": _step_ids(
                run, "soil_available_water", "crop_water_need", "soil_water_balance"
            )},
        )
        indicators["soil_water_stress_coefficient"] = Indicator(
            name="soil_water_stress_coefficient",
            value=float(balances["ks"]),
            unit="dimensionless",
            source=_gateway_or_local(run, "soil_water_balance"),
            formula="Ks = (TAW - Dr) / ((1 - p) TAW), Ks = 1 for Dr <= RAW (FAO-56 eq. 84)",
            family="environmental",
            provenance={"steps": _step_ids(run, "soil_water_balance")},
        )

    runoff = _values(run, "runoff_curve_number")
    if runoff and runoff.get("runoff_depth_mm") is not None:
        indicators["runoff_depth_mm"] = Indicator(
            name="runoff_depth_mm",
            value=float(runoff["runoff_depth_mm"]),
            unit="mm",
            source=_gateway_or_local(run, "runoff_curve_number"),
            formula="SCS-CN: Q = (P - Ia)^2 / (P + 0.8 S), Ia = 0.2 S, S = 25400/CN - 254 "
            "(NRCS National Engineering Handbook Part 630 / TR-55)",
            family="environmental",
            provenance={"steps": _step_ids(run, "runoff_curve_number")},
        )
        indicators["curve_number_change_mm"] = Indicator(
            name="curve_number_change_mm",
            value=float(runoff["curve_number_change_mm"]),
            unit="curve number points",
            source=_gateway_or_local(run, "runoff_curve_number"),
            formula="scenario land-management CN adjustment applied to the baseline CN",
            family="environmental",
            provenance={"steps": _step_ids(run, "runoff_curve_number")},
        )

    drawdown = _values(run, "groundwater_drawdown")
    if drawdown and drawdown.get("aquifer_drawdown_m") is not None:
        indicators["aquifer_drawdown_m"] = Indicator(
            name="aquifer_drawdown_m",
            value=float(drawdown["drawdown_m"]),
            unit="m",
            source=_gateway_or_local(run, "groundwater_drawdown"),
            formula="Theis (1935): s = Q/(4 pi T) W(u), u = r^2 S/(4 T t) "
            "(confined aquifer, fully penetrating well)",
            family="environmental",
            provenance={"steps": _step_ids(run, "groundwater_drawdown", "irrigation_applied")},
        )

    return indicators


# --------------------------------------------------------------------------- #
# Economic                                                                     #
# --------------------------------------------------------------------------- #


def economic_indicators(run: Mapping[str, Any]) -> dict[str, Indicator]:
    """Economic indicators: NPV, IRR, benefit-cost, payback, VaR and water value.

    The money unit is whatever the scenario's market section states (the shipped
    catalog uses the Iranian rial, ``IRR``); the gateway's economics routes
    suffix their outputs with ``_irr`` for the same reason, and this package
    carries the unit explicitly rather than relying on that suffix.
    """
    indicators: dict[str, Indicator] = {}
    currency = _values(run, "economics_financial").get("currency", "currency")
    financial = _values(run, "economics_financial")
    if financial:
        for key, unit, formula in (
            ("npv_irr", currency, "NPV = -I + sum CF_t/(1+r)^t (gateway ECON_FINANCIAL)"),
            ("irr_percentage", "%", "discount rate at which NPV = 0 (gateway ECON_FINANCIAL)"),
            ("payback_period_years", "years", "interpolated period in which the cumulative "
             "net cash flow turns non-negative (gateway ECON_FINANCIAL)"),
        ):
            if key in financial and financial[key] is not None:
                indicators[key] = Indicator(
                    name=key,
                    value=float(financial[key]),
                    unit=unit,
                    source=_gateway_or_local(run, "economics_financial"),
                    formula=formula,
                    family="economic",
                    provenance={"steps": _step_ids(run, "economics_financial")},
                )
        if financial.get("roi_simple_percentage") is not None:
            indicators["roi_percentage"] = Indicator(
                name="roi_percentage",
                value=float(financial["roi_simple_percentage"]),
                unit="%",
                source=_gateway_or_local(run, "economics_financial"),
                formula="(total inflows - initial investment) / initial investment x 100",
                family="economic",
                provenance={"steps": _step_ids(run, "economics_financial")},
            )

    bcr = _values(run, "economics_bcr")
    if bcr and bcr.get("bcr") is not None:
        indicators["benefit_cost_ratio"] = Indicator(
            name="benefit_cost_ratio",
            value=float(bcr["bcr"]),
            unit="dimensionless",
            source=_gateway_or_local(run, "economics_bcr"),
            formula="BCR = PV(benefits)/PV(costs) with both present values computed "
            "separately through the gateway ECON_NPV route",
            family="economic",
            provenance={"steps": _step_ids(run, "economics_bcr")},
        )

    local_econ = _values(run, "economics_local")
    if local_econ:
        net_revenue = local_econ.get("net_revenue_irr")
        if net_revenue is not None:
            indicators["net_revenue"] = Indicator(
                name="net_revenue",
                value=float(net_revenue),
                unit=f"{currency}/year",
                source=_gateway_or_local(run, "economics_local"),
                formula="gross revenue (gateway ECON_AG_REVENUE) - total annual cost "
                "(gateway ECON_AG_COST)",
                family="economic",
                provenance={"steps": _step_ids(run, "economics_revenue", "economics_cost")},
            )
        if "water_productivity_kg_m3" in local_econ:
            indicators["water_productivity"] = Indicator(
                name="water_productivity",
                value=float(local_econ["water_productivity_kg_m3"]),
                unit="kg/m3",
                source=_gateway_or_local(run, "economics_local"),
                formula="WP = Y / ET with the FAO WaPOR unit bridge "
                "1 mm over 1 ha = 10 m3",
                family="economic",
                provenance={"steps": _step_ids(run, "crop_yield", "economics_local")},
            )
        if "irrigation_water_use_efficiency_kg_m3" in local_econ:
            indicators["irrigation_water_use_efficiency"] = Indicator(
                name="irrigation_water_use_efficiency",
                value=float(local_econ["irrigation_water_use_efficiency_kg_m3"]),
                unit="kg/m3",
                source=_gateway_or_local(run, "economics_local"),
                formula="IWUE = Y / irrigation water applied (gross depth), "
                "Keller & Bliesner (1990)",
                family="economic",
                provenance={"steps": _step_ids(run, "crop_yield", "irrigation_applied")},
            )
        if "land_expectation_value" in local_econ:
            indicators["land_expectation_value"] = Indicator(
                name="land_expectation_value",
                value=float(local_econ["land_expectation_value"]),
                unit=currency,
                source=_gateway_or_local(run, "economics_local"),
                formula="LEV = V (1+r)^R / ((1+r)^R - 1) for a perpetual rotation of "
                "R years (Faustmann 1849)",
                family="economic",
                provenance={"steps": _step_ids(run, "economics_local")},
            )

    price_risk = _values(run, "market_price_risk")
    if price_risk:
        indicators["price_value_at_risk"] = Indicator(
            name="price_value_at_risk",
            value=float(price_risk["value_at_risk_irr"]),
            unit=f"{currency}/tonne at the stated confidence level",
            source=_gateway_or_local(run, "market_price_risk"),
            formula="VaR = base_price * |z_alpha| * sigma * sqrt(T) "
            "(gateway ECON_PRICE_RISK, normal lower tail)",
            family="economic",
            provenance={"steps": _step_ids(run, "market_price_risk")},
        )
    yield_risk = _values(run, "yield_risk")
    if yield_risk:
        indicators["net_revenue_value_at_risk"] = Indicator(
            name="net_revenue_value_at_risk",
            value=float(yield_risk["value_at_risk_revenue_irr"]),
            unit=f"{currency} of gross revenue",
            source=_gateway_or_local(run, "yield_risk"),
            formula="VaR = |z_alpha| * yield_std_dev * area * price (gateway ECON_YIELD_RISK)",
            family="economic",
            provenance={"steps": _step_ids(run, "yield_risk", "crop_yield")},
        )

    return indicators


# --------------------------------------------------------------------------- #
# Social                                                                      #
# --------------------------------------------------------------------------- #


def social_indicators(run: Mapping[str, Any]) -> dict[str, Indicator]:
    """Social indicators: direct employment and the household income effect."""
    indicators: dict[str, Indicator] = {}
    social = _values(run, "social_employment")
    if not social:
        return indicators

    indicators["direct_employment_fte"] = Indicator(
        name="direct_employment_fte",
        value=float(social["direct_employment_fte"]),
        unit="FTE",
        source=_gateway_or_local(run, "social_employment"),
        formula="FTE = area(ha) * employment intensity(FTE/ha) * (months per year / 12)",
        family="social",
        provenance={"steps": _step_ids(run, "social_employment")},
    )
    indicators["induced_employment_fte"] = Indicator(
        name="induced_employment_fte",
        value=float(social["induced_employment_fte"]),
        unit="FTE",
        source=_gateway_or_local(run, "social_employment"),
        formula="induced = direct FTE * household size * locally spent income fraction "
        "* local employment multiplier (simplified Keynesian leakages model)",
        family="social",
        provenance={"steps": _step_ids(run, "social_employment")},
    )
    if "household_income_effect" in social:
        indicators["household_income_effect"] = Indicator(
            name="household_income_effect",
            value=float(social["household_income_effect"]),
            unit="currency per household per year",
            source=_gateway_or_local(run, "social_employment"),
            formula="annual net income / number of households",
            family="social",
            provenance={"steps": _step_ids(run, "social_employment")},
        )
    return indicators


# --------------------------------------------------------------------------- #
# Food security                                                                #
# --------------------------------------------------------------------------- #


def food_security_indicators(run: Mapping[str, Any]) -> dict[str, Indicator]:
    """Food-security indicators: production, supply, sufficiency, yield gap."""
    indicators: dict[str, Indicator] = {}
    food = _values(run, "food_security")
    if not food:
        return indicators

    scopes = ("project", "district")
    for scope in scopes:
        block = food.get(scope)
        if not isinstance(block, Mapping):
            continue
        indicators[f"production_{scope}_tonnes"] = Indicator(
            name=f"production_{scope}_tonnes",
            value=float(block["production_tonnes"]),
            unit="tonnes per year",
            source=_gateway_or_local(run, "food_security"),
            formula="yield (gateway CROP_YIELD) x area",
            family="food",
            provenance={"steps": _step_ids(run, "crop_yield", "food_security")},
        )
        indicators[f"per_capita_supply_{scope}_kg"] = Indicator(
            name=f"per_capita_supply_{scope}_kg",
            value=float(block["per_capita_supply_kg"]),
            unit="kg per person per year",
            source=_gateway_or_local(run, "food_security"),
            formula="production / population for the same population bound "
            "(production side only: no import, export, feed or seed terms)",
            family="food",
            provenance={"steps": _step_ids(run, "food_security")},
        )
        indicators[f"self_sufficiency_ratio_{scope}"] = Indicator(
            name=f"self_sufficiency_ratio_{scope}",
            value=float(block["self_sufficiency_ratio"]),
            unit="dimensionless",
            source=_gateway_or_local(run, "food_security"),
            formula="SSR = production / consumption over the same commodity, "
            "population and period",
            family="food",
            provenance={"steps": _step_ids(run, "food_security")},
        )
        indicators[f"import_dependency_ratio_{scope}"] = Indicator(
            name=f"import_dependency_ratio_{scope}",
            value=float(block["import_dependency_ratio"]),
            unit="fraction of consumption",
            source=_gateway_or_local(run, "food_security"),
            formula="IDR = max(0, 1 - SSR): a production surplus is clipped to zero "
            "rather than reported as a negative import bill",
            family="food",
            provenance={"steps": _step_ids(run, "food_security")},
        )

    if "yield_gap_kg_ha" in food:
        indicators["cereal_yield_gap"] = Indicator(
            name="cereal_yield_gap",
            value=float(food["yield_gap_kg_ha"]),
            unit="kg/ha",
            source="proxy",
            formula="yield gap = attainable yield (a scenario reference input, not a model "
            "output) - modelled yield",
            family="food",
            provenance={"steps": _step_ids(run, "crop_yield", "food_security")},
        )
    return indicators


# --------------------------------------------------------------------------- #
# Assembly                                                                     #
# --------------------------------------------------------------------------- #


def all_indicator_families(run: Mapping[str, Any]) -> dict[str, dict[str, Indicator]]:
    """Every indicator family for one run, keyed by family name."""
    return {
        "environmental": environmental_indicators(run),
        "economic": economic_indicators(run),
        "social": social_indicators(run),
        "food": food_security_indicators(run),
    }


def flatten_indicators(families: Mapping[str, Mapping[str, Indicator]]) -> dict[str, float]:
    """A flat ``{indicator_name: value}`` view for a consumer that wants numbers.

    The list of names is not fixed here: whatever families a run produced is
    what this returns, so a partially failed run flattens to the subset it
    computed instead of a padded, zero-filled row.
    """
    flat: dict[str, float] = {}
    for family, indicators in families.items():
        for name, indicator in indicators.items():
            flat[f"{family}.{name}"] = indicator.as_dict()["value"]
    return flat


def water_productivity_cross_check(run: Mapping[str, Any]) -> float:
    """Recompute water productivity from the run's own yield and ETc, kg/m3.

    Used by the test suite to prove the indicator arithmetic is reproducible
    from the steps it claims to come from, rather than asserted from the
    indicator record itself.
    """
    yield_kg_ha = _require(run, "crop_yield", "yield_kg_ha")
    etc_mm = _require(run, "crop_water_need", "etc_season_mm")
    return water_productivity(yield_kg_ha, etc_mm)
