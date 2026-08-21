"""
Platform Router - First real API endpoint for Eco Nojin
========================================================

This router connects:
- Supabase (database)
- Open-Meteo (climate data)
- C++ Bridge (accelerated computations)
- Scientific Motors (Python logic)

Follows the Hybrid Intelligence Pattern:
- C++ for hot-path kernels
- Python for decisions & orchestration
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import httpx

from services.supabase.client import get_supabase_client
from engine.hydroma.cpp_bridge import (
    is_cpp_available,
    get_telemetry,
    reset_telemetry,
    ndvi,
    evi,
    ndvi_array,
    rusle_annual_soil_loss,
    estimate_rainfall_erosivity,
    penman_monteith_et0,
    simulate_crop_water,
)

logger = logging.getLogger("econojin.platform")

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


# =============================================================================
# Pydantic Models
# =============================================================================

class LandscapeCreate(BaseModel):
    """Request model for creating a landscape."""
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., pattern=r'^[a-z0-9-]+$')
    country: str = Field(..., min_length=2, max_length=2)
    province: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    area_ha: float = Field(..., gt=0, le=100000)


class LandscapeOut(BaseModel):
    """Response model for landscape."""
    id: str
    name: str
    slug: str
    country: str
    province: Optional[str]
    created_at: str


class AnalyzeRequest(BaseModel):
    """Request model for land analysis."""
    name: str = Field(..., min_length=2, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    area_ha: float = Field(..., gt=0, le=100000)
    crop_type: Optional[str] = "wheat"
    soil_texture: Optional[str] = "loam"


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    landscape_id: str
    name: str
    location: Dict[str, float]
    area_ha: float
    timestamp: str
    
    # Computed results
    climate: Dict[str, Any]
    vegetation: Dict[str, Any]
    erosion: Dict[str, Any]
    irrigation: Dict[str, Any]
    carbon: Dict[str, Any]
    
    # Decision layer results (Python)
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    
    # Performance telemetry
    performance: Dict[str, Any]


# =============================================================================
# Helper Functions
# =============================================================================

async def fetch_climate_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch climate data from Open-Meteo (free, no API key needed).
    Returns last 30 days of weather data.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    end_date = datetime(2023, 12, 31)
    start_date = end_date - timedelta(days=30)
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration",
        "timezone": "auto",
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            daily = data.get("daily", {})
            
            return {
                "source": "Open-Meteo ERA5",
                "period": f"{start_date.date()} to {end_date.date()}",
                "days": len(daily.get("time", [])),
                "avg_temp_max": _safe_mean(daily.get("temperature_2m_max")),
                "avg_temp_min": _safe_mean(daily.get("temperature_2m_min")),
                "total_precip_mm": _safe_sum(daily.get("precipitation_sum")),
                "avg_et0_mm": _safe_mean(daily.get("et0_fao_evapotranspiration")),
                "raw_daily": daily,
            }
        except Exception as e:
            logger.warning(f"Climate fetch failed: {e}")
            return {
                "source": "fallback",
                "error": str(e),
                "avg_temp_max": 25.0,
                "avg_temp_min": 10.0,
                "total_precip_mm": 50.0,
                "avg_et0_mm": 4.0,
            }


def _safe_mean(values: Optional[List]) -> float:
    """Calculate mean safely."""
    if not values:
        return 0.0
    valid = [v for v in values if v is not None]
    return sum(valid) / len(valid) if valid else 0.0


def _safe_sum(values: Optional[List]) -> float:
    """Calculate sum safely."""
    if not values:
        return 0.0
    return sum(v for v in values if v is not None)


def assess_risks(climate: Dict, erosion_rate: float, carbon_rate: float) -> Dict[str, Any]:
    """
    Python decision layer - assess risks based on computed data.
    This is where BUSINESS RULES live (not in C++).
    """
    risks = {}
    
    # Drought risk
    if climate.get("total_precip_mm", 100) < 30:
        risks["drought"] = "HIGH"
    elif climate.get("total_precip_mm", 100) < 60:
        risks["drought"] = "MEDIUM"
    else:
        risks["drought"] = "LOW"
    
    # Erosion risk
    if erosion_rate > 10:
        risks["erosion"] = "CRITICAL"
    elif erosion_rate > 5:
        risks["erosion"] = "HIGH"
    elif erosion_rate > 2:
        risks["erosion"] = "MEDIUM"
    else:
        risks["erosion"] = "LOW"
    
    # Carbon potential
    if carbon_rate > 2:
        risks["carbon_potential"] = "EXCELLENT"
    elif carbon_rate > 1:
        risks["carbon_potential"] = "GOOD"
    elif carbon_rate > 0.5:
        risks["carbon_potential"] = "MODERATE"
    else:
        risks["carbon_potential"] = "LOW"
    
    return risks


def generate_recommendations(risks: Dict, climate: Dict) -> List[str]:
    """
    Python decision layer - generate actionable recommendations.
    """
    recs = []
    
    if risks.get("drought") in ["HIGH", "MEDIUM"]:
        recs.append("💧 Consider drip irrigation to reduce water usage by 40%")
        recs.append("🌱 Select drought-resistant crop varieties")
    
    if risks.get("erosion") in ["CRITICAL", "HIGH"]:
        recs.append("🌿 Plant cover crops to reduce erosion")
        recs.append("🏔️ Implement contour farming on slopes")
    
    if risks.get("carbon_potential") in ["EXCELLENT", "GOOD"]:
        recs.append("🌍 This land is suitable for carbon credit projects")
        recs.append("💰 Potential revenue: $30-50/hectare/year from carbon credits")
    
    if climate.get("avg_et0_mm", 0) > 5:
        recs.append("☀️ High evapotranspiration - monitor soil moisture closely")
    
    if not recs:
        recs.append("✅ Land conditions are favorable for standard practices")
    
    return recs


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/health")
async def platform_health():
    """Health check for platform router."""
    return {
        "status": "operational",
        "service": "platform",
        "cpp_available": is_cpp_available(),
        "supabase_available": get_supabase_client() is not None,
    }


@router.get("/landscapes", response_model=List[LandscapeOut])
async def list_landscapes():
    """List all landscapes from Supabase."""
    client = get_supabase_client()
    try:
        result = client.table("platform_landscapes").select("*").execute()
        return result.data
    except Exception as e:
        logger.error(f"Failed to list landscapes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/landscapes", response_model=LandscapeOut)
async def create_landscape(data: LandscapeCreate):
    """Create a new landscape in Supabase."""
    client = get_supabase_client()
    try:
        result = client.table("platform_landscapes").insert({
            "name": data.name,
            "slug": f"{data.slug}-{int(time.time()) % 1000000}",
            "country": data.country,
            "province": data.province,
            "geo_boundary": {
                "type": "Point",
                "coordinates": [data.longitude, data.latitude],
            },
        }).execute()
        
        if result.data:
            return result.data[0]
        raise HTTPException(status_code=500, detail="Failed to create landscape")
    except Exception as e:
        logger.error(f"Failed to create landscape: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_land(request: AnalyzeRequest):
    """
    Full land analysis - the MAIN endpoint of the platform.
    
    Flow:
    1. Create/retrieve landscape in Supabase
    2. Fetch climate data from Open-Meteo
    3. Run C++ accelerated computations
    4. Apply Python decision layer
    5. Save and return results
    """
    reset_telemetry()
    t_start = time.perf_counter()
    
    client = get_supabase_client()
    
    # -------------------------------------------------------------------------
    # Step 1: Create landscape in Supabase
    # -------------------------------------------------------------------------
    slug = request.name.lower().replace(" ", "-")[:40] + "-" + str(int(time.time()) % 1000000)
    try:
        landscape_result = client.table("platform_landscapes").insert({
            "name": request.name,
            "slug": f"{slug}-{int(time.time()) % 1000000}",
            "country": "IR",  # Default for now
            "province": None,
            "geo_boundary": {
                "type": "Point",
                "coordinates": [request.longitude, request.latitude],
            },
        }).execute()
        
        landscape_id = str(landscape_result.data[0]["id"])
    except Exception as e:
        # Try to find existing
        try:
            existing = client.table("platform_landscapes").select("id").eq("slug", slug).execute()
            if existing.data:
                landscape_id = str(existing.data[0]["id"])
            else:
                raise
        except Exception:
            logger.error(f"Landscape create failed: {e}")
            landscape_id = "temp-" + slug
    
    # -------------------------------------------------------------------------
    # Step 2: Fetch climate data (Python I/O)
    # -------------------------------------------------------------------------
    climate = await fetch_climate_data(request.latitude, request.longitude)
    
    # -------------------------------------------------------------------------
    # Step 3: C++ Accelerated Computations
    # -------------------------------------------------------------------------
    
    # 3a. NDVI (simulated for now - in real use would come from Sentinel-2)
    t_ndvi_start = time.perf_counter()
    # Simulate a grid of NDVI values
    try:
        import numpy as np
        red_grid = np.random.uniform(0.05, 0.3, (100, 100)).astype(np.float32)
        nir_grid = np.random.uniform(0.2, 0.7, (100, 100)).astype(np.float32)
        
        # Use C++ accelerated NDVI
        ndvi_grid = ndvi_array(red_grid, nir_grid)
        avg_ndvi = float(np.mean(ndvi_grid))
        vegetation_health = "GOOD" if avg_ndvi > 0.4 else "MODERATE" if avg_ndvi > 0.2 else "POOR"
    except Exception as e:
        logger.warning(f"NDVI array failed: {e}")
        avg_ndvi = 0.35
        vegetation_health = "MODERATE"
    
    t_ndvi = (time.perf_counter() - t_ndvi_start) * 1000
    
    # 3b. RUSLE Erosion (C++ accelerated)
    t_rusle_start = time.perf_counter()
    try:
        R = estimate_rainfall_erosivity(climate.get("total_precip_mm", 300))
        K = 0.3  # Soil erodibility (default loam)
        LS = 1.5  # Slope factor (default)
        C = 0.5  # Cover factor
        P = 1.0  # Practice factor
        
        erosion_rate = rusle_annual_soil_loss(R, K, LS, C, P)
    except Exception as e:
        logger.warning(f"RUSLE failed: {e}")
        erosion_rate = 3.5
    
    t_rusle = (time.perf_counter() - t_rusle_start) * 1000
    
    # 3c. Irrigation ETo (C++ accelerated)
    try:
        t_min = climate.get("avg_temp_min", 10)
        t_max = climate.get("avg_temp_max", 25)
        et0 = penman_monteith_et0(
            t_min=t_min,
            t_max=t_max,
            rh_min=40,
            rh_max=80,
            wind_speed=2.0,
            latitude=request.latitude,
            doy=180,
        )
    except Exception as e:
        logger.warning(f"Penman-Monteith failed: {e}")
        et0 = climate.get("avg_et0_mm", 4.0)
    
    # 3d. Carbon sequestration potential (simplified)
    # RothC would go here in real scenario
    base_carbon_rate = 1.5  # tCO2e/ha/year (typical for sustainable practices)
    carbon_rate = base_carbon_rate * (1 + avg_ndvi)
    total_carbon_potential = carbon_rate * request.area_ha
    
    # -------------------------------------------------------------------------
    # Step 4: Python Decision Layer (Business Rules)
    # -------------------------------------------------------------------------
    risk_assessment = assess_risks(climate, erosion_rate, carbon_rate)
    recommendations = generate_recommendations(risk_assessment, climate)
    
    # -------------------------------------------------------------------------
    # Step 5: Save results to Supabase
    # -------------------------------------------------------------------------
    try:
        client.table("platform_carbon_projects").insert({
            "landscape_id": landscape_id,
            "name": request.name + " - Carbon Project",
            "project_type": "soil_carbon",
            "area_ha": request.area_ha,
            "duration_years": 30,
            "status": "draft",
        }).execute()
    except Exception as e:
        logger.warning(f"Could not save carbon project: {e}")
    
    # -------------------------------------------------------------------------
    # Step 6: Performance telemetry
    # -------------------------------------------------------------------------
    t_total = (time.perf_counter() - t_start) * 1000
    telemetry = get_telemetry()
    
    performance = {
        "total_ms": round(t_total, 2),
        "ndvi_ms": round(t_ndvi, 2),
        "rusle_ms": round(t_rusle, 2),
        "cpp_calls": telemetry["cpp_calls"],
        "fallback_calls": telemetry["fallback_calls"],
        "cpp_time_ms": round(telemetry["total_cpp_time_ms"], 2),
        "fallback_time_ms": round(telemetry["total_fallback_time_ms"], 2),
        "cpp_available": is_cpp_available(),
    }
    
    # -------------------------------------------------------------------------
    # Step 7: Build response
    # -------------------------------------------------------------------------
    return AnalysisResult(
        landscape_id=landscape_id,
        name=request.name,
        location={
            "latitude": request.latitude,
            "longitude": request.longitude,
        },
        area_ha=request.area_ha,
        timestamp=datetime.utcnow().isoformat(),
        
        climate={
            "source": climate.get("source"),
            "period": climate.get("period"),
            "avg_temp_max_c": round(climate.get("avg_temp_max", 0), 1),
            "avg_temp_min_c": round(climate.get("avg_temp_min", 0), 1),
            "total_precip_mm": round(climate.get("total_precip_mm", 0), 1),
            "avg_et0_mm_day": round(climate.get("avg_et0_mm", 0), 2),
        },
        
        vegetation={
            "avg_ndvi": round(avg_ndvi, 3),
            "health": vegetation_health,
            "grid_size": "100x100",
        },
        
        erosion={
            "rusle_rate_t_ha_yr": round(erosion_rate, 2),
            "risk_level": risk_assessment["erosion"],
            "R_factor": round(R, 2) if 'R' in locals() else None,
        },
        
        irrigation={
            "et0_mm_day": round(et0, 2),
            "annual_water_need_mm": round(et0 * 365 * 0.7, 0),  # 70% of ETo
            "recommendation": "drip" if climate.get("total_precip_mm", 100) < 100 else "sprinkler",
        },
        
        carbon={
            "rate_tCO2e_ha_yr": round(carbon_rate, 2),
            "total_potential_tCO2e": round(total_carbon_potential, 1),
            "annual_value_usd": round(total_carbon_potential * 30, 2),  # $30/tCO2e
            "suitability": risk_assessment["carbon_potential"],
        },
        
        risk_assessment=risk_assessment,
        recommendations=recommendations,
        
        performance=performance,
    )


@router.get("/stats")
async def platform_stats():
    """Platform statistics."""
    client = get_supabase_client()
    
    stats = {
        "cpp_available": is_cpp_available(),
    }
    
    try:
        landscapes = client.table("platform_landscapes").select("id").execute()
        stats["total_landscapes"] = len(landscapes.data)
    except Exception:
        stats["total_landscapes"] = 0
    
    try:
        projects = client.table("platform_carbon_projects").select("id", "status").execute()
        stats["total_projects"] = len(projects.data)
        stats["active_projects"] = sum(1 for p in projects.data if p.get("status") == "active")
    except Exception:
        stats["total_projects"] = 0
        stats["active_projects"] = 0
    
    return stats

# =============================================================================
# Python Fallbacks for C++ functions with signature mismatches
# =============================================================================

def _py_ndvi_array(red, nir):
    """
    Python fallback for ndvi_array.
    Works with numpy arrays or sequences.
    """
    try:
        import numpy as np
        red = np.asarray(red, dtype=np.float32)
        nir = np.asarray(nir, dtype=np.float32)
        denom = nir + red + 1e-10
        return (nir - red) / denom
    except Exception:
        # Pure Python fallback
        if isinstance(red, (list, tuple)):
            return [[(n - r) / (n + r + 1e-10) for r, n in zip(row_r, row_n)]
                    for row_r, row_n in zip(red, nir)]
        return (nir - red) / (nir + red + 1e-10)


def _py_penman_monteith_et0(
    t_min, t_max, rh_min, rh_max, wind_speed, latitude, doy,
    **kwargs
):
    """
    Python fallback for FAO-56 Penman-Monteith ETo.
    Reference: Allen et al. 1998, FAO Irrigation and Drainage Paper 56.
    """
    import math
    
    # Mean temperature
    t_mean = (t_min + t_max) / 2.0
    
    # Saturation vapor pressure (kPa)
    def es(T):
        return 0.6108 * math.exp((17.27 * T) / (T + 237.3))
    
    es_tmax = es(t_max)
    es_tmin = es(t_min)
    es_mean = (es_tmax + es_tmin) / 2.0
    
    # Actual vapor pressure (kPa)
    ea = (es_tmin * (rh_max / 100.0) + es_tmax * (rh_min / 100.0)) / 2.0
    
    # Slope of saturation vapor pressure curve (kPa/°C)
    delta = (4098 * es_mean) / ((t_mean + 237.3) ** 2)
    
    # Psychrometric constant (kPa/°C) - assuming sea level
    P = 101.3  # kPa
    gamma = 0.000665 * P
    
    # Extraterrestrial radiation (MJ/m²/day)
    lat_rad = latitude * math.pi / 180.0
    Gsc = 0.0820  # Solar constant
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365.0)
    dec = 0.409 * math.sin(2 * math.pi * doy / 365.0 - 1.39)
    
    ws = math.acos(-math.tan(lat_rad) * math.tan(dec))
    Ra = (24 * 60 / math.pi) * Gsc * dr * (
        ws * math.sin(lat_rad) * math.sin(dec) +
        math.cos(lat_rad) * math.cos(dec) * math.sin(ws)
    )
    
    # Net shortwave radiation (assuming grass reference)
    Rns = 0.77 * Ra  # albedo 0.23
    
    # Net longwave radiation (simplified)
    sigma = 4.903e-9  # MJ/K⁴/m²/day
    Rnl = sigma * (((t_max + 273.16)**4 + (t_min + 273.16)**4) / 2) * (
        0.34 - 0.14 * math.sqrt(ea)
    ) * (1.35 * min(Ra * 0.75 + 0.25, 1.0) - 0.35)
    
    Rn = Rns - Rnl
    
    # Soil heat flux (daily, assume 0 for grass)
    G = 0.0
    
    # FAO-56 Penman-Monteith
    numerator = 0.408 * delta * (Rn - G) + gamma * (900 / (t_mean + 273)) * wind_speed * (es_mean - ea)
    denominator = delta + gamma * (1 + 0.34 * wind_speed)
    
    et0 = numerator / denominator
    return max(0.0, et0)


# Override the bridge functions with fallbacks
import logging
_logger = logging.getLogger("econojin.platform")

# Wrap ndvi_array
_original_ndvi_array = ndvi_array

def ndvi_array_with_fallback(red, nir):
    try:
        result = _original_ndvi_array(red, nir)
        # Check if result is valid
        if result is None or (hasattr(result, 'size') and result.size == 0):
            raise ValueError("Empty result")
        return result
    except Exception as e:
        _logger.debug(f"C++ ndvi_array failed, using Python: {e}")
        return _py_ndvi_array(red, nir)

ndvi_array = ndvi_array_with_fallback

# Wrap penman_monteith_et0
_original_penman = penman_monteith_et0

def penman_monteith_with_fallback(**kwargs):
    try:
        result = _original_penman(**kwargs)
        if result is None or (isinstance(result, float) and math.isnan(result)):
            raise ValueError("Invalid result")
        return result
    except Exception as e:
        _logger.debug(f"C++ penman_monteith failed, using Python: {e}")
        return _py_penman_monteith_et0(**kwargs)

import math
penman_monteith_et0 = penman_monteith_with_fallback

