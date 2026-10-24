# ECO-02: Scientific Knowledge Registry

## Scientific Theory Catalog (KT-001)

---

## Source Evidence
- ECO-01/02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md
- ECO-01/07-MODEL-QUALITY-MATRIX.md
- ECO-01/08-EQUATION-AND-UNIT-FORENSICS.md

---

## Theoretical Foundations

| Theory | Origin | Year | Application |
|--------|--------|------|-------------|
| Penman-Monteith | FAO-56 | 1998 | Reference ET (CANON-001) |
| Hargreaves-Samani | Hargreaves & Samani | 1985 | Simplified ET (CANON-002) |
| Thornthwaite | Thornthwaite | 1948 | PET estimation (CANON-003) |
| Priestley-Taylor | Priestley & Taylor | 1972 | Radiation ET (CANON-007) |
| Jensen-Haise | Jensen & Haise | 1963 | Energy balance ET (CANON-008) |
| Richards Equation | Richards | 1931 | Soil water flow |
| Darcy's Law | Darcy | 1856 | Groundwater flow |
| Manning's Equation | Manning | 1889 | Open channel flow |
| Continuity Equation | - | - | Mass conservation |
| Bernoulli's Principle | Bernoulli | 1738 | Flow hydraulics |
| Saint-Venant | Saint-Venant | 1876 | Unsteady flow |
| Richards-Boguchutskii | Various | - | Snowmelt modeling |
| Dalton's Law | Dalton | 1802 | Gas partial pressure |
| Fourier's Law | Fourier | 1822 | Heat transfer |
| Planck's Law | Planck | 1900 | Radiation physics |
| Stefan-Boltzmann | Stefan/Boltzmann | 1859/1884 | Radiation emission |

---

## Climate Science Theory

| Theory | Application | Model References |
|--------|-------------|-----------------|
| Navier-Stokes | Atmospheric dynamics | WRF, HRRR |
| Primitive Equations | Climate modeling | CMIP6, RegCM |
| Radiative Transfer | Energy balance | MODIS, Sentinel-2 |
| Cloud Physics | Precipitation formation | GPM IMERG |
| Land Surface Schemes | ET, heat flux | MODIS ET |

---

## Hydrological Theory

| Theory | Application | Model References |
|--------|-------------|-----------------|
| Richards Equation | Infiltration | Soil water models |
| Darcy's Law | Groundwater | MODFLOW |
| Muskingum | Flood routing | HEC-HMS |
| SCS-CN Method | Runoff | SWAT |
| Boussinesq | Unconfined flow | Groundwater |

---

## Agronomic Theory

| Theory | Application | Model References |
|--------|-------------|-----------------|
| Crop Coefficient | ETc calculation | FAO-56 (CANON-009) |
| Water Productivity | Yield response | AquaCrop (CANON-010) |
| Soil Water Balance | Plant water uptake | Crop models |
| Light Interception | Radiation use efficiency | Crop models |

---

## Theoretical Maturity Scale

| Maturity | Definition | Count |
|----------|------------|-------|
| VERIFIED | Field-validated theory | 8 |
| SCIENTIFICALLY_SUPPORTED | Theory accepted, limited validation | 4 |
| IMPLEMENTATION_VERIFIED | Code matches theory | 0 |
| CODE_ONLY | No theoretical basis | 0 |
| STUB | Placeholder | 0 |

---

## Equation Validation

### Validated Equations (UNIFORMAT verified)
| Equation | Formula | Variables | Units |
|----------|---------|-----------|-------|
| Penman-Monteith | ET0 = (ΔRn + ρa·Cp·es - ea)/(Δ+γ) | Δ, Rn, ρa, Cp, es, ea, γ | mm/day |
| Hargreaves | ET0 = 0.0023(Tmax-Tmin)^0.5(Ra)^0.5(Ta+17.8) | Tmax, Tmin, Ta, Ra | mm/day |
| Thornthwaite | PET = 16(P/12)(10Ta/I)^α | P, Ta, I, α | mm/month |
| Darcy's Law | Q = -KAdh/dl | K, A, dh, dl | m³/s |
| Continuity | dS/dt = I - O | S, I, O | m³ |

---

## Theoretical Uncertainty

| Theory | Uncertainty Source | Mitigation |
|--------|-------------------|------------|
| Penman-Monteith | Input data quality | Evidence Engine validation |
| Hargreaves | Simplified assumptions | Use as supplementary |
| Climate Models | Scenario uncertainty | CMIP6 ensemble |
| Groundwater | Parameter heterogeneity | Monte Carlo |
| Crop Models | Genetic variability | Calibration |

---

## Peer-Review Status

| Theory | Peer-Reviewed | Citation Count |
|--------|--------------|----------------|
| Penman-Monteith | ✅ FAO-56 | >10,000 |
| Hargreaves | ✅ Agricultural | >5,000 |
| Thornthwaite | ✅ Climatic | >3,000 |
| Darcy's Law | ✅ Hydrogeology | >8,000 |
| Richards | ✅ Soil physics | >4,000 |

---

## Knowledge Integration Flow

```
Scientific Theory (KT-001)
    ↓ (implemented in)
Engineering Method (KT-002)
    ↓ (applied at)
Domain Expertise (KT-003)
    ↓ (validated with)
Observational Data (KT-004)
    ↓ (provenance tagged by)
Evidence Engine
    ↓ (consumed by)
Decision Engine (Tasmimyar)
    ↓ (augmented by)
AI Layer (KT-009) [isolated]
```

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/02*