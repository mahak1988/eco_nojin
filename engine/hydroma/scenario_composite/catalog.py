"""Scenario-template catalog: the composite scenarios, as data.

A composite scenario is not hardcoded in the engine: it is a name looked up
here, whose parameter defaults are then merged with the caller's overrides.
That keeps the four templates the platform is asked for -- drought response,
irrigation modernisation, biofertilizer adoption and the 2050 SSP2-4.5
projection -- inspectable and editable as data instead of as code paths, and
lets a caller add a template by adding one entry.

The catalog is JSON-serialisable by construction: ``template_as_dict`` and
``catalog_as_dict`` return plain dicts/lists/strings/numbers, and
``load_catalog`` accepts either a YAML or a JSON document with the same shape,
so a deployment can ship its own templates in a file without a code change.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

__all__ = [
    "SCENARIO_SECTIONS",
    "TEMPLATE_NAMES",
    "SCENARIO_TEMPLATES",
    "template_names",
    "get_template",
    "merge_overrides",
    "template_as_dict",
    "catalog_as_dict",
    "load_catalog",
    "dump_catalog",
]


#: The six sections a composite scenario definition carries. Anything outside
#: this set is rejected by :meth:`CompositeScenarioEngine.define_scenario`,
#: because a silently ignored typo in a scenario file is a silent loss of scope.
SCENARIO_SECTIONS: tuple[str, ...] = (
    "climate",
    "irrigation",
    "land_use",
    "market",
    "policy",
    "social",
)

#: The names of the templates this module ships.
TEMPLATE_NAMES: tuple[str, ...] = (
    "drought_response",
    "irrigation_modernisation",
    "biofertilizer_adoption",
    "climate_2050_ssp245",
)

#: The catalog itself. Every value is a JSON scalar (or a list of dicts whose
#: values are JSON scalars), so ``json.dumps(catalog_as_dict())`` round-trips.
SCENARIO_TEMPLATES: dict[str, dict[str, Any]] = {
    # ------------------------------------------------------------------ #
    # Drought response: the SSP climate shock is kept, rainfed area is
    # claimed back through deficit irrigation, and the policy lever is a
    # capital subsidy that makes the water infrastructure affordable.
    # ------------------------------------------------------------------ #
    "drought_response": {
        "description": (
            "Synthetic semi-arid wheat system under a drought signal: the climate "
            "projection is applied, supplemental irrigation is capped at the water "
            "the basin can allocate, and a capital subsidy funds the works."
        ),
        "parameters": {
            "climate": {
                "baseline_annual_precip_mm": 300.0,
                "baseline_annual_et0_mm": 1800.0,
                "ssp": "SSP2-4.5",
                "target_year": 2050,
                "precip_shock_fraction": 0.7,
                "rainfall_factor": 1.0,
            },
            "irrigation": {
                "method": "sprinkler",
                "efficiency": 0.65,
                "allowable_depletion": 0.55,
                "effective_rain_fraction": 0.7,
                "max_net_applied_mm": 250.0,
            },
            "land_use": {
                "crop": "wheat",
                "texture": "loam",
                "curve_number_baseline": 80.0,
                "curve_number_change": 0.0,
                "crop_coefficient": 1.1,
                "root_depth_m": 1.0,
                "management_yield_factor": 1.0,
            },
            "market": {"price_per_tonne": 20000000.0, "volatility": 0.18},
            "policy": {"capital_subsidy_fraction": 0.4},
            "social": {},
        },
    },
    # ------------------------------------------------------------------ #
    # Irrigation modernisation: sprinkler -> drip raises the efficiency
    # the irrigation routes consume, lowers the curve number (less runoff
    # from the field surface) and raises pumping demand for the aquifer.
    # ------------------------------------------------------------------ #
    "irrigation_modernisation": {
        "description": (
            "Modernisation of an existing scheme: sprinkler irrigation replaced by "
            "drip, which raises application efficiency, lowers the field curve "
            "number and raises the drawdown the same crop demand causes."
        ),
        "parameters": {
            "climate": {
                "baseline_annual_precip_mm": 300.0,
                "baseline_annual_et0_mm": 1800.0,
                "ssp": "SSP2-4.5",
                "target_year": 2050,
                "rainfall_factor": 1.0,
            },
            "irrigation": {
                "method": "drip",
                "efficiency": 0.9,
                "allowable_depletion": 0.55,
                "effective_rain_fraction": 0.7,
                "max_net_applied_mm": 350.0,
            },
            "land_use": {
                "crop": "wheat",
                "texture": "loam",
                "curve_number_baseline": 80.0,
                "curve_number_change": -6.0,
                "crop_coefficient": 1.1,
                "root_depth_m": 1.2,
                "management_yield_factor": 1.0,
            },
            "market": {"price_per_tonne": 20000000.0, "volatility": 0.18},
            "policy": {"capital_subsidy_fraction": 0.25},
            "social": {},
        },
    },
    # ------------------------------------------------------------------ #
    # Biofertilizer adoption: an input subsidy for the biological input
    # (it raises the operating cost the costing route sees) and a
    # scenario-declared yield response, which is labelled a proxy.
    # ------------------------------------------------------------------ #
    "biofertilizer_adoption": {
        "description": (
            "Adoption of a biofertilizer programme: the biological input is priced "
            "into the operating cost through an input subsidy, and the yield "
            "response is a scenario-declared factor rather than a model output."
        ),
        "parameters": {
            "climate": {
                "baseline_annual_precip_mm": 300.0,
                "baseline_annual_et0_mm": 1800.0,
                "ssp": "SSP2-4.5",
                "target_year": 2050,
                "rainfall_factor": 1.0,
            },
            "irrigation": {
                "method": "sprinkler",
                "efficiency": 0.65,
                "allowable_depletion": 0.55,
                "effective_rain_fraction": 0.7,
                "max_net_applied_mm": 300.0,
            },
            "land_use": {
                "crop": "wheat",
                "texture": "loam",
                "curve_number_baseline": 80.0,
                "curve_number_change": 0.0,
                "crop_coefficient": 1.1,
                "root_depth_m": 1.0,
                "management_yield_factor": 1.08,
            },
            "market": {"price_per_tonne": 20000000.0, "volatility": 0.18},
            "policy": {
                "capital_subsidy_fraction": 0.0,
                "input_subsidy_fraction": 0.3,
                "biofertilizer_cost_per_ha_irr": 450000.0,
            },
            "social": {},
        },
    },
    # ------------------------------------------------------------------ #
    # The 2050 SSP2-4.5 projection run on its own, with the baseline
    # management and no policy intervention: the climate-only comparison
    # case the other three templates are measured against.
    # ------------------------------------------------------------------ #
    "climate_2050_ssp245": {
        "description": (
            "The 2050 SSP2-4.5 projection applied to the baseline semi-arid wheat "
            "system, with baseline management and no policy intervention: the "
            "climate-only comparison case."
        ),
        "parameters": {
            "climate": {
                "baseline_annual_precip_mm": 300.0,
                "baseline_annual_et0_mm": 1800.0,
                "ssp": "SSP2-4.5",
                "target_year": 2050,
                "rainfall_factor": 1.0,
            },
            "irrigation": {
                "method": "sprinkler",
                "efficiency": 0.65,
                "allowable_depletion": 0.55,
                "effective_rain_fraction": 0.7,
                "max_net_applied_mm": 250.0,
            },
            "land_use": {
                "crop": "wheat",
                "texture": "loam",
                "curve_number_baseline": 80.0,
                "curve_number_change": 0.0,
                "crop_coefficient": 1.1,
                "root_depth_m": 1.0,
                "management_yield_factor": 1.0,
            },
            "market": {"price_per_tonne": 20000000.0, "volatility": 0.18},
            "policy": {"capital_subsidy_fraction": 0.0, "input_subsidy_fraction": 0.0},
            "social": {},
        },
    },
}


#: The engine's own defaults for the parameters the templates do not set. A
#: template therefore only states what differs from this baseline, and a
#: scenario defined from no template at all still has a complete parameter set.
_DEFAULTS: dict[str, dict[str, Any]] = {
    "climate": {
        "latitude_deg": 32.0,
        "elevation_m": 1200.0,
        "doy": 196,
        "baseline_temp_min_c": 12.0,
        "baseline_temp_max_c": 28.0,
        "baseline_mean_temp_c": 20.0,
        "rh_min_pct": 20.0,
        "rh_max_pct": 65.0,
        "wind_speed_m_s": 1.8,
        "solar_radiation_mj_m2_day": 22.0,
        "temp_delta_c": 0.0,
        "precip_shock_fraction": 1.0,
        "co2_ppm": 420.0,
    },
    "irrigation": {
        "method": "sprinkler",
        "efficiency": 0.65,
        "allowable_depletion": 0.55,
        "effective_rain_fraction": 0.7,
        "max_net_applied_mm": 250.0,
    },
    "land_use": {
        "crop": "wheat",
        "texture": "loam",
        "curve_number_baseline": 80.0,
        "curve_number_change": 0.0,
        "crop_coefficient": 1.1,
        "root_depth_m": 1.0,
        "season_days": 180,
        "area_ha": 10.0,
        "management_yield_factor": 1.0,
        "attainable_yield_kg_ha": 4500.0,
        "yield_std_dev_kg_ha": 700.0,
        "aquifer_transmissivity_m2_day": 400.0,
        "aquifer_storativity": 0.0002,
        "well_distance_m": 150.0,
        "pumping_days": 120.0,
    },
    "market": {
        "price_per_tonne": 20000000.0,
        "volatility": 0.18,
        "discount_rate": 0.12,
        "project_lifetime_years": 15,
        "currency": "IRR",
        "initial_investment_irr": 500000000.0,
        "salvage_value_irr": 0.0,
        "confidence_level": 0.05,
        "labor_hours_per_hectare": 50.0,
        "labor_cost_per_hour_irr": 200000.0,
        "seed_cost_per_hectare_irr": 500000.0,
        "fertilizer_cost_per_hectare_irr": 300000.0,
        "machinery_cost_per_hectare_irr": 200000.0,
        "land_rent_per_hectare_irr": 100000.0,
        "other_variable_costs_per_hectare_irr": 80000.0,
    },
    "policy": {
        "capital_subsidy_fraction": 0.0,
        "input_subsidy_fraction": 0.0,
        "biofertilizer_cost_per_ha_irr": 0.0,
    },
    "social": {
        "population_served": 60,
        "district_population": 5000,
        "households": 14,
        "household_size": 4.3,
        "per_capita_consumption_kg": 165.0,
        "employment_intensity_fte_per_ha": 0.8,
        "employment_months_per_year": 10.0,
        "income_spent_locally_fraction": 0.4,
        "local_employment_multiplier": 0.02,
    },
}


def template_names() -> list[str]:
    """The names of the templates shipped by this module."""
    return list(TEMPLATE_NAMES)


def get_template(name: str) -> dict[str, Any]:
    """The template record for ``name`` (description + parameters)."""
    if name not in SCENARIO_TEMPLATES:
        known = ", ".join(template_names())
        raise KeyError(f"unknown scenario template {name!r}; known templates: {known}")
    return SCENARIO_TEMPLATES[name]


def merge_overrides(template: Mapping[str, Any] | None, overrides: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Merge a template's parameters with the engine defaults, then overrides.

    The merge is one level deep (``template``/``defaults`` give whole sections,
    ``overrides`` replaces whole sections): a caller who wants to change one
    parameter of a section passes the whole section back, which keeps the
    effective scenario readable as one document instead of a diff of diffs.
    """
    merged: dict[str, dict[str, Any]] = {
        section: dict(values) for section, values in _DEFAULTS.items()
    }
    if template is not None:
        parameters = template.get("parameters", {})
        for section, values in parameters.items():
            if section in merged:
                merged[section].update(dict(values))
            else:
                merged[section] = dict(values)
    for section, values in (overrides or {}).items():
        if section in merged:
            merged[section].update(dict(values))
        else:
            merged[section] = dict(values)
    return merged


def template_as_dict(name: str) -> dict[str, Any]:
    """One template as a plain (JSON-serialisable) dict."""
    return dict(get_template(name))


def catalog_as_dict() -> dict[str, Any]:
    """The whole catalog as a plain (JSON-serialisable) dict."""
    return {
        "sections": list(SCENARIO_SECTIONS),
        "templates": {name: template_as_dict(name) for name in template_names()},
    }


def load_catalog(path: str | Path) -> dict[str, Any]:
    """Load a catalog document from a YAML or JSON file.

    The shape expected is :func:`catalog_as_dict`'s, i.e. a ``templates``
    mapping of ``name -> {description, parameters}`` plus an optional
    ``sections`` list. A YAML document needs PyYAML; a JSON document does not,
    and both return the same structure so the caller cannot tell which parser
    ran.
    """
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() in (".yaml", ".yml"):
        try:
            # PyYAML ships no type hints in this environment; the import is
            # optional and guarded, so the untyped import is by design.
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:  # pragma: no cover - environment guard
            raise RuntimeError(
                f"loading {source.name} needs PyYAML; install it or ship the template "
                "as JSON (load_catalog accepts .json without PyYAML)"
            ) from exc
        return dict(yaml.safe_load(text) or {})
    return dict(json.loads(text))


def dump_catalog(path: str | Path, payload: Mapping[str, Any] | None = None) -> Path:
    """Write a catalog document, choosing YAML or JSON from the file suffix.

    Written with a trailing newline so the artifact diffs cleanly, and with
    ``sort_keys`` off so section order stays the order the engine documents.
    """
    document = catalog_as_dict() if payload is None else dict(payload)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix.lower() in (".yaml", ".yml"):
        try:
            # PyYAML ships no type hints in this environment; the import is
            # optional and guarded, so the untyped import is by design.
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:  # pragma: no cover - environment guard
            raise RuntimeError(
                f"writing {target.name} needs PyYAML; write the template as .json "
                "instead (dump_catalog accepts .json without PyYAML)"
            ) from exc
        target.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    else:
        target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return target
