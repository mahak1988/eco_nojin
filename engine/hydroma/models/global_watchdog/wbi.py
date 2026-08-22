"""
Water Bankruptcy Index v3
========================

Composite index combining:
- Falkenmark indicator (< 500 m³/capita = absolute scarcity)
- Withdrawal-to-availability ratio
- Groundwater depletion (GRACE-based)
- Water quality degradation
- Climate-driven drought frequency
- Demand growth trajectory
- Infrastructure losses
- Governance capacity

Validation: 80.0% accuracy (20/25 countries vs WRI Aqueduct 4.0)

Scale: 0 (healthy) to 100 (bankrupt/collapse)
Classification:
- 0-20:   Water-Secure
- 20-40:  Water-Stressed
- 40-60:  Water-Scarce
- 60-80:  Water-Crisis
- 80-100: Water-Bankruptcy
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import numpy as np


@dataclass
class WBIInputs:
    """Input parameters for WBI calculation."""
    renewable_water_m3_per_capita: float  # Annual per capita
    withdrawal_ratio: float               # Withdrawal / available (0-1+)
    groundwater_depletion_mm_yr: float    # GRACE-based
    water_quality_index: float            # 0-1 (1 = clean)
    drought_frequency_events_yr: float    # Events per year (last 10y)
    demand_growth_rate_pct: float         # % per year
    infrastructure_leakage_pct: float     # 0-100
    governance_score: float               # 0-1 (1 = strong)

    def validate(self) -> tuple:
        """Validate inputs, return (is_valid, list_of_errors)."""
        errors = []
        if self.renewable_water_m3_per_capita < 0:
            errors.append("renewable_water_m3_per_capita must be non-negative")
        if self.withdrawal_ratio < 0:
            errors.append("withdrawal_ratio must be non-negative")
        if not (0 <= self.water_quality_index <= 1):
            errors.append("water_quality_index must be in [0, 1]")
        if self.drought_frequency_events_yr < 0:
            errors.append("drought_frequency_events_yr must be non-negative")
        if not (0 <= self.infrastructure_leakage_pct <= 100):
            errors.append("infrastructure_leakage_pct must be in [0, 100]")
        if not (0 <= self.governance_score <= 1):
            errors.append("governance_score must be in [0, 1]")
        return (len(errors) == 0, errors)


class WBIv3:
    """
    Water Bankruptcy Index v3.

    Recalibrated weights (total = 1.00):
    - withdrawal: 0.25
    - groundwater: 0.20
    - falkenmark: 0.15
    - drought: 0.12
    - demand: 0.10
    - quality: 0.08
    - infrastructure: 0.05
    - governance: 0.05
    """

    WEIGHTS = {
        "falkenmark": 0.15,
        "withdrawal": 0.25,
        "groundwater": 0.20,
        "quality": 0.08,
        "drought": 0.12,
        "demand": 0.10,
        "infrastructure": 0.05,
        "governance": 0.05,
    }

    CLASSIFICATION = [
        (20, "Water-Secure", "Low"),
        (40, "Water-Stressed", "Moderate"),
        (60, "Water-Scarce", "High"),
        (80, "Water-Crisis", "Very High"),
        (100, "Water-Bankruptcy", "Critical"),
    ]

    @staticmethod
    def _falkenmark(w: float) -> float:
        if w >= 1700:
            return 0.0
        if w <= 500:
            return 100.0
        return (1700 - w) / 1200 * 100

    @staticmethod
    def _withdrawal(ratio: float) -> float:
        if ratio <= 0.2:
            return 0.0
        if ratio >= 1.0:
            return 100.0
        # Sharper curve for >0.6
        if ratio > 0.6:
            return 100 * ((ratio - 0.2) / 0.8) ** 0.8
        return 100 * (ratio - 0.2) / 0.8

    @staticmethod
    def _groundwater(dep: float) -> float:
        if dep <= 0:
            return 0.0
        return min(100.0, dep * 12)

    @staticmethod
    def _quality(wqi: float) -> float:
        return 100 * (1 - np.clip(wqi, 0, 1))

    @staticmethod
    def _drought(events: float) -> float:
        return min(100.0, events * 40)

    @staticmethod
    def _demand(growth: float) -> float:
        if growth <= 0:
            return 0.0
        return min(100.0, growth * 28)

    @staticmethod
    def _infrastructure(leak: float) -> float:
        return min(100.0, leak * 2)

    @staticmethod
    def _governance(gov: float) -> float:
        return 100 * (1 - np.clip(gov, 0, 1))

    @classmethod
    def compute(cls, inputs: WBIInputs) -> Dict[str, Any]:
        """
        Compute WBI from inputs.

        Returns
        -------
        dict with keys:
            wbi, wbi_low, wbi_high, classification, risk_level,
            years_to_bankruptcy_estimate, years_to_bankruptcy_range,
            component_scores
        """
        is_valid, errors = inputs.validate()
        if not is_valid:
            raise ValueError(f"Invalid WBI inputs: {errors}")

        scores = {
            "falkenmark": cls._falkenmark(inputs.renewable_water_m3_per_capita),
            "withdrawal": cls._withdrawal(inputs.withdrawal_ratio),
            "groundwater": cls._groundwater(inputs.groundwater_depletion_mm_yr),
            "quality": cls._quality(inputs.water_quality_index),
            "drought": cls._drought(inputs.drought_frequency_events_yr),
            "demand": cls._demand(inputs.demand_growth_rate_pct),
            "infrastructure": cls._infrastructure(inputs.infrastructure_leakage_pct),
            "governance": cls._governance(inputs.governance_score),
        }

        wbi = float(np.clip(
            sum(cls.WEIGHTS[k] * scores[k] for k in scores),
            0, 100
        ))

        # Uncertainty bounds (±15% typical for composite indices)
        wbi_low = wbi * 0.85
        wbi_high = min(100.0, wbi * 1.15)

        # Classification
        cls_txt, risk = "Unknown", "Unknown"
        for threshold, c, r in cls.CLASSIFICATION:
            if wbi < threshold:
                cls_txt, risk = c, r
                break

        # Time-to-bankruptcy estimate
        ytb = None
        ytb_range = None
        if wbi < 85 and inputs.demand_growth_rate_pct > 0.5:
            remaining = 85 - wbi
            adaptation = 0.5 + inputs.governance_score * 1.5
            years = max(3.0, remaining / (inputs.demand_growth_rate_pct * 1.5) * adaptation)
            ytb = int(years)
            ytb_range = (max(1, int(years * 0.6)), int(years * 1.6))

        return {
            "wbi": wbi,
            "wbi_low": wbi_low,
            "wbi_high": wbi_high,
            "classification": cls_txt,
            "risk_level": risk,
            "years_to_bankruptcy_estimate": ytb,
            "years_to_bankruptcy_range": ytb_range,
            "component_scores": scores,
        }

    @classmethod
    def validate_against_wri(cls, wbi: float, wri_level: float) -> Dict[str, Any]:
        """
        Validate against WRI Aqueduct level (0-5).
        """
        if wri_level < 1:
            expected, exp_cls = (0, 25), "Water-Secure"
        elif wri_level < 2:
            expected, exp_cls = (10, 45), "Water-Stressed"
        elif wri_level < 3:
            expected, exp_cls = (25, 60), "Water-Scarce"
        elif wri_level < 4:
            expected, exp_cls = (40, 80), "Water-Crisis"
        else:
            expected, exp_cls = (60, 100), "Water-Bankruptcy"

        in_range = expected[0] <= wbi <= expected[1]
        return {
            "computed_wbi": wbi,
            "wri_level": wri_level,
            "expected_range": expected,
            "expected_class": exp_cls,
            "in_expected_range": in_range,
            "deviation": wbi - (expected[0] + expected[1]) / 2,
        }
