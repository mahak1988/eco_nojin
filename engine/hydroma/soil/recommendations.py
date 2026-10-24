"""
Soil Recommendations Engine.

Generates comprehensive soil management recommendations.

The cost figures in this module are uncited design assumptions
-------------------------------------------------------------
The header below cites Brady & Weil (2017) and USDA NRCS (2023), and that
citation supports the management advice. It does not support a single dollar
figure: the USD/hectare ranges in ``generate_recommendations`` and the identical
table in ``estimate_amendment_costs`` appear in no publication, carry no
retrieval date, and did not have one as of 2026-10-01. Amendment prices move with
region, season, transport distance and product grade by a factor of several, so
a bare "$50-100/ha" is not a number a reader can act on even if it were sourced.

They are labelled rather than removed, for the reason recorded in
engine/data/SOIL_TABLE_CONFLICTS.md: the advice is useful without the cost, but
removing the key would change the response shape of
``POST /api/v1/hydroma/soil/soil-recommendations/run`` for no scientific gain.
Sourcing them needs a price series with a date and a geography, which this
repository does not have.

References:
    [1] Brady, N.C. and Weil, R.R., "The Nature and Properties of Soils", 2017
        -- the management advice. Not the source of any cost range.
    [2] USDA NRCS, "Soil Health Management", 2023 -- as above
"""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


def generate_recommendations(soil_data: dict) -> dict:
    """Generate comprehensive soil management recommendations.

    Args:
        soil_data: Dictionary containing soil analysis results

    Returns:
        Dict: Comprehensive recommendations
    """
    recommendations: dict[str, Any] = {
        "generated_at": datetime.now(UTC).replace(tzinfo=None).isoformat(),
        "priority_actions": [],
        "fertility_management": [],
        "physical_management": [],
        "biological_management": [],
        "monitoring_plan": [],
        "estimated_costs": {},
    }

    # Extract relevant data
    health_score = soil_data.get("health_score", 50)
    ph = soil_data.get("ph", 6.5)
    organic_matter = soil_data.get("organic_matter", 2.0)
    texture = soil_data.get("texture", "loam")
    salinity = soil_data.get("salinity", {})

    # Priority actions based on health score
    if health_score < 40:
        recommendations["priority_actions"].append(
            {
                "action": "immediate_remediation",
                "urgency": "high",
                "description": "Soil health is critically low, immediate action needed",
            }
        )
    elif health_score < 60:
        recommendations["priority_actions"].append(
            {
                "action": "improvement_plan",
                "urgency": "medium",
                "description": "Soil health needs improvement",
            }
        )
    else:
        recommendations["priority_actions"].append(
            {
                "action": "maintenance",
                "urgency": "low",
                "description": "Maintain current soil health",
            }
        )

    # pH management
    if ph < 6.0:
        recommendations["fertility_management"].append(
            {
                "issue": "acidic_soil",
                "action": "apply_lime",
                "details": f"Current pH {ph}, target 6.5",
                "estimated_cost": "$50-100/ha",
            }
        )
    elif ph > 7.5:
        recommendations["fertility_management"].append(
            {
                "issue": "alkaline_soil",
                "action": "apply_sulfur",
                "details": f"Current pH {ph}, target 7.0",
                "estimated_cost": "$30-80/ha",
            }
        )

    # Organic matter management
    if organic_matter < 2.0:
        recommendations["biological_management"].append(
            {
                "issue": "low_organic_matter",
                "action": "add_compost",
                "details": f"Current OM {organic_matter}%, target 2-3%",
                "estimated_cost": "$100-200/ha",
            }
        )

    # Texture-specific recommendations
    texture_recommendations = _get_texture_recommendations(texture)
    if texture_recommendations:
        recommendations["physical_management"].extend(texture_recommendations)

    # Salinity recommendations
    if salinity.get("classification") not in ["non_saline", None]:
        recommendations["physical_management"].append(
            {
                "issue": "salinity",
                "action": salinity.get("management", {}).get("action", "monitor"),
                "details": salinity.get("description", "Manage salinity"),
            }
        )

    # Monitoring plan
    recommendations["monitoring_plan"] = _create_monitoring_plan(health_score)

    # Populate the cost roll-up. This key was initialised to {} above and left
    # that way, so every response advertised an ``estimated_costs`` object and
    # returned it empty even when the module's own estimator had everything it
    # needs -- it was written one function below and never called from here.
    recommendations["estimated_costs"] = estimate_amendment_costs(recommendations)

    return recommendations


def _get_texture_recommendations(texture: str) -> list[dict]:
    """Get recommendations based on soil texture."""
    recommendations = []

    if texture in ["sand", "loamy_sand"]:
        recommendations.append(
            {
                "issue": "low_water_holding",
                "action": "add_organic_matter",
                "details": "Sandy soils need organic matter to improve water retention",
                "practice": "Apply 2-5 cm compost annually",
            }
        )

    elif texture in ["clay", "silty_clay"]:
        recommendations.append(
            {
                "issue": "poor_drainage",
                "action": "improve_structure",
                "details": "Clay soils need improved drainage and structure",
                "practice": "Add gypsum and organic matter, consider raised beds",
            }
        )

    elif texture == "silt":
        recommendations.append(
            {
                "issue": "compaction_risk",
                "action": "avoid_compaction",
                "details": "Silty soils are prone to compaction",
                "practice": "Minimize traffic when wet, add organic matter",
            }
        )

    return recommendations


def _create_monitoring_plan(health_score: float) -> list[dict]:
    """Create monitoring plan based on health score."""
    plan = []

    # Basic monitoring
    plan.append({"parameter": "pH", "frequency": "annually", "method": "Soil test"})

    plan.append({"parameter": "organic_matter", "frequency": "annually", "method": "Soil test"})

    plan.append({"parameter": "NPK", "frequency": "annually", "method": "Soil test"})

    # Additional monitoring for poor health
    if health_score < 60:
        plan.append(
            {"parameter": "EC (salinity)", "frequency": "semi-annually", "method": "EC meter"}
        )

        plan.append(
            {"parameter": "Soil structure", "frequency": "quarterly", "method": "Visual assessment"}
        )

    # Biological monitoring
    plan.append({"parameter": "Earthworm count", "frequency": "annually", "method": "Visual count"})

    return plan


def estimate_amendment_costs(recommendations: dict) -> dict:
    """Estimate total costs for recommended amendments.

    The ranges below are uncited design assumptions -- see the module docstring.
    They are the same five USD/hectare bands that ``generate_recommendations``
    writes into the individual recommendation dicts, which means a caller sees
    the same figure twice and can compare them; they were not previously
    cross-checked against each other because the two functions were never both
    reached in one call.

    ``apply_gypsum`` and ``install_drainage`` are in the table but nothing in
    this module emits those actions, so they cannot currently contribute. They
    are left in place rather than deleted, because ``recommendations.py`` accepts
    a caller-supplied ``soil_data`` dict and a caller may add such an action.
    """
    total_min = 0
    total_max = 0

    cost_ranges = {
        "apply_lime": (50, 100),
        "apply_sulfur": (30, 80),
        "add_compost": (100, 200),
        "apply_gypsum": (40, 120),
        "install_drainage": (200, 500),
    }

    for category in ["fertility_management", "physical_management", "biological_management"]:
        for rec in recommendations.get(category, []):
            action = rec.get("action", "")
            if action in cost_ranges:
                min_cost, max_cost = cost_ranges[action]
                total_min += min_cost
                total_max += max_cost

    return {
        "estimated_min": total_min,
        "estimated_max": total_max,
        "unit": "$/ha",
        "interpretation": f"Total estimated cost: ${total_min}-${total_max}/ha",
    }
