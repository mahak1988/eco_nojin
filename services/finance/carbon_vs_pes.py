"""The two cost models, side by side, in Decimal.

Added 2026-10-03 with ADR-0011. Every constant here is a MEASURED external
figure or a DERIVED arithmetic result from one; the docstring of each names its
source and marks derived values. Nothing is an estimate of our own pricing,
because no willingness-to-pay figure exists anywhere in the reachable evidence --
see ADR-0011's "What we do not know".

This module exists so the argument in ADR-0011 can be re-run rather than
believed. Every function is pure; there is no database and no network.
"""

from __future__ import annotations

from decimal import Decimal

# --- External figures. Sources and dates in ADR-0011 section 2. -------------
MEASUREMENT_USD_PER_HA = Decimal("32")  # Paul et al. 2019, via EDF synthesis
CREDIT_PRICE_USD_PER_T_LOW = Decimal("10")  # EDF, citing EM SOVCM 2020
CREDIT_PRICE_USD_PER_T_HIGH = Decimal("15")
RESAMPLING_INTERVAL_YEARS = Decimal("5")  # the engine's own verification cadence
SWOF_USD_PER_ACRE = Decimal("35")  # DERIVED: 10.5e6 / 300_000 acres
ACRES_PER_HECTARE = Decimal("2.47105")

# The engine's own table, services/scientific_motors/carbon_sequestration.py.
# Low end of each range, i.e. the practice that is hardest to pay for.
ADDITIONALITY_T_PER_HA_NO_TILL = Decimal("0.5")
ADDITIONALITY_T_PER_HA_RESIDUE = Decimal("0.3")


def sampling_cost_per_ha_per_year(interval_years: Decimal = RESAMPLING_INTERVAL_YEARS) -> Decimal:
    """Amortised measurement cost. DERIVED: 32 / interval.

    Only the sampling line. Audit, registry and project-management overhead are
    NOT included because no source publishes a composite figure -- ADR-0011
    records that as a negative result rather than inventing one.
    """
    if interval_years <= 0:
        raise ValueError("interval must be positive")
    return (MEASUREMENT_USD_PER_HA / interval_years).quantize(Decimal("0.01"))


def break_even_additionality(
    price_per_t: Decimal, interval_years: Decimal = RESAMPLING_INTERVAL_YEARS
) -> Decimal:
    """tCO2e/ha/yr a farm must deliver just to cover sampling. DERIVED."""
    if price_per_t <= 0:
        raise ValueError("price must be positive")
    cost = sampling_cost_per_ha_per_year(interval_years)
    return (cost / price_per_t).quantize(Decimal("0.01"))


def credit_route_margin(
    additionality_t: Decimal,
    price_per_t: Decimal,
    interval_years: Decimal = RESAMPLING_INTERVAL_YEARS,
) -> Decimal:
    """USD/ha/yr left for the farmer. Negative means the farmer loses money."""
    revenue = additionality_t * price_per_t
    cost = sampling_cost_per_ha_per_year(interval_years)
    return (revenue - cost).quantize(Decimal("0.01"))


def per_area_equivalent(usd_per_acre: Decimal = SWOF_USD_PER_ACRE) -> Decimal:
    """The one documented real per-area rate, converted to per-hectare."""
    return (usd_per_acre * ACRES_PER_HECTARE).quantize(Decimal("0.01"))


def ratio_per_area_to_per_tonne(
    usd_per_acre: Decimal,
    additionality_t: Decimal,
    price_per_t: Decimal,
    interval_years: Decimal = RESAMPLING_INTERVAL_YEARS,
) -> Decimal:
    """How many times better per-area payment is than per-tonne payment.

    This is the number the pivot rests on. It is not a claim that PES is
    universally better; it is what the two published figures imply for a farm
    at this additionality.
    """
    per_area = per_area_equivalent(usd_per_acre)
    per_tonne = credit_route_margin(additionality_t, price_per_t, interval_years)
    if per_tonne == 0:
        raise ValueError("per-tonne margin is zero; ratio undefined")
    return (per_area / per_tonne).quantize(Decimal("0.01"))
