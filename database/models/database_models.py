"""Database models for new analyses and designs."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from database.models import Base # Assuming base is defined in database/base.py
import json
from datetime import datetime, timezone

# --- Topography ---
class TopographyAnalysisResult(Base):
    __tablename__ = 'topography_analysis_results'
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String, index=True)
    dem_path = Column(String)
    analysis_types = Column(Text) # Store as JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    slope_map_path = Column(String)
    aspect_map_path = Column(String)
    curvature_map_path = Column(String)
    flow_direction_map_path = Column(String)
    flow_accumulation_map_path = Column(String)

# --- Runoff ---
class RunoffCalculationResult(Base):
    __tablename__ = 'runoff_calculation_results'
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String, index=True)
    precipitation_mm = Column(Float)
    curve_number = Column(Float)
    area_ha = Column(Float)
    method = Column(String)
    volume_m3 = Column(Float)
    peak_flow_m3s = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# --- Groundwater ---
class GroundwaterModelResult(Base):
    __tablename__ = 'groundwater_model_results'
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String, index=True)
    model_type = Column(String)
    transmissivity_m2day = Column(Float)
    storativity = Column(Float)
    pumping_rate_m3day = Column(Float)
    observation_distance_m = Column(Float)
    time_days = Column(Float)
    drawdown_m = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# --- Crop Water Requirement ---
class CropWaterReqResult(Base):
    __tablename__ = 'crop_water_req_results'
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String, index=True)
    crop_type = Column(String)
    planting_date = Column(DateTime)
    harvest_date = Column(DateTime)
    seasonal_water_requirement_mm = Column(Float)
    daily_et_crop_data = Column(Text) # Store as JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# --- Structure Design ---
class StructureDesignResult(Base):
    __tablename__ = 'structure_design_results'
    id = Column(Integer, primary_key=True, index=True)
    design_id = Column(String, unique=True, index=True)
    site_location_lat = Column(Float)
    site_location_lon = Column(Float)
    structure_type = Column(String)
    area_ha = Column(Float)
    max_flow_m3s = Column(Float)
    geometry_geojson = Column(Text) # Store GeoJSON as text
    material_estimate = Column(Text) # Store as JSON string
    cost_estimate_usd = Column(Float)
    design_summary = Column(Text) # Store as JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# --- Irrigation Design ---
class IrrigationDesignResult(Base):
    __tablename__ = 'irrigation_design_results'
    id = Column(Integer, primary_key=True, index=True)
    design_id = Column(String, unique=True, index=True)
    site_location_lat = Column(Float)
    site_location_lon = Column(Float)
    crop_type = Column(String)
    area_ha = Column(Float)
    irrigation_type = Column(String)
    layout_geojson = Column(Text) # Store GeoJSON as text
    equipment_list = Column(Text) # Store as JSON string
    irrigation_schedule = Column(Text) # Store as JSON string
    design_summary = Column(Text) # Store as JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# --- Calibration ---
class CalibrationResult(Base):
    __tablename__ = 'calibration_results'
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)
    site_id = Column(String, index=True)
    calibrated_parameters = Column(Text) # Store as JSON string
    best_objective_value = Column(Float)
    history = Column(Text) # Store as JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
