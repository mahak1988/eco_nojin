"""
Scenario-level risk assessment: aggregation of the existing VaR primitives.

The scenario-writing path needs one risk figure per scenario run. The
arithmetic that produces it is not defined here — it already exists, three
times over, in :mod:`engine.hydroma.economics.risk`:

* :func:`~engine.hydroma.economics.risk.assess_market_price_risk` — price
  VaR, ``VaR_price = base_price * |Z_alpha| * sigma_T`` with
  ``sigma_T = sigma * sqrt(T)`` (``economics/risk.py:42-47``).
* :func:`~engine.hydroma.economics.risk.assess_yield_risk` — revenue VaR,
  ``VaR_rev = |Z_alpha| * sigma_yield * area * price``
  (``economics/risk.py:91-96``).
* :func:`~engine.hydroma.economics.risk.assess_combined_project_risk` — the
  aggregation of the per-stream VaRs (``economics/risk.py:115-137``).

``perform_comprehensive_risk_analysis`` re-runs those three with the
parameters the economics layer already parameterised, scales the per-tonne
price VaR up to the project's projected quantity, and folds the two
resulting loss ratios into one bounded score. When the caller supplies no
market data the function reports zeros and says so; it never estimates a
risk it has no inputs for.

Overall risk score (documented contract, in [0, 1])
---------------------------------------------------
::

    price_loss_ratio = clamp01( price_var_irr / (quantity_ton * base_price) )
    yield_loss_ratio = clamp01( yield_var_irr / expected_total_revenue_irr )
    overall_risk_score = 0.5 * price_loss_ratio + 0.5 * yield_loss_ratio

``price_loss_ratio`` reduces to ``|Z_alpha| * sigma_price * sqrt(T)``, because
the price VaR is linear in the price and revenue is linear in the price, so
the quantity cancels out of the denominator. That is the monotonicity the
scenario tests rely on: the ratio is non-decreasing in ``sigma_price`` and
never falls when price volatility rises. Both ratios are capped at 1, and the
weights sum to 1, so the weighted mean of two numbers in [0, 1] is itself in
[0, 1]. A score of 0 means "no modelled downside at the assessed confidence
level"; 1 means "the modelled downside of at least one stream is at least its
whole revenue base".
"""

from __future__ import annotations

import math
from typing import Any

from engine.hydroma.economics.risk import (
    assess_combined_project_risk,
    assess_market_price_risk,
    assess_yield_risk,
)

__all__ = ["perform_comprehensive_risk_analysis"]

#: Weights of the two assessed downside streams in the overall score. They
#: sum to 1 so a weighted mean of two [0, 1] ratios is itself in [0, 1].
_MARKET_WEIGHT = 0.5
_YIELD_WEIGHT = 0.5

#: Lower-tail confidence level (alpha) used when the caller carries none.
_DEFAULT_CONFIDENCE_LEVEL = 0.05

_RISK_FORMULA = (
    "overall_risk_score = 0.5 * clamp01(price_var_irr / (quantity_ton * "
    "base_price)) + 0.5 * clamp01(yield_var_irr / expected_total_revenue_irr)"
)


def _as_dict(value: Any) -> dict[str, Any]:
    """Return ``value`` when it is a mapping, otherwise an empty dict."""
    return value if isinstance(value, dict) else {}


def _finite(value: Any, default: float = 0.0) -> float:
    """Coerce to a finite float, returning ``default`` for anything else."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _clamp01(value: float) -> float:
    """Clamp into [0, 1] so the bounded contract holds by construction."""
    return min(1.0, max(0.0, value))


def _no_market_data_result(reason: str) -> dict[str, Any]:
    """The honest no-data result: the same keys, zeros, and the reason.

    Every figure is zero rather than estimated. A caller that receives this
    structure can distinguish "no downside was modelled" from "a downside was
    modelled and it was small", which a fabricated number would not.
    """
    return {
        "market_data_available": False,
        "per_stream_var_irr": {},
        "per_stream_var_detail": {},
        "total_var_irr": 0.0,
        "total_var_to_projected_revenue_ratio": 0.0,
        "volatility_adjusted_price_risk": {
            "volatility_fraction": 0.0,
            "time_horizon_years": 0,
            "confidence_level": _DEFAULT_CONFIDENCE_LEVEL,
            "value_at_risk_per_ton_irr": 0.0,
            "value_at_risk_percentage": 0.0,
            "value_at_risk_irr": 0.0,
            "share_of_price_base_at_risk": 0.0,
        },
        "loss_ratios": {"market_price": 0.0, "yield": 0.0},
        "overall_risk_score": 0.0,
        "risk_formula": _RISK_FORMULA,
        "notes": reason,
    }


def _projected_quantity_ton(
    economic_analysis: dict[str, Any], base_price: float
) -> tuple[float, str]:
    """Quantity the price VaR is scaled by, and where that quantity came from.

    ``assess_market_price_risk`` takes a price *level*, so its
    ``value_at_risk_irr`` is an IRR-per-tonne figure. Turning it into a
    project-level IRR amount needs the quantity the project is expected to
    sell, which the revenue analysis carries directly; the fallbacks stay
    inside the same economic analysis so the source is always reported.
    """
    revenue = _as_dict(economic_analysis.get("revenue"))
    for key in ("agricultural_revenue_with_biofert", "agricultural_revenue_without_biofert"):
        stream = _as_dict(revenue.get(key))
        quantity = _finite(stream.get("total_yield_ton"))
        if quantity > 0:
            return quantity, f"revenue.{key}.total_yield_ton"

    roi = _as_dict(economic_analysis.get("roi"))
    quantity = _finite(roi.get("total_yield_per_year_ton"))
    if quantity > 0:
        return quantity, "roi.total_yield_per_year_ton"

    total_revenue = _finite(revenue.get("total_revenue_irr"))
    if total_revenue > 0 and base_price > 0:
        return total_revenue / base_price, "revenue.total_revenue_irr / base_price_irr"

    return 0.0, "none (the economic analysis carries no quantity)"


def _horizon_years(market_risk: dict[str, Any]) -> int:
    """Assessment horizon in whole years, floored at one."""
    horizon = _finite(market_risk.get("time_horizon_years"), 0.0)
    return max(1, int(horizon))


def perform_comprehensive_risk_analysis(
    simulation_outputs: dict[str, Any],
    economic_analysis: dict[str, Any],
) -> dict[str, Any]:
    """Aggregate the project's existing VaR primitives into one risk report.

    Args:
        simulation_outputs: Output of the simulation chain, e.g. its
            ``AquaCropOutput.yield_t_ha``. Reported for traceability only —
            the VaR arithmetic is already parameterised by the economics
            layer, so a simulated yield here would double-count it.
        economic_analysis: Result of
            ``calculate_agricultural_project_economics``. Its
            ``risk_assessment`` section carries the two VaR primitives the
            economics layer computed, which this function re-runs and
            aggregates.

    Returns:
        Dictionary with ``per_stream_var_irr`` (per-stream VaR),
        ``total_var_irr``, ``volatility_adjusted_price_risk`` (the
        time-horizon-scaled price downside) and ``overall_risk_score`` in
        [0, 1], whose formula is in the module docstring. When no market data
        is carried, the same keys are returned with zeros and a note saying
        so, never an estimated figure.
    """
    risk_assessment = _as_dict(economic_analysis.get("risk_assessment"))
    market_risk = _as_dict(risk_assessment.get("market_price_risk"))
    yield_risk = _as_dict(risk_assessment.get("yield_risk"))

    base_price = _finite(market_risk.get("base_price_irr"))
    volatility = _finite(market_risk.get("volatility_fraction"))
    confidence_level = _finite(
        market_risk.get("confidence_level"), _DEFAULT_CONFIDENCE_LEVEL
    )

    if base_price <= 0.0 or volatility < 0.0:
        return _no_market_data_result(
            "No market price data in the economic analysis: "
            "risk_assessment.market_price_risk needs a positive base_price_irr "
            "and a non-negative volatility_fraction. Risk metrics are reported "
            "as zero rather than estimated."
        )

    # --- Aggregation over the existing primitives, not a new model ----------
    # Re-run both VaR primitives with the parameters the economics layer
    # already used, so every figure below is traceable to economics/risk.py
    # rather than to arithmetic duplicated here.
    market_stream = assess_market_price_risk(
        base_price=base_price,
        volatility=volatility,
        time_horizon_years=_horizon_years(market_risk),
        confidence_level=confidence_level,
    )
    price_var_per_ton = _finite(market_stream["value_at_risk_irr"])

    quantity_ton, quantity_source = _projected_quantity_ton(economic_analysis, base_price)
    price_var_irr = price_var_per_ton * quantity_ton
    price_revenue_base = base_price * quantity_ton
    price_loss_ratio = _clamp01(
        price_var_irr / price_revenue_base if price_revenue_base > 0 else 0.0
    )

    yield_stream = assess_yield_risk(
        expected_yield=_finite(yield_risk.get("expected_yield_per_ha")),
        yield_std_dev=_finite(yield_risk.get("yield_std_dev_per_ha")),
        area_hectares=_finite(yield_risk.get("area_hectares")),
        price_per_unit=_finite(yield_risk.get("price_per_unit_irr")),
        confidence_level=confidence_level,
    )
    yield_var_irr = _finite(yield_stream["value_at_risk_revenue_irr"])
    yield_revenue_base = _finite(yield_stream["expected_total_revenue_irr"])
    yield_stream_assessed = yield_revenue_base > 0
    yield_loss_ratio = _clamp01(
        yield_var_irr / yield_revenue_base if yield_stream_assessed else 0.0
    )

    # --- Total VaR through the project's own aggregator ---------------------
    # assess_combined_project_risk reads value_at_risk_revenue_irr first and
    # falls back to value_at_risk_irr, so the price stream is handed its
    # project-level figure under the key the aggregator actually sums.
    price_stream_project = {
        **market_stream,
        "value_at_risk_revenue_irr": price_var_irr,
        "value_at_risk_per_ton_irr": price_var_per_ton,
        "projected_quantity_ton": quantity_ton,
        "quantity_source": quantity_source,
    }
    combined = assess_combined_project_risk(
        [price_stream_project, yield_stream], cost_streams_with_risks=[]
    )
    total_var_irr = _finite(combined["total_identified_revenue_var_irr"])

    projected_revenue = _finite(_as_dict(economic_analysis.get("revenue")).get("total_revenue_irr"))
    overall_risk_score = _clamp01(
        _MARKET_WEIGHT * price_loss_ratio + _YIELD_WEIGHT * yield_loss_ratio
    )

    # --- Traceability of the simulated yield against the economics one -----
    aquacrop = _as_dict(_as_dict(simulation_outputs).get("AquaCropOutput"))
    simulated_yield = _finite(aquacrop.get("yield_t_ha"))

    notes = [
        "Per-stream VaRs are summed by assess_combined_project_risk, which is an "
        "upper bound on the joint downside whenever the two streams are not "
        "perfectly correlated; a correlated Monte Carlo would report a smaller "
        "combined figure.",
        f"Price VaR scaled to the project level by {quantity_ton:.4f} t, read from "
        f"{quantity_source}.",
    ]
    if not yield_stream_assessed:
        notes.append(
            "No yield variability data in the economic analysis "
            "(risk_assessment.yield_risk); the yield stream contributes zero to "
            "the score rather than an estimated figure."
        )

    return {
        "market_data_available": True,
        "simulated_yield_t_ha": simulated_yield,
        "per_stream_var_irr": {
            "market_price": price_var_irr,
            "yield": yield_var_irr,
        },
        "per_stream_var_detail": {
            "market_price": price_stream_project,
            "yield": yield_stream,
        },
        "total_var_irr": total_var_irr,
        "total_var_to_projected_revenue_ratio": (
            total_var_irr / projected_revenue if projected_revenue > 0 else 0.0
        ),
        "volatility_adjusted_price_risk": {
            "volatility_fraction": volatility,
            "time_horizon_years": market_stream["time_horizon_years"],
            "confidence_level": confidence_level,
            "value_at_risk_per_ton_irr": price_var_per_ton,
            "value_at_risk_percentage": _finite(market_stream["value_at_risk_percentage"]),
            "value_at_risk_irr": price_var_irr,
            "expected_worst_case_price_irr": _finite(
                market_stream["expected_worst_case_price_irr"]
            ),
            "share_of_price_base_at_risk": price_loss_ratio,
        },
        "loss_ratios": {
            "market_price": price_loss_ratio,
            "yield": yield_loss_ratio,
        },
        "revenue_bases_irr": {
            "market_price": price_revenue_base,
            "yield": yield_revenue_base,
            "projected_total_revenue": projected_revenue,
        },
        "weights": {"market_price": _MARKET_WEIGHT, "yield": _YIELD_WEIGHT},
        "overall_risk_score": overall_risk_score,
        "risk_formula": _RISK_FORMULA,
        "notes": " ".join(notes),
    }
