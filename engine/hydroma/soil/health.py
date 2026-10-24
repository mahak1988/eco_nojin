"""
Soil Health Assessment.

Implements comprehensive soil health index calculation.

References:
    [1] USDA NRCS, "Soil Quality Indicators", 2023
    [2] Doran, J.W. and Parkin, T.B., "Defining and Assessing Soil Quality",
        in Defining Soil Quality for a Sustainable Environment, 1994
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Soil health indicators with weights.
#
# These seven are the whole table and the weights sum to 0.85, not 1.00. That is
# deliberate: the index is a weighted *mean* over the indicators that are
# actually measured, so the total is a normalisation constant rather than a share
# of a fixed budget, and every applied weight is now a weight the function really
# applies. The result dict reports the applied weights and they sum to the same
# 0.85, so the table and the arithmetic can no longer disagree.
#
# It used to declare nine. ``structure`` (0.05) and ``biological_activity`` (0.10)
# were removed on 2026-10-01 because nothing could score them:
#
#   * ``calculate_soil_health_index`` has no parameter for either, so the two
#     were never scored and the 0.15 they held was silently redistributed over
#     the other seven by the division below. A reader who trusted the table got
#     wrong numbers: the effective weights were ph 0.176 and organic matter
#     0.235, not 0.15 and 0.20, and 0.118 rather than 0.10 for each of the
#     other five. (0.15/0.85, 0.20/0.85, 0.10/0.85.)
#   * No caller has the data. ``assess_soil_quality`` and
#     ``engine/hydroma/biofertilizer/trials.py`` both call this function with
#     five arguments, and the API spec in
#     ``services/api_gateway/routers/hydroma_soil.py`` collects seven. Scoring
#     the two would mean defaulting them to a neutral 50 -- which is what
#     ``cec`` and ``texture`` do -- and that changes every published score.
#   * ``structure``'s "optimal" entry is ``("granular", "crumb")``, a pair of
#     structure *types*. ``_score_indicator`` needs a numeric range, and no
#     table of structure classes and their scores exists to replace it.
#
# Scoring them is defensible and adding the inputs is a product decision, not a
# repair. Deleting them is the action that does not invent a number. The weights
# were deliberately NOT redistributed over the remaining seven: doing so would
# move every score the engine has ever published, and the honest statement of a
# weighted mean does not need them to.
#
# ``tests/unit/test_soil_docstring_examples.py`` recorded the 1.00-vs-0.85 gap as
# a characterisation test and said whoever settled this had to change it on
# purpose. Its ``test_declared_weights_sum_to_one_but_only_a_subset_is_scored``
# now fails on ``assert declared_total == 1.0``; that file is not owned by this
# package, so the replacement assertion is in the hand-off in the change report
# rather than applied here.
#: weight/optimal pairs per indicator; ``optimal`` is a numeric range for the
#: scored indicators and the labelled pair for ``texture`` (scored by
#: ``_score_texture`` instead).
HEALTH_INDICATORS: dict[str, dict[str, Any]] = {
    "ph": {"weight": 0.15, "optimal": (6.0, 7.5)},
    "organic_matter": {"weight": 0.20, "optimal": (2.0, 5.0)},
    "nitrogen": {"weight": 0.10, "optimal": (30, 80)},
    "phosphorus": {"weight": 0.10, "optimal": (20, 60)},
    "potassium": {"weight": 0.10, "optimal": (100, 300)},
    "cec": {"weight": 0.10, "optimal": (10, 30)},
    "texture": {"weight": 0.10, "optimal": ("loam", "silt_loam")},
}


def calculate_soil_health_index(
    ph: float,
    organic_matter: float,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    cec: float | None = None,
    texture: str | None = None,
) -> dict:
    """Calculate comprehensive Soil Health Index.

    The Soil Health Index (SHI) is a weighted average of multiple
    soil quality indicators, each scored from 0-100.

    Args:
        ph: Soil pH
        organic_matter: Organic matter percentage
        nitrogen: Nitrogen (ppm)
        phosphorus: Phosphorus (ppm)
        potassium: Potassium (ppm)
        cec: Cation Exchange Capacity (optional)
        texture: USDA texture class (optional)

    Returns:
        Dict: Soil health assessment with scores and interpretation

    Example:
        >>> result = calculate_soil_health_index(6.5, 2.5, 50, 30, 200)
        >>> print(result['overall_score'])
        88.2

    Two things about that 88.2:

    1. This example claimed 78.5 until 2026-10-01. The five NPK-style arguments
       all sit inside their optimal ranges, so they each score 100.
    2. The index cannot reach 100 on *these* arguments, and that is now correct
       rather than a defect: ``cec`` and ``texture`` are optional and both
       default to a neutral 50 when omitted, so they hold the score at
       (100 * 0.65 + 50 * 0.20) / 0.85 even for a soil that is optimal on
       everything it was asked about. Supply them -- ``cec=20.0``,
       ``texture="loam"`` -- and the same soil scores 100.0, so the returned
       ``"max_score": 100`` is reachable.

    Concretely::

        scored at 100: ph .15 + organic_matter .20 + nitrogen .10
                          + phosphorus .10 + potassium .10   = 0.65
        scored at  50: cec .10 + texture .10                  = 0.20
        (100 * 0.65 + 50 * 0.20) / 0.85                       = 88.235...

    The number did not change on 2026-10-01 when the weight table was reduced to
    the seven indicators this function scores: the division was already by the
    applied weight, so removing two never-scored entries moved nothing.

    References:
        [1] USDA NRCS, 2023
    """
    scores = {}

    # Score each indicator
    scores["ph"] = _score_indicator(ph, HEALTH_INDICATORS["ph"]["optimal"])
    scores["organic_matter"] = _score_indicator(
        organic_matter, HEALTH_INDICATORS["organic_matter"]["optimal"]
    )
    scores["nitrogen"] = _score_indicator(nitrogen, HEALTH_INDICATORS["nitrogen"]["optimal"])
    scores["phosphorus"] = _score_indicator(phosphorus, HEALTH_INDICATORS["phosphorus"]["optimal"])
    scores["potassium"] = _score_indicator(potassium, HEALTH_INDICATORS["potassium"]["optimal"])

    if cec is not None:
        scores["cec"] = _score_indicator(cec, HEALTH_INDICATORS["cec"]["optimal"])
    else:
        scores["cec"] = 50  # Neutral score

    if texture is not None:
        scores["texture"] = _score_texture(texture)
    else:
        scores["texture"] = 50

    # Weighted mean over the indicators actually scored. The denominator is the
    # applied weight, not a constant 1.0: `weights` below reports exactly these
    # keys, and `HEALTH_INDICATORS` now contains nothing this function does not
    # score, so the table and the arithmetic cannot drift apart again.
    total_weight = sum(HEALTH_INDICATORS[k]["weight"] for k in scores)
    weighted_sum = sum(scores[k] * HEALTH_INDICATORS[k]["weight"] for k in scores)

    overall_score = weighted_sum / total_weight

    # Interpretation
    interpretation = _interpret_health_score(overall_score)

    # Identify limiting factors
    limiting_factors = _identify_limiting_factors(scores)

    return {
        "overall_score": round(overall_score, 1),
        "max_score": 100,
        "individual_scores": scores,
        "weights": {k: HEALTH_INDICATORS[k]["weight"] for k in scores},
        "interpretation": interpretation,
        "limiting_factors": limiting_factors,
        "recommendations": _generate_health_recommendations(scores, limiting_factors),
    }


def _score_indicator(value: float, optimal: tuple[float, float]) -> float:
    """Score an indicator based on optimal range.

    Scoring function:
        - 100 if within optimal range
        - Decreases linearly outside optimal range
        - 0 if far from optimal
    """
    min_val, max_val = optimal

    if min_val <= value <= max_val:
        return 100.0

    # Calculate distance from optimal
    if value < min_val:
        distance = min_val - value
        range_width = min_val  # Distance to zero
    else:
        distance = value - max_val
        range_width = max_val  # Distance from max

    if range_width == 0:
        return 50.0

    # Linear decrease
    score = max(0, 100 - (distance / range_width) * 100)

    return score


def _score_texture(texture: str) -> float:
    """Score soil texture based on agricultural suitability."""
    texture_scores = {
        "loam": 100,
        "silt_loam": 100,
        "clay_loam": 90,
        "sandy_loam": 85,
        "silt": 80,
        "silty_clay_loam": 75,
        "loamy_sand": 70,
        "sandy_clay_loam": 65,
        "sand": 50,
        "clay": 50,
        "silty_clay": 45,
        "sandy_clay": 40,
    }

    return texture_scores.get(texture, 60)


def _interpret_health_score(score: float) -> dict:
    """Interpret overall health score."""
    if score >= 80:
        return {
            "rating": "excellent",
            "description": "Soil is in excellent health",
            "productivity": "High productivity potential",
            "sustainability": "Very sustainable",
        }
    elif score >= 60:
        return {
            "rating": "good",
            "description": "Soil is in good health",
            "productivity": "Good productivity potential",
            "sustainability": "Sustainable with management",
        }
    elif score >= 40:
        return {
            "rating": "fair",
            "description": "Soil health needs improvement",
            "productivity": "Moderate productivity",
            "sustainability": "Requires attention",
        }
    else:
        return {
            "rating": "poor",
            "description": "Soil health is poor",
            "productivity": "Limited productivity",
            "sustainability": "Needs significant improvement",
        }


def _identify_limiting_factors(scores: dict) -> list[dict]:
    """Identify factors limiting soil health."""
    limiting = []

    for indicator, score in scores.items():
        if score < 60:  # Below 60 is limiting
            limiting.append(
                {
                    "indicator": indicator,
                    "score": score,
                    "severity": "critical" if score < 40 else "moderate",
                }
            )

    # Sort by score (worst first)
    limiting.sort(key=lambda x: x["score"])

    return limiting


def _generate_health_recommendations(scores: dict, limiting_factors: list) -> list[str]:
    """Generate recommendations based on scores."""
    recommendations = []

    for factor in limiting_factors[:3]:  # Top 3 limiting factors
        indicator = factor["indicator"]

        if indicator == "ph":
            if scores["ph"] < 50:
                recommendations.append("Adjust pH with lime or sulfur")
            else:
                recommendations.append("Monitor pH regularly")

        elif indicator == "organic_matter":
            recommendations.append("Add compost or cover crops to increase organic matter")

        elif indicator == "nitrogen":
            recommendations.append("Consider nitrogen-fixing cover crops or fertilizer")

        elif indicator == "phosphorus":
            recommendations.append("Add phosphorus amendments if needed")

        elif indicator == "potassium":
            recommendations.append("Consider potassium amendments")

        elif indicator == "cec":
            recommendations.append("Increase organic matter to improve CEC")

    if not recommendations:
        recommendations.append("Maintain current soil management practices")

    return recommendations


def assess_soil_quality(
    ph: float, organic_matter: float, nitrogen: float, phosphorus: float, potassium: float
) -> dict:
    """Comprehensive soil quality assessment.

    This is a simplified interface that combines health index
    with fertility assessment.
    """
    # Calculate health index
    health = calculate_soil_health_index(ph, organic_matter, nitrogen, phosphorus, potassium)

    # Fertility assessment
    fertility = _assess_fertility(nitrogen, phosphorus, potassium)

    return {
        "health_index": health,
        "fertility": fertility,
        "overall_assessment": _combine_assessments(health, fertility),
    }


def _assess_fertility(nitrogen: float, phosphorus: float, potassium: float) -> dict:
    """Assess soil fertility based on NPK levels."""

    def assess_level(value, low, medium, high):
        if value < low:
            return "deficient"
        elif value < medium:
            return "low"
        elif value < high:
            return "optimal"
        else:
            return "excessive"

    n_status = assess_level(nitrogen, 20, 40, 80)
    p_status = assess_level(phosphorus, 15, 30, 60)
    k_status = assess_level(potassium, 100, 150, 300)

    # Overall fertility
    statuses = [n_status, p_status, k_status]

    if all(s == "optimal" for s in statuses):
        overall = "high"
    elif any(s == "deficient" for s in statuses):
        overall = "low"
    else:
        overall = "moderate"

    return {"nitrogen": n_status, "phosphorus": p_status, "potassium": k_status, "overall": overall}


def _combine_assessments(health: dict, fertility: dict) -> dict:
    """Combine health and fertility assessments."""
    health_rating = health["interpretation"]["rating"]
    fertility_rating = fertility["overall"]

    # Combine ratings
    rating_scores = {
        "excellent": 4,
        "good": 3,
        "moderate": 2,
        "fair": 2,
        "poor": 1,
        "low": 1,
        "high": 3,
    }

    health_score = rating_scores.get(health_rating, 2)
    fertility_score = rating_scores.get(fertility_rating, 2)

    combined_score = (health_score + fertility_score) / 2

    if combined_score >= 3.5:
        combined_rating = "excellent"
    elif combined_score >= 2.5:
        combined_rating = "good"
    elif combined_score >= 1.5:
        combined_rating = "fair"
    else:
        combined_rating = "poor"

    return {
        "combined_rating": combined_rating,
        "health_rating": health_rating,
        "fertility_rating": fertility_rating,
        "management_priority": "maintain" if combined_score >= 3 else "improve",
    }
