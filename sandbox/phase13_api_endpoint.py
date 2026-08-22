"""
Phase 13: FastAPI Endpoint for Hydroma Global Watchdog
======================================================

هدف: ارائه ۱۰ مدل یکپارچه به‌صورت REST API

Endpoints:
- GET  /                      → Service info
- GET  /health                → Health check
- GET  /api/v1/regions        → List available regions
- POST /api/v1/analyze        → Analyze a region
- GET  /api/v1/analyze/{region} → Get analysis for region
- GET  /docs                  → Swagger UI (auto-generated)

Usage:
    python sandbox/phase13_api_endpoint.py
    
    یا:
    uvicorn sandbox.phase13_api_endpoint:app --reload --port 8000

Test with curl:
    curl http://localhost:8000/
    curl http://localhost:8000/api/v1/regions
    curl http://localhost:8000/api/v1/analyze/Iran_Isfahan
    curl -X POST http://localhost:8000/api/v1/analyze \
         -H "Content-Type: application/json" \
         -d '{"region": "Yemen_Sanaa", "crop_type": "wheat"}'

Dependencies:
    pip install fastapi uvicorn
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# Path Setup
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================================
# Check FastAPI availability
# ============================================================================

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("=" * 80)
    print("❌ FastAPI not installed. Install with:")
    print("   pip install fastapi uvicorn")
    print("=" * 80)
    sys.exit(1)

# ============================================================================
# Import Orchestrator
# ============================================================================

try:
    from sandbox.phase12_unified_orchestrator import (
        RegionAnalyzer, MockProviders, AnalysisResult
    )
    print("✅ Orchestrator imported successfully")
except ImportError as e:
    print(f"❌ Cannot import orchestrator: {e}")
    print("   Run phase12_unified_orchestrator.py first to verify it works")
    sys.exit(1)

# ============================================================================
# SQLite Cache Integration (Phase 15)
# ============================================================================

_sqlite_cache_instance = None


def get_sqlite_cache():
    """Get SQLite cache instance (lazy initialization)."""
    global _sqlite_cache_instance
    if _sqlite_cache_instance is None:
        try:
            from engine.hydroma.models.cache import SQLiteCache
            _sqlite_cache_instance = SQLiteCache()
            print(f"✅ SQLite cache initialized: {_sqlite_cache_instance.db_path}")
        except ImportError as imp_err:
            print(f"⚠️  SQLite cache not installed: {imp_err}")
            _sqlite_cache_instance = False
        except Exception as exc_err:
            print(f"⚠️  SQLite cache failed to initialize: {exc_err}")
            _sqlite_cache_instance = False
    if _sqlite_cache_instance is False:
        return None
    return _sqlite_cache_instance



# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Hydroma Global Watchdog API",
    description=(
        "Scientific assessment platform for global water security.\n\n"
        "**Models included:**\n"
        "- KGC: Köppen-Geiger climate classification\n"
        "- WBI: Water Bankruptcy Index\n"
        "- EWSI: EcoNojin Water Stress Index\n"
        "- HY-RUE: Radiation Use Efficiency (yield prediction)\n"
        "- ECSI: Carbon Sequestration Index\n"
        "- HDVI: Drought Vulnerability Index\n"
        "- EPIA: Precision Irrigation Advisor\n"
        "- H-Pheno: Phenology Detection\n"
        "- ESRI: Salinity Risk Index\n"
        "- HLHS: Landscape Health Score\n\n"
        "**Validation:** 9 of 10 models validated against peer-reviewed literature.\n"
        "**Disclaimer:** Probabilistic assessments, not deterministic predictions."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

try:
    from pydantic import BaseModel, Field
except ImportError:
    # pydantic comes with fastapi
    from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request body for analysis endpoint."""
    region: str = Field(..., description="Region name (from /regions endpoint)")
    crop_type: str = Field(
        default="wheat",
        description="Crop type (wheat, maize, rice, potato)"
    )


class AnalyzeResponse(BaseModel):
    """Response with analysis result."""
    success: bool
    region: str
    timestamp: str
    execution_time_ms: float
    analysis: Dict[str, Any]
    warnings: List[str] = []


class RegionInfo(BaseModel):
    """Information about an available region."""
    name: str
    latitude: float
    longitude: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str
    models_available: List[str]
    regions_count: int


# ============================================================================
# Global State
# ============================================================================

# Initialize analyzer once (lazy)
_analyzer: Optional[RegionAnalyzer] = None
_cache: Dict[str, AnalysisResult] = {}


def get_analyzer() -> RegionAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = RegionAnalyzer()
    return _analyzer


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", summary="Service Information")
def root():
    """Get service information."""
    return {
        "service": "Hydroma Global Watchdog API",
        "version": "1.0.0",
        "description": "Scientific assessment platform for global water security",
        "documentation": "/docs",
        "regions_endpoint": "/api/v1/regions",
        "analyze_endpoint": "/api/v1/analyze",
        "created_by": "EcoNojin Scientific Council",
        "status": "operational",
    }


@app.get("/health", response_model=HealthResponse, summary="Health Check")
def health():
    """Check service health and available models."""
    try:
        analyzer = get_analyzer()
        models = ["KGC", "WBI", "EWSI", "HY-RUE", "ECSI",
                  "HDVI", "EPIA", "H-Pheno", "ESRI", "HLHS"]
        regions_count = len(MockProviders.PRESETS)
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
            models_available=models,
            regions_count=regions_count,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")


@app.get("/api/v1/regions",
         response_model=List[RegionInfo],
         summary="List Available Regions")
def list_regions():
    """Get list of available regions for analysis."""
    regions = []
    for name, data in MockProviders.PRESETS.items():
        regions.append(RegionInfo(
            name=name,
            latitude=data["lat"],
            longitude=data["lon"],
        ))
    return regions


@app.post("/api/v1/analyze",
          response_model=AnalyzeResponse,
          summary="Analyze Region (POST)")
def analyze_post(request: AnalyzeRequest):
    """
    Analyze a region for water security and agricultural productivity.

    Returns comprehensive analysis including:
    - Climate classification (Köppen-Geiger)
    - Water bankruptcy assessment
    - Crop yield prediction
    - Irrigation recommendations
    - Drought vulnerability
    - Carbon sequestration potential
    - Landscape health score
    """
    return _run_analysis(request.region, request.crop_type)


@app.get("/api/v1/analyze/{region_name}",
         response_model=AnalyzeResponse,
         summary="Analyze Region (GET)")
def analyze_get(
    region_name: str,
    crop_type: str = Query(default="wheat",
                           description="Crop type"),
    force_refresh: bool = Query(default=False,
                                description="Force recompute (ignore cache)"),
):
    """
    Get analysis for a region (cached).

    Use POST /api/v1/analyze for more control or force_refresh=true to bypass cache.
    """
    cache_key = f"{region_name}:{crop_type}"
    
    if not force_refresh and cache_key in _cache:
        result = _cache[cache_key]
        return AnalyzeResponse(
            success=True,
            region=result.region_name,
            timestamp=result.timestamp,
            execution_time_ms=result.execution_time_ms,
            analysis=result.to_dict(),
            warnings=result.warnings,
        )
    
    # Try SQLite cache first
    sqlite_cache = get_sqlite_cache()
    if sqlite_cache and not force_refresh:
        cached = sqlite_cache.get(region_name, crop_type)
        if cached:
            return AnalyzeResponse(
                success=True,
                region=cached["region_name"],
                timestamp=cached.get("cached_at", datetime.now(timezone.utc).isoformat()),
                execution_time_ms=0.0,
                analysis=cached,
                warnings=cached.get("warnings", []),
            )
    
    return _run_analysis(region_name, crop_type, cache_key=cache_key, sqlite_cache=sqlite_cache)


def _run_analysis(region: str, crop_type: str,
                  cache_key: Optional[str] = None,
                  sqlite_cache = None) -> AnalyzeResponse:
    """Internal: run analysis with error handling."""
    t0 = time.time()
    
    # Validate region
    if region not in MockProviders.PRESETS:
        available = list(MockProviders.PRESETS.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Region '{region}' not found. Available: {available}"
        )
    
    # Validate crop type
    valid_crops = ["wheat", "maize", "rice", "potato"]
    if crop_type not in valid_crops:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid crop '{crop_type}'. Valid: {valid_crops}"
        )
    
    try:
        analyzer = get_analyzer()
        result = analyzer.analyze(region, crop_type)
        
        # Cache result in memory
        if cache_key:
            _cache[cache_key] = result
        
        # Cache result in SQLite (persistent)
        if sqlite_cache:
            try:
                sqlite_cache.store(
                    region_name=result.region_name,
                    crop_type=result.crop_type,
                    result=result.to_dict(),
                    lat=result.lat,
                    lon=result.lon,
                    ttl_hours=24,
                )
            except Exception as e:
                print(f"⚠️  SQLite cache store failed: {e}")
        
        return AnalyzeResponse(
            success=True,
            region=result.region_name,
            timestamp=result.timestamp,
            execution_time_ms=result.execution_time_ms,
            analysis=result.to_dict(),
            warnings=result.warnings,
        )
    
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        return AnalyzeResponse(
            success=False,
            region=region,
            timestamp=datetime.now(timezone.utc).isoformat(),
            execution_time_ms=elapsed,
            analysis={"error": str(e)},
            warnings=[f"Analysis failed: {e}"],
        )


@app.get("/api/v1/cache/stats", summary="Cache Statistics")
def cache_stats():
    """Get cache statistics (memory + SQLite)."""
    result = {
        "memory_cache": {
            "cached_analyses": len(_cache),
            "cache_keys": list(_cache.keys()),
        },
    }
    sqlite_cache = get_sqlite_cache()
    if sqlite_cache:
        result["sqlite_cache"] = sqlite_cache.stats()
    return result


@app.delete("/api/v1/cache", summary="Clear Cache")
def clear_cache():
    """Clear all cached analyses (memory + SQLite)."""
    count = len(_cache)
    _cache.clear()
    
    sqlite_cache = get_sqlite_cache()
    sqlite_count = 0
    if sqlite_cache:
        sqlite_count = sqlite_cache.clear_all()
    
    total = count + sqlite_count
    return {
        "message": f"Cleared {total} cached analyses",
        "memory": count,
        "sqlite": sqlite_count,
    }


@app.get("/api/v1/models", summary="List Models with Descriptions")
def list_models():
    """Detailed information about each model."""
    return {
        "models": {
            "KGC": {
                "name": "Köppen-Geiger Climate Classification",
                "version": "v5",
                "accuracy": 0.88,
                "description": "Classifies climate zones based on temperature and precipitation",
                "reference": "Peel et al. (2007) HESS",
            },
            "WBI": {
                "name": "Water Bankruptcy Index",
                "version": "v3",
                "accuracy": 0.80,
                "description": "Composite index for water security assessment",
                "reference": "WRI Aqueduct 4.0 (2023)",
            },
            "EWSI": {
                "name": "EcoNojin Water Stress Index",
                "description": "Multi-source water stress detection",
                "inputs": ["Sentinel-2 NDMI", "VPD", "Soil moisture"],
            },
            "HY-RUE": {
                "name": "Hydroma Radiation Use Efficiency",
                "description": "Crop yield prediction from PAR and LAI",
                "reference": "Monteith (1977)",
            },
            "ECSI": {
                "name": "EcoNojin Carbon Sequestration Index",
                "description": "Soil carbon dynamics based on RothC",
                "reference": "Coleman & Jenkinson (1996)",
            },
            "HDVI": {
                "name": "Hydroma Drought Vulnerability Index",
                "description": "Multi-scale drought assessment",
                "reference": "McKee et al. (1993), Kogan (1995)",
            },
            "EPIA": {
                "name": "EcoNojin Precision Irrigation Advisor",
                "description": "Irrigation scheduling based on FAO-56",
                "reference": "Allen et al. (1998) FAO-56",
            },
            "H-Pheno": {
                "name": "Hydroma Phenology Detection",
                "description": "Crop phenological stage detection",
                "status": "Requires real Sentinel-2 time series for full accuracy",
            },
            "ESRI": {
                "name": "EcoNojin Salinity Risk Index",
                "description": "Salinity risk assessment",
                "reference": "Ayers & Westcot (1985) FAO-29",
            },
            "HLHS": {
                "name": "Hydroma Landscape Health Score",
                "description": "Composite landscape health for fund management",
            },
        }
    }


# ============================================================================
# Main Runner
# ============================================================================

def main():
    """Run the FastAPI server."""
    print("=" * 80)
    print("🚀 PHASE 13: HYDROMA GLOBAL WATCHDOG API")
    print("=" * 80)
    print()
    print("📡 API Endpoints:")
    print("   🌐 http://localhost:8000/           - Service info")
    print("   💊 http://localhost:8000/health      - Health check")
    print("   📋 http://localhost:8000/api/v1/regions - Available regions")
    print("   🔍 http://localhost:8000/api/v1/analyze/{region} - Analyze")
    print("   📚 http://localhost:8000/api/v1/models - Model descriptions")
    print()
    print("📖 Documentation:")
    print("   📕 Swagger UI: http://localhost:8000/docs")
    print("   📗 ReDoc:      http://localhost:8000/redoc")
    print()
    print("🧪 Test with curl:")
    print("   curl http://localhost:8000/")
    print("   curl http://localhost:8000/api/v1/regions")
    print("   curl http://localhost:8000/api/v1/analyze/Iran_Isfahan")
    print("   curl http://localhost:8000/api/v1/analyze/Yemen_Sanaa?crop_type=wheat")
    print()
    print("=" * 80)
    print("Starting server on http://localhost:8000 ...")
    print("Press Ctrl+C to stop")
    print("=" * 80)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()