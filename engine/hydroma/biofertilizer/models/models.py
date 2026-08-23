"""
Nojin Biofertilizer - SQLAlchemy Models
=======================================
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class NojinStrain(Base):
    """Repository of bacterial strains."""
    __tablename__ = "nojin_strains"
    
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
    """Product formulations."""
    __tablename__ = "nojin_formulations"
    
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
    """Application plans."""
    __tablename__ = "nojin_application_plans"
    
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
    """Field trial records."""
    __tablename__ = "nojin_field_trials"
    
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
    """Calibration history."""
    __tablename__ = "nojin_calibration_records"
    
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