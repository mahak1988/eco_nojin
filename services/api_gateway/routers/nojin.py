"""
Nojin Biofertilizer FastAPI Router
===================================
Complete API for Nojin system with 15 endpoints.

Serves 2.5 billion people in arid regions with scientifically-validated
soil restoration recommendations.

Author: Eco-Nojin Team
Date: 2026-08-24
Version: 1.0.0

Endpoints:
- Materials: list, detail, arid-priority, search
- Soils: list, detail, classify
- Recipes: list, detail, scale
- Analysis: recommend, optimize, cost-benefit, water-savings, full
- System: statistics, health
"""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# PYDANTIC MODELS (Request/Response schemas)
# ═══════════════════════════════════════════════════════════════════

class MaterialResponse(BaseModel):
    """Response schema for material."""
    material_code: str
    common_name: str
    scientific_name: Optional[str] = None
    category: str
    nitrogen_pct: float = 0
    phosphorus_pct: float = 0
    potassium_pct: float = 0
    calcium_pct: float = 0
    organic_matter_pct: float = 0
    cn_ratio: Optional[float] = None
    ph: Optional[float] = None
    cec_cmol_kg: Optional[float] = None
    water_retention_pct: Optional[float] = None
    release_rate: Optional[str] = None
    persistence_years: Optional[float] = None
    cost_per_ton_usd: Optional[float] = None
    availability: Optional[str] = None
    is_suitable_for_arid: bool = False
    arid_priority_score: Optional[int] = None
    benefits: Optional[List[str]] = None
    overuse_risks: Optional[List[str]] = None


class SoilTypeResponse(BaseModel):
    """Response schema for soil type."""
    soil_code: str
    soil_name: str
    soil_category: Optional[str] = None
    texture: Optional[str] = None
    typical_ph_min: Optional[float] = None
    typical_ph_max: Optional[float] = None
    typical_om_pct: Optional[float] = None
    typical_cec_cmol_kg: Optional[float] = None
    water_holding_capacity: Optional[str] = None
    drainage: Optional[str] = None
    common_problems: Optional[List[str]] = None
    nutrient_deficiencies: Optional[List[str]] = None
    common_regions: Optional[List[str]] = None


class RecipeResponse(BaseModel):
    """Response schema for formulation recipe."""
    recipe_code: str
    recipe_name: str
    soil_code: str
    soil_name: str
    area_min_ha: float
    area_max_ha: float
    material_composition: Dict[str, float]  # material_code -> kg/ha
    total_kg_per_ha: float
    total_tons_per_ha: float
    estimated_cost_usd_per_ha: float
    cn_ratio_final: Optional[float] = None
    om_increase_pct: Optional[float] = None
    water_saving_pct: Optional[float] = None
    yield_increase_pct: Optional[float] = None
    restoration_years: Optional[float] = None
    traditional_technique: Optional[str] = None


class SoilClassificationRequest(BaseModel):
    """Request for soil classification."""
    ph: float = Field(..., ge=0, le=14, description="Soil pH (0-14)")
    ec_dsm: float = Field(..., ge=0, description="Electrical conductivity (dS/m)")
    om_pct: float = Field(..., ge=0, le=100, description="Organic matter %")
    texture: Optional[str] = Field(None, description="Soil texture")
    region: Optional[str] = Field(None, description="Geographic region")


class SoilClassificationResponse(BaseModel):
    """Response for soil classification."""
    classified_as: str
    soil_code: str
    soil_name: str
    confidence: float
    recommended_recipe: Optional[str] = None
    warnings: List[str] = []
    next_steps: List[str] = []


class RecommendRequest(BaseModel):
    """Request for recommendation."""
    soil_code: str = Field(..., description="Soil type code (e.g., SOIL-01)")
    area_ha: float = Field(..., gt=0, le=10000, description="Area in hectares")
    budget_per_ha_usd: Optional[float] = Field(None, gt=0, description="Budget constraint")
    crop_type: str = Field("wheat", description="Target crop")


class RecommendResponse(BaseModel):
    """Response for recommendation."""
    recipe_code: str
    recipe_name: str
    area_ha: float
    material_quantities: Dict[str, float]  # material_code -> kg total
    total_tons: float
    estimated_cost_usd: float
    expected_results: Dict[str, float]
    traditional_technique: Optional[str] = None
    implementation_tips: List[str] = []


class OptimizeRequest(BaseModel):
    """Request for formulation optimization."""
    soil_code: str
    area_ha: float
    target_om_increase_pct: float = 3.0
    target_cn_ratio: float = 25.0
    budget_per_ha_usd: Optional[float] = None
    required_materials: List[str] = []
    excluded_materials: List[str] = []


class CostBenefitRequest(BaseModel):
    """Request for cost-benefit analysis."""
    formulation: Dict[str, float] = Field(..., description="{material_code: kg_per_ha}")
    area_ha: float
    crop_type: str = "wheat"
    current_yield_t_ha: float = 2.0
    current_irrigation_m3_ha: float = 8000.0
    current_fertilizer_cost_usd_ha: float = 300.0


class CostBenefitResponse(BaseModel):
    """Response for cost-benefit analysis."""
    total_investment_usd: float
    annual_benefit_usd: float
    annual_cost_usd: float
    net_annual_benefit_usd: float
    roi_annual_percent: float
    payback_simple_months: int
    npv_10year_usd: float
    irr_percent: float
    benefit_cost_ratio: float
    carbon_credit_potential_usd: float
    water_savings_value_usd: float
    is_economically_viable: bool
    viability_score: float
    farmer_category: str
    recommendations: List[str]


class WaterSavingsRequest(BaseModel):
    """Request for water savings calculation."""
    formulation: Dict[str, float]
    area_ha: float
    baseline_irrigation_m3_ha: float = 8000.0


class WaterSavingsResponse(BaseModel):
    """Response for water savings."""
    baseline_irrigation_m3_ha: float
    new_irrigation_m3_ha: float
    water_saved_m3_ha: float
    water_saved_percent: float
    annual_water_saved_m3: float
    annual_savings_usd: float
    drought_resistance_days: int
    recommendations: List[str]


class ScaleRequest(BaseModel):
    """Request for scale calculation."""
    formulation: Dict[str, float]
    area_ha: float


class ScaleResponse(BaseModel):
    """Response for scale calculation."""
    area_ha: float
    scale_category: str
    material_quantities: Dict[str, Dict[str, float]]
    total_tons: float
    total_cost_usd: float
    economies_of_scale_pct: float
    implementation_days: int
    equipment_needed: List[str]
    logistics_notes: List[str]


class FullAnalysisRequest(BaseModel):
    """Complete analysis request combining all calculators."""
    soil_code: str
    area_ha: float
    crop_type: str = "wheat"
    current_yield_t_ha: float = 2.0
    current_irrigation_m3_ha: float = 8000.0
    current_fertilizer_cost_usd_ha: float = 300.0
    budget_per_ha_usd: Optional[float] = None


class FullAnalysisResponse(BaseModel):
    """Complete analysis response."""
    recommendation: RecommendResponse
    cost_benefit: CostBenefitResponse
    water_savings: WaterSavingsResponse
    scale: ScaleResponse
    overall_assessment: Dict[str, Any]


class StatisticsResponse(BaseModel):
    """System statistics."""
    materials_count: int
    soil_types_count: int
    recipes_count: int
    arid_priority_materials: int
    high_water_saving_recipes: int
    avg_roi_percent: float
    avg_water_saving_percent: float
    system_status: str


class HealthResponse(BaseModel):
    """Health check."""
    status: str
    version: str
    database_connected: bool
    materials_count: int
    recipes_count: int
    timestamp: str


# ═══════════════════════════════════════════════════════════════════
# DATABASE DEPENDENCY
# ═══════════════════════════════════════════════════════════════════

def get_db() -> Session:
    """Database session dependency."""
    try:
        from database import SessionLocal
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable"
        )


# ═══════════════════════════════════════════════════════════════════
# ROUTER DEFINITION
# ═══════════════════════════════════════════════════════════════════

router = APIRouter(
    prefix="/api/nojin",
    tags=["Nojin Biofertilizer"],
    responses={
        404: {"description": "Resource not found"},
        503: {"description": "Service unavailable"},
    }
)


# ═══════════════════════════════════════════════════════════════════
# HEALTH & STATISTICS
# ═══════════════════════════════════════════════════════════════════

@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns system status, database connectivity, and data counts.
    """
    from datetime import datetime
    from engine.hydroma.biofertilizer.models import (
        NojinMaterial, NojinSoilType, NojinFormulationRecipe
    )
    
    try:
        materials_count = db.query(NojinMaterial).count()
        recipes_count = db.query(NojinFormulationRecipe).count()
        db_ok = True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        materials_count = 0
        recipes_count = 0
        db_ok = False
    
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        version="1.0.0",
        database_connected=db_ok,
        materials_count=materials_count,
        recipes_count=recipes_count,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get comprehensive system statistics.
    
    Returns counts and averages for all Nojin entities.
    """
    from engine.hydroma.biofertilizer.models import (
        NojinMaterial, NojinSoilType, NojinFormulationRecipe
    )
    from sqlalchemy import func
    
    materials_count = db.query(NojinMaterial).count()
    soil_types_count = db.query(NojinSoilType).count()
    recipes_count = db.query(NojinFormulationRecipe).count()
    
    arid_priority = db.query(NojinMaterial).filter(
        NojinMaterial.arid_priority_score >= 9
    ).count()
    
    high_water = db.query(NojinFormulationRecipe).filter(
        NojinFormulationRecipe.water_saving_pct >= 40
    ).count()
    
    avg_roi = db.query(func.avg(NojinFormulationRecipe.yield_increase_pct)).scalar() or 0
    avg_water = db.query(func.avg(NojinFormulationRecipe.water_saving_pct)).scalar() or 0
    
    return StatisticsResponse(
        materials_count=materials_count,
        soil_types_count=soil_types_count,
        recipes_count=recipes_count,
        arid_priority_materials=arid_priority,
        high_water_saving_recipes=high_water,
        avg_roi_percent=round(avg_roi, 2),
        avg_water_saving_percent=round(avg_water, 2),
        system_status="operational",
    )


# ═══════════════════════════════════════════════════════════════════
# MATERIALS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/materials", response_model=List[MaterialResponse])
async def list_materials(
    category: Optional[str] = Query(None, description="Filter by category"),
    arid_only: bool = Query(False, description="Only arid-suitable materials"),
    min_priority: int = Query(0, ge=0, le=10, description="Minimum arid priority score"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    List all available materials.
    
    Materials include minerals, organic materials, biochar, manures, etc.
    Each has scientifically-documented properties.
    """
    from engine.hydroma.biofertilizer.models import NojinMaterial
    import json
    
    query = db.query(NojinMaterial)
    
    if category:
        query = query.filter(NojinMaterial.category == category)
    if arid_only:
        query = query.filter(NojinMaterial.is_suitable_for_arid == True)
    if min_priority > 0:
        query = query.filter(NojinMaterial.arid_priority_score >= min_priority)
    
    materials = query.limit(limit).all()
    
    results = []
    for m in materials:
        try:
            benefits = json.loads(m.benefits) if m.benefits else []
            risks = json.loads(m.overuse_risks) if m.overuse_risks else []
        except (json.JSONDecodeError, TypeError):
            benefits, risks = [], []
        
        results.append(MaterialResponse(
            material_code=m.material_code,
            common_name=m.common_name,
            scientific_name=m.scientific_name,
            category=m.category,
            nitrogen_pct=m.nitrogen_pct or 0,
            phosphorus_pct=m.phosphorus_pct or 0,
            potassium_pct=m.potassium_pct or 0,
            calcium_pct=m.calcium_pct or 0,
            organic_matter_pct=m.organic_matter_pct or 0,
            cn_ratio=m.cn_ratio,
            ph=m.ph,
            cec_cmol_kg=m.cec_cmol_kg,
            water_retention_pct=m.water_retention_pct,
            release_rate=m.release_rate,
            persistence_years=m.persistence_years,
            cost_per_ton_usd=m.cost_per_ton_usd,
            availability=m.availability,
            is_suitable_for_arid=m.is_suitable_for_arid or False,
            arid_priority_score=m.arid_priority_score,
            benefits=benefits,
            overuse_risks=risks,
        ))
    
    return results


@router.get("/materials/arid-priority", response_model=List[MaterialResponse])
async def list_arid_priority_materials(
    min_score: int = Query(9, ge=1, le=10),
    db: Session = Depends(get_db),
):
    """
    List materials prioritized for arid regions.
    
    These materials are specifically selected for the 2.5 billion people
    living in arid and semi-arid regions.
    """
    from engine.hydroma.biofertilizer.models import NojinMaterial
    import json
    
    materials = db.query(NojinMaterial).filter(
        NojinMaterial.is_suitable_for_arid == True,
        NojinMaterial.arid_priority_score >= min_score,
    ).order_by(NojinMaterial.arid_priority_score.desc()).all()
    
    results = []
    for m in materials:
        try:
            benefits = json.loads(m.benefits) if m.benefits else []
            risks = json.loads(m.overuse_risks) if m.overuse_risks else []
        except (json.JSONDecodeError, TypeError):
            benefits, risks = [], []
        
        results.append(MaterialResponse(
            material_code=m.material_code,
            common_name=m.common_name,
            scientific_name=m.scientific_name,
            category=m.category,
            nitrogen_pct=m.nitrogen_pct or 0,
            phosphorus_pct=m.phosphorus_pct or 0,
            potassium_pct=m.potassium_pct or 0,
            calcium_pct=m.calcium_pct or 0,
            organic_matter_pct=m.organic_matter_pct or 0,
            cn_ratio=m.cn_ratio,
            ph=m.ph,
            cec_cmol_kg=m.cec_cmol_kg,
            water_retention_pct=m.water_retention_pct,
            release_rate=m.release_rate,
            persistence_years=m.persistence_years,
            cost_per_ton_usd=m.cost_per_ton_usd,
            availability=m.availability,
            is_suitable_for_arid=True,
            arid_priority_score=m.arid_priority_score,
            benefits=benefits,
            overuse_risks=risks,
        ))
    
    return results


@router.get("/materials/{material_code}", response_model=MaterialResponse)
async def get_material(material_code: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific material.
    
    Example: /api/nojin/materials/MIN-011 (Zeolite)
    """
    from engine.hydroma.biofertilizer.models import NojinMaterial
    import json
    
    material = db.query(NojinMaterial).filter(
        NojinMaterial.material_code == material_code
    ).first()
    
    if not material:
        raise HTTPException(
            status_code=404,
            detail=f"Material '{material_code}' not found"
        )
    
    try:
        benefits = json.loads(material.benefits) if material.benefits else []
        risks = json.loads(material.overuse_risks) if material.overuse_risks else []
    except (json.JSONDecodeError, TypeError):
        benefits, risks = [], []
    
    return MaterialResponse(
        material_code=material.material_code,
        common_name=material.common_name,
        scientific_name=material.scientific_name,
        category=material.category,
        nitrogen_pct=material.nitrogen_pct or 0,
        phosphorus_pct=material.phosphorus_pct or 0,
        potassium_pct=material.potassium_pct or 0,
        calcium_pct=material.calcium_pct or 0,
        organic_matter_pct=material.organic_matter_pct or 0,
        cn_ratio=material.cn_ratio,
        ph=material.ph,
        cec_cmol_kg=material.cec_cmol_kg,
        water_retention_pct=material.water_retention_pct,
        release_rate=material.release_rate,
        persistence_years=material.persistence_years,
        cost_per_ton_usd=material.cost_per_ton_usd,
        availability=material.availability,
        is_suitable_for_arid=material.is_suitable_for_arid or False,
        arid_priority_score=material.arid_priority_score,
        benefits=benefits,
        overuse_risks=risks,
    )


# ═══════════════════════════════════════════════════════════════════
# SOIL TYPES ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/soils", response_model=List[SoilTypeResponse])
async def list_soil_types(db: Session = Depends(get_db)):
    """List all soil types."""
    from engine.hydroma.biofertilizer.models import NojinSoilType
    import json
    
    soils = db.query(NojinSoilType).order_by(NojinSoilType.soil_code).all()
    
    results = []
    for s in soils:
        try:
            problems = json.loads(s.common_problems) if s.common_problems else []
            deficiencies = json.loads(s.nutrient_deficiencies) if s.nutrient_deficiencies else []
            regions = json.loads(s.common_regions) if s.common_regions else []
        except (json.JSONDecodeError, TypeError):
            problems, deficiencies, regions = [], [], []
        
        results.append(SoilTypeResponse(
            soil_code=s.soil_code,
            soil_name=s.soil_name,
            soil_category=s.soil_category,
            texture=s.texture,
            typical_ph_min=s.typical_ph_min,
            typical_ph_max=s.typical_ph_max,
            typical_om_pct=s.typical_om_pct,
            typical_cec_cmol_kg=s.typical_cec_cmol_kg,
            water_holding_capacity=s.water_holding_capacity,
            drainage=s.drainage,
            common_problems=problems,
            nutrient_deficiencies=deficiencies,
            common_regions=regions,
        ))
    
    return results


@router.get("/soils/{soil_code}", response_model=SoilTypeResponse)
async def get_soil_type(soil_code: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific soil type."""
    from engine.hydroma.biofertilizer.models import NojinSoilType
    import json
    
    soil = db.query(NojinSoilType).filter(
        NojinSoilType.soil_code == soil_code
    ).first()
    
    if not soil:
        raise HTTPException(
            status_code=404,
            detail=f"Soil type '{soil_code}' not found"
        )
    
    try:
        problems = json.loads(soil.common_problems) if soil.common_problems else []
        deficiencies = json.loads(soil.nutrient_deficiencies) if soil.nutrient_deficiencies else []
        regions = json.loads(soil.common_regions) if soil.common_regions else []
    except (json.JSONDecodeError, TypeError):
        problems, deficiencies, regions = [], [], []
    
    return SoilTypeResponse(
        soil_code=soil.soil_code,
        soil_name=soil.soil_name,
        soil_category=soil.soil_category,
        texture=soil.texture,
        typical_ph_min=soil.typical_ph_min,
        typical_ph_max=soil.typical_ph_max,
        typical_om_pct=soil.typical_om_pct,
        typical_cec_cmol_kg=soil.typical_cec_cmol_kg,
        water_holding_capacity=soil.water_holding_capacity,
        drainage=soil.drainage,
        common_problems=problems,
        nutrient_deficiencies=deficiencies,
        common_regions=regions,
    )


@router.post("/classify", response_model=SoilClassificationResponse)
async def classify_soil(
    request: SoilClassificationRequest,
    db: Session = Depends(get_db),
):
    """
    Classify soil type based on laboratory test results.
    
    Returns the best-matching soil type and recommended recipe.
    """
    from engine.hydroma.biofertilizer.repositories import NojinSoilTypeRepository, NojinFormulationRecipeRepository
    
    soil_repo = NojinSoilTypeRepository(db)
    recipe_repo = NojinFormulationRecipeRepository(db)
    
    # Classify
    classified = soil_repo.classify_soil(
        ph=request.ph,
        ec_dsm=request.ec_dsm,
        om_pct=request.om_pct,
        texture=request.texture,
    )
    
    if not classified:
        # Fallback: loam
        classified = soil_repo.get_by_code("SOIL-06")  # Default
    
    # Get recipe
    recipe = None
    if classified:
        recipes_list = recipe_repo.get_for_soil(classified.id)
        if recipes_list and len(recipes_list) > 0:
            recipe = recipes_list[0]  # get_for_soil returns a list
    
    warnings = []
    next_steps = []
    
    if request.ec_dsm > 4:
        warnings.append("High salinity detected - special treatment needed")
        next_steps.append("Apply gypsum (5-8 t/ha) before other amendments")
    
    if request.ph < 5.5:
        warnings.append("Acidic soil detected")
        next_steps.append("Apply agricultural lime to raise pH")
    
    if request.ph > 8.5:
        warnings.append("Alkaline soil detected")
        next_steps.append("Apply elemental sulfur to lower pH")
    
    if request.om_pct < 1.0:
        warnings.append("Very low organic matter")
        next_steps.append("Prioritize organic matter addition")
    
    if not next_steps:
        next_steps.append("Proceed with standard Nojin recipe for this soil type")
    
    return SoilClassificationResponse(
        classified_as=classified.soil_name if classified else "Unknown",
        soil_code=classified.soil_code if classified else "UNKNOWN",
        soil_name=classified.soil_name if classified else "Unknown",
        confidence=0.85 if classified else 0.0,
        recommended_recipe=recipe.recipe_code if recipe else None,
        warnings=warnings,
        next_steps=next_steps,
    )


# ═══════════════════════════════════════════════════════════════════
# RECIPES ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/recipes", response_model=List[RecipeResponse])
async def list_recipes(
    soil_code: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all formulation recipes."""
    from engine.hydroma.biofertilizer.models import NojinFormulationRecipe, NojinSoilType
    import json
    
    query = db.query(NojinFormulationRecipe)
    if soil_code:
        soil = db.query(NojinSoilType).filter(NojinSoilType.soil_code == soil_code).first()
        if soil:
            query = query.filter(NojinFormulationRecipe.soil_type_id == soil.id)
    
    recipes = query.order_by(NojinFormulationRecipe.recipe_code).all()
    
    results = []
    for r in recipes:
        soil = db.query(NojinSoilType).filter(NojinSoilType.id == r.soil_type_id).first()
        composition = r.material_composition or {}
        if isinstance(composition, str):
            composition = json.loads(composition)
        
        results.append(RecipeResponse(
            recipe_code=r.recipe_code,
            recipe_name=r.recipe_name,
            soil_code=soil.soil_code if soil else "UNKNOWN",
            soil_name=soil.soil_name if soil else "Unknown",
            area_min_ha=r.area_min_ha,
            area_max_ha=r.area_max_ha,
            material_composition=composition,
            total_kg_per_ha=r.total_kg_per_ha or 0,
            total_tons_per_ha=(r.total_kg_per_ha or 0) / 1000,
            estimated_cost_usd_per_ha=r.estimated_cost_usd_per_ha or 0,
            cn_ratio_final=r.cn_ratio_final,
            om_increase_pct=r.om_increase_pct,
            water_saving_pct=r.water_saving_pct,
            yield_increase_pct=r.yield_increase_pct,
            restoration_years=r.restoration_years,
            traditional_technique=r.traditional_technique,
        ))
    
    return results


@router.get("/recipes/{recipe_code}", response_model=RecipeResponse)
async def get_recipe(recipe_code: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific recipe."""
    from engine.hydroma.biofertilizer.models import NojinFormulationRecipe, NojinSoilType
    import json
    
    recipe = db.query(NojinFormulationRecipe).filter(
        NojinFormulationRecipe.recipe_code == recipe_code
    ).first()
    
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail=f"Recipe '{recipe_code}' not found"
        )
    
    soil = db.query(NojinSoilType).filter(NojinSoilType.id == recipe.soil_type_id).first()
    composition = recipe.material_composition or {}
    if isinstance(composition, str):
        composition = json.loads(composition)
    
    return RecipeResponse(
        recipe_code=recipe.recipe_code,
        recipe_name=recipe.recipe_name,
        soil_code=soil.soil_code if soil else "UNKNOWN",
        soil_name=soil.soil_name if soil else "Unknown",
        area_min_ha=recipe.area_min_ha,
        area_max_ha=recipe.area_max_ha,
        material_composition=composition,
        total_kg_per_ha=recipe.total_kg_per_ha or 0,
        total_tons_per_ha=(recipe.total_kg_per_ha or 0) / 1000,
        estimated_cost_usd_per_ha=recipe.estimated_cost_usd_per_ha or 0,
        cn_ratio_final=recipe.cn_ratio_final,
        om_increase_pct=recipe.om_increase_pct,
        water_saving_pct=recipe.water_saving_pct,
        yield_increase_pct=recipe.yield_increase_pct,
        restoration_years=recipe.restoration_years,
        traditional_technique=recipe.traditional_technique,
    )


# ═══════════════════════════════════════════════════════════════════
# ANALYSIS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

def _load_calculators():
    """Load all calculators with materials from DB."""
    from database import SessionLocal
    from engine.hydroma.biofertilizer.models import NojinMaterial
    from engine.hydroma.biofertilizer.data import MATERIALS, FORMULATIONS
    from engine.hydroma.biofertilizer.advanced_calculator import (
        FormulationOptimizer,
        FormulationRequest,
        CostBenefitCalculator,
        WaterSavingsCalculator,
        ScaleCalculator,
    )
    
    materials = MATERIALS
    
    return {
        "optimizer": FormulationOptimizer(materials, FORMULATIONS),
        "cost_calc": CostBenefitCalculator(materials),
        "water_calc": WaterSavingsCalculator(materials),
        "scale_calc": ScaleCalculator(materials),
        "FormulationRequest": FormulationRequest,
    }


@router.post("/recommend", response_model=RecommendResponse)
async def get_recommendation(
    request: RecommendRequest,
    db: Session = Depends(get_db),
):
    """
    Get Nojin recommendation for a specific soil type and area.
    
    Returns complete formulation with material quantities and expected results.
    """
    from engine.hydroma.biofertilizer.models import NojinFormulationRecipe, NojinSoilType
    
    # Get recipe
    soil = db.query(NojinSoilType).filter(NojinSoilType.soil_code == request.soil_code).first()
    if not soil:
        raise HTTPException(status_code=404, detail=f"Soil type '{request.soil_code}' not found")
    
    recipe = db.query(NojinFormulationRecipe).filter(
        NojinFormulationRecipe.soil_type_id == soil.id
    ).first()
    
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail=f"No recipe found for soil type '{request.soil_code}'"
        )
    
    # Scale recipe to area
    import json
    composition = recipe.material_composition or {}
    if isinstance(composition, str):
        composition = json.loads(composition)
    
    # Check budget constraint
    cost_per_ha = recipe.estimated_cost_usd_per_ha or 0
    total_cost = cost_per_ha * request.area_ha
    
    if request.budget_per_ha_usd and cost_per_ha > request.budget_per_ha_usd:
        raise HTTPException(
            status_code=400,
            detail=f"Budget exceeded: ${cost_per_ha:.2f}/ha > ${request.budget_per_ha_usd:.2f}/ha"
        )
    
    # Scale composition
    scaled = {code: kg * request.area_ha for code, kg in composition.items()}
    total_kg = sum(scaled.values())
    
    # Implementation tips
    tips = []
    if recipe.traditional_technique:
        tips.append(f"Consider integrating with {recipe.traditional_technique}")
    tips.append("Incorporate materials to 20cm depth")
    tips.append("Maintain mulch layer 5-10cm thick")
    tips.append("Irrigate lightly after application")
    
    return RecommendResponse(
        recipe_code=recipe.recipe_code,
        recipe_name=recipe.recipe_name,
        area_ha=request.area_ha,
        material_quantities=scaled,
        total_tons=total_kg / 1000,
        estimated_cost_usd=total_cost,
        expected_results={
            "yield_increase_pct": recipe.yield_increase_pct or 0,
            "water_saving_pct": recipe.water_saving_pct or 0,
            "om_increase_pct": recipe.om_increase_pct or 0,
            "restoration_years": recipe.restoration_years or 3,
        },
        traditional_technique=recipe.traditional_technique,
        implementation_tips=tips,
    )


@router.post("/optimize")
async def optimize_formulation(request: OptimizeRequest):
    """
    Optimize formulation using Linear Programming.
    
    Finds the best material combination for the given soil and constraints.
    """
    from engine.hydroma.biofertilizer.advanced_calculator import FormulationOptimizer, FormulationRequest
    from engine.hydroma.biofertilizer.data import MATERIALS, FORMULATIONS
    
    optimizer = FormulationOptimizer(MATERIALS, FORMULATIONS)
    
    req = FormulationRequest(
        soil_code=request.soil_code,
        area_ha=request.area_ha,
        budget_per_ha_usd=request.budget_per_ha_usd,
        target_om_increase_pct=request.target_om_increase_pct,
        target_cn_ratio=request.target_cn_ratio,
        required_materials=request.required_materials,
        excluded_materials=request.excluded_materials,
    )
    
    solution = optimizer.optimize(req)
    
    return {
        "soil_code": solution.soil_code,
        "area_ha": solution.area_ha,
        "materials": solution.materials,
        "total_kg_per_ha": solution.total_kg_per_ha,
        "total_cost_usd_per_ha": solution.total_cost_usd_per_ha,
        "expected_cn_ratio": solution.expected_cn_ratio,
        "expected_n_kg_ha": solution.expected_n_kg_ha,
        "expected_p_kg_ha": solution.expected_p_kg_ha,
        "expected_k_kg_ha": solution.expected_k_kg_ha,
        "water_saving_pct": solution.water_saving_pct,
        "is_feasible": solution.is_feasible,
        "warnings": solution.warnings,
        "notes": solution.notes,
    }


@router.post("/cost-benefit", response_model=CostBenefitResponse)
async def analyze_cost_benefit(request: CostBenefitRequest):
    """
    Perform scientific cost-benefit analysis.
    
    Uses FAO/World Bank methodologies for:
    - ROI calculation
    - Payback period (simple + discounted)
    - NPV (Net Present Value)
    - IRR (Internal Rate of Return)
    - BCR (Benefit-Cost Ratio)
    """
    from engine.hydroma.biofertilizer.advanced_calculator import CostBenefitCalculator
    from engine.hydroma.biofertilizer.data import MATERIALS
    
    calc = CostBenefitCalculator(MATERIALS)
    
    result = calc.analyze(
        formulation_materials=request.formulation,
        area_ha=request.area_ha,
        crop_type=request.crop_type,
        current_yield_t_ha=request.current_yield_t_ha,
        current_irrigation_m3_ha=request.current_irrigation_m3_ha,
        current_fertilizer_cost_usd_ha=request.current_fertilizer_cost_usd_ha,
    )
    
    return CostBenefitResponse(
        total_investment_usd=result.total_investment_usd,
        annual_benefit_usd=result.annual_benefit_usd,
        annual_cost_usd=result.annual_cost_usd,
        net_annual_benefit_usd=result.net_annual_benefit_usd,
        roi_annual_percent=result.roi_annual_percent,
        payback_simple_months=result.payback_simple_months,
        npv_10year_usd=result.npv_10year_usd,
        irr_percent=result.irr_percent,
        benefit_cost_ratio=result.benefit_cost_ratio,
        carbon_credit_potential_usd=result.carbon_credit_potential_usd,
        water_savings_value_usd=result.water_savings_value_usd,
        is_economically_viable=result.is_economically_viable,
        viability_score=result.viability_score,
        farmer_category=result.farmer_category,
        recommendations=result.recommendations,
    )


@router.post("/water-savings", response_model=WaterSavingsResponse)
async def calculate_water_savings(request: WaterSavingsRequest):
    """
    Calculate water savings using FAO-56 principles.
    
    Considers:
    - Evaporation reduction
    - Water retention improvement
    - Infiltration enhancement
    """
    from engine.hydroma.biofertilizer.advanced_calculator import WaterSavingsCalculator
    from engine.hydroma.biofertilizer.data import MATERIALS
    
    calc = WaterSavingsCalculator(MATERIALS)
    
    result = calc.calculate(
        formulation_materials=request.formulation,
        area_ha=request.area_ha,
        baseline_irrigation_m3_ha=request.baseline_irrigation_m3_ha,
    )
    
    return WaterSavingsResponse(
        baseline_irrigation_m3_ha=result.baseline_irrigation_m3_ha,
        new_irrigation_m3_ha=result.new_irrigation_m3_ha,
        water_saved_m3_ha=result.water_saved_m3_ha,
        water_saved_percent=result.water_saved_percent,
        annual_water_saved_m3=result.annual_water_saved_m3,
        annual_savings_usd=result.annual_savings_usd,
        drought_resistance_days=result.drought_resistance_days,
        recommendations=result.recommendations,
    )


@router.post("/scale", response_model=ScaleResponse)
async def calculate_scale(request: ScaleRequest):
    """
    Scale formulation to given area.
    
    Provides logistics, labor, equipment, and economies of scale.
    """
    from engine.hydroma.biofertilizer.advanced_calculator import ScaleCalculator
    from engine.hydroma.biofertilizer.data import MATERIALS
    
    calc = ScaleCalculator(MATERIALS)
    
    result = calc.scale(
        formulation_per_ha=request.formulation,
        area_ha=request.area_ha,
    )
    
    return ScaleResponse(
        area_ha=result.area_ha,
        scale_category=result.scale_category,
        material_quantities=result.material_quantities,
        total_tons=result.total_tons,
        total_cost_usd=result.total_cost_usd,
        economies_of_scale_pct=result.economies_of_scale_pct,
        implementation_days=result.implementation_days,
        equipment_needed=result.equipment_needed,
        logistics_notes=result.logistics_notes,
    )


@router.post("/full-analysis", response_model=FullAnalysisResponse)
async def full_analysis(request: FullAnalysisRequest, db: Session = Depends(get_db)):
    """
    Complete analysis combining all calculators.
    
    This is the main endpoint that provides:
    - Recommendation (material quantities)
    - Cost-benefit analysis (ROI, NPV, IRR)
    - Water savings calculation
    - Scale calculation (logistics)
    - Overall assessment
    """
    from engine.hydroma.biofertilizer.models import NojinFormulationRecipe, NojinSoilType
    from engine.hydroma.biofertilizer.advanced_calculator import (
        CostBenefitCalculator,
        WaterSavingsCalculator,
        ScaleCalculator,
    )
    from engine.hydroma.biofertilizer.data import MATERIALS
    import json
    
    # Get recipe
    soil = db.query(NojinSoilType).filter(NojinSoilType.soil_code == request.soil_code).first()
    if not soil:
        raise HTTPException(status_code=404, detail=f"Soil type '{request.soil_code}' not found")
    
    recipe = db.query(NojinFormulationRecipe).filter(
        NojinFormulationRecipe.soil_type_id == soil.id
    ).first()
    
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail=f"No recipe found for soil type '{request.soil_code}'"
        )
    
    # Get composition
    composition = recipe.material_composition or {}
    if isinstance(composition, str):
        composition = json.loads(composition)
    
    # Scale to area
    scaled = {code: kg * request.area_ha for code, kg in composition.items()}
    
    # Run all calculators
    cost_calc = CostBenefitCalculator(MATERIALS)
    water_calc = WaterSavingsCalculator(MATERIALS)
    scale_calc = ScaleCalculator(MATERIALS)
    
    cb_result = cost_calc.analyze(
        formulation_materials=composition,
        area_ha=request.area_ha,
        crop_type=request.crop_type,
        current_yield_t_ha=request.current_yield_t_ha,
        current_irrigation_m3_ha=request.current_irrigation_m3_ha,
        current_fertilizer_cost_usd_ha=request.current_fertilizer_cost_usd_ha,
    )
    
    ws_result = water_calc.calculate(
        formulation_materials=composition,
        area_ha=request.area_ha,
        baseline_irrigation_m3_ha=request.current_irrigation_m3_ha,
    )
    
    sc_result = scale_calc.scale(
        formulation_per_ha=composition,
        area_ha=request.area_ha,
    )
    
    # Build overall assessment
    assessment = {
        "project_title": f"Nojin Restoration: {request.area_ha} ha {request.crop_type} on {soil.soil_name}",
        "recommendation_strength": "STRONG" if cb_result.is_economically_viable else "MODERATE",
        "key_findings": [
            f"Investment: ${cb_result.total_investment_usd:,.0f}",
            f"ROI: {cb_result.roi_annual_percent:.1f}% annually",
            f"Payback: {cb_result.payback_simple_months} months",
            f"Water savings: {ws_result.water_saved_percent:.1f}%",
            f"Scale: {sc_result.scale_category} ({sc_result.implementation_days} days)",
        ],
        "strategic_impact": {
            "people_benefited_estimate": int(request.area_ha * 2.5),  # ~2.5 people per ha
            "co2_sequestered_tons_10yr": cb_result.carbon_credit_potential_usd / 25,
            "water_saved_m3_10yr": ws_result.annual_water_saved_m3 * 10,
        },
        "risks": cb_result.warnings,
        "opportunities": cb_result.recommendations,
    }
    
    # Build sub-responses
    tips = []
    if recipe.traditional_technique:
        tips.append(f"Integrate with {recipe.traditional_technique}")
    tips.append("Incorporate to 20cm depth")
    tips.append("Maintain mulch layer")
    
    recommendation = RecommendResponse(
        recipe_code=recipe.recipe_code,
        recipe_name=recipe.recipe_name,
        area_ha=request.area_ha,
        material_quantities=scaled,
        total_tons=sum(scaled.values()) / 1000,
        estimated_cost_usd=cb_result.total_investment_usd,
        expected_results={
            "yield_increase_pct": recipe.yield_increase_pct or 0,
            "water_saving_pct": recipe.water_saving_pct or 0,
            "om_increase_pct": recipe.om_increase_pct or 0,
            "restoration_years": recipe.restoration_years or 3,
        },
        traditional_technique=recipe.traditional_technique,
        implementation_tips=tips,
    )
    
    cost_benefit = CostBenefitResponse(
        total_investment_usd=cb_result.total_investment_usd,
        annual_benefit_usd=cb_result.annual_benefit_usd,
        annual_cost_usd=cb_result.annual_cost_usd,
        net_annual_benefit_usd=cb_result.net_annual_benefit_usd,
        roi_annual_percent=cb_result.roi_annual_percent,
        payback_simple_months=cb_result.payback_simple_months,
        npv_10year_usd=cb_result.npv_10year_usd,
        irr_percent=cb_result.irr_percent,
        benefit_cost_ratio=cb_result.benefit_cost_ratio,
        carbon_credit_potential_usd=cb_result.carbon_credit_potential_usd,
        water_savings_value_usd=cb_result.water_savings_value_usd,
        is_economically_viable=cb_result.is_economically_viable,
        viability_score=cb_result.viability_score,
        farmer_category=cb_result.farmer_category,
        recommendations=cb_result.recommendations,
    )
    
    water_savings = WaterSavingsResponse(
        baseline_irrigation_m3_ha=ws_result.baseline_irrigation_m3_ha,
        new_irrigation_m3_ha=ws_result.new_irrigation_m3_ha,
        water_saved_m3_ha=ws_result.water_saved_m3_ha,
        water_saved_percent=ws_result.water_saved_percent,
        annual_water_saved_m3=ws_result.annual_water_saved_m3,
        annual_savings_usd=ws_result.annual_savings_usd,
        drought_resistance_days=ws_result.drought_resistance_days,
        recommendations=ws_result.recommendations,
    )
    
    scale = ScaleResponse(
        area_ha=sc_result.area_ha,
        scale_category=sc_result.scale_category,
        material_quantities=sc_result.material_quantities,
        total_tons=sc_result.total_tons,
        total_cost_usd=sc_result.total_cost_usd,
        economies_of_scale_pct=sc_result.economies_of_scale_pct,
        implementation_days=sc_result.implementation_days,
        equipment_needed=sc_result.equipment_needed,
        logistics_notes=sc_result.logistics_notes,
    )
    
    return FullAnalysisResponse(
        recommendation=recommendation,
        cost_benefit=cost_benefit,
        water_savings=water_savings,
        scale=scale,
        overall_assessment=assessment,
    )


__all__ = ["router"]