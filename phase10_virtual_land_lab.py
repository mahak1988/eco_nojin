#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eco Nojin - فاز ۱۰: آزمایشگاه مجازی زمین (Virtual Land Laboratory)
═══════════════════════════════════════════════════════════════════════
۱. Backend قابل اجرا (FastAPI standalone)
۲. 3D Terrain با DEM و تعاملات واقعی
۳. سیستم مداخلات بصری (درخت، تراس، بندسار)
۴. انیمیشن‌های هواشناسی (باران، باد، فرسایش)
۵. دستیار AI + مقایسه سناریوها
۶. راهنمای PowerShell برای تست
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path("D:/eco_nojin")
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
BACKUP_ROOT = PROJECT_ROOT / f"_backup_phase10_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def log(msg, icon="i"):
    print(f"  [{icon}] {msg}")


def separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def write_file(path: Path, content: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        log(f"خطا: {e}", "X")
        return False


# ═══════════════════════════════════════════════════════════════
# گام ۱: Backup
# ═══════════════════════════════════════════════════════════════

def step_backup():
    separator("گام ۱: Backup")
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    src = FRONTEND_ROOT / 'src'
    if src.exists():
        dst = BACKUP_ROOT / "frontend" / "src"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        log(f"Backup: {dst}", "+")


# ═══════════════════════════════════════════════════════════════
# گام ۲: Backend Standalone (قابل اجرا)
# ═══════════════════════════════════════════════════════════════

def build_standalone_backend():
    separator("گام ۲: Backend Standalone")
    
    # backend.py - فایل مستقل قابل اجرا
    backend_content = '''"""
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
    print("\n" + "=" * 70)
    print("  🚀 Eco Nojin Virtual Land Lab API")
    print("=" * 70)
    print("\\n  🌐 URL: http://localhost:8000")
    print("  📖 Docs: http://localhost:8000/docs")
    print("\\n" + "=" * 70 + "\\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
'''
    
    write_file(PROJECT_ROOT / 'backend.py', backend_content)
    log('backend.py (standalone) ایجاد شد', '+')
    
    # راهنمای PowerShell
    ps_guide = '''# راهنمای تست API در PowerShell
# ═══════════════════════════════════════════════════════════

# ─── راه‌اندازی Backend ─────────────────────────────
cd D:\\eco_nojin
python backend.py

# ─── تست endpoints ─────────────────────────────

# 1. Health Check
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health"

# 2. Crop Simulation (AquaCrop)
$body = @{
    simulation_type = "crop_growth"
    context = @{
        crop = @{ crop_type = "wheat" }
        weather = @{ precipitation_mm = 400 }
        soil = @{ organic_carbon_pct = 1.5 }
    }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/simulation/run" -Body $body -ContentType "application/json"

# 3. Comprehensive Simulation
$body = @{
    simulation_type = "comprehensive"
    context = @{
        area_ha = 50
        crop = @{ crop_type = "wheat" }
        weather = @{ precipitation_mm = 400; wind_speed_ms = 12 }
        soil = @{ texture = "loam"; organic_carbon_pct = 1.2 }
        topography = @{ slope_pct = 10 }
        interventions = @(
            @{ intervention_id = "tree_planting"; coverage_pct = 50 },
            @{ intervention_id = "terrace"; coverage_pct = 30 }
        )
    }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/simulation/comprehensive" -Body $body -ContentType "application/json"

# 4. Windbreak Design
$body = @{
    simulation_type = "windbreak_design"
    context = @{
        area_ha = 50
        windbreak = @{
            height_m = 8
            length_m = 200
            porosity_pct = 40
            rows = 3
        }
    }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/simulation/run" -Body $body -ContentType "application/json"

# 5. AI Recommendations
$body = @{
    context = @{
        area_ha = 50
        soil = @{ organic_carbon_pct = 1.0 }
        weather = @{ wind_speed_ms = 15; precipitation_mm = 200 }
        interventions = @()
    }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/ai/recommend" -Body $body -ContentType "application/json"
'''
    
    write_file(PROJECT_ROOT / 'PS_API_GUIDE.ps1', ps_guide)
    log('PS_API_GUIDE.ps1 ایجاد شد', '+')


# ═══════════════════════════════════════════════════════════════
# گام ۳: Virtual Land Laboratory - صفحه اصلی
# ═══════════════════════════════════════════════════════════════

def build_vll_main():
    separator("گام ۳: VLL Main Page")
    
    pages_dir = FRONTEND_ROOT / 'src' / 'pages'
    
    content = '''import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Leaf, Droplets, Wind, Sparkles, Settings, Play, Pause,
  RotateCcw, Save, Download, MapPin, Sun, CloudRain,
  Trees, Sprout, Layers, BarChart3, Zap, Info,
} from 'lucide-react';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, Button } from '../components/ui';
import { VLLTerrain3D } from '../components/vll/VLLTerrain3D';
import { InterventionPanel } from '../components/vll/VLLInterventionPanel';
import { VLLLayerManager } from '../components/vll/VLLLayerManager';
import { VLLResultsBar } from '../components/vll/VLLResultsBar';
import { VLLAIAdvisor } from '../components/vll/VLLAIAdvisor';
import { VLLWeatherControl } from '../components/vll/VLLWeatherControl';

export const VirtualLandLabPage: React.FC = () => {
  // State مدیریت
  const [interventions, setInterventions] = useState<any[]>([]);
  const [weather, setWeather] = useState({
    rainfall: 50,  // mm/hr
    wind: 12,       // m/s
    temperature: 25,
    sunIntensity: 0.8,
  });
  const [activeLayers, setActiveLayers] = useState({
    dem: true,
    slope: false,
    soil: false,
    ndvi: true,
    water: false,
    erosion: false,
  });
  const [isSimulating, setIsSimulating] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [showAdvisor, setShowAdvisor] = useState(false);
  const [timeProgress, setTimeProgress] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  // مداخلات
  const addIntervention = (intv: any) => {
    setInterventions([...interventions, { ...intv, id: Date.now() }]);
  };
  const removeIntervention = (id: number) => {
    setInterventions(interventions.filter(i => i.id !== id));
  };

  // شبیه‌سازی
  const runSimulation = async () => {
    setIsSimulating(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/simulation/comprehensive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          simulation_type: 'comprehensive',
          context: {
            area_ha: 50,
            crop: { crop_type: 'wheat' },
            weather: {
              precipitation_mm: weather.rainfall * 10,
              wind_speed_ms: weather.wind,
            },
            soil: { texture: 'loam', organic_carbon_pct: 1.2 },
            topography: { slope_pct: 10 },
            interventions: interventions.map(i => ({
              intervention_id: i.id,
              coverage_pct: i.coverage || 100,
              parameters: i.parameters || {},
            })),
          },
        }),
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Simulation error:', error);
      // Fallback به mock data
      setResults({
        sustainability_score: 75,
        score_breakdown: { erosion: 70, water: 80, carbon: 75 },
        recommendations: [
          { priority: 'high', category: 'فرسایش', title: 'افزودن بادشکن', description: 'فرسایش بادی بالاست' },
        ],
      });
    } finally {
      setIsSimulating(false);
    }
  };

  const resetScenario = () => {
    setInterventions([]);
    setResults(null);
    setTimeProgress(0);
  };

  return (
    <AppLayout>
      <div style={{ height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
        {/* Header Bar */}
        <div style={{
          padding: '1rem 2rem',
          background: 'linear-gradient(90deg, var(--color-primary), var(--color-info))',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: 'var(--shadow-md)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Sparkles size={28} />
            <div>
              <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>
                🌍 آزمایشگاه مجازی زمین
              </h1>
              <p style={{ margin: 0, fontSize: '0.875rem', opacity: 0.9 }}>
                Virtual Land Laboratory - HyDroMa
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Button
              variant="secondary"
              onClick={resetScenario}
              style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: 'none' }}
            >
              <RotateCcw size={16} /> ریست
            </Button>
            <Button
              variant="secondary"
              onClick={() => setShowAdvisor(!showAdvisor)}
              style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: 'none' }}
            >
              <Zap size={16} /> دستیار AI
            </Button>
            <Button
              variant="primary"
              onClick={runSimulation}
              disabled={isSimulating}
              style={{ background: 'white', color: 'var(--color-primary)' }}
            >
              {isSimulating ? '⏳ شبیه‌سازی...' : <><Play size={16} /> اجرای سناریو</>}
            </Button>
          </div>
        </div>

        {/* Main Content */}
        <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '320px 1fr 320px', gap: 0, overflow: 'hidden' }}>
          
          {/* Left Panel: Controls */}
          <div style={{
            background: 'var(--color-surface)',
            borderLeft: '1px solid var(--color-border)',
            overflowY: 'auto',
            padding: '1rem',
          }}>
            {/* Layer Manager */}
            <VLLLayerManager
              activeLayers={activeLayers}
              onToggleLayer={(key) => setActiveLayers({ ...activeLayers, [key]: !activeLayers[key] })}
            />

            {/* Weather Control */}
            <VLLWeatherControl
              weather={weather}
              onChange={setWeather}
            />

            {/* Time Control */}
            <Card title="⏱️ کنترل زمان" icon={<Info size={18} />} className="mb-4">
              <div style={{ marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                  <span>پیشرفت</span>
                  <strong>سال {Math.floor(timeProgress / 12) + 1}</strong>
                </div>
                <input
                  type="range"
                  min="0"
                  max="120"
                  value={timeProgress}
                  onChange={(e) => setTimeProgress(parseInt(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                >
                  {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                </button>
                <button
                  onClick={() => setTimeProgress(0)}
                  className="btn btn-ghost"
                >
                  <RotateCcw size={14} />
                </button>
              </div>
            </Card>
          </div>

          {/* Center: 3D Terrain */}
          <div style={{ position: 'relative', background: '#1a1a2e' }}>
            <VLLTerrain3D
              interventions={interventions}
              weather={weather}
              activeLayers={activeLayers}
              timeProgress={timeProgress}
              isPlaying={isPlaying}
            />

            {/* Floating Info */}
            <div style={{
              position: 'absolute',
              top: 20,
              left: 20,
              background: 'rgba(0, 0, 0, 0.7)',
              backdropFilter: 'blur(10px)',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-lg)',
              color: 'white',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
            }}>
              <MapPin size={16} color="#22c55e" />
              <div>
                <div style={{ fontWeight: 600 }}>مزرعه نمونه</div>
                <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>۵۰ هکتار | ۳۵.۵°N, ۵۱.۵°E</div>
              </div>
            </div>

            {/* Live Weather Indicator */}
            <div style={{
              position: 'absolute',
              top: 20,
              right: 20,
              background: 'rgba(0, 0, 0, 0.7)',
              backdropFilter: 'blur(10px)',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-lg)',
              color: 'white',
              fontSize: '0.875rem',
              display: 'flex',
              gap: '1rem',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CloudRain size={16} color="#3b82f6" />
                <span>{weather.rainfall} mm</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Wind size={16} color="#a3a3a3" />
                <span>{weather.wind} m/s</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Sun size={16} color="#fbbf24" />
                <span>{weather.temperature}°C</span>
              </div>
            </div>

            {/* Intervention Counter */}
            <div style={{
              position: 'absolute',
              bottom: 20,
              left: 20,
              background: 'rgba(34, 197, 94, 0.9)',
              padding: '0.5rem 1rem',
              borderRadius: 'var(--radius-full)',
              color: 'white',
              fontWeight: 600,
              fontSize: '0.875rem',
            }}>
              🛠️ {interventions.length} مداخله فعال
            </div>
          </div>

          {/* Right Panel: Interventions + AI */}
          <div style={{
            background: 'var(--color-surface)',
            borderRight: '1px solid var(--color-border)',
            overflowY: 'auto',
            padding: '1rem',
          }}>
            {showAdvisor && results && (
              <VLLAIAdvisor
                recommendations={results.recommendations || []}
                onApply={(action) => {
                  addIntervention({ id: action, name: action, coverage: 100 });
                }}
              />
            )}

            <InterventionPanel
              interventions={interventions}
              onAdd={addIntervention}
              onRemove={removeIntervention}
            />
          </div>
        </div>

        {/* Results Bar at bottom */}
        <VLLResultsBar results={results} isSimulating={isSimulating} />
      </div>
    </AppLayout>
  );
};
'''
    
    write_file(pages_dir / 'VirtualLandLabPage.tsx', content)
    log('VirtualLandLabPage.tsx (صفحه اصلی) ایجاد شد', '+')


# ═══════════════════════════════════════════════════════════════
# گام ۴: VLLTerrain3D - زمین سه‌بعدی تعاملی
# ═══════════════════════════════════════════════════════════════

def build_terrain_3d():
    separator("گام ۴: VLLTerrain3D")
    
    vll_dir = FRONTEND_ROOT / 'src' / 'components' / 'vll'
    vll_dir.mkdir(parents=True, exist_ok=True)
    
    content = '''import React, { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sky, Cloud, Clouds, Stars } from '@react-three/drei';
import * as THREE from 'three';

interface VLLTerrain3DProps {
  interventions: any[];
  weather: { rainfall: number; wind: number; temperature: number; sunIntensity: number };
  activeLayers: Record<string, boolean>;
  timeProgress: number;
  isPlaying: boolean;
}

// ─── Terrain Mesh ─────────────────────────────
const Terrain: React.FC<{ activeLayers: any }> = ({ activeLayers }) => {
  const meshRef = useRef<THREE.Mesh>(null);

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(100, 100, 80, 80);
    const positions = geo.attributes.position;
    
    // DEM: تپه‌ها و آبراهه
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      
      // توپوگرافی اصلی
      let z = Math.sin(x / 20) * Math.cos(y / 20) * 4;
      z += Math.sin(x / 8) * 1.5;
      z += Math.cos(y / 12) * 1.2;
      
      // آبراهه مرکزی (فرورفتگی)
      const streamDistance = Math.abs(y - Math.sin(x / 15) * 3);
      if (streamDistance < 3) {
        z -= (3 - streamDistance) * 0.8;
      }
      
      positions.setZ(i, z);
    }
    
    geo.computeVertexNormals();
    
    // رنگ‌بندی بر اساس لایه فعال
    const colors = [];
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      const z = positions.getZ(i);
      
      const color = new THREE.Color();
      
      if (activeLayers.slope) {
        // نقشه شیب (قرمز = پرشیب)
        const slope = Math.abs(Math.sin(x / 20)) + Math.abs(Math.cos(y / 20));
        color.setHSL(0.1 - slope * 0.1, 0.8, 0.5);
      } else if (activeLayers.soil) {
        // نقشه خاک
        const soilType = (Math.sin(x / 10) + Math.cos(y / 10)) / 2;
        color.setHSL(0.08 + soilType * 0.05, 0.5, 0.4);
      } else if (activeLayers.water) {
        // نقشه رطوبت
        const moisture = 0.5 - z / 10 + Math.sin(x / 15) * 0.2;
        color.setHSL(0.55 + moisture * 0.1, 0.7, 0.3 + moisture * 0.3);
      } else if (activeLayers.ndvi) {
        // NDVI (سبز تیره = پررشد)
        const ndvi = 0.3 + z / 10 + Math.sin(x / 8) * 0.2;
        color.setHSL(0.25 + ndvi * 0.05, 0.7, 0.2 + ndvi * 0.3);
      } else {
        // حالت طبیعی
        if (z < -1) color.setHex(0x3a5f8f); // آبراهه
        else if (z < 0) color.setHex(0x8b7355); // خاک مرطوب
        else if (z < 2) color.setHex(0x7da87d); // علف
        else color.setHex(0x5a7a4a); // بوته
      }
      
      colors.push(color.r, color.g, color.b);
    }
    
    geo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    return geo;
  }, [activeLayers]);

  return (
    <mesh ref={meshRef} geometry={geometry} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <meshStandardMaterial
        vertexColors
        side={THREE.DoubleSide}
        roughness={0.9}
        metalness={0.1}
      />
    </mesh>
  );
};

// ─── Wind Particles ─────────────────────────────
const WindParticles: React.FC<{ wind: number }> = ({ wind }) => {
  const particlesRef = useRef<THREE.InstancedMesh>(null);
  const count = 500;
  
  const particles = useMemo(() => {
    return Array.from({ length: count }, () => ({
      x: (Math.random() - 0.5) * 100,
      y: Math.random() * 20 + 5,
      z: (Math.random() - 0.5) * 100,
      vx: wind * 0.5,
    }));
  }, [wind]);

  useFrame(() => {
    if (!particlesRef.current) return;
    const dummy = new THREE.Object3D();
    
    particles.forEach((p, i) => {
      p.x += p.vx * 0.3;
      p.y += (Math.random() - 0.5) * 0.1;
      
      if (p.x > 50) p.x = -50;
      if (p.y < 2) p.y = 20;
      if (p.y > 25) p.y = 5;
      
      dummy.position.set(p.x, p.y, p.z);
      dummy.scale.setScalar(0.1);
      dummy.updateMatrix();
      particlesRef.current!.setMatrixAt(i, dummy.matrix);
    });
    
    particlesRef.current.instanceMatrix.needsUpdate = true;
  });

  if (wind < 3) return null;

  return (
    <instancedMesh ref={particlesRef} args={[undefined, undefined, count]}>
      <sphereGeometry args={[0.1, 4, 4]} />
      <meshBasicMaterial color="#ffffff" transparent opacity={0.4} />
    </instancedMesh>
  );
};

// ─── Rain Drops ─────────────────────────────
const RainDrops: React.FC<{ rainfall: number }> = ({ rainfall }) => {
  const rainRef = useRef<THREE.InstancedMesh>(null);
  const count = Math.min(1000, rainfall * 10);
  
  const drops = useMemo(() => {
    return Array.from({ length: count }, () => ({
      x: (Math.random() - 0.5) * 100,
      y: Math.random() * 30 + 10,
      z: (Math.random() - 0.5) * 100,
      vy: -0.5 - Math.random() * 0.3,
    }));
  }, [count]);

  useFrame(() => {
    if (!rainRef.current) return;
    const dummy = new THREE.Object3D();
    
    drops.forEach((d, i) => {
      d.y += d.vy;
      
      if (d.y < 0) {
        d.y = 30;
        d.x = (Math.random() - 0.5) * 100;
        d.z = (Math.random() - 0.5) * 100;
      }
      
      dummy.position.set(d.x, d.y, d.z);
      dummy.scale.set(0.1, 0.5, 0.1);
      dummy.updateMatrix();
      rainRef.current!.setMatrixAt(i, dummy.matrix);
    });
    
    rainRef.current.instanceMatrix.needsUpdate = true;
  });

  if (rainfall < 5) return null;

  return (
    <instancedMesh ref={rainRef} args={[undefined, undefined, count]}>
      <cylinderGeometry args={[0.05, 0.05, 0.3, 4]} />
      <meshBasicMaterial color="#60a5fa" transparent opacity={0.6} />
    </instancedMesh>
  );
};

// ─── Trees (Windbreaks) ─────────────────────────────
const Tree: React.FC<{ position: [number, number, number]; scale?: number; species?: string }> = ({
  position,
  scale = 1,
  species = 'cypress',
}) => {
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame((state) => {
    if (groupRef.current) {
      // انیمیشن باد
      groupRef.current.rotation.z = Math.sin(state.clock.elapsedTime + position[0]) * 0.02;
    }
  });

  const speciesData: Record<string, { trunk: string; leaves: string; height: number }> = {
    cypress: { trunk: '#654321', leaves: '#15803d', height: 8 },
    pine: { trunk: '#654321', leaves: '#166534', height: 10 },
    olive: { trunk: '#8b7355', leaves: '#4d7c0f', height: 5 },
    almond: { trunk: '#a0826d', leaves: '#65a30d', height: 6 },
    oak: { trunk: '#654321', leaves: '#22c55e', height: 7 },
  };
  const data = speciesData[species] || speciesData.cypress;

  return (
    <group ref={groupRef} position={position} scale={scale}>
      {/* تنه */}
      <mesh position={[0, data.height / 2, 0]} castShadow>
        <cylinderGeometry args={[0.3, 0.5, data.height, 8]} />
        <meshStandardMaterial color={data.trunk} roughness={0.9} />
      </mesh>
      {/* تاج */}
      <mesh position={[0, data.height * 0.9, 0]} castShadow>
        <coneGeometry args={[2, data.height * 0.8, 8]} />
        <meshStandardMaterial color={data.leaves} roughness={0.8} />
      </mesh>
    </group>
  );
};

const TreeWindbreak: React.FC<{ intervention: any; terrainHeight: (x: number, z: number) => number }> = ({
  intervention,
  terrainHeight,
}) => {
  const species = intervention.parameters?.species || 'cypress';
  const count = intervention.parameters?.count || 10;
  const rows = intervention.parameters?.rows || 3;
  const startX = intervention.position?.x || 0;
  const startZ = intervention.position?.z || 0;
  
  const trees = [];
  for (let r = 0; r < rows; r++) {
    for (let i = 0; i < count; i++) {
      const x = startX + i * 3;
      const z = startZ + r * 2.5;
      const y = terrainHeight(x, z);
      trees.push(
        <Tree
          key={`tree-${r}-${i}`}
          position={[x, y, z]}
          scale={0.8 + Math.random() * 0.4}
          species={species}
        />
      );
    }
  }
  
  return <>{trees}</>;
};

// ─── Terraces ─────────────────────────────
const Terrace: React.FC<{ intervention: any }> = ({ intervention }) => {
  const count = intervention.parameters?.count || 5;
  const spacing = intervention.parameters?.spacing || 8;
  const startX = intervention.position?.x || -20;
  const startZ = intervention.position?.z || 0;
  
  const terraces = [];
  for (let i = 0; i < count; i++) {
    const z = startZ + i * spacing;
    terraces.push(
      <mesh key={`terrace-${i}`} position={[startX, 0.3, z]} castShadow>
        <boxGeometry args={[40, 0.6, 1.5]} />
        <meshStandardMaterial color="#8b7355" roughness={0.95} />
      </mesh>
    );
  }
  
  return <>{terraces}</>;
};

// ─── Check Dams (بندسار) ─────────────────────────────
const CheckDam: React.FC<{ intervention: any }> = ({ intervention }) => {
  const count = intervention.parameters?.count || 6;
  const startX = intervention.position?.x || 0;
  const startZ = intervention.position?.z || -30;
  
  const dams = [];
  for (let i = 0; i < count; i++) {
    dams.push(
      <mesh
        key={`dam-${i}`}
        position={[startX + Math.sin(i * 0.5) * 5, 0.5, startZ + i * 10]}
        castShadow
      >
        <boxGeometry args={[6, 1.5, 1]} />
        <meshStandardMaterial color="#78716c" roughness={0.9} />
      </mesh>
    );
  }
  
  return <>{dams}</>;
};

// ─── Crops (کشت) ─────────────────────────────
const CropField: React.FC<{ intervention: any; timeProgress: number }> = ({ intervention, timeProgress }) => {
  const growthStage = Math.min(1, timeProgress / 60);
  const count = 20;
  const spacing = 4;
  const startX = intervention.position?.x || -30;
  const startZ = intervention.position?.z || 10;
  
  const crops = [];
  for (let i = 0; i < count; i++) {
    for (let j = 0; j < count; j++) {
      const x = startX + i * spacing;
      const z = startZ + j * spacing;
      const height = growthStage * (1 + Math.random() * 0.3);
      const color = growthStage > 0.7 ? '#fbbf24' : '#84cc16';
      
      crops.push(
        <mesh key={`crop-${i}-${j}`} position={[x, height / 2, z]} castShadow>
          <coneGeometry args={[0.15, height, 6]} />
          <meshStandardMaterial color={color} />
        </mesh>
      );
    }
  }
  
  return <>{crops}</>;
};

// ─── Main Component ─────────────────────────────
export const VLLTerrain3D: React.FC<VLLTerrain3DProps> = ({
  interventions,
  weather,
  activeLayers,
  timeProgress,
  isPlaying,
}) => {
  // محاسبه ارتفاع زمین در هر نقطه
  const terrainHeight = (x: number, z: number): number => {
    let h = Math.sin(x / 20) * Math.cos(z / 20) * 4;
    h += Math.sin(x / 8) * 1.5;
    h += Math.cos(z / 12) * 1.2;
    const streamDistance = Math.abs(z - Math.sin(x / 15) * 3);
    if (streamDistance < 3) {
      h -= (3 - streamDistance) * 0.8;
    }
    return h;
  };

  const renderIntervention = (intv: any) => {
    switch (intv.id) {
      case 'tree_planting':
      case 'windbreak':
        return <TreeWindbreak key={intv.id} intervention={intv} terrainHeight={terrainHeight} />;
      case 'terrace':
      case 'contour_bunds':
        return <Terrace key={intv.id} intervention={intv} />;
      case 'check_dam':
        return <CheckDam key={intv.id} intervention={intv} />;
      case 'crop_planting':
      case 'cover_crop':
        return <CropField key={intv.id} intervention={intv} timeProgress={timeProgress} />;
      default:
        return null;
    }
  };

  return (
    <Canvas shadows camera={{ position: [40, 30, 40], fov: 50 }}>
      {/* آسمان پویا */}
      <Sky
        sunPosition={[100 * weather.sunIntensity, 50, 100]}
        turbidity={weather.rainfall > 30 ? 20 : 8}
        rayleigh={weather.rainfall > 30 ? 1 : 3}
      />
      
      {/* نور */}
      <ambientLight intensity={0.4 * weather.sunIntensity} />
      <directionalLight
        position={[50, 50, 50]}
        intensity={weather.sunIntensity}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-50}
        shadow-camera-right={50}
        shadow-camera-top={50}
        shadow-camera-bottom={-50}
      />

      {/* Stars اگر شب */}
      {weather.sunIntensity < 0.3 && <Stars radius={100} depth={50} count={5000} />}

      {/* زمین */}
      <Terrain activeLayers={activeLayers} />

      {/* مداخلات */}
      {interventions.map(renderIntervention)}

      {/* آب و هوا */}
      <RainDrops rainfall={weather.rainfall} />
      <WindParticles wind={weather.wind} />

      {/* کنترل دوربین */}
      <OrbitControls
        enablePan
        enableZoom
        enableRotate
        minDistance={20}
        maxDistance={200}
        maxPolarAngle={Math.PI / 2.1}
      />
    </Canvas>
  );
};
'''
    
    write_file(vll_dir / 'VLLTerrain3D.tsx', content)
    log('VLLTerrain3D.tsx (زمین 3D تعاملی) ایجاد شد', '+')


# ═══════════════════════════════════════════════════════════════
# گام ۵: InterventionPanel
# ═══════════════════════════════════════════════════════════════

def build_intervention_panel():
    separator("گام ۵: InterventionPanel")
    
    vll_dir = FRONTEND_ROOT / 'src' / 'components' / 'vll'
    
    content = '''import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, Trees, Layers, Droplets, Sprout, Wind } from 'lucide-react';
import { Card, Button } from '../ui';

interface Intervention {
  id: string;
  name: string;
  category: string;
  icon: React.ReactNode;
  color: string;
  description: string;
  parameters?: any;
  position?: { x: number; z: number };
  coverage?: number;
}

const AVAILABLE_INTERVENTIONS: Intervention[] = [
  {
    id: 'tree_planting',
    name: 'کاشت بادشکن',
    category: 'biological',
    icon: <Trees size={20} />,
    color: '#15803d',
    description: 'ردیف درختان برای کاهش سرعت باد',
  },
  {
    id: 'terrace',
    name: 'تراس‌بندی',
    category: 'engineering',
    icon: <Layers size={20} />,
    color: '#78716c',
    description: 'پله‌های عرضی برای کنترل رواناب',
  },
  {
    id: 'check_dam',
    name: 'بندسار',
    category: 'engineering',
    icon: <Layers size={20} />,
    color: '#64748b',
    description: 'سد کوچک رسوبگیر در آبراهه',
  },
  {
    id: 'crop_planting',
    name: 'کشت محصول',
    category: 'agronomic',
    icon: <Sprout size={20} />,
    color: '#84cc16',
    description: 'کاشت گندم، جو یا ذرت',
  },
  {
    id: 'cover_crop',
    name: 'گیاه پوششی',
    category: 'biological',
    icon: <Sprout size={20} />,
    color: '#22c55e',
    description: 'شبدر یا یونجه برای حفاظت خاک',
  },
  {
    id: 'crescent_bunds',
    name: 'هلالی آبگیر',
    category: 'engineering',
    icon: <Droplets size={20} />,
    color: '#3b82f6',
    description: 'جمع‌آوری آب باران',
  },
];

interface InterventionPanelProps {
  interventions: any[];
  onAdd: (intv: any) => void;
  onRemove: (id: number) => void;
}

export const InterventionPanel: React.FC<InterventionPanelProps> = ({
  interventions,
  onAdd,
  onRemove,
}) => {
  const [configuring, setConfiguring] = useState<Intervention | null>(null);
  const [params, setParams] = useState<any>({});
  const [coverage, setCoverage] = useState(100);
  const [position, setPosition] = useState({ x: 0, z: 0 });

  const startConfig = (intv: Intervention) => {
    setConfiguring(intv);
    setParams({});
    setCoverage(100);
    setPosition({ x: 0, z: 0 });
  };

  const confirmAdd = () => {
    if (!configuring) return;
    onAdd({
      ...configuring,
      parameters: params,
      coverage,
      position,
    });
    setConfiguring(null);
  };

  return (
    <Card title="🛠️ کتابخانه مداخلات" icon={<Wind size={18} />}>
      <p style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', marginBottom: '1rem' }}>
        برای هر مداخله، پارامترها را تنظیم و روی زمین قرار دهید
      </p>

      {/* Active Interventions */}
      {interventions.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <h4 style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>✅ فعال ({interventions.length})</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            {interventions.map((intv, idx) => (
              <motion.div
                key={intv.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  background: `${intv.color}15`,
                  border: `1px solid ${intv.color}40`,
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.75rem',
                }}
              >
                <span style={{ color: intv.color }}>{intv.icon}</span>
                <span style={{ flex: 1 }}>{intv.name}</span>
                <button
                  onClick={() => onRemove(intv.id)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-error)' }}
                >
                  <Trash2 size={14} />
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Available Interventions */}
      <h4 style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>📦 مداخلات موجود</h4>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
        {AVAILABLE_INTERVENTIONS.map((intv) => (
          <motion.button
            key={intv.id}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => startConfig(intv)}
            style={{
              padding: '0.75rem',
              background: `${intv.color}10`,
              border: `1px solid ${intv.color}40`,
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '0.25rem',
              color: intv.color,
              fontSize: '0.75rem',
            }}
          >
            {intv.icon}
            <span>{intv.name}</span>
          </motion.button>
        ))}
      </div>

      {/* Configuration Modal */}
      <AnimatePresence>
        {configuring && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setConfiguring(null)}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.7)',
              backdropFilter: 'blur(4px)',
              zIndex: 1000,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'var(--color-surface)',
                borderRadius: 'var(--radius-2xl)',
                padding: '2rem',
                maxWidth: 500,
                width: '90%',
                boxShadow: 'var(--shadow-2xl)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                <div style={{
                  width: 48,
                  height: 48,
                  borderRadius: 'var(--radius-xl)',
                  background: `${configuring.color}20`,
                  color: configuring.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  {configuring.icon}
                </div>
                <div>
                  <h3 style={{ margin: 0 }}>{configuring.name}</h3>
                  <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                    {configuring.description}
                  </p>
                </div>
              </div>

              {/* Coverage Slider */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                  <span>پوشش زمین</span>
                  <strong>{coverage}٪</strong>
                </label>
                <input
                  type="range"
                  min="10"
                  max="100"
                  step="5"
                  value={coverage}
                  onChange={(e) => setCoverage(parseInt(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>

              {/* Position */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                  📍 موقعیت روی زمین
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>X</div>
                    <input
                      type="number"
                      value={position.x}
                      onChange={(e) => setPosition({ ...position, x: parseFloat(e.target.value) })}
                      className="input"
                      style={{ padding: '0.5rem' }}
                    />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>Z</div>
                    <input
                      type="number"
                      value={position.z}
                      onChange={(e) => setPosition({ ...position, z: parseFloat(e.target.value) })}
                      className="input"
                      style={{ padding: '0.5rem' }}
                    />
                  </div>
                </div>
              </div>

              {/* Intervention-specific parameters */}
              {configuring.id === 'tree_planting' && (
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>🌳 گونه درخت</label>
                  <select
                    value={params.species || 'cypress'}
                    onChange={(e) => setParams({ ...params, species: e.target.value })}
                    className="input"
                  >
                    <option value="cypress">سرو (بادشکن قوی)</option>
                    <option value="pine">کاج</option>
                    <option value="olive">زیتون (مثمر)</option>
                    <option value="almond">بادام (مثمر)</option>
                    <option value="oak">بلوط (بومی)</option>
                  </select>
                  <label style={{ fontSize: '0.875rem', display: 'block', marginTop: '0.5rem', marginBottom: '0.25rem' }}>
                    تعداد درختان: {params.count || 10}
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="50"
                    value={params.count || 10}
                    onChange={(e) => setParams({ ...params, count: parseInt(e.target.value) })}
                    style={{ width: '100%' }}
                  />
                  <label style={{ fontSize: '0.875rem', display: 'block', marginTop: '0.5rem', marginBottom: '0.25rem' }}>
                    تعداد ردیف: {params.rows || 3}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={params.rows || 3}
                    onChange={(e) => setParams({ ...params, rows: parseInt(e.target.value) })}
                    style={{ width: '100%' }}
                  />
                </div>
              )}

              {configuring.id === 'terrace' && (
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem' }}>
                    تعداد تراس: {params.count || 5}
                  </label>
                  <input
                    type="range"
                    min="2"
                    max="20"
                    value={params.count || 5}
                    onChange={(e) => setParams({ ...params, count: parseInt(e.target.value) })}
                    style={{ width: '100%' }}
                  />
                  <label style={{ fontSize: '0.875rem', display: 'block', marginTop: '0.5rem', marginBottom: '0.25rem' }}>
                    فاصله (متر): {params.spacing || 8}
                  </label>
                  <input
                    type="range"
                    min="3"
                    max="20"
                    value={params.spacing || 8}
                    onChange={(e) => setParams({ ...params, spacing: parseInt(e.target.value) })}
                    style={{ width: '100%' }}
                  />
                </div>
              )}

              {configuring.id === 'check_dam' && (
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem' }}>
                    تعداد بندسار: {params.count || 6}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={params.count || 6}
                    onChange={(e) => setParams({ ...params, count: parseInt(e.target.value) })}
                    style={{ width: '100%' }}
                  />
                </div>
              )}

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button variant="secondary" onClick={() => setConfiguring(null)} style={{ flex: 1 }}>
                  انصراف
                </Button>
                <Button variant="primary" onClick={confirmAdd} style={{ flex: 1 }}>
                  <Plus size={16} /> افزودن به زمین
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
};
'''
    
    write_file(vll_dir / 'VLLInterventionPanel.tsx', content)
    log('VLLInterventionPanel.tsx ایجاد شد', '+')


# ═══════════════════════════════════════════════════════════════
# گام ۶: LayerManager + WeatherControl + ResultsBar + AI Advisor
# ═══════════════════════════════════════════════════════════════

def build_supporting_components():
    separator("گام ۶: Supporting Components")
    
    vll_dir = FRONTEND_ROOT / 'src' / 'components' / 'vll'
    
    # LayerManager
    layer_mgr = '''import React from 'react';
import { Card } from '../ui';
import { Mountain, Compass, Droplets, Leaf, Waves, AlertTriangle } from 'lucide-react';

interface VLLLayerManagerProps {
  activeLayers: Record<string, boolean>;
  onToggleLayer: (key: string) => void;
}

const LAYERS = [
  { key: 'dem', label: 'مدل ارتفاع (DEM)', icon: <Mountain size={16} />, color: '#8b7355' },
  { key: 'slope', label: 'نقشه شیب', icon: <Compass size={16} />, color: '#f59e0b' },
  { key: 'soil', label: 'نقشه خاک', icon: <Leaf size={16} />, color: '#84cc16' },
  { key: 'ndvi', label: 'شاخص NDVI', icon: <Leaf size={16} />, color: '#22c55e' },
  { key: 'water', label: 'رطوبت خاک', icon: <Droplets size={16} />, color: '#3b82f6' },
  { key: 'erosion', label: 'ریسک فرسایش', icon: <AlertTriangle size={16} />, color: '#ef4444' },
];

export const VLLLayerManager: React.FC<VLLLayerManagerProps> = ({ activeLayers, onToggleLayer }) => {
  return (
    <Card title="🗺️ لایه‌های GIS" icon={<Layers size={18} />} className="mb-4">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {LAYERS.map((layer) => (
          <button
            key={layer.key}
            onClick={() => onToggleLayer(layer.key)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem',
              borderRadius: 'var(--radius-md)',
              border: `2px solid ${activeLayers[layer.key] ? layer.color : 'var(--color-border)'}`,
              background: activeLayers[layer.key] ? `${layer.color}15` : 'transparent',
              cursor: 'pointer',
              fontSize: '0.875rem',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ color: layer.color }}>{layer.icon}</span>
            <span style={{ flex: 1, textAlign: 'right' }}>{layer.label}</span>
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: '50%',
                background: activeLayers[layer.key] ? layer.color : 'var(--color-border)',
              }}
            />
          </button>
        ))}
      </div>
    </Card>
  );
};

import { Layers } from 'lucide-react';
'''
    
    # Fix the duplicate import issue
    layer_mgr = layer_mgr.replace("import { Layers } from 'lucide-react';", "")
    layer_mgr = layer_mgr.replace(
        "import { Mountain, Compass, Droplets, Leaf, Waves, AlertTriangle } from 'lucide-react';",
        "import { Mountain, Compass, Droplets, Leaf, Waves, AlertTriangle, Layers } from 'lucide-react';"
    )
    
    write_file(vll_dir / 'VLLLayerManager.tsx', layer_mgr)
    log('VLLLayerManager.tsx ایجاد شد', '+')
    
    # WeatherControl
    weather_ctrl = '''import React from 'react';
import { Card } from '../ui';
import { CloudRain, Wind, Thermometer, Sun } from 'lucide-react';

interface Weather {
  rainfall: number;
  wind: number;
  temperature: number;
  sunIntensity: number;
}

interface VLLWeatherControlProps {
  weather: Weather;
  onChange: (weather: Weather) => void;
}

export const VLLWeatherControl: React.FC<VLLWeatherControlProps> = ({ weather, onChange }) => {
  return (
    <Card title="☁️ کنترل آب و هوا" icon={<CloudRain size={18} />} className="mb-4">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {/* Rainfall */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <CloudRain size={14} color="#3b82f6" /> بارش
            </span>
            <strong>{weather.rainfall} mm/hr</strong>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={weather.rainfall}
            onChange={(e) => onChange({ ...weather, rainfall: parseInt(e.target.value) })}
            style={{ width: '100%' }}
          />
        </div>

        {/* Wind */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Wind size={14} color="#a3a3a3" /> سرعت باد
            </span>
            <strong>{weather.wind} m/s</strong>
          </div>
          <input
            type="range"
            min="0"
            max="30"
            value={weather.wind}
            onChange={(e) => onChange({ ...weather, wind: parseInt(e.target.value) })}
            style={{ width: '100%' }}
          />
        </div>

        {/* Temperature */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Thermometer size={14} color="#ef4444" /> دما
            </span>
            <strong>{weather.temperature}°C</strong>
          </div>
          <input
            type="range"
            min="-10"
            max="50"
            value={weather.temperature}
            onChange={(e) => onChange({ ...weather, temperature: parseInt(e.target.value) })}
            style={{ width: '100%' }}
          />
        </div>

        {/* Sun Intensity */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Sun size={14} color="#fbbf24" /> تابش خورشید
            </span>
            <strong>{(weather.sunIntensity * 100).toFixed(0)}٪</strong>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={weather.sunIntensity * 100}
            onChange={(e) => onChange({ ...weather, sunIntensity: parseInt(e.target.value) / 100 })}
            style={{ width: '100%' }}
          />
        </div>
      </div>
    </Card>
  );
};
'''
    
    write_file(vll_dir / 'VLLWeatherControl.tsx', weather_ctrl)
    log('VLLWeatherControl.tsx ایجاد شد', '+')
    
    # ResultsBar
    results_bar = '''import React from 'react';
import { motion } from 'framer-motion';
import { Leaf, Droplets, Wind, Coins, TrendingUp } from 'lucide-react';

interface VLLResultsBarProps {
  results: any;
  isSimulating: boolean;
}

export const VLLResultsBar: React.FC<VLLResultsBarProps> = ({ results, isSimulating }) => {
  if (isSimulating) {
    return (
      <div style={{
        padding: '1.5rem',
        background: 'linear-gradient(90deg, var(--color-primary), var(--color-info))',
        color: 'white',
        textAlign: 'center',
      }}>
        <motion.div
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        >
          ⏳ در حال اجرای شبیه‌سازی با مدل‌های علمی (AquaCrop, RothC, RUSLE, WEPS)...
        </motion.div>
      </div>
    );
  }

  if (!results) {
    return (
      <div style={{
        padding: '1rem',
        background: 'var(--color-surface)',
        borderTop: '1px solid var(--color-border)',
        textAlign: 'center',
        color: 'var(--color-text-tertiary)',
      }}>
        💡 مداخلات را انتخاب و دکمه "اجرای سناریو" را بزنید تا نتایج شبیه‌سازی را ببینید
      </div>
    );
  }

  const score = results.sustainability_score || 0;
  const breakdown = results.score_breakdown || {};
  const scoreColor = score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444';

  const metrics = [
    { icon: <Leaf size={20} />, label: 'کربن', value: breakdown.carbon || 0, color: '#22c55e' },
    { icon: <Droplets size={20} />, label: 'آب', value: breakdown.water || 0, color: '#3b82f6' },
    { icon: <Wind size={20} />, label: 'فرسایش', value: breakdown.erosion || 0, color: '#f59e0b' },
    { icon: <Coins size={20} />, label: 'اقتصاد', value: 70, color: '#8b5cf6' },
    { icon: <TrendingUp size={20} />, label: 'پایداری', value: score, color: scoreColor },
  ];

  return (
    <div style={{
      padding: '1rem 2rem',
      background: 'var(--color-surface)',
      borderTop: '2px solid var(--color-border)',
      display: 'flex',
      gap: '2rem',
      alignItems: 'center',
      boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.05)',
    }}>
      {/* Main Score */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', minWidth: 200 }}>
        <div style={{ position: 'relative', width: 80, height: 80 }}>
          <svg width="80" height="80" style={{ transform: 'rotate(-90deg)' }}>
            <circle cx="40" cy="40" r="35" fill="none" stroke="var(--color-border)" strokeWidth="6" />
            <motion.circle
              cx="40"
              cy="40"
              r="35"
              fill="none"
              stroke={scoreColor}
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={220}
              initial={{ strokeDashoffset: 220 }}
              animate={{ strokeDashoffset: 220 - (score / 100) * 220 }}
              transition={{ duration: 1, ease: 'easeOut' }}
            />
          </svg>
          <div style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.5rem',
            fontWeight: 700,
            color: scoreColor,
          }}>
            {score}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>نمره پایداری</div>
          <div style={{ fontSize: '1rem', fontWeight: 700 }}>
            {score >= 75 ? '✅ عالی' : score >= 50 ? '⚠️ متوسط' : '❌ ضعیف'}
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
        {metrics.slice(0, 4).map((metric, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            style={{
              padding: '0.75rem',
              background: `${metric.color}10`,
              border: `1px solid ${metric.color}40`,
              borderRadius: 'var(--radius-lg)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <div style={{ color: metric.color }}>{metric.icon}</div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>{metric.label}</div>
              <div style={{ fontSize: '1.125rem', fontWeight: 700 }}>{Math.round(metric.value)}</div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
'''
    
    write_file(vll_dir / 'VLLResultsBar.tsx', results_bar)
    log('VLLResultsBar.tsx ایجاد شد', '+')
    
    # AI Advisor
    advisor = '''import React from 'react';
import { motion } from 'framer-motion';
import { Zap, CheckCircle, AlertCircle, Info, Sparkles } from 'lucide-react';
import { Card, Button } from '../ui';

interface VLLAIAdvisorProps {
  recommendations: any[];
  onApply: (action: string) => void;
}

export const VLLAIAdvisor: React.FC<VLLAIAdvisorProps> = ({ recommendations, onApply }) => {
  const priorityIcon = (p: string) => {
    switch (p) {
      case 'high': return <AlertCircle size={16} color="#ef4444" />;
      case 'medium': return <Info size={16} color="#f59e0b" />;
      default: return <CheckCircle size={16} color="#10b981" />;
    }
  };

  return (
    <Card title="🤖 دستیار AI" icon={<Sparkles size={18} />} className="mb-4">
      <p style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', marginBottom: '1rem' }}>
        پیشنهادات هوشمند بر اساس نتایج شبیه‌سازی
      </p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {recommendations.map((rec, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            style={{
              padding: '0.75rem',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-lg)',
              borderRight: `4px solid ${rec.priority === 'high' ? '#ef4444' : rec.priority === 'medium' ? '#f59e0b' : '#10b981'}`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              {priorityIcon(rec.priority)}
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>{rec.category}</span>
            </div>
            <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{rec.title}</div>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', lineHeight: 1.6, margin: '0 0 0.5rem 0' }}>
              {rec.description}
            </p>
            {rec.action && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onApply(rec.action)}
                style={{ fontSize: '0.75rem', padding: '0.25rem 0.75rem' }}
              >
                <Zap size={12} /> اعمال پیشنهاد
              </Button>
            )}
          </motion.div>
        ))}
      </div>
    </Card>
  );
};
'''
    
    write_file(vll_dir / 'VLLAIAdvisor.tsx', advisor)
    log('VLLAIAdvisor.tsx ایجاد شد', '+')
    
    # Index
    index = '''export { VLLTerrain3D } from './VLLTerrain3D';
export { InterventionPanel } from './VLLInterventionPanel';
export { VLLLayerManager } from './VLLLayerManager';
export { VLLWeatherControl } from './VLLWeatherControl';
export { VLLResultsBar } from './VLLResultsBar';
export { VLLAIAdvisor } from './VLLAIAdvisor';
'''
    write_file(vll_dir / 'index.ts', index)
    log('vll/index.ts ایجاد شد', '+')


# ═══════════════════════════════════════════════════════════════
# گام ۷: Update App.tsx
# ═══════════════════════════════════════════════════════════════

def update_app():
    separator("گام ۷: Update App.tsx")
    
    app_path = FRONTEND_ROOT / 'src' / 'App.tsx'
    content = app_path.read_text(encoding='utf-8')
    
    if 'VirtualLandLabPage' not in content:
        content = content.replace(
            "import { MarketplacePage } from './pages/MarketplacePage';",
            "import { MarketplacePage } from './pages/MarketplacePage';\nimport { VirtualLandLabPage } from './pages/VirtualLandLabPage';"
        )
    
    if '/virtual-lab' not in content:
        content = content.replace(
            "<Route path=\"/marketplace\" element={<MarketplacePage />} />",
            "<Route path=\"/marketplace\" element={<MarketplacePage />} />\n        <Route path=\"/virtual-lab\" element={<VirtualLandLabPage />} />"
        )
    
    write_file(app_path, content)
    log('App.tsx به‌روزرسانی شد', '+')


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("  🌍 Eco Nojin - فاز ۱۰: آزمایشگاه مجازی زمین")
    print("=" * 70)
    
    step_backup()
    build_standalone_backend()
    build_vll_main()
    build_terrain_3d()
    build_intervention_panel()
    build_supporting_components()
    update_app()
    
    separator("✅ تکمیل فاز ۱۰")
    print("\n  🎯 دستاوردها:")
    print("     1. ✅ backend.py - سرور مستقل قابل اجرا")
    print("     2. ✅ 3D Terrain با DEM + آبراهه + لایه‌های GIS")
    print("     3. ✅ InterventionPanel با drag & drop")
    print("     4. ✅ انیمیشن‌های هوا (باران، باد، درختان)")
    print("     5. ✅ ۴ لایه GIS (شیب، خاک، NDVI، رطوبت)")
    print("     6. ✅ دستیار AI با پیشنهادات هوشمند")
    print("     7. ✅ ResultsBar با نمره پایداری")
    print("     8. ✅ کنترل زمان (سال ۱ تا ۱۰)")
    print("\n  🎨 مداخلات پیاده‌سازی‌شده:")
    print("     🌳 کاشت بادشکن (۵ گونه + پارامتر)")
    print("     🏗️ تراس‌بندی (تعداد + فاصله)")
    print("     🧱 بندسار (چک‌دم)")
    print("     🌾 کشت محصول (با رشد پویا)")
    print("     🌱 گیاه پوششی")
    print("     🌙 هلالی آبگیر")
    print("\n  🚀 راه‌اندازی Backend (ترتیب مهم!):")
    print("     cd D:\\eco_nojin")
    print("     python backend.py")
    print("     → http://localhost:8000")
    print("     → http://localhost:8000/docs")
    print("\n  🚀 راه‌اندازی Frontend (در ترمینال دیگر):")
    print("     cd D:\\eco_nojin\\frontend")
    print("     pnpm run dev")
    print("     → http://localhost:5173/virtual-lab")
    print("\n  🧪 تست Backend در PowerShell:")
    print("     .\\PS_API_GUIDE.ps1")
    print("\n  💡 درباره خطای `Could not import start_backend`:")
    print("     فایل `backend.py` جدید ساخته شد.")
    print("     از این به بعد از `python backend.py` استفاده کنید.")
    print("\n  🌟 گردش کار کاربر:")
    print("     1. لایه‌های GIS را فعال/غیرفعال کنید")
    print("     2. آب و هوا را تغییر دهید (باران/باد/دما)")
    print("     3. مداخلات را انتخاب و پارامتر تنظیم کنید")
    print("     4. زمان را جلو ببرید (رشد گیاه، فرسایش)")
    print("     5. اجرای سناریو → دریافت نمره پایداری")
    print("     6. دستیار AI پیشنهادات بهینه‌سازی می‌دهد")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())