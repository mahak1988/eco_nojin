"""
Soil Salinity Analysis.

Implements salinity classification and management recommendations.

Two ruff rules are deliberately not satisfied in this file:

* SIM116 (a chain of if/elif returning a dict should be a lookup table). The
  five branches are five distinct multi-line records, not one value, and the
  function also takes `ec` and varies its content by threshold. Folding it into
  a dict literal would move the ec-dependent parts into lambdas and make the
  table harder to read, not easier.
* SIM108 (a two-branch if/else should be a ternary). The else branch carries a
  comment explaining that a polar night reads as a clear sky, which is the
  reason for the value rather than an accident. A ternary would keep the value
  and drop the reason.

References:
    [1] USDA, "Diagnosis and Improvement of Saline and Alkali Soils",
        Agriculture Handbook 60, 1954
    [2] Rhoades, J.D., et al., "Using Soil Salinity to Improve Crop Production",
        2000
"""

import logging
from typing import Any

from .chemistry import AMENDMENT_ESP_THRESHOLD

logger = logging.getLogger(__name__)

# Salinity classification thresholds (EC in dS/m)
SALINITY_CLASSES: dict[str, dict[str, Any]] = {
    "non_saline": {"max_ec": 2, "description": "No salinity problem"},
    "slightly_saline": {"max_ec": 4, "description": "Yield of sensitive crops may be affected"},
    "moderately_saline": {"max_ec": 8, "description": "Yield of many crops is restricted"},
    "strongly_saline": {"max_ec": 16, "description": "Only tolerant crops yield satisfactorily"},
    "very_strongly_saline": {
        "max_ec": float("inf"),
        "description": "Only very tolerant crops yield",
    },
}


def classify_salinity(ec: float) -> dict:
    """Classify soil salinity based on electrical conductivity.

    Args:
        ec: Electrical conductivity (dS/m)

    Returns:
        Dict: Salinity classification and interpretation

    Example:
        >>> result = classify_salinity(6.5)
        >>> print(result['classification'])
        'moderately_saline'

    References:
        [1] USDA Handbook 60, 1954
    """
    if ec < 0:
        raise ValueError("EC cannot be negative")

    # Determine classification
    for class_name, thresholds in SALINITY_CLASSES.items():
        if ec < thresholds["max_ec"]:
            classification = class_name
            description = thresholds["description"]
            break

    # Crop tolerance recommendations
    crop_recommendations = _get_crop_recommendations(classification)

    # Management recommendations
    management = _get_management_recommendations(classification, ec)

    return {
        "ec": ec,
        "unit": "dS/m",
        "classification": classification,
        "description": description,
        "crop_recommendations": crop_recommendations,
        "management": management,
    }


def _get_crop_recommendations(classification: str) -> dict:
    """Get crop recommendations based on salinity."""
    recommendations = {
        "non_saline": {
            "suitable_crops": ["Most crops", "Sensitive vegetables", "Fruits"],
            "limitation": "None",
        },
        "slightly_saline": {
            "suitable_crops": ["Wheat", "Corn", "Tomato", "Lettuce"],
            "avoid": ["Very sensitive crops", "Strawberry"],
            "limitation": "Sensitive crops may show reduced yield",
        },
        "moderately_saline": {
            "suitable_crops": ["Barley", "Cotton", "Sugar beet", "Date palm"],
            "avoid": ["Sensitive vegetables", "Most fruits"],
            "limitation": "Only moderately tolerant crops",
        },
        "strongly_saline": {
            "suitable_crops": ["Barley", "Cotton", "Sugar beet", "Some grasses"],
            "avoid": ["Most field crops", "Vegetables"],
            "limitation": "Severe limitation",
        },
        "very_strongly_saline": {
            "suitable_crops": ["Salt-tolerant grasses", "Some halophytes"],
            "avoid": ["All conventional crops"],
            "limitation": "Extreme limitation",
        },
    }

    return recommendations.get(classification, recommendations["non_saline"])


def _get_management_recommendations(classification: str, ec: float) -> dict:
    """Get management recommendations based on salinity."""
    if classification == "non_saline":
        return {
            "action": "no_action_needed",
            "description": "Maintain current practices",
            "monitoring": "Regular EC monitoring",
        }

    elif classification == "slightly_saline":
        return {
            "action": "monitor_and_manage",
            "description": "Monitor EC and adjust irrigation",
            "practices": [
                "Ensure good drainage",
                "Use quality irrigation water",
                "Avoid over-irrigation",
            ],
        }

    elif classification == "moderately_saline":
        return {
            "action": "leaching_required",
            "description": "Leaching may be needed",
            "practices": [
                "Apply excess irrigation for leaching",
                "Install or improve drainage",
                "Consider gypsum application if sodic",
            ],
        }

    else:
        return {
            "action": "major_remediation",
            "description": "Significant remediation required",
            "practices": [
                "Install subsurface drainage",
                "Heavy leaching applications",
                "Chemical amendments (gypsum)",
                "Consider salt-tolerant crops",
            ],
        }


def calculate_leaching_requirement(
    ec_soil: float, ec_water: float, target_ec: float | None = None
) -> dict:
    """Calculate leaching requirement to reduce soil salinity.

    Formula, as implemented below:
        LR = EC_water / (5 * target_ec - EC_water)

    This docstring used to state ``LR = EC_water / (EC_soil - EC_water)``, which
    the code has never computed. The code is right and the docstring was wrong;
    see the comment at the ``denominator`` below for why the factor of 5 is
    there. Note that ``ec_soil`` appears only in the early-return comparisons and
    never in the ratio: the standard formulation depends on the *target*, not on
    where the soil currently is.

    Args:
        ec_soil: Current soil EC (dS/m)
        ec_water: Irrigation water EC (dS/m)
        target_ec: Target soil EC (optional)

    Returns:
        Dict: Leaching requirement calculations
    """
    if ec_soil <= ec_water:
        return {"leaching_required": False, "reason": "Soil EC is not higher than water EC"}

    if target_ec is None:
        target_ec = 4.0  # Target for most crops

    # Simplified leaching requirement
    if ec_soil <= target_ec:
        return {
            "leaching_required": False,
            "reason": f"Soil EC ({ec_soil}) is already below target ({target_ec})",
        }

    # Leaching requirement after FAO-29 (Ayers & Westcot 1985) / Rhoades (1974):
    #     LR = ECw / (5 * ECe - ECw)
    # The factor 5 converts the soil-saturation extract (ECe) to the
    # average root-zone salinity; omitting it over-estimates LR ~5-6x.
    denominator = 5.0 * target_ec - ec_water
    if denominator <= 0:
        return {
            "leaching_required": True,
            "reason": "Irrigation water EC is too high relative to the target "
            "soil EC - this water is not suitable without blending",
            "current_ec": ec_soil,
            "target_ec": target_ec,
            "water_ec": ec_water,
        }
    lr = ec_water / denominator
    # LR is physically bounded to (0, 1); no arbitrary floor is imposed so a
    # small requirement is reported honestly instead of being inflated.
    lr = min(0.95, max(0.0, lr))

    return {
        "leaching_required": True,
        "leaching_fraction": round(lr, 3),
        "leaching_percentage": round(lr * 100, 1),
        "current_ec": ec_soil,
        "target_ec": target_ec,
        "water_ec": ec_water,
        "interpretation": f"Apply {lr * 100:.1f}% extra water for leaching",
    }


def calculate_sodic_soil_amendment(
    esp: float, soil_depth: float, bulk_density: float = 1.4
) -> dict:
    """Calculate gypsum requirement for sodic soil amendment.

    Args:
        esp: Exchangeable Sodium Percentage
        soil_depth: Soil depth to amend, in **centimetres**. This is the unit the
            depth factor below is calibrated in (a 15 cm reference layer). The
            API spec for this tool labels the same argument "Soil depth" with
            unit "m" and a default of 0.3, so a caller going through
            services/api_gateway/routers/hydroma_soil.py passes metres into a
            centimetre formula and the depth factor comes out 100x too small --
            ESP 15 at 0.3 returns 100 kg/ha where 30 cm returns 10000 kg/ha.
            Fixed in the router, not here: guessing which unit the caller meant
            would change every published rate.
        bulk_density: Soil bulk density (g/cm3). **Accepted and not used.** The
            gypsum requirement is a mass per area, so bulk density does not
            enter it; it was never read by any branch. The result below now says
            so explicitly instead of leaving the reader to wonder.

    Returns:
        Dict: Gypsum requirement calculations
            so rather than leaving a caller to assume the value was used.

    Returns:
        Dict: Gypsum requirement calculations
    """
    # Decision record 2026-10-10 (gap G-H20): an in-flight edit made
    # ``bulk_density`` a *required* positional parameter, which broke two
    # strict tests that call this function without it. Making it defaulted
    # restores the pre-edit public signature without changing any result: the
    # AST of this function reads no ``bulk_density`` name at all, so the
    # default of 1.4 g/cm3 (the value every other route in this package uses)
    # cannot affect a number. If the parameter is ever meant to enter the
    # calculation, that is a model change and follows brake SB-03/SB-07 with a
    # decision record in GAP-REGISTER.md.
    if esp < AMENDMENT_ESP_THRESHOLD:
        return {
            "gypsum_required": False,
            "reason": (f"ESP ({esp}) is below amendment threshold ({AMENDMENT_ESP_THRESHOLD:g})"),
            "bulk_density_ignored": True,
        }

    # Gypsum requirement. The comment above used to say "1 ton gypsum per
    # 1000 m2 per 5 ESP points above 10", which is not what this code does in
    # either respect: the rate is per **100 m2** and per **1** ESP point (so 1
    # t/100 m2 per 10 points). The units returned, "tons/100m2", and the
    # kg/ha conversion below are mutually consistent -- 1 t/100 m2 is 10000
    # kg/ha -- so the code was self-consistent and the comment was wrong.
    #
    # What the corrected comment does *not* establish is that the coefficient is
    # right. 0.1 t/100 m2 per ESP point is 10 t/ha per ESP point, and at the
    # 15 cm reference depth that is 50 t/ha for a soil 5 ESP points over the
    # trigger -- roughly an order of magnitude above the rates normally quoted
    # for gypsum reclamation, and five times the rule the comment itself stated.
    # The coefficient is a design assumption with no citation and it is left
    # unchanged: replacing it needs a source, not a guess.

    esp_excess = esp - AMENDMENT_ESP_THRESHOLD
    gypsum_rate = esp_excess * 0.1  # tons per 100 m2, per ESP point above 10

    # Scale for depth
    depth_factor = soil_depth / 15  # Reference depth 15 cm
    gypsum_rate *= depth_factor

    # Convert to kg/ha
    gypsum_kg_ha = gypsum_rate * 10000  # tons/100m2 * 10000 = kg/ha

    return {
        "gypsum_required": True,
        "gypsum_rate": round(gypsum_rate, 2),
        "gypsum_unit": "tons/100m²",
        "gypsum_kg_per_ha": round(gypsum_kg_ha, 0),
        "esp": esp,
        "soil_depth": soil_depth,
        "soil_depth_unit": "cm",
        "bulk_density_ignored": True,
        "interpretation": f"Apply {gypsum_kg_ha:.0f} kg/ha of gypsum",
    }
