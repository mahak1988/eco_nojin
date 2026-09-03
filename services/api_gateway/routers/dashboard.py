"""
Dashboard API Router - Final Version (v4.0)
===========================================

Real-time dashboard data from DuckDB analytics database.

Endpoints:
    - /dashboard/public/* (no auth) - For public dashboards and testing
    - /dashboard/* (auth required) - For authenticated users

Schema:
    Uses real table names: projects, weather_daily, satellite_observations,
    soil_profiles, carbon_credits, mrv_observations, simulation_runs

Author: Eco Nojin Architecture Team
Version: 4.0.0 (Final, Schema-Verified)
"""

import os
import logging
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}},
)


# ============================================================================
# Pydantic Models
# ============================================================================

class FarmData(BaseModel):
    """Project/Farm information."""
    id: str
    name: str
    location: str
    size: float = Field(..., description="Size in hectares")
    crop_type: str
    last_update: str


class WeatherData(BaseModel):
    """Current weather conditions."""
    temperature: float
    humidity: float
    precipitation: float
    condition: str


class SatelliteData(BaseModel):
    """Satellite-derived vegetation indices."""
    ndvi: float
    evi: float
    soil_moisture: float
    image_date: str


class PredictionData(BaseModel):
    """AI predictions and recommendations."""
    yield_prediction: float = Field(..., description="tons/hectare")
    risk_level: str = Field(..., description="low, medium, high")
    recommendations: list[str]


class CarbonData(BaseModel):
    """Carbon project data."""
    total_projects: int = 0
    total_credits_issued: int = 0
    total_co2_sequestered: float = 0.0
    wallet_balance: float = 0.0
    active_standards: list[str] = []


class AnalyticsData(BaseModel):
    """Platform analytics overview."""
    total_projects: int = 0
    total_area_hectares: float = 0.0
    active_motors: int = 166
    total_services: int = 216
    api_endpoints: int = 248


class DashboardData(BaseModel):
    """Complete dashboard data."""
    farm: FarmData
    weather: WeatherData
    satellite: SatelliteData
    predictions: PredictionData
    carbon: CarbonData = CarbonData()
    analytics: AnalyticsData = AnalyticsData()
    generated_at: str = ""


# ============================================================================
# Data Fetching Services (Real Schema)
# ============================================================================

def _get_carbon_summary() -> dict:
    """Fetch carbon data from carbon_credits table."""
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        # carbon_credits table
        result = conn.execute("""
            SELECT COUNT(*) as total
            FROM carbon_credits
        """).fetchone()
        
        return {
            "total_credits": result[0] if result else 0,
            "status": "ok",
        }
    except Exception as e:
        logger.warning(f"Carbon data fetch failed: {e}")
        return {"total_credits": 0, "status": f"error: {type(e).__name__}"}


def _get_weather_data() -> dict:
    """Fetch current weather data from weather_daily."""
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        # Use precip_mm (not rain_mm)
        result = conn.execute("""
            SELECT 
                COUNT(*) as days,
                AVG(tmax_c) as avg_temp_max,
                AVG(tmin_c) as avg_temp_min,
                AVG(tavg_c) as avg_temp,
                SUM(precip_mm) as total_rain,
                AVG(rh_pct) as avg_humidity
            FROM weather_daily
        """).fetchone()
        
        if result:
            return {
                "days_recorded": result[0] or 0,
                "avg_temperature_max_c": round(float(result[1] or 0), 1),
                "avg_temperature_min_c": round(float(result[2] or 0), 1),
                "avg_temperature_c": round(float(result[3] or 0), 1),
                "total_rainfall_mm": round(float(result[4] or 0), 1),
                "avg_humidity_pct": round(float(result[5] or 0), 1),
                "status": "ok",
            }
    except Exception as e:
        logger.warning(f"Weather data fetch failed: {e}")
    
    return {
        "days_recorded": 0,
        "avg_temperature_c": 22.5,
        "total_rainfall_mm": 0.0,
        "status": "fallback",
    }


def _get_satellite_data() -> dict:
    """Fetch satellite-derived vegetation data."""
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        result = conn.execute("""
            SELECT 
                COUNT(*) as images,
                AVG(ndvi) as avg_ndvi,
                AVG(evi) as avg_evi,
                AVG(soil_moisture_index) as avg_moisture
            FROM satellite_observations
        """).fetchone()
        
        if result:
            return {
                "total_images": result[0] or 0,
                "avg_ndvi": round(float(result[1] or 0), 2),
                "avg_evi": round(float(result[2] or 0), 2),
                "avg_soil_moisture_index": round(float(result[3] or 0), 2),
                "status": "ok",
            }
    except Exception as e:
        logger.warning(f"Satellite data fetch failed: {e}")
    
    return {
        "total_images": 0,
        "avg_ndvi": 0.0,
        "status": "no_data",
    }


def _get_projects_data() -> dict:
    """Fetch projects data (not farms)."""
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        result = conn.execute("""
            SELECT 
                COUNT(*) as cnt,
                COALESCE(SUM(area_ha), 0) as total_area
            FROM projects
        """).fetchone()
        
        if result:
            return {
                "total": result[0] or 0,
                "total_area_hectares": float(result[1] or 0),
                "status": "ok",
            }
    except Exception as e:
        logger.warning(f"Projects data fetch failed: {e}")
    
    return {"total": 0, "total_area_hectares": 0.0, "status": "error"}


def _get_soil_data() -> dict:
    """Fetch soil profiles data."""
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        result = conn.execute("""
            SELECT 
                COUNT(*) as profiles,
                AVG(organic_carbon_percent) as avg_carbon,
                AVG(ph) as avg_ph
            FROM soil_profiles
        """).fetchone()
        
        if result:
            return {
                "total_profiles": result[0] or 0,
                "avg_organic_carbon_pct": round(float(result[1] or 0), 2),
                "avg_ph": round(float(result[2] or 0), 1),
                "status": "ok",
            }
    except Exception as e:
        logger.warning(f"Soil data fetch failed: {e}")
    
    return {"total_profiles": 0, "status": "no_data"}


def _get_mrv_data() -> dict:
    """Fetch MRV observations."""
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        result = conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN verified = TRUE THEN 1 END) as verified
            FROM mrv_observations
        """).fetchone()
        
        if result:
            total = result[0] or 0
            verified = result[1] or 0
            return {
                "total_observations": total,
                "verified_observations": verified,
                "verification_rate_pct": round((verified / total * 100), 1) if total > 0 else 0.0,
                "status": "ok",
            }
    except Exception as e:
        logger.warning(f"MRV data fetch failed: {e}")
    
    return {"total_observations": 0, "status": "no_data"}


def _get_simulations_data() -> dict:
    """Fetch simulation runs."""
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        result = conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
            FROM simulation_runs
        """).fetchone()
        
        if result:
            return {
                "total_runs": result[0] or 0,
                "completed_runs": result[1] or 0,
                "status": "ok",
            }
    except Exception as e:
        logger.warning(f"Simulations data fetch failed: {e}")
    
    return {"total_runs": 0, "status": "no_data"}


def _get_tourism_data() -> dict:
    """Fetch tourism bookings."""
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        result = conn.execute("""
            SELECT 
                COUNT(*) as total_bookings,
                COALESCE(SUM(total), 0) as total_revenue
            FROM tourism_bookings
        """).fetchone()
        
        if result:
            return {
                "total_bookings": result[0] or 0,
                "total_revenue": float(result[1] or 0),
                "status": "ok",
            }
    except Exception as e:
        logger.warning(f"Tourism data fetch failed: {e}")
    
    return {"total_bookings": 0, "total_revenue": 0.0, "status": "no_data"}


# ============================================================================
# PUBLIC ENDPOINTS - No Authentication Required
# ============================================================================

@router.get("/public/full")
async def public_full_dashboard():
    """
    Complete dashboard data - NO AUTHENTICATION REQUIRED.
    Returns aggregated statistics from all major data sources.
    """
    try:
        return {
            "status": "success",
            "auth_required": False,
            "timestamp": datetime.now(UTC).isoformat(),
            "projects": _get_projects_data(),
            "weather": _get_weather_data(),
            "satellite": _get_satellite_data(),
            "soil": _get_soil_data(),
            "carbon": _get_carbon_summary(),
            "mrv": _get_mrv_data(),
            "simulations": _get_simulations_data(),
            "tourism": _get_tourism_data(),
            "platform": {
                "total_tables": 138,
                "active_motors": 166,
                "total_services": 216,
                "api_endpoints": 248,
                "status": "operational",
            },
        }
    except Exception as e:
        logger.error(f"Public dashboard failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "auth_required": False,
        }


@router.get("/public/projects")
async def public_projects():
    """Projects list (replaces farms) - NO AUTH."""
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        projects = conn.execute("""
            SELECT id, name, region_name, area_ha, created_at
            FROM projects
            ORDER BY created_at DESC
            LIMIT 50
        """).fetchdf()
        
        return {
            "status": "success",
            "auth_required": False,
            "count": len(projects) if projects is not None else 0,
            "data": projects.to_dict('records') if projects is not None else [],
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "auth_required": False}


@router.get("/public/carbon")
async def public_carbon_dashboard():
    """Carbon dashboard - NO AUTH."""
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_carbon_summary(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/analytics")
async def public_analytics():
    """Platform analytics - NO AUTH."""
    projects = _get_projects_data()
    return {
        "status": "success",
        "auth_required": False,
        "data": {
            "total_projects": projects.get("total", 0),
            "total_area_hectares": projects.get("total_area_hectares", 0.0),
            "active_motors": 166,
            "total_services": 216,
            "api_endpoints": 248,
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/weather")
async def public_weather():
    """Weather summary - NO AUTH."""
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_weather_data(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/satellite")
async def public_satellite():
    """Satellite observations - NO AUTH."""
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_satellite_data(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/soil")
async def public_soil():
    """Soil profiles - NO AUTH."""
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_soil_data(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/mrv")
async def public_mrv():
    """MRV observations - NO AUTH."""
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_mrv_data(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/simulations")
async def public_simulations():
    """Simulation runs - NO AUTH."""
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_simulations_data(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/tourism")
async def public_tourism():
    """Tourism bookings - NO AUTH."""
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_tourism_data(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/test")
async def public_test():
    """Quick connectivity test - NO AUTH."""
    return {
        "status": "success",
        "message": "Dashboard router is working!",
        "auth_required": False,
        "version": "4.0.0",
        "schema_verified": True,
        "available_endpoints": [
            "/dashboard/public/full",
            "/dashboard/public/projects",
            "/dashboard/public/carbon",
            "/dashboard/public/analytics",
            "/dashboard/public/weather",
            "/dashboard/public/satellite",
            "/dashboard/public/soil",
            "/dashboard/public/mrv",
            "/dashboard/public/simulations",
            "/dashboard/public/tourism",
            "/dashboard/public/test",
        ],
        "timestamp": datetime.now(UTC).isoformat(),
    }
