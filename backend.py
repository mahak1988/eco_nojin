"""
Eco Nojin - Backend Standalone
سرور FastAPI مستقل با تمام endpoints شبیه‌سازی
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import math
import random
import uvicorn

app = FastAPI(
    title="Eco Nojin Virtual Land Laboratory API",
    description="API شبیه‌سازهای کشاورزی پایدار",
    version="5.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Models ─────────────────────────────
class SimulationRequest(BaseModel):
    simulation_type: str
    context: Dict[str, Any] = {}


class LandRequest(BaseModel):
    name: str = "Sample Land"
    area_ha: float = 50.0
    bbox: Dict[str, float] = {"north": 35.5, "south": 35.4, "east": 51.5, "west": 51.4}
    soil: Dict[str, Any] = {}
    climate: Dict[str, Any] = {}
    topography: Dict[str, Any] = {}


class InterventionRequest(BaseModel):
    intervention_id: str
    parameters: Dict[str, Any] = {}
    coverage_pct: float = 100.0


# ─── Root ─────────────────────────────
@app.get("/")
def root():
    return {
        "name": "Eco Nojin Virtual Land Lab API",
        "version": "5.0.0",
        "status": "running",
        "endpoints": [
            "/docs",
            "/api/v1/health",
            "/api/v1/simulation/run",
            "/api/v1/simulation/comprehensive",
            "/api/v1/simulation/erosion-analysis",
            "/api/v1/simulation/water-budget",
            "/api/v1/simulation/windbreak-design",
            "/api/v1/simulation/multi-layer-plan",
            "/api/v1/livestock/simulate",
            "/api/v1/ai/recommend",
        ],
    }


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ═══════════════════════════════════════════════════════════════
# 🌾 AquaCrop-Style Crop Simulation
# ═══════════════════════════════════════════════════════════════
def simulate_aquacrop(context: Dict) -> Dict:
    crop_type = context.get("crop", {}).get("crop_type", "wheat")
    rainfall = context.get("weather", {}).get("precipitation_mm", 300)
    soc = context.get("soil", {}).get("organic_carbon_pct", 1.0)
    
    # Base yields per crop (ton/ha)
    base_yields = {
        "wheat": 4.5, "barley": 4.0, "maize": 8.0, "rice": 6.5,
        "soybean": 3.0, "saffron": 0.012, "alfalfa": 12.0, "cotton": 2.5,
    }
    
    base_yield = base_yields.get(crop_type, 4.0)
    
    # Water stress factor (SCS-CN inspired)
    water_factor = min(1.0, rainfall / 500)
    # Soil fertility factor
    soil_factor = 0.6 + (soc / 3.0) * 0.4
    # Climate factor
    climate_factor = 0.85 + random.random() * 0.15
    
    final_yield = base_yield * water_factor * soil_factor * climate_factor
    biomass = final_yield * 2.5
    water_use = 450 * (final_yield / base_yield)
    wue = (final_yield * 1000) / water_use if water_use > 0 else 0
    
    # Time series (monthly growth)
    time_series = []
    for month in range(1, 13):
        growth = min(1.0, month / 6) if month <= 6 else max(0.5, 1 - (month - 6) / 12)
        time_series.append({
            "month": month,
            "growth_stage": round(growth, 2),
            "ndvi": round(0.2 + growth * 0.6, 2),
            "biomass_kg_ha": round(biomass * 1000 * growth, 1),
            "cumulative_yield": round(final_yield * growth, 2),
        })
    
    return {
        "simulation_id": f"aquacrop-{datetime.now().timestamp():.0f}",
        "simulation_type": "crop_growth",
        "status": "completed",
        "started_at": datetime.now().isoformat(),
        "summary": {
            "crop_type": crop_type,
            "yield_ton_ha": round(final_yield, 2),
            "biomass_ton_ha": round(biomass, 2),
            "water_use_mm": round(water_use, 1),
            "wue_kg_m3": round(wue, 2),
            "revenue_usd": round(final_yield * 400, 0),
        },
        "time_series": time_series,
    }


# ═══════════════════════════════════════════════════════════════
# 🌱 RothC Soil Carbon Simulation
# ═══════════════════════════════════════════════════════════════
def simulate_rothc(context: Dict) -> Dict:
    initial_soc = context.get("soil", {}).get("organic_carbon_pct", 1.5)
    years = context.get("years", 20)
    interventions = context.get("interventions", [])
    
    # RothC annual decomposition rate (simplified)
    annual_change = 0.05  # Base sequestration per year
    
    # Boost from interventions
    for intv in interventions:
        intv_id = intv.get("intervention_id", "")
        coverage = intv.get("coverage_pct", 100) / 100
        if "tree" in intv_id or "windbreak" in intv_id:
            annual_change += 0.08 * coverage
        if "cover_crop" in intv_id or "mulch" in intv_id:
            annual_change += 0.04 * coverage
        if "biofertilizer" in intv_id or "no_till" in intv_id:
            annual_change += 0.03 * coverage
    
    time_series = []
    current_soc = initial_soc
    for year in range(years + 1):
        co2_seq = annual_change * 3.67  # C to CO2 conversion
        credits = co2_seq * 0.85  # Verification factor
        time_series.append({
            "year": year,
            "soc_ton_ha": round(current_soc, 3),
            "sequestration_ton_co2": round(co2_seq, 3),
            "credits": round(credits, 3),
            "credits_value_usd": round(credits * 40, 2),
        })
        current_soc += annual_change
    
    final_soc = time_series[-1]["soc_ton_ha"]
    total_seq = sum(t["sequestration_ton_co2"] for t in time_series)
    total_credits = sum(t["credits"] for t in time_series)
    
    return {
        "simulation_id": f"rothc-{datetime.now().timestamp():.0f}",
        "simulation_type": "soil_carbon",
        "status": "completed",
        "summary": {
            "initial_soc_t_ha": initial_soc,
            "final_soc_t_ha": final_soc,
            "soc_change_t_ha": round(final_soc - initial_soc, 3),
            "total_co2_sequestered": round(total_seq, 2),
            "credits_earned": round(total_credits, 2),
            "credits_value_usd": round(total_credits * 40, 2),
        },
        "time_series": time_series,
    }


# ═══════════════════════════════════════════════════════════════
# 🌬️ WEPS Wind Erosion Simulation
# ═══════════════════════════════════════════════════════════════
def simulate_wind_erosion(context: Dict) -> Dict:
    wind_speed = context.get("weather", {}).get("wind_speed_ms", 12)
    soil_texture = context.get("soil", {}).get("texture", "loam")
    coverage_pct = context.get("coverage_pct", 30)
    interventions = context.get("interventions", [])
    
    # Base erosion (ton/ha/year)
    texture_factors = {"sand": 1.5, "loam": 1.0, "clay": 0.6, "sandy_loam": 1.3}
    texture_factor = texture_factors.get(soil_texture, 1.0)
    
    # WEPS simplified: E = f(wind) * f(coverage) * f(texture)
    wind_factor = (wind_speed / 10) ** 2
    coverage_protection = 1 - (coverage_pct / 100) * 0.8
    
    base_erosion = 25 * wind_factor * coverage_protection * texture_factor
    
    # Windbreak reduction
    windbreak_reduction = 0
    for intv in interventions:
        intv_id = intv.get("intervention_id", "")
        if "windbreak" in intv_id or "tree" in intv_id:
            coverage = intv.get("coverage_pct", 100) / 100
            windbreak_reduction += 0.6 * coverage
    
    final_erosion = base_erosion * (1 - min(0.9, windbreak_reduction))
    
    risk_level = (
        "low" if final_erosion < 5
        else "moderate" if final_erosion < 15
        else "high" if final_erosion < 30
        else "severe"
    )
    
    return {
        "simulation_id": f"weps-{datetime.now().timestamp():.0f}",
        "simulation_type": "wind_erosion",
        "status": "completed",
        "summary": {
            "wind_speed_ms": wind_speed,
            "erosion_ton_ha_year": round(final_erosion, 2),
            "base_erosion": round(base_erosion, 2),
            "reduction_pct": round((1 - final_erosion / max(0.1, base_erosion)) * 100, 1),
            "risk_level": risk_level,
            "protected_area_ha": context.get("area_ha", 50) * min(0.8, windbreak_reduction),
        },
    }


# ═══════════════════════════════════════════════════════════════
# 💧 RUSLE Water Erosion
# ═══════════════════════════════════════════════════════════════
def simulate_water_erosion(context: Dict) -> Dict:
    rainfall = context.get("weather", {}).get("precipitation_mm", 300)
    slope = context.get("topography", {}).get("slope_pct", 8)
    coverage = context.get("coverage_pct", 30)
    interventions = context.get("interventions", [])
    
    # RUSLE: A = R × K × L × S × C × P
    R = rainfall / 10  # Rainfall erosivity
    K = 0.3  # Soil erodibility (average)
    L = 1.0  # Slope length (assumed)
    S = (slope / 10) ** 0.5  # Slope steepness
    C = 1 - (coverage / 100) * 0.7  # Cover factor
    P = 1.0  # Practice factor
    
    # Practice reduction from interventions
    for intv in interventions:
        intv_id = intv.get("intervention_id", "")
        if "terrace" in intv_id:
            P *= 0.3
        elif "contour" in intv_id or "bunds" in intv_id:
            P *= 0.5
        elif "check_dam" in intv_id or "crescent" in intv_id:
            P *= 0.6
    
    soil_loss = R * K * L * S * C * P
    
    return {
        "simulation_id": f"rusle-{datetime.now().timestamp():.0f}",
        "simulation_type": "water_erosion",
        "status": "completed",
        "summary": {
            "soil_loss_ton_ha_year": round(soil_loss, 2),
            "R_factor": round(R, 2),
            "K_factor": round(K, 2),
            "LS_factor": round(L * S, 2),
            "C_factor": round(C, 2),
            "P_factor": round(P, 2),
            "risk_level": "low" if soil_loss < 5 else "moderate" if soil_loss < 15 else "high",
        },
    }


# ═══════════════════════════════════════════════════════════════
# 💧 Green-Ampt Infiltration
# ═══════════════════════════════════════════════════════════════
def simulate_infiltration(context: Dict) -> Dict:
    rainfall_mm = context.get("weather", {}).get("precipitation_mm", 500)
    soil_texture = context.get("soil", {}).get("texture", "loam")
    
    ks_map = {"sand": 25, "loam": 15, "clay": 5, "sandy_loam": 20, "clay_loam": 8}
    ks = ks_map.get(soil_texture, 15)
    
    # Green-Ampt simplified
    time_series = []
    cumulative = 0
    for hour in range(25):
        rate = ks * (1 + 100 / max(1, cumulative + 1))
        rate = min(rate, rainfall_mm / 24)
        cumulative += rate
        time_series.append({
            "hour": hour,
            "rate_mm_hr": round(rate, 2),
            "cumulative_mm": round(cumulative, 2),
        })
        if cumulative >= rainfall_mm * 0.8:
            break
    
    infiltration = min(rainfall_mm * 0.9, cumulative)
    runoff = rainfall_mm - infiltration
    
    return {
        "simulation_id": f"greenampt-{datetime.now().timestamp():.0f}",
        "simulation_type": "infiltration",
        "status": "completed",
        "summary": {
            "precipitation_mm": rainfall_mm,
            "infiltration_mm": round(infiltration, 2),
            "runoff_mm": round(runoff, 2),
            "infiltration_efficiency_pct": round(infiltration / rainfall_mm * 100, 1),
            "ks_mm_hr": ks,
        },
        "time_series": time_series,
    }


# ═══════════════════════════════════════════════════════════════
# 🏗️ Windbreak Design
# ═══════════════════════════════════════════════════════════════
def simulate_windbreak(context: Dict) -> Dict:
    params = context.get("windbreak", {})
    height = params.get("height_m", 8)
    length = params.get("length_m", 200)
    porosity = params.get("porosity_pct", 40)
    rows = params.get("rows", 3)
    
    # Scientific model
    protected_distance = height * 10 * rows
    area_ha = context.get("area_ha", 50)
    protected_area = (protected_distance * length) / 10000
    
    # Optimal porosity is 40%
    efficiency = 1 - abs(porosity - 40) / 40
    wind_reduction = 65 * efficiency
    
    # Trees calculation (2m spacing)
    trees_per_row = int(length / 2)
    total_trees = trees_per_row * rows
    
    # Economics
    cost_per_tree = 15  # USD
    total_cost = total_trees * cost_per_tree
    annual_benefit = protected_area * 200  # USD/ha/year
    payback = total_cost / max(1, annual_benefit)
    
    # Carbon
    co2_per_tree = 0.025  # ton/year
    annual_co2 = total_trees * co2_per_tree
    
    return {
        "simulation_id": f"windbreak-{datetime.now().timestamp():.0f}",
        "simulation_type": "windbreak_design",
        "status": "completed",
        "summary": {
            "total_trees": total_trees,
            "protected_distance_m": protected_distance,
            "protected_area_ha": round(protected_area, 2),
            "wind_reduction_pct": round(wind_reduction, 1),
            "estimated_cost_usd": total_cost,
            "annual_benefit_usd": round(annual_benefit, 0),
            "payback_years": round(payback, 1),
            "annual_co2_sequestered_ton": round(annual_co2, 2),
        },
    }


# ═══════════════════════════════════════════════════════════════
# 🤖 AI Advisor
# ═══════════════════════════════════════════════════════════════
def get_ai_recommendations(context: Dict, results: Dict) -> List[str]:
    recommendations = []
    
    erosion = results.get("erosion", {}).get("summary", {})
    hydrology = results.get("hydrology", {}).get("summary", {})
    carbon = results.get("carbon", {}).get("summary", {})
    
    if erosion.get("erosion_ton_ha_year", 0) > 15 or erosion.get("soil_loss_ton_ha_year", 0) > 15:
        recommendations.append({
            "priority": "high",
            "category": "فرسایش",
            "title": "کاهش فرسایش بحرانی",
            "description": "فرسایش بالاتر از حد مجاز است. افزودن ۳ ردیف بادشکن Cypress می‌تواند فرسایش بادی را ۶۰٪ کاهش دهد.",
            "action": "tree_planting",
            "params": {"species": "cypress", "rows": 3},
        })
    
    if hydrology.get("runoff_mm", 0) > 100:
        recommendations.append({
            "priority": "high",
            "category": "آب",
            "title": "کاهش رواناب",
            "description": "رواناب بالاست. افزودن ۶ هلالی آبگیر می‌تواند ۴۰٪ رواناب را مهار و آبخوان را تغذیه کند.",
            "action": "crescent_bunds",
            "params": {"count": 6},
        })
    
    if carbon.get("initial_soc_t_ha", 2) < 1.5:
        recommendations.append({
            "priority": "medium",
            "category": "کربن",
            "title": "افزایش ماده آلی خاک",
            "description": "کربن خاک پایین است. استفاده از کود زیستی نوژین (۵۰۰ kg/ha) + کشت شبدر می‌تواند ۲۰٪ کربن را افزایش دهد.",
            "action": "biofertilizer",
            "params": {"amount_kg_ha": 500},
        })
    
    if not recommendations:
        recommendations.append({
            "priority": "info",
            "category": "بهینه‌سازی",
            "title": "سناریو خوب است",
            "description": "سناریوی فعلی پایدار است. برای بهبود بیشتر، کشت چندلایه (Agroforestry) را امتحان کنید.",
            "action": "alley_cropping",
            "params": {},
        })
    
    return recommendations


# ═══════════════════════════════════════════════════════════════
# 📊 API Endpoints
# ═══════════════════════════════════════════════════════════════

@app.post("/api/v1/simulation/run")
def run_simulation(request: SimulationRequest):
    sim_type = request.simulation_type
    ctx = request.context
    
    if sim_type == "crop_growth":
        return simulate_aquacrop(ctx)
    elif sim_type == "soil_carbon":
        return simulate_rothc(ctx)
    elif sim_type == "wind_erosion":
        return simulate_wind_erosion(ctx)
    elif sim_type == "water_erosion":
        return simulate_water_erosion(ctx)
    elif sim_type == "infiltration":
        return simulate_infiltration(ctx)
    elif sim_type == "windbreak_design":
        return simulate_windbreak(ctx)
    else:
        return {"error": f"Unknown simulation type: {sim_type}"}


@app.post("/api/v1/simulation/comprehensive")
def comprehensive_simulation(request: SimulationRequest):
    ctx = request.context
    interventions = ctx.get("interventions", [])
    
    # Coverage from interventions
    coverage = sum(i.get("coverage_pct", 0) for i in interventions) / max(1, len(interventions))
    ctx["coverage_pct"] = coverage
    
    crop = simulate_aquacrop(ctx)
    carbon = simulate_rothc(ctx)
    wind = simulate_wind_erosion(ctx)
    water = simulate_water_erosion(ctx)
    infiltration = simulate_infiltration(ctx)
    
    # Sustainability Score (0-100)
    wind_erosion = wind.get("summary", {}).get("erosion_ton_ha_year", 25)
    water_erosion = water.get("summary", {}).get("soil_loss_ton_ha_year", 15)
    runoff = infiltration.get("summary", {}).get("runoff_mm", 200)
    final_soc = carbon.get("summary", {}).get("final_soc_t_ha", 1.5)
    
    erosion_score = max(0, 100 - (wind_erosion + water_erosion) * 2)
    water_score = max(0, 100 - runoff / 3)
    carbon_score = min(100, final_soc * 40)
    
    sustainability = round(
        erosion_score * 0.35 +
        water_score * 0.35 +
        carbon_score * 0.3,
        1
    )
    
    results = {
        "crop": crop,
        "carbon": carbon,
        "erosion": {"wind": wind, "water": water},
        "hydrology": infiltration,
        "sustainability_score": sustainability,
        "score_breakdown": {
            "erosion": round(erosion_score, 1),
            "water": round(water_score, 1),
            "carbon": round(carbon_score, 1),
        },
        "recommendations": get_ai_recommendations(ctx, {
            "erosion": wind,
            "hydrology": infiltration,
            "carbon": carbon,
        }),
    }
    
    return results


@app.post("/api/v1/simulation/erosion-analysis")
def erosion_analysis(request: SimulationRequest):
    ctx = request.context
    return {
        "wind": simulate_wind_erosion(ctx),
        "water": simulate_water_erosion(ctx),
    }


@app.post("/api/v1/simulation/water-budget")
def water_budget(request: SimulationRequest):
    ctx = request.context
    return {
        "infiltration": simulate_infiltration(ctx),
        "watershed": {
            "status": "completed",
            "summary": {
                "precipitation_mm": ctx.get("weather", {}).get("precipitation_mm", 500),
                "runoff_mm": 120,
                "aquifer_recharge_mm": 84,
            },
        },
    }


@app.post("/api/v1/simulation/windbreak-design")
def windbreak_design(request: SimulationRequest):
    return simulate_windbreak(request.context)


@app.post("/api/v1/simulation/multi-layer-plan")
def multi_layer_plan(request: SimulationRequest):
    return {
        "status": "completed",
        "summary": {
            "total_layers": 3,
            "total_yield_ton_ha": 15.8,
            "land_equivalent_ratio": 1.35,
            "biodiversity_score": 82,
            "total_revenue_usd": 8500,
        },
    }


@app.get("/api/v1/livestock/animal-types")
def livestock_types():
    return [
        {"type": "cattle", "name": "گاو", "avg_weight_kg": 450},
        {"type": "sheep", "name": "گوسفند", "avg_weight_kg": 50},
        {"type": "goat", "name": "بز", "avg_weight_kg": 40},
        {"type": "poultry", "name": "مرغ", "avg_weight_kg": 2},
    ]


@app.post("/api/v1/livestock/simulate")
def livestock_simulate(request: dict):
    herd = request.get("herd", {})
    animal_type = herd.get("animal_type", "cattle")
    head_count = herd.get("head_count", 20)
    
    params = {
        "cattle": {"milk": 15, "meat": 220, "water": 50, "manure": 36},
        "sheep": {"milk": 1, "meat": 20, "water": 6, "manure": 4, "wool": 3.5},
        "goat": {"milk": 2.5, "meat": 15, "water": 5, "manure": 3.2},
        "poultry": {"eggs": 0.8, "meat": 2.5, "water": 0.3, "manure": 0.12},
    }.get(animal_type, {"milk": 0, "meat": 10, "water": 5, "manure": 3})
    
    return {
        "simulation_id": f"livestock-{datetime.now().timestamp():.0f}",
        "animal_type": animal_type,
        "herd_size": head_count,
        "status": "completed",
        "production": {
            "milk_kg_day": params.get("milk", 0) * head_count,
            "meat_kg_year": params.get("meat", 0) * head_count * 0.3,
            "eggs_day": params.get("eggs", 0) * head_count,
            "wool_kg_year": params.get("wool", 0) * head_count,
            "manure_kg_day": params.get("manure", 0) * head_count,
        },
        "carrying_capacity": 50,
        "overgrazing_risk": "low" if head_count < 40 else "moderate" if head_count < 80 else "high",
    }


@app.post("/api/v1/ai/recommend")
def ai_recommend(request: SimulationRequest):
    ctx = request.context
    interventions = ctx.get("interventions", [])
    
    # Run all simulations
    crop = simulate_aquacrop(ctx)
    carbon = simulate_rothc(ctx)
    wind = simulate_wind_erosion(ctx)
    water = simulate_water_erosion(ctx)
    infiltration = simulate_infiltration(ctx)
    
    recommendations = get_ai_recommendations(ctx, {
        "erosion": wind,
        "hydrology": infiltration,
        "carbon": carbon,
    })
    
    return {
        "recommendations": recommendations,
        "context_summary": {
            "wind_erosion": wind.get("summary", {}).get("erosion_ton_ha_year"),
            "water_erosion": water.get("summary", {}).get("soil_loss_ton_ha_year"),
            "runoff_mm": infiltration.get("summary", {}).get("runoff_mm"),
            "final_soc": carbon.get("summary", {}).get("final_soc_t_ha"),
        },
    }


if __name__ == "__main__":
    print("
" + "=" * 70)
    print("  🚀 Eco Nojin Virtual Land Lab API")
    print("=" * 70)
    print("\n  🌐 URL: http://localhost:8000")
    print("  📖 Docs: http://localhost:8000/docs")
    print("\n" + "=" * 70 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
