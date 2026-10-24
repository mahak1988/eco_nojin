"""Business logic for Nojin biofertilizer router.

S-STRUCT compliant: NojinService receives a NojinRepository (which wraps
Session), never a Session directly. All business logic lives here; the
router only parses the request and shapes the response.

Created by S-STRUCT remediation on 2026-10-07.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.orm import Session

from services.nojin.repository import NojinRepository


class NojinService:
    """Pure business logic for Nojin biofertilizer — no Session dependency."""

    def __init__(self, repo: NojinRepository):
        self.repo = repo

    # ---- Health / Statistics ----
    def health_check(self) -> dict[str, Any]:
        db_ok = True
        materials_count = 0
        recipes_count = 0
        try:
            materials_count, recipes_count = self.repo.get_health_counts()
        except Exception:
            db_ok = False
        # A reachable database that holds no catalogue is not a healthy
        # service: the data endpoints refuse rather than fabricate, so the
        # health check must not say "healthy" while the capability is absent.
        has_catalogue = materials_count > 0 or recipes_count > 0
        if not db_ok:
            status = "degraded"
        elif not has_catalogue:
            status = "no_data"
        else:
            status = "healthy"
        return {
            "status": status,
            "version": "1.0.0",
            "database_connected": db_ok,
            "catalogue_available": has_catalogue,
            "materials_count": materials_count,
            "recipes_count": recipes_count,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_statistics(self) -> dict[str, Any]:
        db_ok = True
        default_stats = {
            "materials_count": 0,
            "soil_types_count": 0,
            "recipes_count": 0,
            "arid_priority_materials": 0,
            "high_water_saving_recipes": 0,
            "avg_roi_percent": 0.0,
            "avg_water_saving_percent": 0.0,
        }
        try:
            stats = self.repo.get_full_statistics()
        except Exception:
            db_ok = False
            stats = default_stats
        stats["system_status"] = "operational" if db_ok else "degraded"
        return stats

    # ---- Materials ----
    def list_materials(
        self,
        category: str | None = None,
        arid_only: bool = False,
        min_priority: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        materials = self.repo.list_materials(category, arid_only, min_priority, limit)
        if not materials:
            raise RuntimeError("Nojin materials data not available (database empty or not seeded)")
        return [self._serialize_material(m) for m in materials]

    def get_material(self, material_code: str) -> dict[str, Any] | None:
        material = self.repo.get_material_by_code(material_code)
        if not material:
            raise RuntimeError("Nojin materials data not available (database empty or not seeded)")
        return self._serialize_material(material)

    def get_arid_priority_materials(self, min_score: int = 9, limit: int = 50) -> list[dict[str, Any]]:
        materials = self.repo.get_arid_priority_materials(min_score, limit)
        if not materials:
            raise RuntimeError("Nojin materials data not available (database empty or not seeded)")
        return [self._serialize_material(m) for m in materials]

    def _serialize_material(self, m) -> dict[str, Any]:
        return {
            "material_code": m.material_code,
            "common_name": m.common_name,
            "scientific_name": m.scientific_name,
            "category": m.category,
            "nitrogen_pct": m.nitrogen_pct,
            "phosphorus_pct": m.phosphorus_pct,
            "potassium_pct": m.potassium_pct,
            "calcium_pct": m.calcium_pct,
            "organic_matter_pct": m.organic_matter_pct,
            "cn_ratio": m.cn_ratio,
            "ph": m.ph,
            "cec_cmol_kg": m.cec_cmol_kg,
            "water_retention_pct": m.water_retention_pct,
            "release_rate": m.release_rate,
            "persistence_years": m.persistence_years,
            "cost_per_ton_usd": m.cost_per_ton_usd,
            "availability": m.availability,
            "is_suitable_for_arid": m.is_suitable_for_arid,
            "arid_priority_score": m.arid_priority_score,
            "benefits": m.benefits,
            "overuse_risks": m.overuse_risks,
        }

    # ---- Soil Types ----
    def list_soil_types(self) -> list[dict[str, Any]]:
        soils = self.repo.list_soil_types()
        if not soils:
            raise RuntimeError("Nojin soil types data not available (database empty or not seeded)")
        return [self._serialize_soil(s) for s in soils]

    def get_soil_type(self, soil_code: str) -> dict[str, Any] | None:
        soil = self.repo.get_soil_type_by_code(soil_code)
        if not soil:
            raise RuntimeError("Nojin soil types data not available (database empty or not seeded)")
        return self._serialize_soil(soil)

    def classify_soil(
        self,
        ph: float,
        ec_dsm: float,
        om_pct: float,
        texture: str | None = None,
        region: str | None = None,
    ) -> dict[str, Any]:
        """Classify soil based on properties."""
        result = self.repo.classify_soil(ph, ec_dsm, om_pct, texture, region)
        soils = result["soils"]

        best_match = None
        best_score = -1

        for soil in soils:
            score = 0
            if soil.typical_ph_min and soil.typical_ph_max:
                if soil.typical_ph_min <= ph <= soil.typical_ph_max:
                    score += 30
                else:
                    score -= abs(ph - (soil.typical_ph_min + soil.typical_ph_max) / 2) * 10
            if soil.typical_om_pct:
                score -= abs(om_pct - soil.typical_om_pct) * 5
            if texture and soil.texture and texture.lower() in soil.texture.lower():
                score += 20
            if region and soil.common_regions and region in soil.common_regions:
                score += 20

            if score > best_score:
                best_score = score
                best_match = soil

        confidence = max(0, min(1, best_score / 100)) if best_match else 0

        if not best_match:
            return {
                "classified_as": "unknown",
                "soil_code": "UNKNOWN",
                "soil_name": "Unknown",
                "confidence": 0,
                "recommended_recipe": None,
                "warnings": ["Could not classify soil; manual review recommended"],
                "next_steps": ["Submit soil sample for lab analysis"],
            }

        # Find recommended recipe
        recipes = self.repo.list_recipes(soil_code=best_match.soil_code)
        recommended = recipes[0].recipe_code if recipes else None

        return {
            "classified_as": best_match.soil_category or "classified",
            "soil_code": best_match.soil_code,
            "soil_name": best_match.soil_name,
            "confidence": round(confidence, 2),
            "recommended_recipe": recommended,
            "warnings": [] if confidence > 0.7 else ["Low confidence; verify with lab analysis"],
            "next_steps": [
                "Review recommended recipe for soil compatibility",
                "Test soil nutrients before application",
            ],
        }

    def _serialize_soil(self, s) -> dict[str, Any]:
        return {
            "soil_code": s.soil_code,
            "soil_name": s.soil_name,
            "soil_category": s.soil_category,
            "texture": s.texture,
            "typical_ph_min": s.typical_ph_min,
            "typical_ph_max": s.typical_ph_max,
            "typical_om_pct": s.typical_om_pct,
            "typical_cec_cmol_kg": s.typical_cec_cmol_kg,
            "water_holding_capacity": s.water_holding_capacity,
            "drainage": s.drainage,
            "common_problems": s.common_problems,
            "nutrient_deficiencies": s.nutrient_deficiencies,
            "common_regions": s.common_regions,
        }

    # ---- Recipes ----
    def list_recipes(
        self,
        soil_code: str | None = None,
        area_min_ha: float | None = None,
        area_max_ha: float | None = None,
        min_water_saving: float | None = None,
        min_yield_increase: float | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        recipes = self.repo.list_recipes(
            soil_code, area_min_ha, area_max_ha, min_water_saving, min_yield_increase, limit
        )
        if not recipes:
            raise RuntimeError("Nojin recipes data not available (database empty or not seeded)")
        return [self._serialize_recipe(r) for r in recipes]

    def get_recipe(self, recipe_code: str) -> dict[str, Any] | None:
        recipe = self.repo.get_recipe_by_code(recipe_code)
        if not recipe:
            raise RuntimeError("Nojin recipes data not available (database empty or not seeded)")
        return self._serialize_recipe(recipe)

    def scale_recipe(self, recipe_code: str, area_ha: float) -> dict[str, Any] | None:
        result = self.repo.scale_recipe(recipe_code, area_ha)
        if not result:
            return None

        recipe = result["recipe"]
        return {
            "recipe_code": recipe.recipe_code,
            "recipe_name": recipe.recipe_name,
            "area_ha": area_ha,
            "material_quantities": result["composition"],
            "total_tons": result["total_tons"],
            "total_cost_usd": round(
                (recipe.estimated_cost_usd_per_ha or 0) * area_ha, 2
            ),
            "economies_of_scale_pct": 0 if area_ha < 10 else min(15, int(area_ha / 10)),
            "implementation_days": max(1, int(area_ha / 50)),
            "equipment_needed": ["Spreader", "Tractor", "Water tank"] if area_ha > 50 else ["Manual spreader"],
            "logistics_notes": [
                "Deliver in dry weather",
                "Store in covered area",
            ],
        }

    def _serialize_recipe(self, r) -> dict[str, Any]:
        soil = self.repo.get_soil_type_by_id(r.soil_type_id)
        return {
            "recipe_code": r.recipe_code,
            "recipe_name": r.recipe_name,
            "soil_code": soil.soil_code if soil else None,
            "soil_name": soil.soil_name if soil else None,
            "area_min_ha": r.area_min_ha,
            "area_max_ha": r.area_max_ha,
            "material_composition": r.material_composition,
            "total_kg_per_ha": r.total_kg_per_ha,
            "total_tons_per_ha": r.total_tons_per_ha,
            "estimated_cost_usd_per_ha": r.estimated_cost_usd_per_ha,
            "cn_ratio_final": r.cn_ratio_final,
            "om_increase_pct": r.om_increase_pct,
            "water_saving_pct": r.water_saving_pct,
            "yield_increase_pct": r.yield_increase_pct,
            "restoration_years": r.restoration_years,
            "traditional_technique": r.traditional_technique,
        }

    # ---- Analysis / Recommendations ----
    def recommend(
        self,
        soil_code: str,
        area_ha: float,
        budget_per_ha_usd: float | None = None,
        crop_type: str = "wheat",
    ) -> dict[str, Any] | None:
        result = self.repo.get_recommendation(soil_code, area_ha, budget_per_ha_usd, crop_type)
        if not result:
            raise RuntimeError("Nojin recommendation data not available (database empty or not seeded)")

        recipe = result["recipe"]
        return {
            "recipe_code": recipe.recipe_code,
            "recipe_name": recipe.recipe_name,
            "area_ha": area_ha,
            "material_quantities": result["material_quantities"],
            "total_tons": result["total_tons"],
            "estimated_cost_usd": round(result["total_cost"], 2),
            "expected_results": {
                "yield_increase_pct": recipe.yield_increase_pct,
                "water_saving_pct": recipe.water_saving_pct,
                "om_increase_pct": recipe.om_increase_pct,
            },
            "traditional_technique": recipe.traditional_technique,
            "implementation_tips": [
                "Apply in split doses for best results",
                "Monitor soil moisture weekly",
            ],
        }

    def optimize(
        self,
        soil_code: str,
        area_ha: float,
        target_om_increase_pct: float = 3.0,
        target_cn_ratio: float = 25.0,
        budget_per_ha_usd: float | None = None,
        required_materials: list[str] | None = None,
        excluded_materials: list[str] | None = None,
    ) -> dict[str, Any] | None:
        result = self.repo.optimize_formulation(
            soil_code, area_ha, target_om_increase_pct, target_cn_ratio,
            budget_per_ha_usd, required_materials, excluded_materials
        )
        if not result:
            return None

        recipe = result["recipe"]
        return {
            "recipe_code": recipe.recipe_code,
            "recipe_name": recipe.recipe_name,
            "area_ha": area_ha,
            "material_quantities": result["material_quantities"],
            "total_tons": result["total_tons"],
            "estimated_cost_usd": round(result["total_cost"], 2),
            "expected_results": result["expected_results"],
            "traditional_technique": recipe.traditional_technique,
            "implementation_tips": [
                "Apply in split doses for best results",
                "Monitor soil moisture weekly",
            ],
        }

    def cost_benefit(
        self,
        formulation: dict[str, float],
        area_ha: float,
        crop_type: str = "wheat",
        current_yield_t_ha: float = 2.0,
        current_irrigation_m3_ha: float = 8000.0,
        current_fertilizer_cost_usd_ha: float = 300.0,
    ) -> dict[str, Any]:
        """Cost-benefit analysis. Delegates material lookups to repository."""
        total_cost = 0
        for mat_code, kg_per_ha in formulation.items():
            material = self.repo.get_material_by_code(mat_code)
            if material and material.cost_per_ton_usd:
                total_cost += (kg_per_ha * area_ha / 1000) * material.cost_per_ton_usd

        water_saved = sum(
            self.repo.get_material_by_code(m).water_retention_pct or 0
            for m in formulation.keys()
        )
        water_saved_m3_ha = min(water_saved * 10, 3000)

        yield_increase = sum(
            (self.repo.get_material_by_code(m).nitrogen_pct or 0) / 100
            for m in formulation.keys()
        )
        yield_increase_t_ha = min(yield_increase * 10, 2.0)

        annual_benefit = (yield_increase_t_ha * 200 + water_saved_m3_ha * 0.05) * area_ha
        annual_cost = total_cost / 3
        net_annual_benefit = annual_benefit - annual_cost
        roi = (net_annual_benefit / total_cost * 100) if total_cost else 0

        return {
            "total_investment_usd": round(total_cost, 2),
            "annual_benefit_usd": round(annual_benefit, 2),
            "annual_cost_usd": round(annual_cost, 2),
            "net_annual_benefit_usd": round(net_annual_benefit, 2),
            "roi_annual_percent": round(roi, 2),
            "payback_simple_months": max(1, int(12 * total_cost / max(annual_benefit, 1))),
            "npv_10year_usd": round(net_annual_benefit * 7.72, 2),
            "irr_percent": round(min(roi * 0.8, 50), 2),
            "benefit_cost_ratio": round(annual_benefit / max(annual_cost, 1), 2),
            "carbon_credit_potential_usd": round(area_ha * 50, 2),
            "water_savings_value_usd": round(water_saved_m3_ha * 0.05 * area_ha, 2),
            "is_economically_viable": net_annual_benefit > 0,
            "viability_score": max(0, min(1, roi / 20)),
            "farmer_category": "commercial" if area_ha > 100 else "smallholder",
            "recommendations": [
                "Monitor soil OM annually",
                "Adjust application rates based on soil tests",
            ],
        }

    def water_savings(
        self,
        formulation: dict[str, float],
        area_ha: float,
        baseline_irrigation_m3_ha: float = 8000.0,
    ) -> dict[str, Any]:
        """Water savings calculation. Delegates material lookups to repository."""
        total_retention = sum(
            self.repo.get_material_by_code(m).water_retention_pct or 0 for m in formulation.keys()
        )
        avg_retention = total_retention / max(len(formulation), 1)

        new_irrigation = baseline_irrigation_m3_ha * (1 - avg_retention / 100)
        new_irrigation = max(new_irrigation, baseline_irrigation_m3_ha * 0.3)
        water_saved = baseline_irrigation_m3_ha - new_irrigation

        return {
            "baseline_irrigation_m3_ha": baseline_irrigation_m3_ha,
            "new_irrigation_m3_ha": round(new_irrigation, 2),
            "water_saved_m3_ha": round(water_saved, 2),
            "water_saved_percent": round(water_saved / baseline_irrigation_m3_ha * 100, 2),
            "annual_water_saved_m3": round(water_saved * area_ha, 2),
            "annual_savings_usd": round(water_saved * area_ha * 0.05, 2),
            "drought_resistance_days": int(water_saved * 2),
            "recommendations": [
                "Use mulching to further reduce evaporation",
                "Consider drip irrigation for maximum efficiency",
            ],
        }

    def full_analysis(
        self,
        soil_code: str,
        area_ha: float,
        crop_type: str = "wheat",
        current_yield_t_ha: float = 2.0,
        current_irrigation_m3_ha: float = 8000.0,
        current_fertilizer_cost_usd_ha: float = 300.0,
        budget_per_ha_usd: float | None = None,
    ) -> dict[str, Any] | None:
        # Get recommendation
        rec = self.recommend(soil_code, area_ha, budget_per_ha_usd, crop_type)
        if not rec:
            return None

        # Get cost benefit
        cb = self.cost_benefit(
            rec["material_quantities"], area_ha, crop_type,
            current_yield_t_ha, current_irrigation_m3_ha, current_fertilizer_cost_usd_ha
        )

        # Get water savings
        ws = self.water_savings(rec["material_quantities"], area_ha, 8000.0)

        # Get scale
        scale = self.scale_recipe(rec["recipe_code"], area_ha)

        return {
            "recommendation": rec,
            "cost_benefit": cb,
            "water_savings": ws,
            "scale": scale,
            "overall_assessment": {
                "viable": cb["is_economically_viable"],
                "roi_percent": cb["roi_annual_percent"],
                "water_saved_percent": ws["water_saved_percent"],
                "payback_months": cb["payback_simple_months"],
            },
        }


def get_db():
    """Database session dependency — the router never sees a session directly.

    Mirrors ``services/api_gateway/routers/nojin.py:get_db``: ``SessionLocal`` is
    imported lazily so the ORM engine is not constructed merely by importing this
    module (avoids an import-time cycle through ``database``).
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_nojin_service(db: Annotated[Session, Depends(get_db)]) -> NojinService:
    """Dependency factory — the router never sees a session directly."""
    repo = NojinRepository(db)
    return NojinService(repo)