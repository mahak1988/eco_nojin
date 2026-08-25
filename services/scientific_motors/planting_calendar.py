"""
Hydroma Nojin - Global Planting Calendar Generator

Generates hemisphere-aware planting calendars based on:
- Köppen climate classification
- Geographic latitude (N/S hemisphere)
- Frost-free days
- Growing Degree Days (GDD)
- Monsoon/rainy season detection

Scientific basis:
- FAO Crop Calendar Guidelines
- USDA Plant Hardiness Zones
- Phenological Stage Models (GDD-based)

Outputs:
- Planting windows (months)
- Harvest windows
- Growth stage timeline
- Risk alerts (frost, drought, heat stress)
- Best companion crops per season
"""
from __future__ import annotations

import time
import numpy as np
import xarray as xr
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

from .base import (
    AbstractScientificMotor, MotorInput, MotorOutput,
    MotorParameters, MotorResult, MotorStatus, MotorType,
)


# =====================================================================
# Constants & Enums
# =====================================================================

class Hemisphere(Enum):
    NORTHERN = "Northern"
    SOUTHERN = "Southern"
    EQUATORIAL = "Equatorial"


class Season(Enum):
    """فصول کشاورزی جهانی"""
    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"
    RAINY = "Rainy Season"
    DRY = "Dry Season"


# ماه‌های هر فصل بر اساس نیمکره
HEMISPHERE_MONTHS = {
    Hemisphere.NORTHERN: {
        Season.SPRING: [3, 4, 5],
        Season.SUMMER: [6, 7, 8],
        Season.AUTUMN: [9, 10, 11],
        Season.WINTER: [12, 1, 2],
    },
    Hemisphere.SOUTHERN: {
        Season.SPRING: [9, 10, 11],
        Season.SUMMER: [12, 1, 2],
        Season.AUTUMN: [3, 4, 5],
        Season.WINTER: [6, 7, 8],
    },
    Hemisphere.EQUATORIAL: {
        # No real seasons, use rainy/dry
        Season.RAINY: [4, 5, 6, 10, 11],
        Season.DRY: [12, 1, 2, 3, 7, 8, 9],
    },
}

# Planting rules per Köppen climate
# Format: crop_id -> {preferred_seasons, gdd_required, frost_sensitive}
KOPPEN_PLANTING_RULES = {
    # ===== Cereals =====
    "wheat": {
        "BWh": {"season": Season.WINTER, "months_nh": [11, 12], "gdd": 1500, "frost": False},
        "BWk": {"season": Season.WINTER, "months_nh": [10, 11], "gdd": 1500, "frost": False},
        "BSk": {"season": Season.AUTUMN, "months_nh": [10, 11], "gdd": 1600, "frost": False},
        "BSh": {"season": Season.WINTER, "months_nh": [11, 12], "gdd": 1400, "frost": False},
        "Csa": {"season": Season.AUTUMN, "months_nh": [10, 11], "gdd": 1800, "frost": False},
        "Csb": {"season": Season.AUTUMN, "months_nh": [10, 11], "gdd": 1700, "frost": False},
        "Cfa": {"season": Season.AUTUMN, "months_nh": [10, 11], "gdd": 1800, "frost": False},
        "Cfb": {"season": Season.AUTUMN, "months_nh": [9, 10], "gdd": 1600, "frost": False},
        "Dfa": {"season": Season.AUTUMN, "months_nh": [9, 10], "gdd": 1700, "frost": False},
        "Dfb": {"season": Season.SPRING, "months_nh": [4, 5], "gdd": 1500, "frost": False},
        "Dwa": {"season": Season.AUTUMN, "months_nh": [9, 10], "gdd": 1600, "frost": False},
        "default": {"season": Season.AUTUMN, "months_nh": [10, 11], "gdd": 1600, "frost": False},
    },
    "maize": {
        "Aw": {"season": Season.RAINY, "months_nh": [5, 6], "gdd": 2500, "frost": True},
        "BSh": {"season": Season.RAINY, "months_nh": [5, 6], "gdd": 2500, "frost": True},
        "BSk": {"season": Season.SPRING, "months_nh": [4, 5], "gdd": 2700, "frost": True},
        "Cfa": {"season": Season.SPRING, "months_nh": [4, 5], "gdd": 2700, "frost": True},
        "Cwa": {"season": Season.SPRING, "months_nh": [4, 5], "gdd": 2600, "frost": True},
        "Cwb": {"season": Season.SPRING, "months_nh": [4, 5], "gdd": 2400, "frost": True},
        "Dfa": {"season": Season.SPRING, "months_nh": [5, 6], "gdd": 2600, "frost": True},
        "Dwa": {"season": Season.SPRING, "months_nh": [4, 5], "gdd": 2700, "frost": True},
        "default": {"season": Season.SPRING, "months_nh": [4, 5], "gdd": 2600, "frost": True},
    },
    "rice_paddy": {
        "Af": {"season": Season.RAINY, "months_nh": [4, 5], "gdd": 2800, "frost": True},
        "Am": {"season": Season.RAINY, "months_nh": [6, 7], "gdd": 2800, "frost": True},
        "Aw": {"season": Season.RAINY, "months_nh": [6, 7], "gdd": 2700, "frost": True},
        "Cfa": {"season": Season.SPRING, "months_nh": [4, 5], "gdd": 2800, "frost": True},
        "Cwa": {"season": Season.SUMMER, "months_nh": [6, 7], "gdd": 2800, "frost": True},
        "Cwb": {"season": Season.SUMMER, "months_nh": [5, 6], "gdd": 2600, "frost": True},
        "default": {"season": Season.SPRING, "months_nh": [5, 6], "gdd": 2700, "frost": True},
    },
    # ===== Tubers =====
    "potato": {
        "Cfb": {"season": Season.SPRING, "months_nh": [3, 4], "gdd": 1500, "frost": False},
        "Cfa": {"season": Season.SPRING, "months_nh": [2, 3], "gdd": 1500, "frost": False},
        "Cwb": {"season": Season.SPRING, "months_nh": [3, 4], "gdd": 1400, "frost": False},
        "Dfb": {"season": Season.SPRING, "months_nh": [5, 6], "gdd": 1300, "frost": False},
        "Dfc": {"season": Season.SUMMER, "months_nh": [6, 7], "gdd": 1100, "frost": False},
        "Aw": {"season": Season.DRY, "months_nh": [11, 12], "gdd": 1500, "frost": False},
        "default": {"season": Season.SPRING, "months_nh": [3, 4], "gdd": 1400, "frost": False},
    },
    "cassava": {
        "Af": {"season": Season.RAINY, "months_nh": [4, 5], "gdd": 3000, "frost": True},
        "Am": {"season": Season.RAINY, "months_nh": [5, 6], "gdd": 3000, "frost": True},
        "Aw": {"season": Season.RAINY, "months_nh": [5, 6], "gdd": 2800, "frost": True},
        "BSh": {"season": Season.RAINY, "months_nh": [5, 6], "gdd": 2800, "frost": True},
        "Cwa": {"season": Season.SPRING, "months_nh": [9, 10], "gdd": 2800, "frost": True},
        "default": {"season": Season.RAINY, "months_nh": [5, 6], "gdd": 2800, "frost": True},
    },
    # ===== Legumes =====
    "chickpea": {
        "BSk": {"season": Season.AUTUMN, "months_nh": [10, 11], "gdd": 1400, "frost": False},
        "Csa": {"season": Season.AUTUMN, "months_nh": [10, 11], "gdd": 1500, "frost": False},
        "Cfa": {"season": Season.AUTUMN, "months_nh": [10, 11], "gdd": 1500, "frost": False},
        "Cwa": {"season": Season.WINTER, "months_nh": [11, 12], "gdd": 1500, "frost": False},
        "default": {"season": Season.AUTUMN, "months_nh": [10, 11], "gdd": 1400, "frost": False},
    },
    "soybean": {
        "Cfa": {"season": Season.SPRING, "months_nh": [5, 6], "gdd": 2500, "frost": True},
        "Cwa": {"season": Season.SUMMER, "months_nh": [6, 7], "gdd": 2600, "frost": True},
        "Dfa": {"season": Season.SPRING, "months_nh": [5, 6], "gdd": 2500, "frost": True},
        "Aw": {"season": Season.RAINY, "months_nh": [6, 7], "gdd": 2600, "frost": True},
        "default": {"season": Season.SPRING, "months_nh": [5, 6], "gdd": 2500, "frost": True},
    },
    "cowpea": {
        "Aw": {"season": Season.RAINY, "months_nh": [6, 7], "gdd": 2200, "frost": True},
        "BSh": {"season": Season.RAINY, "months_nh": [6, 7], "gdd": 2200, "frost": True},
        "BSk": {"season": Season.SUMMER, "months_nh": [6, 7], "gdd": 2100, "frost": True},
        "Cwa": {"season": Season.SUMMER, "months_nh": [6, 7], "gdd": 2300, "frost": True},
        "default": {"season": Season.SUMMER, "months_nh": [6, 7], "gdd": 2200, "frost": True},
    },
    # ===== Fruits & Perennials =====
    "date_palm": {
        "BWh": {"season": Season.SPRING, "months_nh": [2, 3], "gdd": 4000, "frost": False},
        "BWk": {"season": Season.SPRING, "months_nh": [3, 4], "gdd": 3800, "frost": False},
        "default": {"season": Season.SPRING, "months_nh": [2, 3], "gdd": 3800, "frost": False},
    },
    "olive": {
        "Csa": {"season": Season.AUTUMN, "months_nh": [11, 12], "gdd": 3000, "frost": False},
        "Csb": {"season": Season.AUTUMN, "months_nh": [11, 12], "gdd": 2800, "frost": False},
        "BSk": {"season": Season.AUTUMN, "months_nh": [11, 12], "gdd": 2800, "frost": False},
        "default": {"season": Season.AUTUMN, "months_nh": [11, 12], "gdd": 2800, "frost": False},
    },
    # Default for any crop not listed
    "default": {
        "default": {"season": Season.SPRING, "months_nh": [4, 5], "gdd": 2000, "frost": False},
    },
}


# Crop-specific growth stages (% of total GDD)
GROWTH_STAGES = {
    # crop: [(stage_name, gdd_fraction), ...]
    "wheat": [
        ("Germination", 0.05),
        ("Tillering", 0.20),
        ("Stem elongation", 0.40),
        ("Booting/Heading", 0.60),
        ("Flowering", 0.75),
        ("Grain filling", 0.90),
        ("Maturity/Harvest", 1.00),
    ],
    "maize": [
        ("Germination", 0.05),
        ("Seedling", 0.15),
        ("Vegetative (V6-V12)", 0.40),
        ("Tasseling (VT)", 0.55),
        ("Silking (R1)", 0.65),
        ("Grain fill (R3-R5)", 0.90),
        ("Physiological maturity", 1.00),
    ],
    "rice_paddy": [
        ("Germination", 0.05),
        ("Seedling (nursery)", 0.15),
        ("Tillering", 0.35),
        ("Panicle initiation", 0.55),
        ("Heading/Flowering", 0.75),
        ("Grain filling", 0.95),
        ("Maturity", 1.00),
    ],
    "potato": [
        ("Sprouting", 0.08),
        ("Vegetative growth", 0.30),
        ("Tuber initiation", 0.50),
        ("Tuber bulking", 0.80),
        ("Maturation/Harvest", 1.00),
    ],
    "default": [
        ("Germination/Establishment", 0.10),
        ("Vegetative growth", 0.40),
        ("Reproductive phase", 0.70),
        ("Maturation", 0.90),
        ("Harvest", 1.00),
    ],
}


@dataclass
class PlantingWindow:
    """پنجره کاشت برای یک محصول"""
    crop_id: str
    crop_name: str
    hemisphere: Hemisphere
    planting_months_nh: List[int]  # Northern Hemisphere months
    planting_months_local: List[int]  # Adjusted for local hemisphere
    harvest_months_local: List[int]
    growing_days: int
    gdd_required: int
    frost_sensitive: bool
    koppen: str
    season_name: str


# =====================================================================
# Main Motor
# =====================================================================

class PlantingCalendarMotor(AbstractScientificMotor):
    """
    Global Planting Calendar Generator
    
    Generates hemisphere-aware, Köppen-adapted planting calendars.
    """

    @property
    def motor_type(self) -> MotorType:
        return MotorType.BIOFERTILIZER

    @property
    def display_name(self) -> str:
        return "Global Planting Calendar (Hemisphere-aware)"

    def get_input_requirements(self) -> List[MotorInput]:
        return [
            MotorInput("latitude", "scalar", True, "Latitude (-90 to 90)"),
            MotorInput("koppen_climate", "scalar", True, "Köppen climate code"),
            MotorInput("crops", "list", True, "List of crop IDs from Crop Advisor"),
            MotorInput("frost_free_days", "scalar", False, "Frost-free days per year"),
        ]

    def get_outputs(self) -> List[MotorOutput]:
        return [
            MotorOutput("planting_calendar", "json", "calendar", "Full planting calendar"),
            MotorOutput("growth_stages", "json", "stages", "Phenological timeline"),
            MotorOutput("risk_alerts", "json", "alerts", "Frost/drought/heat risks"),
            MotorOutput("companion_crops", "json", "list", "Recommended companions"),
            MotorOutput("annual_schedule", "json", "months", "Month-by-month guide"),
        ]

    async def execute(self, inputs: Dict[str, Any], parameters: MotorParameters) -> MotorResult:
        start_time = time.time()
        run_id = f"CALENDAR_{int(time.time())}"

        try:
            # --- Extract parameters ---
            latitude = float(parameters.custom_params.get("latitude", inputs.get("latitude", 35.0)))
            koppen = str(parameters.custom_params.get("koppen_climate", inputs.get("koppen_climate", "BSk")))
            crop_ids = parameters.custom_params.get("crops", inputs.get("crops", ["wheat"]))
            frost_free_days = int(parameters.custom_params.get(
                "frost_free_days",
                self._estimate_frost_free_days(latitude, koppen)
            ))

            # --- Detect hemisphere ---
            hemisphere = self._detect_hemisphere(latitude)

            # --- Build planting windows for each crop ---
            planting_windows = []
            for crop_id in crop_ids:
                window = self._build_planting_window(
                    crop_id=crop_id,
                    koppen=koppen,
                    hemisphere=hemisphere,
                    frost_free_days=frost_free_days,
                )
                if window:
                    planting_windows.append(window)

            if not planting_windows:
                return MotorResult(
                    run_id=run_id,
                    motor_type=self.motor_type,
                    status=MotorStatus.FAILED,
                    error_message=f"No valid planting windows for crops: {crop_ids}",
                )

            # --- Generate growth stage timelines ---
            growth_stages = {
                w.crop_id: self._compute_growth_stages(w)
                for w in planting_windows
            }

            # --- Generate risk alerts ---
            risk_alerts = self._generate_risk_alerts(
                planting_windows, latitude, koppen, frost_free_days
            )

            # --- Recommend companion crops ---
            companion_crops = self._recommend_companions(planting_windows, koppen)

            # --- Build annual month-by-month schedule ---
            annual_schedule = self._build_annual_schedule(planting_windows)

            # --- Summary stats ---
            summary = {
                "hemisphere": hemisphere.value,
                "koppen_climate": koppen,
                "latitude": latitude,
                "frost_free_days": frost_free_days,
                "total_crops_scheduled": len(planting_windows),
                "earliest_planting_month": min(
                    min(w.planting_months_local) for w in planting_windows
                ),
                "latest_harvest_month": max(
                    max(w.harvest_months_local) for w in planting_windows
                ),
                "frost_sensitive_crops": sum(
                    1 for w in planting_windows if w.frost_sensitive
                ),
                "risk_alerts_count": len(risk_alerts),
            }

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "planting_calendar": [self._window_to_dict(w) for w in planting_windows],
                    "growth_stages": growth_stages,
                    "risk_alerts": risk_alerts,
                    "companion_crops": companion_crops,
                    "annual_schedule": annual_schedule,
                    "meta": {
                        "hemisphere": hemisphere.value,
                        "koppen": koppen,
                        "latitude": latitude,
                        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                },
                summary=summary,
                execution_time_seconds=time.time() - start_time,
            )

        except Exception as e:
            import traceback
            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message=f"{str(e)}\n{traceback.format_exc()}",
            )

    # =================================================================
    # Helper Methods
    # =================================================================

    def _detect_hemisphere(self, latitude: float) -> Hemisphere:
        """Detect hemisphere from latitude."""
        if abs(latitude) < 10:
            return Hemisphere.EQUATORIAL
        elif latitude > 0:
            return Hemisphere.NORTHERN
        else:
            return Hemisphere.SOUTHERN

    def _estimate_frost_free_days(self, latitude: float, koppen: str) -> int:
        """Estimate frost-free days based on latitude and Köppen."""
        # Köppen-based estimates
        koppen_frost_free = {
            "Af": 365, "Am": 365, "Aw": 365,  # Tropical
            "BWh": 300, "BSh": 280,           # Hot arid
            "BWk": 180, "BSk": 200,           # Cold arid
            "Csa": 270, "Csb": 250, "Csc": 200,  # Mediterranean
            "Cfa": 240, "Cfb": 220, "Cfc": 180,  # Temperate
            "Cwa": 280, "Cwb": 250, "Cwc": 200,  # Subtropical highland
            "Dfa": 180, "Dfb": 150, "Dfc": 100, "Dfd": 70,  # Continental
            "Dwa": 170, "Dwb": 140, "Dwc": 90, "Dwd": 60,
            "ET": 50, "EF": 0,  # Polar
        }
        base = koppen_frost_free.get(koppen, 200)
        
        # Latitude adjustment
        lat_adj = max(0, (abs(latitude) - 30) * 2)
        return max(0, int(base - lat_adj))

    def _build_planting_window(
        self, crop_id: str, koppen: str, hemisphere: Hemisphere,
        frost_free_days: int,
    ) -> Optional[PlantingWindow]:
        """Build a planting window for a specific crop."""
        # Get rules for this crop
        crop_rules = KOPPEN_PLANTING_RULES.get(crop_id, KOPPEN_PLANTING_RULES["default"])
        rule = crop_rules.get(koppen, crop_rules.get("default"))
        
        if rule is None:
            return None

        # Northern Hemisphere reference months
        months_nh = rule["months_nh"]
        season = rule["season"]
        gdd_required = rule["gdd"]
        frost_sensitive = rule["frost"]

        # Adjust for hemisphere
        if hemisphere == Hemisphere.SOUTHERN:
            # Shift by 6 months
            months_local = [(m + 5) % 12 + 1 for m in months_nh]
        elif hemisphere == Hemisphere.EQUATORIAL:
            # Prefer start of rainy season
            months_local = months_nh
        else:
            months_local = months_nh

        # Estimate growing days from GDD
        growing_days = int(gdd_required / 15)  # Average 15 GDD/day

        # Calculate harvest months
        harvest_months_local = []
        for m in months_local:
            harvest_m = (m + int(growing_days / 30) - 1) % 12 + 1
            if harvest_m not in harvest_months_local:
                harvest_months_local.append(harvest_m)

        # Get crop name from our database
        from .crop_database import get_crop_by_id
        crop = get_crop_by_id(crop_id)
        crop_name = crop.name_en if crop else crop_id

        return PlantingWindow(
            crop_id=crop_id,
            crop_name=crop_name,
            hemisphere=hemisphere,
            planting_months_nh=months_nh,
            planting_months_local=months_local,
            harvest_months_local=harvest_months_local,
            growing_days=growing_days,
            gdd_required=gdd_required,
            frost_sensitive=frost_sensitive,
            koppen=koppen,
            season_name=season.value,
        )

    def _compute_growth_stages(self, window: PlantingWindow) -> List[Dict]:
        """Compute phenological growth stages for a crop."""
        crop_stages = GROWTH_STAGES.get(window.crop_id, GROWTH_STAGES["default"])
        total_days = window.growing_days
        start_month = min(window.planting_months_local)

        stages = []
        cumulative_gdd = 0
        for stage_name, fraction in crop_stages:
            stage_gdd = int(window.gdd_required * fraction)
            stage_days = int(total_days * fraction)
            cumulative_gdd = stage_gdd
            
            # Estimate calendar month
            days_from_start = stage_days
            month_offset = days_from_start // 30
            stage_month = (start_month + month_offset - 1) % 12 + 1

            stages.append({
                "stage": stage_name,
                "gdd_cumulative": stage_gdd,
                "days_from_planting": stage_days,
                "estimated_month": stage_month,
                "description": self._stage_description(stage_name, window.crop_id),
            })

        return stages

    def _stage_description(self, stage_name: str, crop_id: str) -> str:
        """Get human-readable stage description."""
        descriptions = {
            "Germination": "Seed sprouts, emergence from soil",
            "Tillering": "Multiple shoots develop from base",
            "Stem elongation": "Rapid vertical growth",
            "Booting/Heading": "Grain head forms inside stem",
            "Flowering": "Reproductive phase, pollination",
            "Grain filling": "Grains accumulate starch",
            "Maturity/Harvest": "Crop ready for harvest",
            "Vegetative growth": "Leaf and stem development",
            "Tuber initiation": "Tubers begin to form",
            "Tuber bulking": "Tubers rapidly increase in size",
        }
        return descriptions.get(stage_name, "Growth stage")

    def _generate_risk_alerts(
        self, windows: List[PlantingWindow], latitude: float,
        koppen: str, frost_free_days: int,
    ) -> List[Dict]:
        """Generate risk alerts based on conditions."""
        alerts = []

        for w in windows:
            # Frost risk
            if w.frost_sensitive and frost_free_days < w.growing_days:
                alerts.append({
                    "crop": w.crop_name,
                    "risk": "FROST",
                    "severity": "HIGH",
                    "description": (
                        f"Growing period ({w.growing_days} days) exceeds "
                        f"frost-free window ({frost_free_days} days)"
                    ),
                    "mitigation": "Use row covers, select early-maturing variety",
                })

            # Heat stress in hot climates
            if koppen in ["BWh", "BSh"] and w.frost_sensitive:
                alerts.append({
                    "crop": w.crop_name,
                    "risk": "HEAT_STRESS",
                    "severity": "MEDIUM",
                    "description": "High temperatures may cause heat stress",
                    "mitigation": "Provide shade, increase irrigation, mulch",
                })

            # Drought risk in arid climates
            if koppen.startswith("B") and w.gdd_required > 2500:
                alerts.append({
                    "crop": w.crop_name,
                    "risk": "DROUGHT",
                    "severity": "MEDIUM",
                    "description": "Long growing season in arid climate",
                    "mitigation": "Use drip irrigation, mulch, drought-tolerant variety",
                })

        return alerts

    def _recommend_companions(
        self, windows: List[PlantingWindow], koppen: str,
    ) -> List[Dict]:
        """Recommend companion crops based on current selection."""
        # Companion planting rules
        companion_rules = {
            "maize": ["bean", "squash"],  # Three sisters
            "wheat": ["chickpea", "lentil"],
            "potato": ["bean", "cabbage"],
            "tomato": ["basil", "carrot"],
            "cassava": ["cowpea", "groundnut"],
        }

        recommendations = []
        crop_ids = [w.crop_id for w in windows]

        for w in windows:
            companions = companion_rules.get(w.crop_id, [])
            for comp in companions:
                if comp not in crop_ids:
                    recommendations.append({
                        "main_crop": w.crop_name,
                        "companion": comp,
                        "benefit": self._companion_benefit(w.crop_id, comp),
                        "timing": "Plant simultaneously or 2 weeks apart",
                    })

        return recommendations[:5]  # Limit to 5

    def _companion_benefit(self, main: str, companion: str) -> str:
        """Describe companion benefit."""
        benefits = {
            ("maize", "bean"): "N-fixation, structural support",
            ("maize", "squash"): "Ground cover, weed suppression",
            ("wheat", "chickpea"): "N-fixation, disease break",
            ("wheat", "lentil"): "N-fixation, soil improvement",
            ("potato", "bean"): "N-fixation, pest deterrence",
            ("tomato", "basil"): "Pest repellent, flavor enhancement",
            ("cassava", "cowpea"): "N-fixation, ground cover",
        }
        return benefits.get((main, companion), "Mutual benefit")

    def _build_annual_schedule(
        self, windows: List[PlantingWindow]
    ) -> Dict[int, List[Dict]]:
        """Build month-by-month activity schedule."""
        schedule = {m: [] for m in range(1, 13)}

        for w in windows:
            # Planting months
            for m in w.planting_months_local:
                schedule[m].append({
                    "action": "PLANT",
                    "crop": w.crop_name,
                    "crop_id": w.crop_id,
                })

            # Harvest months
            for m in w.harvest_months_local:
                schedule[m].append({
                    "action": "HARVEST",
                    "crop": w.crop_name,
                    "crop_id": w.crop_id,
                })

        return {str(k): v for k, v in schedule.items() if v}

    def _window_to_dict(self, w: PlantingWindow) -> Dict:
        """Convert PlantingWindow to Integerizable dict."""
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]
        return {
            "crop_id": w.crop_id,
            "crop_name": w.crop_name,
            "koppen_climate": w.koppen,
            "hemisphere": w.hemisphere.value,
            "season": w.season_name,
            "planting_months_nh": w.planting_months_nh,
            "planting_months_local": w.planting_months_local,
            "planting_month_names": [month_names[m-1] for m in w.planting_months_local],
            "harvest_months_local": w.harvest_months_local,
            "harvest_month_names": [month_names[m-1] for m in w.harvest_months_local],
            "growing_days": w.growing_days,
            "gdd_required": w.gdd_required,
            "frost_sensitive": w.frost_sensitive,
        }
