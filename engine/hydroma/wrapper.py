"""High-level Pythonic wrapper around hydroma_core C++ module.

Provides convenient functions that:
- Accept natural Python types (dicts, lists)
- Handle object creation (RichardsOptions, etc.)
- Return dictionaries instead of C++ objects
- Gracefully fallback to Python if C++ unavailable
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from engine.hydroma import cpp_bindings

    _cpp = cpp_bindings.get_module()
    _available = _cpp is not None
except Exception:
    _cpp = None
    _available = False


def is_available() -> bool:
    return _available


# ============================================================================
# Remote Sensing
# ============================================================================
def compute_ndvi(red: float, nir: float) -> float:
    """Compute NDVI. Returns -1 to 1 (vegetation ~0.3-0.8)."""
    if not _available:
        return (nir - red) / (nir + red) if (nir + red) > 0 else 0.0
    return _cpp.ndvi(red, nir)


def compute_evi(red: float, nir: float, blue: float) -> float:
    """Enhanced Vegetation Index."""
    if not _available:
        g, c1, c2, l = 2.5, 6.0, 7.5, 1.0
        return (
            g * (nir - red) / (nir + c1 * red - c2 * blue + l)
            if (nir + c1 * red - c2 * blue + l) > 0
            else 0.0
        )
    return _cpp.evi(red, nir, blue)


def compute_savi(red: float, nir: float, L: float = 0.5) -> float:
    """Soil-Adjusted Vegetation Index."""
    if not _available:
        return ((nir - red) / (nir + red + L)) * (1 + L) if (nir + red + L) > 0 else 0.0
    return _cpp.savi(red, nir, L)


def compute_all_indices(
    red: float, nir: float, blue: float = 0.1, green: float = 0.3, swir: float = 0.2
) -> dict[str, float]:
    """Compute all available vegetation indices."""
    return {
        "ndvi": compute_ndvi(red, nir),
        "evi": compute_evi(red, nir, blue),
        "savi": compute_savi(red, nir),
        "ndwi": _cpp.ndwi(green, nir) if _available else (green - nir) / (green + nir),
        "nbr": _cpp.nbr(nir, swir) if _available else (nir - swir) / (nir + swir),
    }


# ============================================================================
# Soil Physics
# ============================================================================
def analyze_soil(
    ph: float,
    organic_matter: float,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    clay: float,
    silt: float,
    sand: float,
) -> dict[str, Any]:
    """Comprehensive soil analysis combining C++ physics + heuristic scoring."""
    total = clay + silt + sand
    if total == 0:
        total = 1

    # Texture classification
    clay_pct = (clay / total) * 100
    silt_pct = (silt / total) * 100
    sand_pct = (sand / total) * 100

    if clay_pct > 40:
        texture = "clay"
    elif sand_pct > 70:
        texture = "sandy"
    elif silt_pct > 50:
        texture = "silty"
    else:
        texture = "loam"

    # Use C++ if available
    params = {}
    if _available:
        try:
            tex_class = texture if texture in _cpp.supported_textures() else "loam"
            params = _cpp.soil_params(tex_class)
        except Exception:
            params = {}

    # pH classification
    ph_status = "acidic" if ph < 5.5 else "alkaline" if ph > 7.5 else "neutral"

    # Organic matter rating
    om_rating = "low" if organic_matter < 1 else "moderate" if organic_matter < 3 else "high"

    # Health score (0-100)
    score = 50
    if ph_status == "neutral":
        score += 20
    if om_rating == "high":
        score += 15
    elif om_rating == "moderate":
        score += 8
    if 30 < nitrogen < 80:
        score += 5
    if 20 < phosphorus < 60:
        score += 5
    if 100 < potassium < 300:
        score += 5

    # Recommendations
    recs = []
    if ph_status == "acidic":
        recs.append("Apply lime to raise pH")
    elif ph_status == "alkaline":
        recs.append("Add sulfur or organic matter to lower pH")
    if om_rating == "low":
        recs.append("Add compost to increase organic matter")
    if nitrogen < 30:
        recs.append("Consider nitrogen-fixing cover crops")
    if phosphorus < 20:
        recs.append("Add bone meal or rock phosphate")
    if not recs:
        recs.append("Soil is in good health - maintain current practices")

    return {
        "texture": texture,
        "texture_percentages": {
            "clay": round(clay_pct, 1),
            "silt": round(silt_pct, 1),
            "sand": round(sand_pct, 1),
        },
        "ph_status": ph_status,
        "organic_matter_rating": om_rating,
        "health_score": min(100, score),
        "fertility": "high" if score > 70 else "moderate" if score > 40 else "low",
        "recommendations": recs,
        "van_genuchten_params": {
            "theta_r": getattr(params, "theta_r", None),
            "theta_s": getattr(params, "theta_s", None),
            "alpha": getattr(params, "alpha", None),
            "n": getattr(params, "n", None),
            "Ks_cm_per_day": getattr(params, "Ks", None),
        }
        if params
        else None,
    }


# ============================================================================
# Erosion (RUSLE)
# ============================================================================
def compute_erosion(
    slope_length_m: float,
    slope_percent: float,
    annual_rainfall_mm: float,
    texture: str = "loam",
    c_factor: float = 0.5,
    p_factor: float = 0.8,
) -> dict[str, Any]:
    """Complete RUSLE soil loss calculation."""
    if _available:
        R = _cpp.estimate_rainfall_erosivity(annual_rainfall_mm)
        K = _cpp.soil_erodibility_k(texture)
        LS = _cpp.ls_factor(slope_length_m, slope_percent)
        A = _cpp.rusle_annual_soil_loss(R, K, LS, c_factor, p_factor)
    else:
        R = 0.05 * annual_rainfall_mm
        K = 0.3
        LS = 1.0
        A = R * K * LS * c_factor * p_factor

    risk_level = "low" if A < 5 else "moderate" if A < 15 else "high" if A < 30 else "very high"
    recs = []
    if A > 15:
        recs.append("Urgent: implement contour farming or terraces")
    if A > 5:
        recs.append("Add cover crops or mulch to reduce erosion")
    if c_factor > 0.3:
        recs.append("Increase ground cover (reduce C factor)")
    if not recs:
        recs.append("Erosion rates acceptable")

    return {
        "annual_soil_loss_t_per_ha": round(A, 2),
        "R_factor": round(R if _available else 0.05 * annual_rainfall_mm, 2),
        "K_factor": round(K if _available else 0.3, 3),
        "LS_factor": round(LS if _available else 1.0, 3),
        "C_factor": c_factor,
        "P_factor": p_factor,
        "risk_level": risk_level,
        "recommendations": recs,
    }


# ============================================================================
# Climate Scenarios (IPCC SSP)
# ============================================================================
def apply_scenario(
    baseline_temp: float, baseline_precip: float, scenario: str, target_year: int
) -> dict[str, Any]:
    """Apply IPCC SSP climate scenario."""
    ssp_data = {
        "ssp126": {"temp_increase": 1.8, "precip_change": -0.05, "confidence": 0.85},
        "ssp245": {"temp_increase": 2.7, "precip_change": -0.10, "confidence": 0.75},
        "ssp370": {"temp_increase": 3.6, "precip_change": -0.15, "confidence": 0.65},
        "ssp585": {"temp_increase": 4.4, "precip_change": -0.20, "confidence": 0.55},
    }
    if scenario not in ssp_data:
        return {"error": f"Unknown scenario: {scenario}"}

    data = ssp_data[scenario]
    scale = min((target_year - 2020) / 30, 1.0)
    temp_change = data["temp_increase"] * scale
    precip_change_pct = data["precip_change"] * scale

    projected_temp = baseline_temp + temp_change
    projected_precip = baseline_precip * (1 + precip_change_pct)
    drought_index = max(0, min(1, (temp_change / 5) + abs(precip_change_pct)))

    return {
        "scenario": scenario,
        "year": target_year,
        "projected_temperature": round(projected_temp, 2),
        "projected_precipitation": round(projected_precip, 2),
        "temperature_change": round(temp_change, 2),
        "precipitation_change_percent": round(precip_change_pct * 100, 2),
        "drought_risk_index": round(drought_index, 3),
        "confidence": data["confidence"],
        "impact_assessment": {
            "crop_yield": "decrease expected" if temp_change > 2 else "minimal impact",
            "water_stress": "high"
            if drought_index > 0.6
            else "moderate"
            if drought_index > 0.3
            else "low",
            "adaptation_needed": temp_change > 2.5,
        },
        "recommendations": [
            "Consider drought-tolerant crop varieties"
            if drought_index > 0.5
            else "Maintain current varieties",
            "Implement water harvesting"
            if precip_change_pct < -0.1
            else "Standard water management",
            "Adjust planting dates earlier" if temp_change > 2 else "Maintain traditional calendar",
        ],
    }


# ============================================================================
# Hydrology
# ============================================================================
def route_flood(
    hydrograph: list[float],
    channel_length: float = 1000,
    bed_slope: float = 0.002,
    manning_n: float = 0.03,
    channel_width: float = 5,
) -> dict[str, Any]:
    """Route flood wave through channel using Muskingum-Cunge."""
    if not _available:
        return {"error": "C++ not available"}
    try:
        result = _cpp.route_flood_wave(
            hydrograph, channel_length, 50, manning_n, bed_slope, 10.0, channel_width
        )
        return {
            "peak_inflow": max(hydrograph) if hydrograph else 0,
            "peak_outflow": getattr(result, "peak_outflow", None),
            "time_to_peak": getattr(result, "time_to_peak", None),
            "attenuation": getattr(result, "attenuation", None),
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Convenience summary
# ============================================================================
def get_capabilities() -> dict[str, Any]:
    """List available capabilities."""
    return {
        "cpp_available": _available,
        "remote_sensing": ["ndvi", "evi", "savi", "ndwi", "nbr"],
        "soil_physics": ["van_genuchten_params", "water_retention", "conductivity"],
        "erosion": ["rusle", "soil_erodibility", "ls_factor", "sediment_yield"],
        "hydrology": ["flood_routing", "muskingum_cunge", "manning_depth"],
        "climate": ["scenarios_ssp", "et0_hargreaves", "et0_penman_monteith"],
        "statistics": ["monte_carlo", "latin_hypercube"],
    }
