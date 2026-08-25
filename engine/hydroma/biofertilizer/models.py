"""
Nojin Biofertilizer - Complete Database Schema
===============================================
Merges:
- Phase 1: 5 core models (Strain, Formulation, ApplicationPlan, FieldTrial, CalibrationRecord)
- Phase 2: 7 extended models (Material, SoilType, Recipe, Composition, Guide, CostBenefit, WaterSaving)

Total: 12 SQLAlchemy models
"""

import logging
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

logger = logging.getLogger(__name__)

# Robust Base import with fallback
try:
    from database.base import Base
except ImportError as e:
    logger.warning(f"Could not import Base from database: {e}")
    try:
        from sqlalchemy.orm import declarative_base
        Base = declarative_base()
    except ImportError:
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()


# ═══════════════════════════════════════════════════════════════════
# PHASE 1: CORE MODELS (5 tables)
# ═══════════════════════════════════════════════════════════════════

class NojinStrain(Base):
    """Repository of bacterial strains (Phase 1)."""
    __tablename__ = "nojin_strains"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strain_code = Column(String(50), unique=True, nullable=False)
    species_name = Column(String(200), nullable=False)
    strain_type = Column(String(50), nullable=False)
    function = Column(Text, nullable=False)
    source = Column(Text)
    isolation_location = Column(Text)
    isolation_date = Column(Date)
    genetic_markers = Column(Text)
    biosafety_level = Column(Integer, default=1)
    efficacy_data = Column(Text)
    compatibility_data = Column(Text)
    storage_conditions = Column(Text)
    is_proprietary = Column(Boolean, default=True)
    patent_number = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NojinStrain(code={self.strain_code}, species={self.species_name})>"


class NojinFormulation(Base):
    """Product formulations (Phase 1)."""
    __tablename__ = "nojin_formulations"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    formulation_code = Column(String(50), unique=True, nullable=False)
    commercial_name = Column(String(200), nullable=False)
    carrier_material = Column(String(200))
    formulation_type = Column(String(50), nullable=False)
    application_method = Column(String(100), nullable=False)
    dosage_kg_ha = Column(Float)
    target_crops = Column(Text)
    target_soil_types = Column(Text)
    target_climates = Column(Text)
    efficacy_data = Column(Text)
    compatibility_notes = Column(Text)
    storage_conditions = Column(Text)
    shelf_life_days = Column(Integer)
    is_proprietary = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NojinFormulation(code={self.formulation_code}, name={self.commercial_name})>"


class NojinApplicationPlan(Base):
    """Application plans (Phase 1)."""
    __tablename__ = "nojin_application_plans"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    formulation_id = Column(Integer, ForeignKey("nojin_formulations.id"), nullable=False)
    land_profile_id = Column(Integer, ForeignKey("land_profiles.id"))
    crop_type = Column(String(100), nullable=False)
    application_date = Column(Date, nullable=False)
    application_method = Column(String(100), nullable=False)
    dosage_kg_ha = Column(Float, nullable=False)
    expected_yield_response = Column(Float)
    expected_soil_improvement = Column(Text)
    risk_assessment = Column(Text)
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<NojinApplicationPlan(id={self.id}, crop={self.crop_type})>"


class NojinFieldTrial(Base):
    """Field trial records (Phase 1)."""
    __tablename__ = "nojin_field_trials"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    application_plan_id = Column(Integer, ForeignKey("nojin_application_plans.id"))
    trial_location = Column(Text, nullable=False)
    trial_date = Column(Date, nullable=False)
    crop_type = Column(String(100), nullable=False)
    plot_area_ha = Column(Float)
    treatment_design = Column(Text)
    baseline_data = Column(Text)
    post_application_data = Column(Text)
    yield_response = Column(Float)
    soil_improvement = Column(Text)
    observations = Column(Text)
    statistical_analysis = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<NojinFieldTrial(id={self.id}, location={self.trial_location})>"


class NojinCalibrationRecord(Base):
    """Calibration history (Phase 1)."""
    __tablename__ = "nojin_calibration_records"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    formulation_id = Column(Integer, ForeignKey("nojin_formulations.id"), nullable=False)
    calibration_date = Column(Date, nullable=False)
    calibration_data = Column(Text, nullable=False)
    model_version = Column(String(50), nullable=False)
    parameters_updated = Column(Text)
    validation_results = Column(Text)
    calibration_quality_score = Column(Float)
    calibrated_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<NojinCalibrationRecord(id={self.id}, formulation={self.formulation_id})>"


# ═══════════════════════════════════════════════════════════════════
# PHASE 2: EXTENDED MODELS (7 tables)
# ═══════════════════════════════════════════════════════════════════

class NojinMaterial(Base):
    """Comprehensive material profile with 30+ scientific parameters (Phase 2)."""
    __tablename__ = "nojin_materials"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_code = Column(String(50), unique=True, nullable=False, index=True)
    common_name = Column(String(200), nullable=False)
    scientific_name = Column(String(200))
    category = Column(String(50), nullable=False)
    
    # Nutritional composition
    nitrogen_pct = Column(Float, default=0)
    phosphorus_pct = Column(Float, default=0)
    potassium_pct = Column(Float, default=0)
    calcium_pct = Column(Float, default=0)
    magnesium_pct = Column(Float, default=0)
    sulfur_pct = Column(Float, default=0)
    carbon_pct = Column(Float, default=0)
    organic_matter_pct = Column(Float, default=0)
    
    # Physical properties
    cn_ratio = Column(Float)
    ph = Column(Float)
    ec_dsm_m = Column(Float)
    cec_cmol_kg = Column(Float)
    bulk_density_kg_m3 = Column(Float)
    water_retention_pct = Column(Float)
    porosity_pct = Column(Float)
    surface_area_m2_g = Column(Float)
    
    # Application properties
    release_rate = Column(String(20))
    persistence_years = Column(Float)
    application_rate_kg_ha_min = Column(Float)
    application_rate_kg_ha_max = Column(Float)
    optimal_application_method = Column(String(100))
    
    # Economic
    cost_per_ton_usd = Column(Float)
    availability = Column(String(50))
    source_regions = Column(Text)
    
    # Risk
    overuse_risks = Column(Text)
    incompatibilities = Column(Text)
    safety_notes = Column(Text)
    
    # Scientific metadata
    historical_use = Column(Text)
    modern_research = Column(Text)
    benefits = Column(Text)
    limitations = Column(Text)
    
    # Classification
    is_proprietary = Column(Boolean, default=False)
    is_locally_available = Column(Boolean, default=True)
    is_suitable_for_arid = Column(Boolean, default=False)
    arid_priority_score = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NojinMaterial(code={self.material_code}, name={self.common_name})>"


class NojinSoilType(Base):
    """Soil type classification (Phase 2)."""
    __tablename__ = "nojin_soil_types"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    soil_code = Column(String(50), unique=True, nullable=False, index=True)
    soil_name = Column(String(200), nullable=False)
    soil_category = Column(String(50))
    texture = Column(String(50))
    typical_ph_min = Column(Float)
    typical_ph_max = Column(Float)
    typical_om_pct = Column(Float)
    typical_cec_cmol_kg = Column(Float)
    water_holding_capacity = Column(String(50))
    drainage = Column(String(50))
    common_problems = Column(Text)
    nutrient_deficiencies = Column(Text)
    common_regions = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<NojinSoilType(code={self.soil_code}, name={self.soil_name})>"


class NojinFormulationRecipe(Base):
    """Specific formulation for each soil type (Phase 2)."""
    __tablename__ = "nojin_formulation_recipes"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_code = Column(String(50), unique=True, nullable=False, index=True)
    recipe_name = Column(String(200), nullable=False)
    soil_type_id = Column(Integer, ForeignKey("nojin_soil_types.id"), nullable=False)
    area_min_ha = Column(Float, default=0.1)
    area_max_ha = Column(Float, default=1000.0)
    material_composition = Column(JSON, nullable=False)
    total_kg_per_ha = Column(Float)
    estimated_cost_usd_per_ha = Column(Float)
    cn_ratio_final = Column(Float)
    om_increase_pct = Column(Float)
    water_saving_pct = Column(Float)
    yield_increase_pct = Column(Float)
    restoration_years = Column(Float)
    application_timing = Column(Text)
    application_method = Column(Text)
    frequency_per_year = Column(Integer)
    traditional_technique = Column(String(100))
    integration_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<NojinFormulationRecipe(code={self.recipe_code})>"


class NojinMaterialComposition(Base):
    """Detailed chemical composition (Phase 2)."""
    __tablename__ = "nojin_material_composition"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("nojin_materials.id"), nullable=False)
    n_total_pct = Column(Float)
    n_organic_pct = Column(Float)
    n_ammonium_pct = Column(Float)
    n_nitrate_pct = Column(Float)
    p2o5_total_pct = Column(Float)
    p_available_pct = Column(Float)
    k2o_total_pct = Column(Float)
    k_available_pct = Column(Float)
    ca_pct = Column(Float)
    mg_pct = Column(Float)
    s_pct = Column(Float)
    fe_ppm = Column(Float)
    mn_ppm = Column(Float)
    zn_ppm = Column(Float)
    cu_ppm = Column(Float)
    b_ppm = Column(Float)
    mo_ppm = Column(Float)
    co_ppm = Column(Float)
    ni_ppm = Column(Float)
    humic_acid_pct = Column(Float)
    fulvic_acid_pct = Column(Float)
    amino_acids_pct = Column(Float)
    analysis_date = Column(Date)
    analysis_method = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NojinApplicationGuide(Base):
    """Application guidance (Phase 2)."""
    __tablename__ = "nojin_application_guides"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("nojin_materials.id"), nullable=False)
    season_recommended = Column(String(50))
    soil_moisture_required = Column(String(50))
    temperature_range_c = Column(String(50))
    application_methods = Column(Text)
    incorporation_depth_cm = Column(Float)
    compatible_materials = Column(Text)
    incompatible_materials = Column(Text)
    compatible_crops = Column(Text)
    ppe_required = Column(Text)
    waiting_days_before_planting = Column(Integer)
    waiting_days_before_harvest = Column(Integer)
    storage_conditions = Column(Text)
    shelf_life_days = Column(Integer)
    traditional_application = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NojinCostBenefit(Base):
    """Cost-benefit analysis (Phase 2)."""
    __tablename__ = "nojin_cost_benefit"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    entity_code = Column(String(50))
    material_cost_usd = Column(Float)
    labor_cost_usd = Column(Float)
    equipment_cost_usd = Column(Float)
    total_cost_usd = Column(Float)
    yield_increase_value_usd = Column(Float)
    water_saving_value_usd = Column(Float)
    fertilizer_saving_value_usd = Column(Float)
    carbon_credit_value_usd = Column(Float)
    total_benefit_usd = Column(Float)
    roi_years = Column(Float)
    roi_percentage = Column(Float)
    payback_period_months = Column(Integer)
    suitable_for_smallholder = Column(Boolean)
    suitable_for_subsistence = Column(Boolean)
    suitable_for_commercial = Column(Boolean)
    region_specific = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NojinWaterSaving(Base):
    """Water-saving calculations (Phase 2)."""
    __tablename__ = "nojin_water_saving"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    entity_code = Column(String(50))
    evaporation_reduction_pct = Column(Float)
    water_retention_increase_pct = Column(Float)
    irrigation_reduction_pct = Column(Float)
    soil_temperature_reduction_c = Column(Float)
    water_saved_m3_per_ha_year = Column(Float)
    drought_resistance_improvement = Column(String(50))
    co2_sequestration_t_ha_year = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "Base",
    # Phase 1 (5 models)
    "NojinStrain",
    "NojinFormulation",
    "NojinApplicationPlan",
    "NojinFieldTrial",
    "NojinCalibrationRecord",
    # Phase 2 (7 models)
    "NojinMaterial",
    "NojinSoilType",
    "NojinFormulationRecipe",
    "NojinMaterialComposition",
    "NojinApplicationGuide",
    "NojinCostBenefit",
    "NojinWaterSaving",
]
