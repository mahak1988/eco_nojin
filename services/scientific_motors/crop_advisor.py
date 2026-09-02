"""
Hydroma Nojin - Global Intelligent Crop Advisor
Climate-centric recommendations using Köppen-Geiger classification.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from .base import (
    AbstractScientificMotor,
    MotorInput,
    MotorOutput,
    MotorParameters,
    MotorResult,
    MotorStatus,
    MotorType,
)
from .crop_database import (
    CROP_DATABASE,
    CropFamily,
    CropProfile,
    KoppenClimate,
    climate_description,
)


@dataclass
class CropMatch:
    crop: CropProfile
    suitability_score: float  # 0-100
    limiting_factors: list[str]
    expected_yield: float
    expected_profit_usd: float
    water_balance_mm: float
    confidence: float


@dataclass
class RotationPlan:
    """A single year of the suggested crop rotation (Y1..Y4)."""
    year: int
    crop_name: str
    crop_family: str
    reason: str
    biofertilizer_suggestion: str = ""


class CropAdvisorMotor(AbstractScientificMotor):
    """Global crop advisor - Köppen-climate centric."""

    @property
    def motor_type(self) -> MotorType:
        return MotorType.BIOFERTILIZER

    @property
    def display_name(self) -> str:
        return "Global Intelligent Crop Advisor (Köppen)"

    def get_input_requirements(self) -> list[MotorInput]:
        return [
            MotorInput("soil_ph", "raster", True, "Soil pH"),
            MotorInput("soil_texture", "raster", True, "USDA texture 1-12"),
            MotorInput("slope", "raster", True, "Slope percentage"),
            MotorInput("lcc_class", "raster", True, "LCC class 1-8"),
            MotorInput("altitude_m", "scalar", False, "Altitude meters"),
        ]

    def get_outputs(self) -> list[MotorOutput]:
        return [
            MotorOutput("top_recommendations", "json", "list", "Top crops"),
            MotorOutput("rotation_plan", "json", "years", "Crop rotation"),
            MotorOutput("economic_analysis", "json", "USD", "Economics"),
            MotorOutput("water_budget", "json", "mm", "Water analysis"),
            MotorOutput("climate_info", "json", "info", "Köppen climate details"),
        ]

    async def execute(self, inputs: dict[str, Any], parameters: MotorParameters) -> MotorResult:
        start_time = time.time()
        run_id = f"CROP_{int(time.time())}"

        try:
            # Extract Köppen climate (critical parameter)
            koppen_code = parameters.custom_params.get("koppen_climate", "BSk")
            try:
                # Enum lookup by NAME (square brackets), not by VALUE (parentheses)
                climate = KoppenClimate[koppen_code]
            except KeyError:
                valid_codes = [c.name for c in KoppenClimate]
                return MotorResult(run_id=run_id, motor_type=self.motor_type,
                                   status=MotorStatus.FAILED,
                                   error_message=(
                                       f"Unknown Köppen climate: {koppen_code}. "
                                       f"Valid codes: {valid_codes}"
                                   ))

            soil_ph = self._safe_mean(inputs.get("soil_ph"), 7.0)
            soil_texture = int(self._safe_mean(inputs.get("soil_texture"), 5))
            slope = self._safe_mean(inputs.get("slope"), 5.0)
            lcc_class = int(self._safe_mean(inputs.get("lcc_class"), 3))
            altitude = float(parameters.custom_params.get("altitude_m", 500))
            total_water_mm = float(parameters.custom_params.get("total_water_mm", 600))

            # Match crops
            matches = self._match_all_crops(
                climate, soil_ph, soil_texture, slope, lcc_class, altitude, total_water_mm
            )

            # Apply higher threshold for extreme climates (ET, EF)
            extreme_climates = {"ET", "EF"}
            if climate.name in extreme_climates:
                min_score = 70
                note = "Extreme climate: only highly adapted crops shown"
            else:
                min_score = 25
                note = "Standard filtering applied"

            matches = [m for m in matches if m.suitability_score >= min_score]
            matches = sorted(matches, key=lambda m: m.suitability_score, reverse=True)
            top = matches[:15]

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "top_recommendations": [self._to_dict(m) for m in top],
                    "rotation_plan": self._build_rotation(top, soil_ph, total_water_mm),
                    "economic_analysis": self._economic(top),
                    "water_budget": self._water(top, total_water_mm),
                    "climate_info": {
                        "koppen_code": climate.name,
                        "koppen_name": climate.value,
                        "description": climate_description(climate),
                        "global_examples": self._climate_examples(climate),
                    },
                    "conditions": {
                        "koppen": climate.name,
                        "soil_ph": soil_ph,
                        "soil_texture": soil_texture,
                        "slope_percent": slope,
                        "lcc_class": lcc_class,
                        "altitude_m": altitude,
                        "water_mm": total_water_mm,
                    },
                },
                summary={
                    "evaluated": len(matches),
                    "suitable_60": len([m for m in matches if m.suitability_score >= 60]),
                    "excellent_85": len([m for m in matches if m.suitability_score >= 85]),
                    "best": top[0].crop.name_en if top else None,
                    "max_profit_usd": max((m.expected_profit_usd for m in top), default=0),
                },
                execution_time_seconds=time.time() - start_time,
            )
        except Exception as e:
            return MotorResult(run_id=run_id, motor_type=self.motor_type,
                               status=MotorStatus.FAILED, error_message=str(e))

    def _safe_mean(self, arr, default):
        if arr is None: return default
        if hasattr(arr, 'values'): return float(np.mean(arr.values))
        return float(arr)

    def _match_all_crops(self, climate, ph, tex, slope, lcc, alt, water):
        matches = []
        for crop in CROP_DATABASE.values():
            score, limits = self._score(crop, climate, ph, tex, slope, lcc, alt, water)
            if score > 25:
                adj_yield = crop.economics.yield_ton_ha * (score / 100)
                revenue = adj_yield * 1000 * crop.economics.market_price_per_kg_usd
                profit = revenue - crop.economics.production_cost_per_ha_usd
                matches.append(CropMatch(
                    crop=crop, suitability_score=score, limiting_factors=limits,
                    expected_yield=adj_yield, expected_profit_usd=profit,
                    water_balance_mm=water - crop.water.opt_mm,
                    confidence=0.6 + (score / 250),
                ))
        return matches

    def _score(self, crop, climate, ph, tex, slope, lcc, alt, water):
        scores, limits = [], []

        # 1. Köppen match (WEIGHT 30%)
        if climate in crop.suitable_climates:
            scores.append(("climate", 100))
        else:
            scores.append(("climate", 10))
            limits.append(f"Not adapted to {climate.name} ({climate.value})")

        # 2. pH (WEIGHT 15%)
        if crop.soil.ph_opt_min <= ph <= crop.soil.ph_opt_max:
            ph_score = 100
        elif crop.soil.ph_min <= ph <= crop.soil.ph_max:
            ph_score = 65
        else:
            ph_score = max(0, 40 - abs(ph - (crop.soil.ph_opt_min + crop.soil.ph_opt_max)/2) * 15)
            if ph_score < 40: limits.append(f"pH {ph:.1f} out of range")
        scores.append(("pH", ph_score))

        # 3. Texture (WEIGHT 10%)
        if tex in crop.soil.preferred_texture:
            scores.append(("texture", 100))
        elif abs(tex - np.mean(crop.soil.preferred_texture)) <= 2:
            scores.append(("texture", 70))
        else:
            scores.append(("texture", 35))
            limits.append("Soil texture mismatch")

        # 4. Slope (WEIGHT 10%)
        if slope <= crop.max_slope_percent:
            scores.append(("slope", 100))
        else:
            s = max(0, 100 - (slope - crop.max_slope_percent) * 5)
            scores.append(("slope", s))
            if s < 30: limits.append(f"Slope {slope:.1f}% exceeds {crop.max_slope_percent}%")

        # 5. LCC (WEIGHT 10%)
        if lcc in crop.suitable_lcc_classes:
            scores.append(("LCC", 100))
        else:
            s = max(0, 60 - (lcc - max(crop.suitable_lcc_classes)) * 12)
            scores.append(("LCC", s))
            if s < 30: limits.append(f"LCC class {lcc} unsuitable")

        # 6. Altitude (WEIGHT 10%)
        alt_min, alt_max = crop.altitude_range_m
        if alt_min <= alt <= alt_max:
            scores.append(("altitude", 100))
        else:
            diff = min(abs(alt - alt_min), abs(alt - alt_max))
            s = max(0, 100 - diff / 10)
            scores.append(("altitude", s))
            if s < 40: limits.append(f"Altitude {alt}m outside range {alt_min}-{alt_max}m")

        # 7. Water (WEIGHT 15%)
        if water >= crop.water.opt_mm:
            scores.append(("water", 100))
        elif water >= crop.water.min_mm:
            s = 60 + 40 * (water - crop.water.min_mm) / (crop.water.opt_mm - crop.water.min_mm)
            scores.append(("water", s))
        else:
            s = max(0, 40 * water / crop.water.min_mm)
            scores.append(("water", s))
            if s < 30: limits.append(f"Water deficit ({water:.0f}mm < {crop.water.min_mm}mm needed)")

        weights = {"climate": 0.30, "pH": 0.15, "texture": 0.10, "slope": 0.10,
                   "LCC": 0.10, "altitude": 0.10, "water": 0.15}
        final = sum(s * weights[n] for n, s in scores)
        return final, limits

    def _suggest_varieties(self, top_matches: list[CropMatch], climate: KoppenClimate, soil_ph: float) -> list[VarietyRecommendation]:
        """Suggest specific varieties based on top crop matches."""
        varieties = []
        for match in top_matches[:5]:  # Focus on top 5 crops
            crop = match.crop
            # This is a simplified logic. Real data would come from a variety database linked to CropProfile.
            # Example for wheat under BSk climate
            if crop.name_en.lower() == "wheat" and climate == KoppenClimate.BSk:
                varieties.extend([
                    VarietyRecommendation(
                        variety_name="Chenopod 180-day",
                        parent_crop="Wheat",
                        traits=["Heat tolerant", "Drought resistant"],
                        recommended_region="Central Asia, Iran Central Plateau",
                        performance_metrics={"yield": 4.2, "disease_resistance": 0.75}
                    ),
                    VarietyRecommendation(
                        variety_name="Semi-dwarf Kavir",
                        parent_crop="Wheat",
                        traits=["Short stature", "Salinity tolerant"],
                        recommended_region="Iran Central Plateau, Salt Flats",
                        performance_metrics={"yield": 3.8, "disease_resistance": 0.80}
                    )
                ])
            # Add more logic for other crops and climates
        return varieties

    def _build_rotation(self, matches: list[CropMatch], soil_ph: float, water_mm: float) -> list[RotationPlan]:
        """Build a crop rotation plan considering soil health and biofertilizers."""
        if not matches: return []
        rotation = []
        families_used = set()
        crops_used = set()

        # Y1: Best overall crop
        best_crop = matches[0].crop
        rotation.append(RotationPlan(
            year=1, crop_name=best_crop.name_en, crop_family=best_crop.family.value,
            reason="Highest suitability score", biofertilizer_suggestion="Rhizobium (if legume) or Azotobacter"
        ))
        families_used.add(best_crop.family)
        crops_used.add(best_crop.id)

        # Y2: Complementary crop (e.g., legume for N, or break pest cycle)
        found_legume = False
        for m in matches:
            if m.crop.family == CropFamily.LEGUME and m.crop.id not in crops_used and m.suitability_score > 50:
                rotation.append(RotationPlan(
                    year=2, crop_name=m.crop.name_en, crop_family=m.crop.family.value,
                    reason="Nitrogen fixation and soil improvement", biofertilizer_suggestion="Rhizobium inoculant"
                ))
                families_used.add(m.crop.family)
                crops_used.add(m.crop.id)
                found_legume = True
                break
        if not found_legume:
             # If no legume suitable, pick a different family
             for m in matches:
                 if m.crop.family not in families_used and m.crop.id not in crops_used and m.suitability_score > 50:
                     rotation.append(RotationPlan(
                         year=2, crop_name=m.crop.name_en, crop_family=m.crop.family.value,
                         reason="Diversify crop family", biofertilizer_suggestion="Phosphate Solubilizer"
                     ))
                     families_used.add(m.crop.family)
                     crops_used.add(m.crop.id)
                     break

        # Y3: Another different crop
        for m in matches:
            if m.crop.family not in families_used and m.crop.id not in crops_used and m.suitability_score > 50:
                rotation.append(RotationPlan(
                    year=3, crop_name=m.crop.name_en, crop_family=m.crop.family.value,
                    reason="Further diversification", biofertilizer_suggestion="Mycorrhiza (if low P/K or low OM)"
                ))
                families_used.add(m.crop.family)
                crops_used.add(m.crop.id)
                break

        # Y4: Soil recovery (cover crop or green manure)
        rotation.append(RotationPlan(
            year=4, crop_name="Cover Crop Mix (Legumes + Grasses)", crop_family="Soil Health",
            reason="Soil regeneration, organic matter, erosion control", biofertilizer_suggestion="General Purpose PGPR"
        ))

        return rotation

    def _economic(self, matches):
        out = []
        for m in matches[:5]:
            c = m.crop
            revenue = m.expected_yield * 1000 * c.economics.market_price_per_kg_usd
            roi = (m.expected_profit_usd / c.economics.production_cost_per_ha_usd * 100
                   if c.economics.production_cost_per_ha_usd > 0 else 0)
            out.append({
                "crop": c.name_en, "yield_t_ha": round(m.expected_yield, 2),
                "revenue_usd": int(revenue), "cost_usd": int(c.economics.production_cost_per_ha_usd),
                "profit_usd": int(m.expected_profit_usd), "roi_percent": round(roi, 1),
                "labor_days": c.economics.labor_days_per_ha,
            })
        return out

    def _water(self, matches, total):
        return {
            "available_mm": total,
            "crops": [{
                "crop": m.crop.name_en,
                "required_mm": m.crop.water.opt_mm,
                "balance_mm": round(m.water_balance_mm, 1),
                "drought_tolerance": m.crop.water.drought_tolerance.value,
                "status": "sufficient" if m.water_balance_mm >= 0 else "deficit",
            } for m in matches[:5]],
        }

    def _to_dict(self, m):
        c = m.crop
        return {
            "id": c.id, "name_fa": c.name_fa, "name_en": c.name_en,
            "scientific": c.scientific_name, "family": c.family.value,
            "score": round(m.suitability_score, 1),
            "limiting_factors": m.limiting_factors,
            "planting_months": c.planting_months,
            "growing_days": c.growing_days,
            "yield_t_ha": round(m.expected_yield, 2),
            "profit_usd_ha": int(m.expected_profit_usd),
            "profitability": "positive" if m.expected_profit_usd > 0 else "negative",
            "profitability": "positive" if m.expected_profit_usd > 0 else "negative",
            "water_mm": c.water.opt_mm,
            "water_balance_mm": round(m.water_balance_mm, 1),
            "producers": c.major_producers[:6],
            "uses": c.uses,
            "confidence": round(m.confidence, 2),
            "notes": c.notes,
        }

    def _climate_examples(self, climate):
        examples = {
            KoppenClimate.Af: ["Amazon Basin", "Congo", "Indonesia", "Malaysia"],
            KoppenClimate.Am: ["Mumbai", "Yangon", "Lagos coast", "Manaus"],
            KoppenClimate.Aw: ["Cerrado Brazil", "Serengeti", "Darwin Australia", "Bangkok"],
            KoppenClimate.BWh: ["Sahara", "Arabian Peninsula", "Atacama", "Australian Outback"],
            KoppenClimate.BWk: ["Gobi", "Taklamakan", "Patagonia", "Great Basin USA"],
            KoppenClimate.BSh: ["Sahel", "Australian Rangelands", "NE Brazil", "N Kenya"],
            KoppenClimate.BSk: ["Central Anatolia", "Tehran", "Patagonia steppe", "Great Plains USA"],
            KoppenClimate.Csa: ["Mediterranean coast", "California", "Central Chile", "Cape Town"],
            KoppenClimate.Csb: ["Oregon", "N Portugal", "Cascades"],
            KoppenClimate.Cfa: ["SE USA", "E China", "Uruguay", "E Australia", "N Argentina"],
            KoppenClimate.Cfb: ["W Europe", "New Zealand", "Pacific NW USA", "S Chile"],
            KoppenClimate.Cwa: ["E India", "SE China", "Hong Kong", "S Brazil"],
            KoppenClimate.Cwb: ["Mexico City", "Addis Ababa", "Nairobi", "Bogota"],
            KoppenClimate.Dfa: ["Chicago", "Bucharest", "Sapporo"],
            KoppenClimate.Dfb: ["Moscow", "Minnesota", "Scandinavia", "S Canada"],
            KoppenClimate.Dfc: ["Siberia", "Alaska interior", "N Canada"],
            KoppenClimate.Dwa: ["Beijing", "Seoul", "Pyongyang"],
            KoppenClimate.Dwb: ["Harbin", "Vladivostok"],
            KoppenClimate.ET: ["N Alaska", "N Siberia", "Iceland highlands"],
            KoppenClimate.EF: ["Antarctica", "Greenland interior", "Himalayan peaks"],
        }
        return examples.get(climate, ["Various regions"])