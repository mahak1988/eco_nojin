"""
Soil Chemistry Calculations.

Implements key soil chemistry calculations including:
- Cation Exchange Capacity (CEC)
- Exchangeable Sodium Percentage (ESP)
- Sodium Adsorption Ratio (SAR)
- pH buffering and lime requirement

Provenance of the two estimates in this module
----------------------------------------------
``calculate_cec`` and ``calculate_ph_buffer`` return *estimates*, and neither is
a published formula. Both are labelled as design assumptions where they are
implemented rather than being given a citation they do not support. See the
per-function docstrings. Measuring CEC, buffer capacity and lime requirement is
the only way to get a number that means anything for a particular field.

References:
    [1] Brady, N.C. and Weil, R.R., "The Nature and Properties of Soils",
        15th Edition, Pearson, 2017 -- general background. It is NOT the source
        of the CEC formula below; that attribution was withdrawn 2026-10-01.
    [2] USDA, "Soil Quality Indicators", 2023
"""

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

#: ESP at or above which a soil is *sodic*. USDA Handbook 60 (1951) defines a
#: sodic soil by ESP >= 15; this is a definitional threshold, not a management
#: trigger.
SODIC_ESP_THRESHOLD = 15.0

#: ESP at or above which a sodic-soil amendment is recommended. Lower than
#: SODIC_ESP_THRESHOLD on purpose: structural damage begins before the soil
#: crosses the definitional line. ``salinity.calculate_sodic_soil_amendment``
#: uses the same number as its gypsum trigger.
AMENDMENT_ESP_THRESHOLD = 10.0


def calculate_cec(clay: float, organic_matter: float, ph: float) -> dict:
    """Calculate Cation Exchange Capacity (CEC) -- an unverified estimate.

    CEC is the total capacity of soil to hold exchangeable cations. It is a
    *measured* quantity: a laboratory determines it (NH4OAc at pH 7, or by
    summing the exchangeable bases). This function estimates it from three
    cheap predictors, and the estimate is a design assumption, not a published
    estimator. Any caller that needs a CEC for a particular soil should measure
    it.

    Formula:
        CEC = (clay% x 0.5) + (OM% x 2.0) + max(0, (pH - 5.0) * 0.5)

    What is and is not defensible in the three terms
    -------------------------------------------------
    * ``clay% * 0.5`` meq/100g per % clay. Clay minerals differ by an order of
      magnitude in CEC (kaolinite roughly 0.1, illite 0.5-1.0, smectite 0.7-1.2
      meq/100g of clay), so a single mid-range coefficient cannot be a
      published estimator for "clay". It is a midpoint, and it assumes the
      unknown clay mineralogy.
    * ``OM% * 2.0``. This is the one term with an internal check: it is
      consistent with organic matter carrying about 200 meq/100g, so 1 % OM
      contributes about 2. It is still an assumption about the fraction and
      nature of the organic matter, not a measurement.
    * ``max(0, (pH - 5.0) * 0.5)``. **Not defensible.** This is the term the
      earlier version of this docstring cited to Brady & Weil (2017) Chapter 8,
      and that attribution is withdrawn: a linear additive pH bonus is not how
      variable-charge soils behave, and it is not how a measured CEC behaves
      either. Variable charge arises from pH-dependent surface charge on Fe/Al
      oxides and organic matter; it *reduces* apparent CEC as pH falls toward
      the point of zero charge (roughly pH 7-8), it is strongly nonlinear, and
      it depends on surface potential rather than on bulk soil pH. The
      ``max(0, ...)`` floor makes this worse rather than better: below pH 5 the
      term is pinned at zero, whereas variable-charge behaviour would drive the
      apparent CEC *down*, not hold it. A measured CEC at pH 7 also already
      reflects the pH it was measured at, so adding a pH term double-counts it.

    The arithmetic is unchanged. Replacing the pH term with a real one is a
    modelling decision, not a repair, and the source is not in the repository.

    Args:
        clay: Clay percentage (0-100)
        organic_matter: Organic matter percentage (0-100)
        ph: Soil pH (0-14)

    Returns:
        Dict: CEC results with interpretation

    Raises:
        ValueError: If input values are invalid

    Example:
        >>> result = calculate_cec(30, 2.5, 6.5)
        >>> print(result['cec'])
        20.75

    The 20.75 is not a rounding of 21.5; the arithmetic below is the whole of
    it, and it is here so a reader can check it without running anything::

        clay  30 * 0.5            = 15.00   (clay_contribution)
        om   2.5 * 2.0            =  5.00   (organic_matter_contribution)
        pH  (6.5 - 5.0) * 0.5     =  0.75   (ph_factor, floored at 0)
                                 -------
                                 20.75

    This example claimed 21.5 until 2026-10-01, which matches no combination of
    the three terms. ``result["components"]`` carries the same three numbers and
    they are the authoritative record of how the total was reached.
    """
    # Validate inputs
    if not 0 <= clay <= 100:
        raise ValueError("Clay must be between 0 and 100")
    if not 0 <= organic_matter <= 100:
        raise ValueError("Organic matter must be between 0 and 100")
    if not 0 <= ph <= 14:
        raise ValueError("pH must be between 0 and 14")

    # CEC contribution from clay (meq/100g)
    # Average clay CEC: 0.5 meq/100g per % clay. A midpoint across kaolinite,
    # illite and smectite, which differ by an order of magnitude -- see the
    # docstring.
    clay_cec = clay * 0.5

    # CEC contribution from organic matter
    # OM has very high CEC: ~200 meq/100g, but only 2% of soil
    # So approximately 2.0 meq/100g per % OM
    om_cec = organic_matter * 2.0

    # pH factor. NOT a variable-charge term and not a published estimator: a
    # linear bonus floored at zero, which moves the wrong way relative to
    # variable-charge behaviour. Kept because the arithmetic is part of the
    # published 20.75 example above and is used by the gateway; see the
    # docstring for why the attribution to Brady & Weil was withdrawn.
    ph_factor = max(0, (ph - 5.0) * 0.5)

    # Total CEC
    cec = clay_cec + om_cec + ph_factor

    # Interpretation
    interpretation = _interpret_cec(cec)

    return {
        "cec": round(cec, 2),
        "unit": "meq/100g",
        "components": {
            "clay_contribution": round(clay_cec, 2),
            "organic_matter_contribution": round(om_cec, 2),
            "ph_factor": round(ph_factor, 2),
        },
        "interpretation": interpretation,
    }


def _interpret_cec(cec: float) -> dict:
    """Interpret CEC value."""
    if cec < 5:
        return {
            "rating": "very_low",
            "description": "Very low CEC, sandy soil",
            "fertility_implications": "Low nutrient holding capacity",
            "recommendation": "Add organic matter to improve CEC",
        }
    elif cec < 10:
        return {
            "rating": "low",
            "description": "Low CEC",
            "fertility_implications": "Limited nutrient holding",
            "recommendation": "Increase organic matter",
        }
    elif cec < 20:
        return {
            "rating": "moderate",
            "description": "Moderate CEC",
            "fertility_implications": "Good nutrient holding",
            "recommendation": "Maintain organic matter levels",
        }
    elif cec < 30:
        return {
            "rating": "high",
            "description": "High CEC",
            "fertility_implications": "Excellent nutrient holding",
            "recommendation": "Ideal for most crops",
        }
    else:
        return {
            "rating": "very_high",
            "description": "Very high CEC",
            "fertility_implications": "Outstanding nutrient holding",
            "recommendation": "May need more fertilizer due to high retention",
        }


def calculate_esp(exchangeable_na: float, cec: float) -> dict:
    """Calculate Exchangeable Sodium Percentage (ESP).

    ESP indicates the proportion of sodium on the exchange complex.
    High ESP (>15) indicates sodic soil.

    Formula:
        ESP = (Exchangeable Na / CEC) x 100

    Two thresholds, and why both appear in the result
    --------------------------------------------------
    ``SODIC_ESP_THRESHOLD`` (15) is the definitional one from USDA Handbook 60:
    at or above it the soil *is* sodic. ``AMENDMENT_ESP_THRESHOLD`` (10) is the
    management one and fires earlier, because structural degradation starts
    before the definitional line. They were previously only half-communicated:
    the result reported ``"threshold": 15`` while ``needs_amendment`` was
    computed at 10, so a soil at ESP 12 came back flagged ``True`` with a
    ``threshold`` of 15 next to it. Both numbers are now returned by name, and
    ``salinity.calculate_sodic_soil_amendment`` uses the same 10 as its gypsum
    trigger rather than repeating the literal.

    The band boundaries below (5 and 10) only pick a descriptive label; they do
    not change any decision.

    Args:
        exchangeable_na: Exchangeable sodium (meq/100g)
        cec: Cation Exchange Capacity (meq/100g)

    Returns:
        Dict: ESP results with classification

    Raises:
        ValueError: If input values are invalid
    """
    if cec <= 0:
        raise ValueError("CEC must be positive")
    if exchangeable_na < 0:
        raise ValueError("Exchangeable sodium cannot be negative")

    esp = (exchangeable_na / cec) * 100

    # Classification
    if esp < 5:
        classification = "normal"
        impact = "No sodium problems"
    elif esp < 10:
        classification = "slightly_sodic"
        impact = "Minor structural issues possible"
    elif esp < 15:
        classification = "moderately_sodic"
        impact = "Structural degradation likely"
    else:
        classification = "sodic"
        impact = "Severe structural problems, poor infiltration"

    return {
        "esp": round(esp, 2),
        "unit": "%",
        "classification": classification,
        "impact": impact,
        "threshold": SODIC_ESP_THRESHOLD,
        "amendment_threshold": AMENDMENT_ESP_THRESHOLD,
        "needs_amendment": esp >= AMENDMENT_ESP_THRESHOLD,
    }


def calculate_sar(na: float, ca: float, mg: float) -> dict:
    """Calculate Sodium Adsorption Ratio (SAR).

    SAR is used to assess sodium hazard in irrigation water.

    Formula:
        SAR = Na / sqrt((Ca + Mg) / 2)

    Args:
        na: Sodium concentration (meq/L)
        ca: Calcium concentration (meq/L)
        mg: Magnesium concentration (meq/L)

    Returns:
        Dict: SAR results with classification

    Raises:
        ValueError: If input values are invalid
    """
    if na < 0 or ca < 0 or mg < 0:
        raise ValueError("Ion concentrations cannot be negative")

    denominator = math.sqrt((ca + mg) / 2)

    if denominator == 0:
        raise ValueError("Calcium + Magnesium cannot be zero")

    sar = na / denominator

    # Classification
    if sar < 3:
        classification = "low_sodium"
        hazard = "No sodium hazard"
    elif sar < 6:
        classification = "medium_sodium"
        hazard = "Some sodium hazard"
    elif sar < 9:
        classification = "high_sodium"
        hazard = "Significant sodium hazard"
    else:
        classification = "very_high_sodium"
        hazard = "Severe sodium hazard"

    return {
        "sar": round(sar, 2),
        "unit": "(meq/L)^0.5",
        "classification": classification,
        "hazard": hazard,
        "suitable_for_irrigation": sar < 9,
    }


def calculate_ph_buffer(ph: float, buffer_capacity: float = 0.5) -> dict[str, Any]:
    """
    Calculate pH buffer requirements for soil.

    ``buffer_capacity`` is ACCEPTED AND NOT USED. Every returned dict now
    carries ``"buffer_capacity_ignored": True`` so a caller cannot mistake the
    parameter for one that was honoured. It was documented as "Soil buffer
    capacity (0.1-2.0)" with no hint that it did nothing, and no branch read
    it, so passing a measured buffer capacity returned exactly what passing 0.1
    returned -- 3.0 t/ha of lime at pH 5.0 in both cases.

    Why it is still here
    --------------------
    It is an exported name (``soil.calculate_ph_buffer``) and removing a
    positional parameter is a breaking API change. What a buffer capacity
    *should* modulate is the lime and sulfur rates below, which are literals;
    a rate model is a domain decision, and the source is not in the repository.
    Whoever decides it should either use this parameter or drop it, and the
    ``"buffer_capacity_ignored"`` key is what makes that decision visible in a
    response body rather than buried here.

    The rates themselves are also assumptions, not measurements. A lime
    requirement in t/ha is a function of the depth and bulk density of the layer
    being limed as well as of the pH deficit, and this function assumes neither;
    ``ph_change_expected`` is the target, not a prediction.

    Args:
        ph: Current soil pH
        buffer_capacity: Accepted for interface compatibility and ignored. The
            0.1-2.0 range in the signature is not validated, and cannot be: no
            code path reads it.

    Returns:
        Dictionary with pH correction recommendations
    """
    # This is a universally accepted agronomic constant, not a configuration value
    OPTIMAL_SOIL_PH = 6.5
    target_ph = OPTIMAL_SOIL_PH

    if ph < target_ph:
        # Lime needed
        ph_deficit = target_ph - ph

        # Estimate lime requirement (tons/ha)
        # Rule of thumb: 1 ton lime raises pH by 0.5-1.0. The coefficient below
        # uses the conservative 0.5 end (2 t per pH unit). No depth or bulk
        # density is assumed; see the docstring.
        lime_requirement = ph_deficit * 2  # Conservative estimate

        return {
            "current_ph": ph,
            "target_ph": target_ph,
            "action": "add_lime",
            "ph_status": "acidic",
            "lime_requirement": round(lime_requirement, 2),
            "lime_unit": "tons/ha",
            "ph_change_expected": round(ph_deficit, 2),
            "buffer_capacity_ignored": True,
        }
    elif ph > 7.5:
        # Sulfur needed
        ph_excess = ph - 7.0

        # Estimate sulfur requirement (kg/ha)
        sulfur_requirement = ph_excess * 100

        return {
            "current_ph": ph,
            "target_ph": 7.0,
            "action": "add_sulfur",
            "ph_status": "alkaline",
            "sulfur_requirement": round(sulfur_requirement, 2),
            "sulfur_unit": "kg/ha",
            "ph_change_expected": round(ph_excess, 2),
            "buffer_capacity_ignored": True,
        }
    else:
        # Optimal pH range
        return {
            "current_ph": ph,
            "target_ph": target_ph,
            "action": "no_amendment_needed",
            "ph_status": "optimal",
            "message": "pH is in optimal range (6.5-7.5)",
            "buffer_capacity_ignored": True,
        }
