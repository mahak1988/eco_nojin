"""
Nojin Biofertilizer - Repository Layer (CRUD)
=============================================
Provides data access for all Nojin entities.

Pattern: Repository Pattern with SQLAlchemy sessions.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import SessionLocal

from .models import (
    NojinApplicationPlan,
    NojinCalibrationRecord,
    NojinFieldTrial,
    NojinFormulation,
    NojinFormulationRecipe,
    NojinMaterial,
    NojinSoilType,
    NojinStrain,
)

logger = logging.getLogger(__name__)


class NojinStrainRepository:
    """CRUD operations for NojinStrain."""

    def __init__(self, session: Session | None = None):
        self.session = session or SessionLocal()
        self._owns_session = session is None

    def close(self):
        if self._owns_session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create(self, **kwargs) -> NojinStrain:
        """Create a new strain."""
        strain = NojinStrain(**kwargs)
        self.session.add(strain)
        self.session.commit()
        self.session.refresh(strain)
        logger.info(f"Created strain: {strain.strain_code}")
        return strain

    def get_by_id(self, strain_id: int) -> NojinStrain | None:
        """Get strain by ID."""
        return self.session.query(NojinStrain).filter(NojinStrain.id == strain_id).first()

    def get_by_code(self, strain_code: str) -> NojinStrain | None:
        """Get strain by code."""
        return self.session.query(NojinStrain).filter(
            NojinStrain.strain_code == strain_code
        ).first()

    def get_by_type(self, strain_type: str) -> list[NojinStrain]:
        """Get strains by type."""
        return self.session.query(NojinStrain).filter(
            NojinStrain.strain_type == strain_type
        ).all()

    def get_all(self, limit: int = 100) -> list[NojinStrain]:
        """Get all strains."""
        return self.session.query(NojinStrain).limit(limit).all()

    def search(self, query: str) -> list[NojinStrain]:
        """Search strains by species name or function."""
        search_pattern = f"%{query}%"
        return self.session.query(NojinStrain).filter(
            (NojinStrain.species_name.ilike(search_pattern)) |
            (NojinStrain.function.ilike(search_pattern))
        ).all()

    def update(self, strain_id: int, **kwargs) -> NojinStrain | None:
        """Update a strain."""
        strain = self.get_by_id(strain_id)
        if not strain:
            return None

        for key, value in kwargs.items():
            if hasattr(strain, key):
                setattr(strain, key, value)

        strain.updated_at = datetime.now()
        self.session.commit()
        self.session.refresh(strain)
        logger.info(f"Updated strain: {strain.strain_code}")
        return strain

    def delete(self, strain_id: int) -> bool:
        """Delete a strain."""
        strain = self.get_by_id(strain_id)
        if not strain:
            return False

        self.session.delete(strain)
        self.session.commit()
        logger.info(f"Deleted strain: {strain_id}")
        return True

    def count(self) -> int:
        """Count all strains."""
        return self.session.query(NojinStrain).count()


class NojinFormulationRepository:
    """CRUD operations for NojinFormulation."""

    def __init__(self, session: Session | None = None):
        self.session = session or SessionLocal()
        self._owns_session = session is None

    def close(self):
        if self._owns_session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create(self, **kwargs) -> NojinFormulation:
        """Create a new formulation."""
        formulation = NojinFormulation(**kwargs)
        self.session.add(formulation)
        self.session.commit()
        self.session.refresh(formulation)
        logger.info(f"Created formulation: {formulation.formulation_code}")
        return formulation

    def get_by_id(self, formulation_id: int) -> NojinFormulation | None:
        """Get formulation by ID."""
        return self.session.query(NojinFormulation).filter(
            NojinFormulation.id == formulation_id
        ).first()

    def get_by_code(self, formulation_code: str) -> NojinFormulation | None:
        """Get formulation by code."""
        return self.session.query(NojinFormulation).filter(
            NojinFormulation.formulation_code == formulation_code
        ).first()

    def get_by_type(self, formulation_type: str) -> list[NojinFormulation]:
        """Get formulations by type."""
        return self.session.query(NojinFormulation).filter(
            NojinFormulation.formulation_type == formulation_type
        ).all()

    def get_for_crop(self, crop_type: str) -> list[NojinFormulation]:
        """Get formulations suitable for a crop."""
        search_pattern = f"%{crop_type}%"
        return self.session.query(NojinFormulation).filter(
            NojinFormulation.target_crops.ilike(search_pattern)
        ).all()

    def get_all(self, limit: int = 100) -> list[NojinFormulation]:
        """Get all formulations."""
        return self.session.query(NojinFormulation).limit(limit).all()

    def update(self, formulation_id: int, **kwargs) -> NojinFormulation | None:
        """Update a formulation."""
        formulation = self.get_by_id(formulation_id)
        if not formulation:
            return None

        for key, value in kwargs.items():
            if hasattr(formulation, key):
                setattr(formulation, key, value)

        formulation.updated_at = datetime.now()
        self.session.commit()
        self.session.refresh(formulation)
        logger.info(f"Updated formulation: {formulation.formulation_code}")
        return formulation

    def delete(self, formulation_id: int) -> bool:
        """Delete a formulation."""
        formulation = self.get_by_id(formulation_id)
        if not formulation:
            return False

        self.session.delete(formulation)
        self.session.commit()
        logger.info(f"Deleted formulation: {formulation_id}")
        return True

    def count(self) -> int:
        """Count all formulations."""
        return self.session.query(NojinFormulation).count()


class NojinApplicationPlanRepository:
    """CRUD operations for NojinApplicationPlan."""

    def __init__(self, session: Session | None = None):
        self.session = session or SessionLocal()
        self._owns_session = session is None

    def close(self):
        if self._owns_session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create(self, **kwargs) -> NojinApplicationPlan:
        """Create a new application plan."""
        plan = NojinApplicationPlan(**kwargs)
        self.session.add(plan)
        self.session.commit()
        self.session.refresh(plan)
        logger.info(f"Created application plan: {plan.id}")
        return plan

    def get_by_id(self, plan_id: int) -> NojinApplicationPlan | None:
        """Get plan by ID."""
        return self.session.query(NojinApplicationPlan).filter(
            NojinApplicationPlan.id == plan_id
        ).first()

    def get_by_formulation(self, formulation_id: int) -> list[NojinApplicationPlan]:
        """Get plans by formulation."""
        return self.session.query(NojinApplicationPlan).filter(
            NojinApplicationPlan.formulation_id == formulation_id
        ).all()

    def get_by_land_profile(self, land_profile_id: int) -> list[NojinApplicationPlan]:
        """Get plans by land profile."""
        return self.session.query(NojinApplicationPlan).filter(
            NojinApplicationPlan.land_profile_id == land_profile_id
        ).all()

    def get_upcoming(self, days_ahead: int = 30) -> list[NojinApplicationPlan]:
        """Get upcoming application plans."""
        today = date.today()
        end_date = today + timedelta(days=days_ahead)
        return self.session.query(NojinApplicationPlan).filter(
            NojinApplicationPlan.application_date >= today,
            NojinApplicationPlan.application_date <= end_date,
        ).all()

    def get_all(self, limit: int = 100) -> list[NojinApplicationPlan]:
        """Get all plans."""
        return self.session.query(NojinApplicationPlan).limit(limit).all()

    def update(self, plan_id: int, **kwargs) -> NojinApplicationPlan | None:
        """Update a plan."""
        plan = self.get_by_id(plan_id)
        if not plan:
            return None

        for key, value in kwargs.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        self.session.commit()
        self.session.refresh(plan)
        logger.info(f"Updated application plan: {plan.id}")
        return plan

    def delete(self, plan_id: int) -> bool:
        """Delete a plan."""
        plan = self.get_by_id(plan_id)
        if not plan:
            return False

        self.session.delete(plan)
        self.session.commit()
        logger.info(f"Deleted application plan: {plan_id}")
        return True


class NojinFieldTrialRepository:
    """CRUD operations for NojinFieldTrial."""

    def __init__(self, session: Session | None = None):
        self.session = session or SessionLocal()
        self._owns_session = session is None

    def close(self):
        if self._owns_session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create(self, **kwargs) -> NojinFieldTrial:
        """Create a new field trial."""
        trial = NojinFieldTrial(**kwargs)
        self.session.add(trial)
        self.session.commit()
        self.session.refresh(trial)
        logger.info(f"Created field trial: {trial.id}")
        return trial

    def get_by_id(self, trial_id: int) -> NojinFieldTrial | None:
        """Get trial by ID."""
        return self.session.query(NojinFieldTrial).filter(
            NojinFieldTrial.id == trial_id
        ).first()

    def get_by_application_plan(self, application_plan_id: int) -> list[NojinFieldTrial]:
        """Get trials by application plan."""
        return self.session.query(NojinFieldTrial).filter(
            NojinFieldTrial.application_plan_id == application_plan_id
        ).all()

    def get_for_formulation(self, formulation_id: int) -> list[NojinFieldTrial]:
        """Get all trials for a formulation."""
        return self.session.query(NojinFieldTrial).join(
            NojinApplicationPlan,
            NojinFieldTrial.application_plan_id == NojinApplicationPlan.id
        ).filter(
            NojinApplicationPlan.formulation_id == formulation_id
        ).all()

    def get_with_positive_yield(self) -> list[NojinFieldTrial]:
        """Get trials with positive yield response (for calibration)."""
        return self.session.query(NojinFieldTrial).filter(
            NojinFieldTrial.yield_response > 0
        ).all()

    def get_all(self, limit: int = 100) -> list[NojinFieldTrial]:
        """Get all trials."""
        return self.session.query(NojinFieldTrial).limit(limit).all()

    def update(self, trial_id: int, **kwargs) -> NojinFieldTrial | None:
        """Update a trial."""
        trial = self.get_by_id(trial_id)
        if not trial:
            return None

        for key, value in kwargs.items():
            if hasattr(trial, key):
                setattr(trial, key, value)

        self.session.commit()
        self.session.refresh(trial)
        logger.info(f"Updated field trial: {trial.id}")
        return trial

    def delete(self, trial_id: int) -> bool:
        """Delete a trial."""
        trial = self.get_by_id(trial_id)
        if not trial:
            return False

        self.session.delete(trial)
        self.session.commit()
        logger.info(f"Deleted field trial: {trial_id}")
        return True


class NojinCalibrationRecordRepository:
    """CRUD operations for NojinCalibrationRecord."""

    def __init__(self, session: Session | None = None):
        self.session = session or SessionLocal()
        self._owns_session = session is None

    def close(self):
        if self._owns_session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create(self, **kwargs) -> NojinCalibrationRecord:
        """Create a new calibration record."""
        record = NojinCalibrationRecord(**kwargs)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        logger.info(f"Created calibration record: {record.id}")
        return record

    def get_by_id(self, record_id: int) -> NojinCalibrationRecord | None:
        """Get record by ID."""
        return self.session.query(NojinCalibrationRecord).filter(
            NojinCalibrationRecord.id == record_id
        ).first()

    def get_latest_for_formulation(self, formulation_id: int) -> NojinCalibrationRecord | None:
        """Get latest calibration for a formulation."""
        return self.session.query(NojinCalibrationRecord).filter(
            NojinCalibrationRecord.formulation_id == formulation_id
        ).order_by(desc(NojinCalibrationRecord.calibration_date)).first()

    def get_all_for_formulation(self, formulation_id: int) -> list[NojinCalibrationRecord]:
        """Get all calibrations for a formulation."""
        return self.session.query(NojinCalibrationRecord).filter(
            NojinCalibrationRecord.formulation_id == formulation_id
        ).order_by(desc(NojinCalibrationRecord.calibration_date)).all()

    def get_all(self, limit: int = 100) -> list[NojinCalibrationRecord]:
        """Get all records."""
        return self.session.query(NojinCalibrationRecord).limit(limit).all()


__all__ = [
    "NojinApplicationPlanRepository",
    "NojinCalibrationRecordRepository",
    "NojinFieldTrialRepository",
    "NojinFormulationRepository",
    "NojinStrainRepository",
]


# ═══════════════════════════════════════════════════════════════════
# PHASE 2: EXTENDED REPOSITORIES
# ═══════════════════════════════════════════════════════════════════

class NojinMaterialRepository:
    """CRUD operations for NojinMaterial (43 scientific materials)."""

    def __init__(self, session: Session | None = None):
        self.session = session or SessionLocal()
        self._owns_session = session is None

    def close(self):
        if self._owns_session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create(self, **kwargs) -> NojinMaterial:
        """Create a new material."""
        material = NojinMaterial(**kwargs)
        self.session.add(material)
        self.session.commit()
        self.session.refresh(material)
        logger.info(f"Created material: {material.material_code}")
        return material

    def get_by_id(self, material_id: int) -> NojinMaterial | None:
        """Get material by ID."""
        return self.session.get(NojinMaterial, material_id)

    def get_by_code(self, material_code: str) -> NojinMaterial | None:
        """Get material by code (e.g., MIN-011, CAR-021)."""
        return self.session.query(NojinMaterial).filter(
            NojinMaterial.material_code == material_code
        ).first()

    def get_by_category(self, category: str) -> list[NojinMaterial]:
        """Get materials by category (mineral, organic_plant, organic_animal, carbon, special)."""
        return self.session.query(NojinMaterial).filter(
            NojinMaterial.category == category
        ).order_by(NojinMaterial.material_code).all()

    def get_for_arid_regions(self, min_score: int = 8) -> list[NojinMaterial]:
        """Get materials suitable for arid regions with priority score."""
        return self.session.query(NojinMaterial).filter(
            NojinMaterial.is_suitable_for_arid == True,
            NojinMaterial.arid_priority_score >= min_score
        ).order_by(NojinMaterial.arid_priority_score.desc()).all()

    def get_locally_available(self, region: str = None) -> list[NojinMaterial]:
        """Get locally available materials, optionally filtered by region."""
        query = self.session.query(NojinMaterial).filter(
            NojinMaterial.is_locally_available == True
        )
        if region:
            query = query.filter(NojinMaterial.source_regions.ilike(f"%{region}%"))
        return query.all()

    def search(self, query: str) -> list[NojinMaterial]:
        """Search materials by name, scientific name, or benefits."""
        search_pattern = f"%{query}%"
        return self.session.query(NojinMaterial).filter(
            (NojinMaterial.common_name.ilike(search_pattern)) |
            (NojinMaterial.scientific_name.ilike(search_pattern)) |
            (NojinMaterial.benefits.ilike(search_pattern)) |
            (NojinMaterial.function.ilike(search_pattern) if hasattr(NojinMaterial, 'function') else False)
        ).all()

    def get_by_release_rate(self, rate: str) -> list[NojinMaterial]:
        """Get materials by release rate (fast, medium, slow, very_slow)."""
        return self.session.query(NojinMaterial).filter(
            NojinMaterial.release_rate == rate
        ).all()

    def get_by_ph_range(self, min_ph: float, max_ph: float) -> list[NojinMaterial]:
        """Get materials within pH range."""
        return self.session.query(NojinMaterial).filter(
            NojinMaterial.ph >= min_ph,
            NojinMaterial.ph <= max_ph
        ).all()

    def get_cheap_materials(self, max_cost_usd: float = 50.0) -> list[NojinMaterial]:
        """Get affordable materials (for subsistence farmers)."""
        return self.session.query(NojinMaterial).filter(
            NojinMaterial.cost_per_ton_usd <= max_cost_usd,
            NojinMaterial.cost_per_ton_usd > 0
        ).order_by(NojinMaterial.cost_per_ton_usd).all()

    def get_all(self, limit: int = 100) -> list[NojinMaterial]:
        """Get all materials."""
        return self.session.query(NojinMaterial).limit(limit).all()

    def update(self, material_id: int, **kwargs) -> NojinMaterial | None:
        """Update a material."""
        material = self.get_by_id(material_id)
        if not material:
            return None
        for key, value in kwargs.items():
            if hasattr(material, key):
                setattr(material, key, value)
        material.updated_at = datetime.now()
        self.session.commit()
        self.session.refresh(material)
        return material

    def delete(self, material_id: int) -> bool:
        """Delete a material."""
        material = self.get_by_id(material_id)
        if not material:
            return False
        self.session.delete(material)
        self.session.commit()
        return True

    def count(self) -> int:
        """Count all materials."""
        return self.session.query(NojinMaterial).count()

    def count_by_category(self) -> dict[str, int]:
        """Count materials grouped by category."""
        result = {}
        for category in ["mineral", "organic_plant", "organic_animal", "carbon", "special"]:
            result[category] = self.session.query(NojinMaterial).filter(
                NojinMaterial.category == category
            ).count()
        return result


class NojinSoilTypeRepository:
    """CRUD operations for NojinSoilType (10 soil classifications)."""

    def __init__(self, session: Session | None = None):
        self.session = session or SessionLocal()
        self._owns_session = session is None

    def close(self):
        if self._owns_session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create(self, **kwargs) -> NojinSoilType:
        """Create a new soil type."""
        soil = NojinSoilType(**kwargs)
        self.session.add(soil)
        self.session.commit()
        self.session.refresh(soil)
        return soil

    def get_by_id(self, soil_id: int) -> NojinSoilType | None:
        """Get soil type by ID."""
        return self.session.get(NojinSoilType, soil_id)

    def get_by_code(self, soil_code: str) -> NojinSoilType | None:
        """Get soil type by code (e.g., SOIL-01, SOIL-02)."""
        return self.session.query(NojinSoilType).filter(
            NojinSoilType.soil_code == soil_code
        ).first()

    def get_by_category(self, category: str) -> list[NojinSoilType]:
        """Get soil types by category."""
        return self.session.query(NojinSoilType).filter(
            NojinSoilType.soil_category == category
        ).all()

    def get_by_ph(self, ph: float) -> list[NojinSoilType]:
        """Get soil types where given pH falls in typical range."""
        return self.session.query(NojinSoilType).filter(
            NojinSoilType.typical_ph_min <= ph,
            NojinSoilType.typical_ph_max >= ph
        ).all()

    def get_by_region(self, region: str) -> list[NojinSoilType]:
        """Get soil types common in a specific region."""
        search_pattern = f"%{region}%"
        return self.session.query(NojinSoilType).filter(
            NojinSoilType.common_regions.ilike(search_pattern)
        ).all()

    def classify_soil(
        self,
        ph: float,
        ec_dsm: float,
        om_pct: float,
        texture: str = None,
    ) -> NojinSoilType | None:
        """
        Classify soil based on test results.
        Simple heuristic classifier.
        """
        # Sodic: pH > 8.5
        if ph > 8.5:
            return self.get_by_code("SOIL-03")
        # Saline: EC > 4 dS/m
        elif ec_dsm > 4.0:
            return self.get_by_code("SOIL-02")
        # Acidic: pH < 5.5
        elif ph < 5.5:
            return self.get_by_code("SOIL-05")
        # Sandy: low OM, texture=sand
        elif om_pct < 1.0 and (texture == "sand" or texture == "sandy"):
            return self.get_by_code("SOIL-01")
        # Clay: high OM, clay texture
        elif om_pct > 2.0 and (texture == "clay" or texture == "clayey"):
            return self.get_by_code("SOIL-06")
        # Default to loam
        return None

    def get_all(self) -> list[NojinSoilType]:
        """Get all soil types."""
        return self.session.query(NojinSoilType).order_by(NojinSoilType.soil_code).all()

    def count(self) -> int:
        """Count all soil types."""
        return self.session.query(NojinSoilType).count()


class NojinFormulationRecipeRepository:
    """CRUD operations for NojinFormulationRecipe (10 soil-specific recipes)."""

    def __init__(self, session: Session | None = None):
        self.session = session or SessionLocal()
        self._owns_session = session is None

    def close(self):
        if self._owns_session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create(self, **kwargs) -> NojinFormulationRecipe:
        """Create a new formulation recipe."""
        recipe = NojinFormulationRecipe(**kwargs)
        self.session.add(recipe)
        self.session.commit()
        self.session.refresh(recipe)
        return recipe

    def get_by_id(self, recipe_id: int) -> NojinFormulationRecipe | None:
        """Get recipe by ID."""
        return self.session.get(NojinFormulationRecipe, recipe_id)

    def get_by_code(self, recipe_code: str) -> NojinFormulationRecipe | None:
        """Get recipe by code (e.g., NOJIN-ARID-1)."""
        return self.session.query(NojinFormulationRecipe).filter(
            NojinFormulationRecipe.recipe_code == recipe_code
        ).first()

    def get_for_soil(self, soil_type_id: int) -> list[NojinFormulationRecipe]:
        """Get all recipes for a specific soil type."""
        return self.session.query(NojinFormulationRecipe).filter(
            NojinFormulationRecipe.soil_type_id == soil_type_id
        ).all()

    def get_for_soil_code(self, soil_code: str) -> NojinFormulationRecipe | None:
        """Get recipe for a soil type code."""
        soil = self.session.query(NojinSoilType).filter(
            NojinSoilType.soil_code == soil_code
        ).first()
        if not soil:
            return None
        recipes = self.get_for_soil(soil.id)
        return recipes[0] if recipes else None

    def get_by_traditional_technique(self, technique: str) -> list[NojinFormulationRecipe]:
        """Get recipes integrated with a traditional technique."""
        return self.session.query(NojinFormulationRecipe).filter(
            NojinFormulationRecipe.traditional_technique.ilike(f"%{technique}%")
        ).all()

    def get_affordable(self, max_cost_usd: float = 200.0) -> list[NojinFormulationRecipe]:
        """Get affordable formulations for subsistence farmers."""
        return self.session.query(NojinFormulationRecipe).filter(
            NojinFormulationRecipe.estimated_cost_usd_per_ha <= max_cost_usd
        ).order_by(NojinFormulationRecipe.estimated_cost_usd_per_ha).all()

    def get_high_water_saving(self, min_saving_pct: float = 40.0) -> list[NojinFormulationRecipe]:
        """Get formulations with high water savings."""
        return self.session.query(NojinFormulationRecipe).filter(
            NojinFormulationRecipe.water_saving_pct >= min_saving_pct
        ).order_by(NojinFormulationRecipe.water_saving_pct.desc()).all()

    def get_all(self) -> list[NojinFormulationRecipe]:
        """Get all recipes."""
        return self.session.query(NojinFormulationRecipe).order_by(
            NojinFormulationRecipe.recipe_code
        ).all()

    def scale_recipe(
        self,
        recipe_code: str,
        area_ha: float,
    ) -> dict | None:
        """
        Scale recipe to specific area.
        Returns material quantities for the area.
        """
        recipe = self.get_by_code(recipe_code)
        if not recipe:
            return None

        if area_ha < recipe.area_min_ha or area_ha > recipe.area_max_ha:
            logger.warning(
                f"Area {area_ha} ha outside supported range "
                f"[{recipe.area_min_ha}, {recipe.area_max_ha}]"
            )

        # Scale each material
        composition = recipe.material_composition or {}
        scaled = {}
        for material_code, kg_per_ha in composition.items():
            scaled[material_code] = kg_per_ha * area_ha

        return {
            "recipe_code": recipe.recipe_code,
            "recipe_name": recipe.recipe_name,
            "area_ha": area_ha,
            "material_quantities_kg": scaled,
            "total_kg": recipe.total_kg_per_ha * area_ha,
            "total_tons": (recipe.total_kg_per_ha * area_ha) / 1000,
            "estimated_cost_usd": (recipe.estimated_cost_usd_per_ha or 0) * area_ha,
            "expected_water_saving_m3": (recipe.water_saving_pct or 0) * area_ha * 100,  # Approx
            "expected_yield_increase_pct": recipe.yield_increase_pct,
        }

    def count(self) -> int:
        """Count all recipes."""
        return self.session.query(NojinFormulationRecipe).count()
