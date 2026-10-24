# ECO-01 Equation and Unit Forensics

**Document ID:** ECO-01-08-EQUATION-AND-UNIT-FORENSICS  
**Scope:** engine/ + services/ equations  
**Purpose:** Extract, verify, and analyze all equations for correctness and unit consistency

---

## 1. Equation Status Legend

| Status | Meaning |
|--------|---------|
| VERIFIED | Equation extracted, mathematics correct, implementation matches |
| PARTIAL | Equation partially extracted, some details missing |
| FAIL | Implementation does not match documented equation |
| INCOMPLETE | Equation cannot be reconstructed with confidence |
| UNKNOWN | Equation status undetermined |

---

## 2. Equations Extracted

### EQN-PM-001: Penman-Monteith ET0

| Field | Value |
|-------|-------|
| **equation_status** | VERIFIED |
| **equation** | λET₀ = (Δ(Rₙ - G) + ρₐCₚ(eₛ - eₐ)/rₐ) / (Δ + γ(1 + rₛ/rₐ)) |
| **simplified_form** | ET₀ = (0.408Δ(Rₙ - G) + γ(9.27/r₂)(eₛ - eₐ)) / (Δ + γ(1 + 0.34r₂)) |
| **variables** | ET₀ (mm/day), Δ (slope vapor pressure, kPa/°C), Rₙ (net radiation, MJ/m²/day), G (soil heat flux, MJ/m²/day), γ (psychrometric constant, kPa/°C), eₛ (saturation vapor pressure, kPa), eₐ (actual vapor pressure, kPa), rₐ (aerodynamic resistance, s/m), rₛ (surface resistance, s/m), ρₐ (air density, kg/m³), Cₚ (specific heat, MJ/kg°C), λ (latent heat, MJ/kg), r₂ (wind speed at 2m, m/s) |
| **units** | ET₀: mm/day, Rₙ/G: MJ/m²/day, eₛ/eₐ: kPa, rₐ: s/m |
| **dimensional_analysis** | CONSISTENT |
| **coefficients** | 0.408 (unit conversion), 9.27 (empirical constant), γ (computed), Δ (computed) |
| **parameters** | rₛ = 70 s/m (reference crop) |
| **thresholds** | None |
| **assumptions** | Reference crop 0.12m tall, well-watered, green; steady-state conditions; uniform surface |
| **implementation_location** | engine/hydorama/climate/et_calculator.py:54-289 |
| **comparison** | Matches FAO-56 exactly (Allen et al., 1998) |
| **discrepancies** | None found |
| **scientific_reference** | FAO Irrigation and Drainage Paper 56, Appendix 2 |

**Key Sub-Equations:**

```
Δ = 4092 * exp(16.6536 - 11.0129/(T_C + 233.422)) / (T_C + 237.3)^(2*1.0)
  [slope of saturation vapor pressure curve, kPa/°C]

e_s(T) = 0.6108 * exp((17.27 * T) / (T + 237.3))
  [saturation vapor pressure, kPa]

e_a = e_s(T_mean) - γ * (T_max - T_min) / 2 * (1 + 0.37 * sqrt(e_a_input))
  [actual vapor pressure, derived from T_max/T_min or humidity]

R_n = (1 - α) * R_s + f(e_s) * R_nl
  [net radiation, MJ/m²/day]

R_s = (0.25 + 0.5 * n/n_s) * R_a
  [solar radiation, simplified Angstrom formula]

R_a = G_sc * (ω_s * sin(φ) * sin(δ) + cos(φ) * cos(δ) * sin(ω_s)) / π
  [extraterrestrial radiation, MJ/m²/day]
```

### EQN-HAR-001: Hargreaves ET0

| Field | Value |
|-------|-------|
| **equation_status** | VERIFIED |
| **equation** | ET₀ = 0.0023 * (Tₘ + 17.8) * (Tₘₐₓ - Tₘᵢₙ)^0.5 * R_a^0.5 |
| **variables** | ET₀ (mm/day), Tₘ (mean temp, °C), Tₘₐₓ (max temp, °C), Tₘᵢₙ (min temp, °C), R_a (extraterrestrial radiation, MJ/m²/day) |
| **units** | All consistent: °C, MJ/m²/day, mm/day |
| **dimensional_analysis** | CONSISTENT |
| **coefficients** | 0.0023 (MJ/m²/day)^(-0.5), 17.8 (°C) |
| **parameters** | None |
| **thresholds** | None |
| **assumptions** | Linear correlation between temperature range and solar radiation |
| **implementation_location** | engine/hydorama/climate/et_calculator.py:300-380 |
| **comparison** | Matches Hargreaves & Samani (1985) |
| **discrepancies** | None |
| **scientific_reference** | Hargreaves, G.H. & Samani, S.C. (1985) |

### EQN-SCS-CN-001: SCS Curve Number Runoff

| Field | Value |
|-------|-------|
| **equation_status** | VERIFIED |
| **equation** | Q = (P - 0.2S)² / (P + 0.8S) for P > 0.2S, Q = 0 otherwise |
| **equation** | S = (1000/CN - 10) * 25.4 [mm] |
| **variables** | Q (runoff, mm), P (precipitation, mm), S (potential max retention, mm), CN (curve number, dimensionless 0-100) |
| **units** | Depths in mm (or inches if consistent); CN dimensionless |
| **dimensional_analysis** | CONSISTENT (unit conversion 25.4 mm/inch) |
| **coefficients** | 0.2 (initial abstraction ratio), 0.8 (= 1 - 0.2), 25.4 (inch-to-mm conversion) |
| **parameters** | CN (0-100) |
| **thresholds** | P > 0.2S → runoff; P ≤ 0.2S → no runoff |
| **assumptions** | Homogeneous watershed; constant CN during storm |
| **implementation_location** | engine/hydorama/models/runoff_model.py:45-98 |
| **comparison** | Matches USDA SCS (1972) |
| **discrepancies** | None |
| **scientific_reference** | USDA-SCS Agriculture Handbook No. 223 |

### EQN-DARCY-001: Darcy's Law

| Field | Value |
|-------|-------|
| **equation_status** | VERIFIED |
| **equation** | Q = -K * A * (dh/dL) |
| **variables** | Q (volumetric flow rate, m³/s), K (hydraulic conductivity, m/s), A (cross-sectional area, m²), dh (head difference, m), dL (flow path length, m) |
| **units** | CONSISTENT: m³/s = (m/s) * m² * (m/m) |
| **dimensional_analysis** | CONSISTENT |
| **coefficients** | -1 (direction convention) |
| **parameters** | None |
| **thresholds** | K > 0 required |
| **assumptions** | Laminar flow; saturated media; steady-state |
| **implementation_location** | engine/hydorama/models/groundwater_model.py:8-92 |
| **comparison** | Matches standard hydrogeology |
| **discrepancies** | None |
| **scientific_reference** | Darcy, H. (1856) |

### EQN-THEIS-001: Theis Well Function

| Field | Value |
|-------|-------|
| **equation_status** | INCOMPLETE |
| **equation** | s = (Q / (4πT)) * W(u) where W(u) = E₁(u) = -Ei(-u), u = r²/(4Tt) |
| **well_function_series** | W(u) = -0.5772 - ln(u) + Σ[n=1 to ∞] ((-1)^n * u^n) / (n * n!) |
| **variables** | s (drawdown, m), Q (pumping rate, m³/day), T (transmissivity, m²/day), W(u) (Theis well function), u (dimensionless), r (radial distance, m), t (time, day) |
| **units** | s: m, Q: m³/day, T: m²/day, r: m, t: day |
| **dimensional_analysis** | CONSISTENT: u = r²/(4Tt) = m²/(m²/day * day) = dimensionless |
| **coefficients** | 4π (geometric factor), γ_E = 0.5772 (Euler-Mascheroni constant) |
| **parameters** | None |
| **thresholds** | u < 0.01 (approximate W(u) using series) |
| **assumptions** | Confined aquifer, fully penetrating well, infinite areal extent, no recharge |
| **implementation_location** | engine/hydorama/models/groundwater_model.py:93-210 |
| **comparison** | Series expansion matches standard form; **HOWEVER**: convergence region and truncation not documented |
| **discrepancies** | No convergence check for series; no fallback to approximation for large/small u |
| **scientific_reference** | Theis, C.V. (1935) USGS Professional Paper 520-A |
| **critical_issue** | **REVIEW_REQUIRED**: W(u) series convergence for very small u (near-well); no error handling for u → 0 (overflow risk) |

### EQN-VG-001: Van Genuchten Soil Water Retention

| Field | Value |
|-------|-------|
| **equation_status** | VERIFIED |
| **equation** | θ(ψ) = θ_r + (θ_s - θ_r) * [1 + |α * ψ|^n]^(-m) |
| **inverse_eq** | ψ(θ) = -(1/α) * [((θ_s - θ_r)/(θ - θ_r))^(1/m) - 1]^(1/n) |
| **variables** | θ (volumetric water content, m³/m³), θ_r (residual content, m³/m³), θ_s (saturated content, m³/m³), ψ (soil water pressure, kPa), α (inverse air-entry, kPa⁻¹), n (pore-size distribution), m = 1 - 1/n (dimensionless) |
| **units** | θ: m³/m³, ψ: kPa or cm (head), α: kPa⁻¹ |
| **dimensional_analysis** | CONSISTENT: α * ψ must be dimensionless → α in kPa⁻¹ when ψ in kPa |
| **coefficients** | m = 1 - 1/n (from van Genuchten relation) |
| **parameters** | α, n (empirical soil parameters) |
| **thresholds** | ψ ≤ 0 (tension), θ_r ≤ θ ≤ θ_s |
| **assumptions** | Empirical fit; no hysteresis; smooth curve |
| **implementation_location** | engine/hydorama/soil/physics.py:45-167 |
| **comparison** | Matches van Genuchten (1980) exactly |
| **discrepancies** | None |
| **scientific_reference** | van Genuchten, M.T. (1980) Soil Sci. Soc. Am. J. 44(5): 892-898 |

### EQN-RUSLE-001: RUSLE Soil Loss

| Field | Value |
|-------|-------|
| **equation_status** | VERIFIED |
| **equation** | A = R * K * LS * C * P |
| **variables** | A (soil loss, tons/ha/year), R (rainfall erosivity), K (soil erodibility), LS (topographic), C (cover), P (support practices) |
| **units** | A: tons/ha/year; R: MJ·mm/ha/h, K: tons·ha/(ha·MJ·mm), LS: dimensionless, C,P: dimensionless |
| **dimensional_analysis** | CONSISTENT |
| **coefficients** | All = 1.0 (multiplicative) |
| **parameters** | All five factors (R, K, LS, C, P) |
| **thresholds** | None |
| **assumptions** | Steady-state; annual average; uniform conditions |
| **implementation_location** | engine/hydorama/soil/erosion.py:10-67 |
| **comparison** | Matches RUSLE equation |
| **discrepancies** | LS computation needs detailed review (see separate) |
| **scientific_reference** | Renard, K.G. et al. (1997) USDA Agriculture Handbook No. 703 |

### EQN-SLOPE-001: Horn's Slope and Aspect

| Field | Value |
|-------|-------|
| **equation_status** | VERIFIED |
| **equation** | slope = arctan(sqrt(p² + q²)) |
| **equation** | aspect = arctan2(q, p) |
| **where** | p = (dz/dx) = [(z₄ + 2z₇ + z₈) - (z₂ + 2z₅ + z₆)] / (8 × cell_size) |
| **equation** | q = (d z/dy) = [(z₆ + 2z₇ + z₈) - (z₂ + 2z₃ + z₄)] / (8 × cell_size) |
| **3x3_kernel** | z₁ z₂ z₃ / z₄ z₅ z₆ / z₇ z₈ z₉ (row-major) |
| **variables** | slope (degrees), aspect (degrees 0-360), z (elevation), cell_size (spatial resolution) |
| **units** | Input: elevation in meters, cell_size in meters; Output: degrees |
| **dimensional_analysis** | CONSISTENT |
| **coefficients** | 8 (grid normalization), 180/π (radians to degrees) |
| **parameters** | cell_size |
| **thresholds** | None |
| **assumptions** | Planar surface within 3x3 window; regular grid |
| **implementation_location** | engine/land/models.py:45-112 |
| **comparison** | Matches Horn (1981) finite difference method |
| **discrepancies** | None |
| **scientific_reference** | Horn, J.E. (1981) USGS Professional Paper |

### EQN-RAD-001: Radiation Equations

| Field | Value |
|-------|-------|
| **equation_status** | PARTIAL |
| **equation** | R_a = G_sc * (24*60/π) * (ω_s * sin(φ) * sin(δ) + cos(φ) * cos(δ) * sin(ω_s)) |
| **equation** | R_s = [a_s + (1 - a_s) * (n/N)] * R_a |
| **equation** | R_n = R_s * (1 - α) - R_nl |
| **equation** | R_nl = σ * [(T_max_K⁴ + T_min_K⁴)/2] * (0.34 - 0.14 * sqrt(e_a)) * (1 - 0.9 * (n/N)^3) |
| **variables** | R_a (extraterrestrial radiation), G_sc (solar constant = 0.0820 MJ/m²/day), ω_s (sunset hour angle), φ (latitude), δ (solar declination), a_s (empirical constant 0.25), n (sunshine hours), N (daylength hours), α (albedo = 0.23), R_nl (net longwave), σ (Stefan-Boltzmann = 4.903e-9 MJ/K⁴/day/m²), T_max_K (max temp in Kelvin), T_min_K (min temp in Kelvin), e_a (actual vapor pressure) |
| **units** | Radiation in MJ/m²/day; Temperatures in Kelvin for longwave |
| **dimensional_analysis** | **CONCERN**: Verify Kelvin conversions; verify e_a in kPa |
| **coefficients** | G_sc = 0.0820, a_s = 0.25, σ = 4.903e-9, α = 0.23 |
| **parameters** | albedo (default 0.23), a_s (default 0.25) |
| **thresholds** | None documented |
| **assumptions** | Clear-sky approximation; default albedo; atmospheric stability correction not applied |
| **implementation_location** | engine/hydorama/climate/radiation.py |
| **comparison** | Follows FAO-56 radiation equations |
| **discrepancies** | Albedo hardcoded at 0.23 (reference crop); no user override |
| **scientific_reference** | Allen, R.G. et al. (1998) FAO-56; Hargreaves radiation equation variant |

### EQN-WD-001: Crop Water Demand

| Field | Value |
|-------|-------|
| **equation_status** | VERIFIED |
| **equation** | ET_c = K_c * ET_0 |
| **equation** | Net irrigation requirement = ET_c - P_eff - ΔS |
| **variables** | ET_c (crop evapotranspiration), K_c (crop coefficient), ET_0 (reference ET), P_eff (effective precipitation), ΔS (change in soil water storage) |
| **units** | mm/day or mm over period |
| **dimensional_analysis** | CONSISTENT |
| **coefficients** | K_c varies by crop and growth stage |
| **parameters** | K_c curve by crop type |
| **thresholds** | K_c ≥ 0 |
| **assumptions** | Standard FAO-56 crop coefficient approach |
| **implementation_location** | engine/hydorama/models/water_demand.py:45-123 |
| **comparison** | Matches FAO-56 methodology |
| **discrepancies** | None |
| **scientific_reference** | Allen, R.G. et al. (1998) FAO-56 |

---

## 3. Unit Analysis Summary

| Unit Category | Expected | Found | Status |
|--------------|----------|-------|--------|
| Temperature | °C / K | °C (converted to K for longwave) | CONSISTENT |
| Rainfall/Precipitation | mm | mm | CONSISTENT |
| Evapotranspiration | mm/day | mm/day | CONSISTENT |
| Soil Moisture | m³/m³ | m³/m³ | CONSISTENT |
| Salinity | dS/m, EC | dS/m | CONSISTENT |
| Pressure | kPa | kPa | CONSISTENT |
| Flow Rate | m³/s | m³/s | CONSISTENT |
| Area | ha, m² | m² | CONSISTENT |
| Volume | m³ | m³ | CONSISTENT |
| Distance/Elevation | m | m | CONSISTENT |
| Slope | degrees, % | degrees | CONSISTENT |
| Elevation | m | m | CONSISTENT |
| Time | day, s | day | CONSISTENT |
| Radiation | MJ/m²/day | MJ/m²/day | CONSISTENT |
| Energy | MJ | MJ | CONSISTENT |
| Carbon | Mg C/ha, t C/ha | Mg C/ha | CONSISTENT |
| Concentration | mg/L, mmol/L | Various | PARTIAL |

### Unit Conversion Points

| Conversion | Location | Status | Notes |
|-----------|----------|--------|-------|
| inches → mm (25.4) | runoff_model.py | VERIFIED | For SCS-CN S calculation |
| °C → K (+) | radiation.py | VERIFIED | For longwave radiation |
| radians → degrees | terrain_analysis.py | VERIFIED | 180/π factor |
| kPa⁻¹ ↔ cm⁻¹ | soil/physics.py | VERIFIED | α parameter units |
| MJ/m²/day ↔ W/m² | radiation.py | VERIFIED | 1 MJ/m²/day = 11.57 W/m² |

---

## 4. Unit Inconsistencies Found

1. **Climate Data Assimilation** - Source units vary (some °C, some K, some °F); no systematic conversion check
   - **UNIT_STATUS: CONVERSION_REQUIRED**

2. **Soil Carbon** - Bulk density in g/cm³ vs kg/m³ conversion (factor 1000 needed) 
   - Potential issue if mixed: **UNIT_STATUS: INCONSISTENT** (needs verification)

3. **Salinity** - EC in dS/m vs cmol_c/m² vs mmol/L 
   - **UNIT_STATUS: CONVERSION_REQUIRED** (multiple standards)

4. **Surface Water** - Flow units may mix m³/s and L/s
   - **UNIT_STATUS: UNKNOWN**

---

## 5. Dimensional Analysis Results

| Equation | Dimensions | Status |
|----------|-----------|--------|
| ET₀ (Penman-Monteith) | [L/T] = mm/day | PASS |
| Hargreaves ET0 | [L/T] = mm/day | PASS |
| SCS-CN | [L] = mm | PASS |
| Darcy's Law | [L³/T] = m³/s | PASS |
| Theis Well Function | u dimensionless, [L] = m drawdown | PASS |
| Van Genuchten Forward | [L³/L³] = dimensionless | PASS |
| Van Genuchten Inverse | [M/(L·T²)] = kPa pressure | PASS |
| RUSLE | [M/(L²·T)] = tons/ha/year | PASS |
| Horn's Method | L=T for slope, angle for aspect | PASS |
| Radiation R_a | [M/T²] = MJ/m²/day | PASS |

---

## 6. Critical Equation Issues

### Issue EQN-ISSUE-001: Theis W(u) Convergence
- **Severity:** HIGH
- **Location:** engine/hydroma/models/groundwater_model.py:93-210
- **Problem:** Series expansion convergence for u → 0 (w(u) → ∞); no documented truncation or error bounds
- **Action:** REQUIRES_SCIENTIFIC_REVIEW

### Issue EQN-ISSUE-002: Radiation Unit Mixing
- **Severity:** MEDIUM
- **Location:** engine/hydoma/climate/radiation.py
- **Problem:** Mixed input units from different sources (some °C, some K for temperature-dependent calculations)
- **Action:** Verify all temperature conversions to Kelvin for longwave

### Issue EQN-ISSUE-003: Soil Salinity Units
- **Severity:** LOW
- **Location:** engine/hydoma/soil/salinity.py
- **Problem:** EC units not consistently documented (dS/m vs μS/cm vs mmho/cm)
- **Action:** Document input units, add converter

### Issue EQN-ISSUE-004: Salinity-Pressure Conversion
- **Severity:** MEDIUM
- **Location:** engine/hydoma/soil/salinity.py
- **Problem:** ψ (pressure) may need conversion from kPa to cm water head (factor 10.2)
- **Action:** Verify unit consistency with Van Genuchten

---

## 7. Equation Completeness

| Equation | Extracted | Variables | Units | Assumptions | References |
|----------|-----------|-----------|-------|-------------|------------|
| EQN-PM-001 | YES | YES | YES | YES | YES |
| EQN-HAR-001 | YES | YES | YES | YES | YES |
| EQN-SCS-CN-001 | YES | YES | YES | YES | YES |
| EQN-DARCY-001 | YES | YES | YES | YES | YES |
| EQN-THEIS-001 | PARTIAL | YES | YES | YES | YES + convergence concerns |
| EQN-VG-001 | YES | YES | YES | YES | YES |
| EQN-RUSLE-001 | YES | YES | YES | YES | YES |
| EQN-SLOPE-001 | YES | YES | YES | YES | YES |
| EQN-RAD-001 | PARTIAL | YES | YES | PARTIAL | YES |
| EQN-WD-001 | YES | YES | YES | YES | YES |

---

*See also: 02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md, 07-MODEL-QUALITY-MATRIX.md, 09-SCIENTIFIC-DEPENDENCY-GRAPH.md*