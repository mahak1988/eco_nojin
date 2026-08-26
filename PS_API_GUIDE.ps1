# راهنمای تست API در PowerShell
# ═══════════════════════════════════════════════════════════

# ─── راه‌اندازی Backend ─────────────────────────────
cd D:\eco_nojin
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
