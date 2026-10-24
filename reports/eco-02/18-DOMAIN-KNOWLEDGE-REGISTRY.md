# ECO-02: Domain Knowledge Registry

## Hydrological and Agronomic Domain Knowledge

---

## Source Evidence
- ECO-01/05-DOMAIN-KNOWLEDGE-REGISTRY.md
- ECO-01/03-ENGINEERING-KNOWLEDGE-REGISTRY.md
- ECO-01/02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md

---

## Domain Knowledge Categories

| Category | Description | Key Models |
|----------|-------------|------------|
| Meteorology | Weather and climate | WRF, HRRR, CMIP6 |
| Hydrology | Water flow and transport | HEC-HMS, MODFLOW |
| Agronomy | Crop water and soil | FAO-56, AquaCrop |
| Evapotranspiration | ET calculation methods | Penman-Monteith, Hargreaves |
| Water Resources | Allocation and management | Reservoir, optimization |
| Remote Sensing | Satellite data processing | MODIS, Landsat, Sentinel-2 |
| Groundwater | Subsurface water | MODFLOW, groundwater flow |
| Climate Science | Climate dynamics | RegCM, HadGEM2 |
| Numerical Methods | Computational techniques | Interpolation, optimization |

---

## Iranian-Specific Domain Knowledge (KT-003)

### Local Crop Coefficients (GAP-003)
| Crop | Kc (MID) | Kc (END) | Region | Source |
|------|----------|----------|--------|--------|
| Wheat | 1.15 | 0.45 | Khorasan | FAO-26 adapted |
| Barley | 1.15 | 0.45 | Kermanshah | FAO-26 adapted |
| Rice | 1.2 | 0.45 | Mazandaran | Local studies |
| Cotton | 1.0 | 0.45 | Khuzestan | Local studies |
| Orchard | 0.85 | 0.60 | Various | FAO-26 |

### Regional Climate Characteristics
| Region | Climate Type | Key Features |
|--------|-------------|-------------|
| Alborz | Mediterranean/Mountain | High precipitation, snow |
| Zagros | Semi-arid/Mountainous | Seasonal drought |
| Khorasan | Arid/Cold | Low precipitation, high evap |
| Khuzestan | Hot/Arid | High temp, low precip |
| Mazandaran | Mediterranean/Coastal | High humidity, rainfall |

---

## Engineering Knowledge (KT-002)

### Standard Methods
1. **SCS-CN Method** - Runoff estimation
2. **Muskingum Method** - Flood routing
3. **Darcy's Law** - Groundwater flow
4. **Bernoulli's Equation** - Flow hydraulics
5. **Manning's Equation** - Open channel flow

### Software Standards
| Standard | Application |
|----------|-------------|
| FAO-56 | ET and crop water |
| IEEE 754 | Double precision |
| UNIFORMAT | Unit standardization |
| WGS84 | Spatial reference |

---

## Equation References

From ECO-01/08-EQUATION-AND-UNIT-FORENSICS.md:

### Core Equations
| Equation | Reference | Units |
|----------|-----------|--------|
| Penman-Monteith | FAO-56 Eq 6.7 | mm/day |
| Hargreaves | Hargreaves & Samani (1985) | mm/day |
| Thornthwaite | Thornthwaite (1948) | mm/month |
| Continuity | ∂S/∂t = I - O | m³/s |
| Darcy's Law | Q = -KA(Δh/Δl) | m³/day |
| Manning's | v = (1/n)R^(2/3)S^(1/2) | m/s |

---

## Knowledge Maturity Scale

| Maturity | Definition | Count |
|----------|------------|-------|
| VERIFIED | Peer-reviewed, validated | 8 models |
| SCIENTIFICALLY_SUPPORTED | Theory-backed | 7 models |
| IMPLEMENTATION_VERIFIED | Code matches theory | 6 models |
| CODE_ONLY | No scientific backing | 0 |
| STUB | Placeholder | 1 model |

---

## Integration with Daneshyar

### Knowledge → Evidence
- Verified models → HIGH trust evidence
- Empirical methods → MEDIUM trust evidence
- AI models → LOW trust evidence

### Knowledge ←→ Decision
- Regulatory knowledge → Policy rules (DE-001, DE-009)
- Domain expertise → Resource allocation (DE-003)
- Scientific theory → Risk assessment (DE-002)

---

## Iranian Water Knowledge System (Irrigation Organization Data)

### Key Parameters
| Parameter | Value | Source |
|-----------|-------|--------|
| Net Irrigation Requirement | 5.2 Mm³/year | IOWB (Irrigation and Reclamation) |
| Efficiency (Surface) | 35-50% | FAO-56 |
| Efficiency (Pressurized) | 70-85% | FAO-56 |
| Efficiency (Sprinkler) | 75-90% | FAO-56 |
| Efficiency (Drip) | 90-95% | FAO-56 |

---

## Domain Knowledge Gaps

Per ECO-01/18-RESEARCH-GAPS.md:

| Gap | Description | Priority |
|-----|-------------|----------|
| GAP-003 | Iranian crop coefficients | P1 |
| GAP-004 | Groundwater depletion rates | P1 |
| GAP-005 | Irrigation efficiency | P1 |
| GAP-008 | Soil moisture distribution | P1 |
| GAP-010 | Agricultural drainage | P2 |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/05, 08*