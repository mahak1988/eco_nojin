# ECO-02: Scientific Dependency Graph

## Chain-A: Climate → ET → Demand → Irrigation

---

## Source Evidence
- ECO-01/09-SCIENTIFIC-DEPENDENCY-GRAPH.md
- ECO-01/03-ENGINEERING-KNOWLEDGE-REGISTRY.md
- ECO-01/05-DOMAIN-KNOWLEDGE-REGISTRY.md

---

## Chain-A Dependencies

### Level 1: Climate Forcing
```
CMIP6 (CANON-018) ──→ RegCM (CANON-016) ──→ HadGEM2 (CANON-017)
        │
        └──→ WRF (CANON-014) ──→ HRRR (CANON-015)
```

**Dependencies**:
- CMIP6 → all climate models (downstream consumer)
- RegCM requires CMIP6 boundary conditions
- WRF requires observational forcing data

### Level 2: Reference ET
```
Penman-Monteith (CANON-001) ←─ Hargreaves (CANON-002) ──→ Thornthwaite (CANON-003)
        │                              │
        └──→ Hargreaves-Samani (CANON-005)    └──→ Makkink (CANON-006)
        │
        └──→ Priestley-Taylor (CANON-007)    └──→ Jensen-Haise (CANON-008)
```

**Dependencies**:
- Penman-Monteith requires: temperature, humidity, wind, solar radiation
- Hargreaves requires: temperature only (simplified)
- All ET models depend on Climate Forcing (Level 1)

### Level 3: Water Demand
```
FAO-56 (CANON-009) ──→ Blaney-Crop (CANON-004)
        │
        └──→ Crop Coefficient method
```

**Dependencies**:
- FAO-56 requires: ET0 (from Level 2), crop coefficients
- Blaney-Crop requires: temperature, sunshine hours, crop data

### Level 4: Irrigation
```
AquaCrop (CANON-010) ──→ SWAT (CANON-011)
```

**Dependencies**:
- AquaCrop requires: ET (from Level 2), crop parameters, soil data
- SWAT requires: precipitation, temperature, land use, soil

---

## Dependency Graph (ASCII)

```
Level 1 (Climate)
    ├── CMIP6
    │   ├── RegCM
    │   └── WRF ── HRRR
    └── HadGEM2
        │
Level 2 (ET) ────────────── Level 1 → Level 2
    ├── Penman-Monteith ←──┐
    ├── Hargreaves ←───────┤
    ├── Thornthwaite ←─────┤
    ├── Hargreaves-Samani ←┘
    ├── Makkink ←──────────┐
    ├── Priestley-Taylor ←─┤
    └── Jensen-Haise ←─────┘
         │
Level 3 (Demand) ────────── Level 2 → Level 3
    ├── FAO-56 ←────────────┐
    └── Blaney-Crop ←───────┘
         │
Level 4 (Irrigation) ────── Level 3 → Level 4
    ├── AquaCrop ←──────────┐
    └── SWAT ←──────────────┘

Level 5 (Groundwater) ───── Additional coupling
    └── MODFLOW ←── SWAT (feedback)

Level 6 (Remote Sensing) ─── Observational coupling
    ├── MODIS ET ←── Penman-Monteith (validation)
    ├── Landsat ←── Land use/soil
    └── Sentinel-2 ←── Crop monitoring
```

---

## Cross-Chain Dependencies

### Climate → ET
- All ET models consume climate variables (temperature, precipitation, wind, radiation)
- Climate uncertainty propagates through ET computation

### ET → Demand
- ET0 is input to FAO-56 crop water calculation
- Demand estimation inherits ET model uncertainty

### Demand → Irrigation
- AquaCrop uses crop water requirement from demand models
- SWAT integrates demand across watershed

---

## Groundwater Coupling (Level 5)

```
AquaCrop ──→ MODFLOW
    │          │
    └── Soil water extraction
    └── Irrigation return flow
```

- MODFLOW simulates groundwater response to irrigation
- SWAT provides surface water-groundwater interaction

---

## Validation Layer (Level 6)

```
MODIS ET ──→ Validate ──→ Penman-Monteith
Landsat ──→ Validate ──→ Land use inputs
Sentinel-2 ──→ Validate ──→ Crop parameters
```

---

## Model Maturity in Chain

| Chain Stage | VERIFIED | SCIENTIFICALLY_SUPPORTED | IMPLEMENTATION_VERIFIED |
|-------------|----------|--------------------------|------------------------|
| Climate | CMIP6 | RegCM, HadGEM2, WRF, HRRR | - |
| ET | Penman-Monteith | Hargreaves, Thornthwaite, Priestley-Taylor, Jensen-Haise | Hargreaves-Samani, Makkink |
| Demand | FAO-56 | Blaney-Crop | - |
| Irrigation | - | AquaCrop, SWAT | MODFLOW |
| Remote Sensing | MODIS, Landsat, Sentinel-2 | - | - |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/09*