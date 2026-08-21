"""Transparent MRV dashboard metrics (EM-01, section 3).

Every metric returns a dict that carries a provenance ``data_source`` badge:

- "real"      - derived from measured/observed inputs,
- "simulated" - derived from simulated inputs; a warning is attached and the
                value must never be presented as measured,
- "no_data"   - no observations are available for the site.

Honesty rule: simulated inputs always downgrade the badge to "simulated",
even when the caller declared "real" (a simulated observation on the site
taints the aggregate for that site).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# IPCC: 1 t of carbon sequestered == 3.67 t CO2e.
CO2_TO_CO2E_FACTOR = 3.67

# Default assumptions for SOC stock depth (0-30 cm topsoil, FAO convention)
# and a typical bulk density; documented so results are reproducible.
SOC_DEPTH_M = 0.3
DEFAULT_BULK_DENSITY_G_CM3 = 1.3

EROSION_WARNING = (
    "Inputs are simulated; the value is an estimate and must not be "
    "reported as measured erosion."
)
SOC_WARNING = (
    "SOC change derived from simulated inputs; not verifiable against "
    "field measurements."
)
AREA_WARNING = (
    "Restored area is a simulated estimate; verify with ground survey."
)
INCOME_WARNING = (
    "Household income is a simulated estimate; verify with field survey."
)


def _resolve_source(
    observed_sources: list[str] | None, declared: str
) -> str:
    """Resolve the effective provenance badge for a metric.

    Priority: simulated (any) > real (any observation) > declared.
    """
    sources = [s for s in (observed_sources or []) if s in ("real", "simulated")]
    if "simulated" in sources:
        return "simulated"
    if sources:
        return "real"
    return declared if declared in ("real", "simulated") else "no_data"


def _badge(source: str, warning: str | None) -> dict[str, str | None]:
    """Build the provenance badge dict for one metric."""
    badge: dict[str, str | None] = {"data_source": source}
    if source == "simulated":
        badge["warning"] = warning
    return badge


def rusle_annual_loss(
    rainfall_mm: float,
    slope_length_m: float,
    slope_percent: float,
    c_factor: float = 0.5,
    p_factor: float = 0.8,
    texture: str = "loam",
) -> float:
    """RUSLE annual soil loss (t/ha/yr) via the engine wrapper.

    The wrapper falls back to the standard Python formulation when the
    C++ core is unavailable, so results are always produced honestly.
    """
    from engine.hydroma.wrapper import compute_erosion

    result = compute_erosion(
        slope_length_m, slope_percent, rainfall_mm, texture, c_factor, p_factor
    )
    return float(result["annual_soil_loss_t_per_ha"])


def erosion_reduction(
    soil_loss_before_tha: float,
    soil_loss_after_tha: float,
    area_ha: float,
    data_source: str = "real",
    observed_sources: list[str] | None = None,
) -> dict[str, Any]:
    """Erosion reduction in t/yr from RUSLE soil loss before/after (t/ha/yr).

    The reduction is computed honestly: a negative value means erosion
    increased after the intervention.
    """
    before_t = soil_loss_before_tha * area_ha
    after_t = soil_loss_after_tha * area_ha
    reduction_pct = (
        (soil_loss_before_tha - soil_loss_after_tha) / soil_loss_before_tha * 100.0
        if soil_loss_before_tha > 0
        else None
    )
    source = _resolve_source(observed_sources, data_source)
    return {
        "erosion_before_t_yr": round(before_t, 2),
        "erosion_after_t_yr": round(after_t, 2),
        "erosion_reduction_t_yr": round(before_t - after_t, 2),
        "reduction_pct": round(reduction_pct, 2) if reduction_pct is not None else None,
        "area_ha": area_ha,
        "model": "RUSLE",
        **_badge(source, EROSION_WARNING),
    }


def soc_stock_tha(
    soc_pct: float,
    depth_m: float = SOC_DEPTH_M,
    bulk_density_g_cm3: float = DEFAULT_BULK_DENSITY_G_CM3,
) -> float:
    """Convert SOC % into t C/ha for a soil layer (0-30 cm by default)."""
    return soc_pct / 100.0 * bulk_density_g_cm3 * depth_m * 10000.0


def soc_change_pct(
    soc_before_pct: float,
    soc_after_pct: float,
    data_source: str = "real",
    observed_sources: list[str] | None = None,
) -> dict[str, Any]:
    """Relative SOC change (%) plus the absolute stock delta (t C/ha)."""
    rel_pct = (
        (soc_after_pct - soc_before_pct) / soc_before_pct * 100.0
        if soc_before_pct != 0
        else None
    )
    source = _resolve_source(observed_sources, data_source)
    return {
        "soc_before_pct": soc_before_pct,
        "soc_after_pct": soc_after_pct,
        "soc_change_pct": round(rel_pct, 2) if rel_pct is not None else None,
        "soc_delta_tha": round(
            soc_stock_tha(soc_after_pct) - soc_stock_tha(soc_before_pct), 3
        ),
        "note": "SOC change is relative to baseline; verify with lab measurements.",
        **_badge(source, SOC_WARNING),
    }


def co2e_sequestered(
    soc_delta_tha: float,
    area_ha: float,
    data_source: str = "real",
    observed_sources: list[str] | None = None,
) -> dict[str, Any]:
    """CO2e sequestered (t) = delta SOC (t C) x 3.67 (IPCC factor)."""
    co2e_t = soc_delta_tha * area_ha * CO2_TO_CO2E_FACTOR
    source = _resolve_source(observed_sources, data_source)
    return {
        "soc_delta_tha": round(soc_delta_tha, 3),
        "area_ha": area_ha,
        "co2e_sequestered_t": round(co2e_t, 2),
        "conversion": f"delta_SOC_t x {CO2_TO_CO2E_FACTOR} (IPCC)",
        **_badge(source, SOC_WARNING),
    }


def restored_area_ha(
    area_ha: float,
    data_source: str = "real",
    observed_sources: list[str] | None = None,
) -> dict[str, Any]:
    """Restored area (ha) reported for the site."""
    source = _resolve_source(observed_sources, data_source)
    return {
        "restored_area_ha": area_ha,
        "unit": "ha",
        **_badge(source, AREA_WARNING),
    }


def household_income_usd(
    households: int,
    income_per_household_usd: float,
    data_source: str = "real",
    observed_sources: list[str] | None = None,
) -> dict[str, Any]:
    """Aggregate household income (USD) for the site."""
    source = _resolve_source(observed_sources, data_source)
    return {
        "households": households,
        "income_per_household_usd": income_per_household_usd,
        "household_income_usd": round(households * income_per_household_usd, 2),
        "unit": "USD",
        **_badge(source, INCOME_WARNING),
    }


def compute_dashboard(
    site_id: str,
    area_ha: float | None = None,
    rusle_before_tha: float | None = None,
    rusle_after_tha: float | None = None,
    soc_before_pct: float | None = None,
    soc_after_pct: float | None = None,
    households: int | None = None,
    income_per_household_usd: float | None = None,
    observed_sources: list[str] | None = None,
) -> dict[str, Any]:
    """Compute the transparency dashboard metric set for one site.

    Missing inputs yield None for the affected metric - values are never
    fabricated. ``observed_sources`` lists the data_source of the stored
    observations used for provenance badges.
    """
    metrics: dict[str, Any] = {
        "erosion_reduction_t_yr": None,
        "soc_change_pct": None,
        "co2e_sequestered_t": None,
        "restored_area_ha": None,
        "household_income_usd": None,
    }
    if rusle_before_tha is not None and rusle_after_tha is not None and area_ha is not None:
        metrics["erosion_reduction_t_yr"] = erosion_reduction(
            rusle_before_tha, rusle_after_tha, area_ha,
            observed_sources=observed_sources,
        )
    if soc_before_pct is not None and soc_after_pct is not None:
        metrics["soc_change_pct"] = soc_change_pct(
            soc_before_pct, soc_after_pct, observed_sources=observed_sources
        )
        if area_ha is not None:
            delta_tha = soc_stock_tha(soc_after_pct) - soc_stock_tha(soc_before_pct)
            metrics["co2e_sequestered_t"] = co2e_sequestered(
                delta_tha, area_ha, observed_sources=observed_sources
            )
    if area_ha is not None:
        metrics["restored_area_ha"] = restored_area_ha(
            area_ha, observed_sources=observed_sources
        )
    if households is not None and income_per_household_usd is not None:
        metrics["household_income_usd"] = household_income_usd(
            households, income_per_household_usd, observed_sources=observed_sources
        )
    return {
        "site_id": site_id,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "metrics": metrics,
        "integrity_note": (
            "Metrics derived from simulated inputs are labeled simulated and "
            "must not be reported as measured."
        ),
    }