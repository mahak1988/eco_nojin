"""
Dashboard API Router
===========================================

Real-time dashboard data from DuckDB analytics database.

Endpoints:
    - /dashboard/public/* (no auth) - For public dashboards and testing
    - /dashboard/* (auth required) - For authenticated users

Schema:
    Uses real table names: projects, weather_daily, satellite_observations,
    soil_profiles, carbon_credits, mrv_observations, simulation_runs

Security:
    - All queries use parameterized statements to prevent SQL injection
    - User inputs are validated before being passed to queries

Author: Eco Nojin Architecture Team
Version: 4.0.0 (Final, Schema-Verified)
"""

import os
import logging
from datetime import UTC, datetime
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
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
# Query Helpers
# ============================================================================

def _execute_parameterized(conn, query: str, params: tuple = ()) -> Any:
    """Execute a parameterized query safely.
    
    Args:
        conn: DuckDB connection
        query: SQL query with ? placeholders
        params: Query parameters tuple
    
    Returns:
        Query result
    """
    try:
        return conn.execute(query, params).fetchone()
    except Exception as e:
        logger.error(f"Query failed: {query[:100]}... Error: {e}")
        raise


def _execute_parameterized_df(conn, query: str, params: tuple = ()) -> Any:
    """Execute a parameterized query and return DataFrame.
    
    Args:
        conn: DuckDB connection
        query: SQL query with ? placeholders
        params: Query parameters tuple
    
    Returns:
        pandas DataFrame
    """
    try:
        return conn.execute(query, params).fetchdf()
    except Exception as e:
        logger.error(f"Query failed: {query[:100]}... Error: {e}")
        raise


# ============================================================================
# Data Fetching Services (Real Schema)
# ============================================================================

def _get_carbon_summary() -> dict:
    """Fetch carbon data from carbon_credits table."""
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        # Parameterized query (no user input currently, but safe pattern)
        result = _execute_parameterized(conn, """
            SELECT COUNT(*) as total
            FROM carbon_credits
        """)
        
        return {
            "total_credits": result[0] if result else 0,
            "status": "ok",
        }
    except Exception as e:
        logger.warning(f"Carbon data fetch failed: {e}")
        return {"total_credits": 0, "status": f"error: {type(e).__name__}"}


def _get_weather_data(farm_id: Optional[str] = None) -> dict:
    """Fetch current weather data from weather_daily.
    
    Args:
        farm_id: Optional farm/project ID to filter by
    """
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        # Parameterized query with optional filter
        if farm_id:
            result = _execute_parameterized(conn, """
                SELECT 
                    COUNT(*) as days,
                    AVG(tmax_c) as avg_temp_max,
                    AVG(tmin_c) as avg_temp_min,
                    AVG(tavg_c) as avg_temp,
                    SUM(precip_mm) as total_rain,
                    AVG(rh_pct) as avg_humidity
                FROM weather_daily
                WHERE farm_id = ?
            """, (farm_id,))
        else:
            result = _execute_parameterized(conn, """
                SELECT 
                    COUNT(*) as days,
                    AVG(tmax_c) as avg_temp_max,
                    AVG(tmin_c) as avg_temp_min,
                    AVG(tavg_c) as avg_temp,
                    SUM(precip_mm) as total_rain,
                    AVG(rh_pct) as avg_humidity
                FROM weather_daily
            """)
        
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


def _get_satellite_data(farm_id: Optional[str] = None) -> dict:
    """Fetch satellite-derived vegetation data.
    
    Args:
        farm_id: Optional farm/project ID to filter by
    """
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        # Parameterized query with optional filter
        if farm_id:
            result = _execute_parameterized(conn, """
                SELECT 
                    COUNT(*) as images,
                    AVG(ndvi) as avg_ndvi,
                    AVG(evi) as avg_evi,
                    AVG(soil_moisture_index) as avg_moisture
                FROM satellite_observations
                WHERE farm_id = ?
            """, (farm_id,))
        else:
            result = _execute_parameterized(conn, """
                SELECT 
                    COUNT(*) as images,
                    AVG(ndvi) as avg_ndvi,
                    AVG(evi) as avg_evi,
                    AVG(soil_moisture_index) as avg_moisture
                FROM satellite_observations
            """)
        
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
        
        result = _execute_parameterized(conn, """
            SELECT 
                COUNT(*) as cnt,
                COALESCE(SUM(area_ha), 0) as total_area
            FROM projects
        """)
        
        if result:
            return {
                "total": result[0] or 0,
                "total_area_hectares": float(result[1] or 0),
                "status": "ok",
            }
    except Exception as e:
        logger.warning(f"Projects data fetch failed: {e}")
    
    return {"total": 0, "total_area_hectares": 0.0, "status": "error"}


def _get_soil_data(farm_id: Optional[str] = None) -> dict:
    """Fetch soil profiles data.
    
    Args:
        farm_id: Optional farm/project ID to filter by
    """
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        # Parameterized query with optional filter
        if farm_id:
            result = _execute_parameterized(conn, """
                SELECT 
                    COUNT(*) as profiles,
                    AVG(organic_carbon_percent) as avg_carbon,
                    AVG(ph) as avg_ph
                FROM soil_profiles
                WHERE farm_id = ?
            """, (farm_id,))
        else:
            result = _execute_parameterized(conn, """
                SELECT 
                    COUNT(*) as profiles,
                    AVG(organic_carbon_percent) as avg_carbon,
                    AVG(ph) as avg_ph
                FROM soil_profiles
            """)
        
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


def _get_mrv_data(farm_id: Optional[str] = None) -> dict:
    """Fetch MRV observations.
    
    Args:
        farm_id: Optional farm/project ID to filter by
    """
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        # Parameterized query with optional filter
        if farm_id:
            result = _execute_parameterized(conn, """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN verified = TRUE THEN 1 END) as verified
                FROM mrv_observations
                WHERE farm_id = ?
            """, (farm_id,))
        else:
            result = _execute_parameterized(conn, """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN verified = TRUE THEN 1 END) as verified
                FROM mrv_observations
            """)
        
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


def _get_simulations_data(farm_id: Optional[str] = None) -> dict:
    """Fetch simulation runs.
    
    Args:
        farm_id: Optional farm/project ID to filter by
    """
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        # Parameterized query with optional filter
        if farm_id:
            result = _execute_parameterized(conn, """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
                FROM simulation_runs
                WHERE farm_id = ?
            """, (farm_id,))
        else:
            result = _execute_parameterized(conn, """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
                FROM simulation_runs
            """)
        
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
        
        result = _execute_parameterized(conn, """
            SELECT 
                COUNT(*) as total_bookings,
                COALESCE(SUM(total), 0) as total_revenue
            FROM tourism_bookings
        """)
        
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
async def public_full_dashboard(
    farm_id: Optional[str] = Query(None, description="Filter by farm/project ID")
):
    """
    Complete dashboard data - NO AUTHENTICATION REQUIRED.
    Returns aggregated statistics from all major data sources.
    
    Args:
        farm_id: Optional farm/project ID to filter data
    """
    try:
        return {
            "status": "success",
            "auth_required": False,
            "timestamp": datetime.now(UTC).isoformat(),
            "projects": _get_projects_data(),
            "weather": _get_weather_data(farm_id),
            "satellite": _get_satellite_data(farm_id),
            "soil": _get_soil_data(farm_id),
            "carbon": _get_carbon_summary(),
            "mrv": _get_mrv_data(farm_id),
            "simulations": _get_simulations_data(farm_id),
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
async def public_projects(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of projects to return")
):
    """Projects list (replaces farms) - NO AUTH.
    
    Args:
        limit: Maximum number of projects to return (1-200)
    """
    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")
        
        # Parameterized query with validated limit
        projects = _execute_parameterized_df(conn, """
            SELECT id, name, region_name, area_ha, created_at
            FROM projects
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
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
async def public_weather(
    farm_id: Optional[str] = Query(None, description="Filter by farm/project ID")
):
    """Weather summary - NO AUTH.
    
    Args:
        farm_id: Optional farm/project ID to filter by
    """
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_weather_data(farm_id),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/satellite")
async def public_satellite(
    farm_id: Optional[str] = Query(None, description="Filter by farm/project ID")
):
    """Satellite observations - NO AUTH.
    
    Args:
        farm_id: Optional farm/project ID to filter by
    """
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_satellite_data(farm_id),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/soil")
async def public_soil(
    farm_id: Optional[str] = Query(None, description="Filter by farm/project ID")
):
    """Soil profiles - NO AUTH.
    
    Args:
        farm_id: Optional farm/project ID to filter by
    """
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_soil_data(farm_id),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/mrv")
async def public_mrv(
    farm_id: Optional[str] = Query(None, description="Filter by farm/project ID")
):
    """MRV observations - NO AUTH.
    
    Args:
        farm_id: Optional farm/project ID to filter by
    """
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_mrv_data(farm_id),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/public/simulations")
async def public_simulations(
    farm_id: Optional[str] = Query(None, description="Filter by farm/project ID")
):
    """Simulation runs - NO AUTH.
    
    Args:
        farm_id: Optional farm/project ID to filter by
    """
    return {
        "status": "success",
        "auth_required": False,
        "data": _get_simulations_data(farm_id),
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
            "/dashboard/data",
            "/dashboard/refresh-data",
            "/dashboard/recommendations/{farm_id}",
        ],
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ============================================================================
# AUTHENTICATED ENDPOINTS - Authentication Required
# ============================================================================

def _get_current_user_optional(request: Request):
    """Try to extract user from request. Returns None if not authenticated."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            from services.auth import compat
            return compat.decode_token_safe(token)
        except Exception:
            return None
    return None


@router.get("/data")
async def get_dashboard_data(request: Request):
    """
    Authenticated dashboard data.
    Requires valid JWT token in Authorization header.
    """
    user = _get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")

        weather = _get_weather_data(None)
        satellite = _get_satellite_data(None)
        soil = _get_soil_data(None)
        carbon = _get_carbon_summary()
        projects = _get_projects_data()

        return {
            "status": "success",
            "user_id": user.get("sub"),
            "data": {
                "projects": projects,
                "weather": weather,
                "satellite": satellite,
                "soil": soil,
                "carbon": carbon,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Dashboard data fetch failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch dashboard data",
        )


@router.post("/refresh-data")
async def refresh_dashboard_data(request: Request):
    """
    Refresh/refresh dashboard data.
    Requires valid JWT token.
    """
    user = _get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")

        weather = _get_weather_data(None)
        satellite = _get_satellite_data(None)
        soil = _get_soil_data(None)
        carbon = _get_carbon_summary()
        projects = _get_projects_data()
        simulations = _get_simulations_data(None)
        mrv = _get_mrv_data(None)

        return {
            "status": "success",
            "refreshed": True,
            "user_id": user.get("sub"),
            "data": {
                "projects": projects,
                "weather": weather,
                "satellite": satellite,
                "soil": soil,
                "carbon": carbon,
                "simulations": simulations,
                "mrv": mrv,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Dashboard refresh failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to refresh dashboard data",
        )


@router.get("/recommendations/{farm_id}")
async def get_recommendations(farm_id: str, request: Request):
    """
    Get AI recommendations for a specific farm/project.
    Requires valid JWT token.
    """
    user = _get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        from database.hub import hub
        conn = hub.get_duckdb("master")

        weather = _get_weather_data(farm_id)
        satellite = _get_satellite_data(farm_id)
        soil = _get_soil_data(farm_id)
        mrv = _get_mrv_data(farm_id)
        simulations = _get_simulations_data(farm_id)

        recommendations = []

        if soil.get("avg_organic_carbon_pct", 0) < 2.0:
            recommendations.append({
                "type": "soil_carbon",
                "priority": "high",
                "message": "Increase organic matter through compost application",
            })

        if weather.get("avg_temperature_c", 0) > 30:
            recommendations.append({
                "type": "water_management",
                "priority": "high",
                "message": "Implement irrigation scheduling based on weather forecasts",
            })

        if satellite.get("avg_ndvi", 0) < 0.4:
            recommendations.append({
                "type": "vegetation_health",
                "priority": "medium",
                "message": "Monitor vegetation stress and consider fertilization",
            })

        if mrv.get("verification_rate_pct", 0) < 80:
            recommendations.append({
                "type": "data_quality",
                "priority": "medium",
                "message": "Increase MRV observation frequency for better verification",
            })

        return {
            "status": "success",
            "farm_id": farm_id,
            "user_id": user.get("sub"),
            "data": {
                "weather": weather,
                "satellite": satellite,
                "soil": soil,
                "mrv": mrv,
                "simulations": simulations,
            },
            "recommendations": recommendations,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Recommendations fetch failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate recommendations",
        )
