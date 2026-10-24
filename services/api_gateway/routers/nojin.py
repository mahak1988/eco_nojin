"""
Nojin Biofertilizer FastAPI Router
===================================
S-STRUCT compliant: all DB access delegated to ``services.nojin.service.NojinService``,
which uses ``services.nojin.repository.NojinRepository``. No direct ``db.query`` /
``db.execute`` calls remain in the router. Health probes delegate to the service layer.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from services.nojin.service import get_nojin_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/nojin",
    tags=["Nojin Biofertilizer"],
    responses={
        404: {"description": "Resource not found"},
        503: {"description": "Service unavailable"},
    },
)


def _handle_data_unavailable(exc: RuntimeError) -> HTTPException:
    """Convert RuntimeError (data unavailable) to 503 Service Unavailable."""
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Nojin service unavailable: {exc}",
    )


class MaterialResponse(BaseModel):
    """Response schema for material."""

    material_code: str
    common_name: str
    scientific_name: str | None = None
    category: str
    nitrogen_pct: float = 0
    phosphorus_pct: float = 0
    potassium_pct: float = 0
    calcium_pct: float = 0
    organic_matter_pct: float = 0
    cn_ratio: float | None = None
    ph: float | None = None
    cec_cmol_kg: float | None = None
    water_retention_pct: float | None = None
    release_rate: str | None = None
    persistence_years: float | None = None
    cost_per_ton_usd: float | None = None
    availability: str | None = None
    is_suitable_for_arid: bool = False
    arid_priority_score: int | None = None
    benefits: list[str] | None = None
    overuse_risks: list[str] | None = None


class SoilTypeResponse(BaseModel):
    """Response schema for soil type."""

    soil_code: str
    soil_name: str
    soil_category: str | None = None
    texture: str | None = None
    typical_ph_min: float | None = None
    typical_ph_max: float | None = None
    typical_om_pct: float | None = None
    typical_cec_cmol_kg: float | None = None
    water_holding_capacity: str | None = None
    drainage: str | None = None
    common_problems: list[str] | None = None
    nutrient_deficiencies: list[str] | None = None
    common_regions: list[str] | None = None


class RecipeResponse(BaseModel):
    """Response schema for formulation recipe."""

    recipe_code: str
    recipe_name: str
    soil_code: str
    soil_name: str
    area_min_ha: float
    area_max_ha: float
    material_composition: dict[str, float]
    total_kg_per_ha: float
    total_tons_per_ha: float
    estimated_cost_usd_per_ha: float
    cn_ratio_final: float | None = None
    om_increase_pct: float | None = None
    water_saving_pct: float | None = None
    yield_increase_pct: float | None = None
    restoration_years: float | None = None
    traditional_technique: str | None = None


class SoilClassificationRequest(BaseModel):
    """Request for soil classification."""

    ph: float = Field(..., ge=0, le=14, description="Soil pH (0-14)")
    ec_dsm: float = Field(..., ge=0, description="Electrical conductivity (dS/m)")
    om_pct: float = Field(..., ge=0, le=100, description="Organic matter %")
    texture: str | None = Field(None, description="Soil texture")
    region: str | None = Field(None, description="Geographic region")


class SoilClassificationResponse(BaseModel):
    """Response for soil classification."""

    classified_as: str
    soil_code: str
    soil_name: str
    confidence: float
    recommended_recipe: str | None = None
    warnings: list[str] = []
    next_steps: list[str] = []


class RecommendRequest(BaseModel):
    """Request for recommendation."""

    soil_code: str = Field(..., description="Soil type code (e.g., SOIL-01)")
    area_ha: float = Field(..., gt=0, le=10000, description="Area in hectares")
    budget_per_ha_usd: float | None = Field(None, gt=0, description="Budget constraint")
    crop_type: str = Field("wheat", description="Target crop")


class RecommendResponse(BaseModel):
    """Response for recommendation."""

    recipe_code: str
    recipe_name: str
    area_ha: float
    material_quantities: dict[str, float]
    total_tons: float
    estimated_cost_usd: float
    expected_results: dict[str, float]
    traditional_technique: str | None = None
    implementation_tips: list[str] = []


class OptimizeRequest(BaseModel):
    """Request for formulation optimization."""

    soil_code: str
    area_ha: float
    target_om_increase_pct: float = 3.0
    target_cn_ratio: float = 25.0
    budget_per_ha_usd: float | None = None
    required_materials: list[str] = []
    excluded_materials: list[str] = []


class CostBenefitRequest(BaseModel):
    """Request for cost-benefit analysis."""

    formulation: dict[str, float] = Field(..., description="{material_code: kg_per_ha}")
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
    recommendations: list[str]


class WaterSavingsRequest(BaseModel):
    """Request for water savings calculation."""

    formulation: dict[str, float]
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
    recommendations: list[str]


class ScaleRequest(BaseModel):
    """Request for scale calculation."""

    formulation: dict[str, float]
    area_ha: float


class ScaleResponse(BaseModel):
    """Response for scale calculation."""

    area_ha: float
    scale_category: str
    material_quantities: dict[str, dict[str, float]]
    total_tons: float
    total_cost_usd: float
    economies_of_scale_pct: float
    implementation_days: int
    equipment_needed: list[str]
    logistics_notes: list[str]


class FullAnalysisRequest(BaseModel):
    """Complete analysis request combining all calculators."""

    soil_code: str
    area_ha: float
    crop_type: str = "wheat"
    current_yield_t_ha: float = 2.0
    current_irrigation_m3_ha: float = 8000.0
    current_fertilizer_cost_usd_ha: float = 300.0
    budget_per_ha_usd: float | None = None


class FullAnalysisResponse(BaseModel):
    """Complete analysis response."""

    recommendation: RecommendResponse
    cost_benefit: CostBenefitResponse
    water_savings: WaterSavingsResponse
    scale: ScaleResponse
    overall_assessment: dict[str, Any]


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


def get_db():
    """Database session dependency."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health", response_model=HealthResponse)
def health_check(service: Annotated[Any, Depends(get_nojin_service)]):
    """
    Health check endpoint.

    Returns system status, database connectivity, and data counts.
    """
    health = service.health_check()
    return HealthResponse(**health)


@router.get("/statistics", response_model=StatisticsResponse)
def get_statistics(service: Annotated[Any, Depends(get_nojin_service)]):
    """
    Get comprehensive system statistics.

    Returns counts and averages for all Nojin entities.
    """
    stats = service.get_statistics()
    return StatisticsResponse(**stats)


@router.get("/materials", response_model=list[MaterialResponse])
def list_materials(
    service: Annotated[Any, Depends(get_nojin_service)],
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    arid_only: Annotated[bool, Query(description="Only arid-suitable materials")] = False,
    min_priority: Annotated[int, Query(ge=0, le=10, description="Minimum arid priority score")] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    """
    List all available materials.

    Materials include minerals, organic materials, biochar, manures, etc.
    Each has scientifically-documented properties.
    """
    try:
        materials = service.list_materials(category, arid_only, min_priority, limit)
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    return [MaterialResponse(**m) for m in materials]


@router.get("/materials/arid-priority", response_model=list[MaterialResponse])
def list_arid_priority_materials(
    service: Annotated[Any, Depends(get_nojin_service)],
    min_score: Annotated[int, Query(ge=1, le=10)] = 9,
):
    """
    List materials prioritized for arid regions.

    These materials are specifically selected for the 2.5 billion people
    living in arid and semi-arid regions.
    """
    try:
        materials = service.get_arid_priority_materials(min_score)
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    return [MaterialResponse(**m) for m in materials]


@router.get("/materials/{material_code}", response_model=MaterialResponse)
def get_material(material_code: str, service: Annotated[Any, Depends(get_nojin_service)]):
    """
    Get detailed information about a specific material.

    Example: /api/nojin/materials/MIN-011 (Zeolite)
    """
    try:
        material = service.get_material(material_code)
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    if not material:
        raise HTTPException(status_code=404, detail=f"Material '{material_code}' not found")
    return MaterialResponse(**material)


@router.get("/soils", response_model=list[SoilTypeResponse])
def list_soil_types(service: Annotated[Any, Depends(get_nojin_service)]):
    """List all soil types."""
    try:
        soils = service.list_soil_types()
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    return [SoilTypeResponse(**s) for s in soils]


@router.get("/soils/{soil_code}", response_model=SoilTypeResponse)
def get_soil_type(soil_code: str, service: Annotated[Any, Depends(get_nojin_service)]):
    """Get detailed information about a specific soil type."""
    try:
        soil = service.get_soil_type(soil_code)
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    if not soil:
        raise HTTPException(status_code=404, detail=f"Soil type '{soil_code}' not found")
    return SoilTypeResponse(**soil)


@router.post("/classify", response_model=SoilClassificationResponse)
async def classify_soil(
    request: SoilClassificationRequest,
    service: Annotated[Any, Depends(get_nojin_service)],
):
    """
    Classify soil type based on laboratory test results.

    Returns the best-matching soil type and recommended recipe.
    """
    result = service.classify_soil(
        ph=request.ph,
        ec_dsm=request.ec_dsm,
        om_pct=request.om_pct,
        texture=request.texture,
        region=request.region,
    )

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
        classified_as=result["classified_as"],
        soil_code=result["soil_code"],
        soil_name=result["soil_name"],
        confidence=result["confidence"],
        recommended_recipe=result["recommended_recipe"],
        warnings=warnings,
        next_steps=next_steps,
    )


@router.get("/recipes", response_model=list[RecipeResponse])
def list_recipes(
    service: Annotated[Any, Depends(get_nojin_service)],
    soil_code: str | None = None,
):
    """List all formulation recipes."""
    try:
        recipes = service.list_recipes(soil_code=soil_code)
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    return [RecipeResponse(**r) for r in recipes]


@router.get("/recipes/{recipe_code}", response_model=RecipeResponse)
def get_recipe(recipe_code: str, service: Annotated[Any, Depends(get_nojin_service)]):
    """Get detailed information about a specific recipe."""
    try:
        recipe = service.get_recipe(recipe_code)
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe '{recipe_code}' not found")
    return RecipeResponse(**recipe)


@router.post("/recommend", response_model=RecommendResponse)
def get_recommendation(
    request: RecommendRequest,
    service: Annotated[Any, Depends(get_nojin_service)],
):
    """
    Get Nojin recommendation for a specific soil type and area.

    Returns complete formulation with material quantities and expected results.
    """
    try:
        rec = service.recommend(
            soil_code=request.soil_code,
            area_ha=request.area_ha,
            budget_per_ha_usd=request.budget_per_ha_usd,
            crop_type=request.crop_type,
        )
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    return RecommendResponse(**rec)


@router.post("/scale", response_model=ScaleResponse)
async def calculate_scale(request: ScaleRequest):
    """
    Scale formulation to given area.

    Provides logistics, labor, equipment, and economies of scale.
    """
    from services._gateway_facade import MATERIALS, ScaleCalculator

    calc = ScaleCalculator(MATERIALS)
    result = calc.scale(
        formulation_per_ha=request.formulation,
        area_ha=request.area_ha,
    )
    return ScaleResponse(**result.__dict__) if hasattr(result, '__dict__') else ScaleResponse(**result)


@router.post("/optimize")
async def optimize_formulation(
    request: OptimizeRequest,
    service: Annotated[Any, Depends(get_nojin_service)],
):
    """
    Optimize formulation using Linear Programming.

    Finds the best material combination for the given soil and constraints.
    """
    try:
        result = service.optimize(
            soil_code=request.soil_code,
            area_ha=request.area_ha,
            target_om_increase_pct=request.target_om_increase_pct,
            target_cn_ratio=request.target_cn_ratio,
            budget_per_ha_usd=request.budget_per_ha_usd,
            required_materials=request.required_materials,
            excluded_materials=request.excluded_materials,
        )
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    if not result:
        raise HTTPException(status_code=404, detail=f"No optimal formulation found for soil type '{request.soil_code}'")
    return result


@router.post("/cost-benefit", response_model=CostBenefitResponse)
async def analyze_cost_benefit(
    request: CostBenefitRequest,
    service: Annotated[Any, Depends(get_nojin_service)],
):
    """
    Perform scientific cost-benefit analysis.

    Uses FAO/World Bank methodologies for:
    - ROI calculation
    - Payback period (simple + discounted)
    - NPV (Net Present Value)
    - IRR (Internal Rate of Return)
    - BCR (Benefit-Cost Ratio)
    """
    try:
        cb = service.cost_benefit(
            formulation=request.formulation,
            area_ha=request.area_ha,
            crop_type=request.crop_type,
            current_yield_t_ha=request.current_yield_t_ha,
            current_irrigation_m3_ha=request.current_irrigation_m3_ha,
            current_fertilizer_cost_usd_ha=request.current_fertilizer_cost_usd_ha,
        )
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    return CostBenefitResponse(**cb)


@router.post("/water-savings", response_model=WaterSavingsResponse)
async def calculate_water_savings(
    request: WaterSavingsRequest,
    service: Annotated[Any, Depends(get_nojin_service)],
):
    """
    Calculate water savings using FAO-56 principles.

    Considers:
    - Evaporation reduction
    - Water retention improvement
    - Infiltration enhancement
    """
    try:
        ws = service.water_savings(
            formulation=request.formulation,
            area_ha=request.area_ha,
            baseline_irrigation_m3_ha=request.baseline_irrigation_m3_ha,
        )
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    return WaterSavingsResponse(**ws)


@router.post("/full-analysis", response_model=FullAnalysisResponse)
def full_analysis(
    request: FullAnalysisRequest,
    service: Annotated[Any, Depends(get_nojin_service)],
):
    """
    Complete analysis combining all calculators.

    This is the main endpoint that provides:
    - Recommendation (material quantities)
    - Cost-benefit analysis (ROI, NPV, IRR)
    - Water savings calculation
    - Scale calculation (logistics)
    - Overall assessment
    """
    try:
        result = service.full_analysis(
            soil_code=request.soil_code,
            area_ha=request.area_ha,
            crop_type=request.crop_type,
            current_yield_t_ha=request.current_yield_t_ha,
            current_irrigation_m3_ha=request.current_irrigation_m3_ha,
            current_fertilizer_cost_usd_ha=request.current_fertilizer_cost_usd_ha,
            budget_per_ha_usd=request.budget_per_ha_usd,
        )
    except RuntimeError as exc:
        raise _handle_data_unavailable(exc)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"No recipe found for soil type '{request.soil_code}'"
        )

    rec_data = result["recommendation"]
    cb_data = result["cost_benefit"]
    ws_data = result["water_savings"]
    scale_data = result["scale"]
    assessment = result["overall_assessment"]

    return FullAnalysisResponse(
        recommendation=RecommendResponse(**rec_data),
        cost_benefit=CostBenefitResponse(**cb_data),
        water_savings=WaterSavingsResponse(**ws_data),
        scale=ScaleResponse(**scale_data.__dict__) if hasattr(scale_data, '__dict__') else ScaleResponse(**scale_data),
        overall_assessment=assessment,
    )


__all__ = ["router"]
