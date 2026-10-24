# ECO-02: Glossary and References

## Terminology and Source Attribution

---

## Source Evidence
- ECO-01 all reports
- ECO-02.md canonical architecture requirements
- FAO-56 documentation
- ECO-01/15-DANESHYAR-COMPATIBILITY.md
- ECO-01/16-TASMIMYAR-COMPATIBILITY.md

---

## Glossary

### Persian Terms

| Term | Transliteration | Definition |
|------|-----------------|------------|
| اکو نوژین | Eco Nojin | Ecosystem-based design (project philosophy) |
| دانشیار | Daneshyar | Knowledge engine that manages knowledge types |
| تصمیمیار | Tasmimyar | Decision engine that evaluates policy rules |

### Technical Terms

| Term | Definition |
|------|------------|
| **Canonical Asset** | Authoritative implementation of a scientific model (CANON-XXX) |
| **Maturity Scale** | Classification of model scientific validity (VERIFIED→STUB) |
| **UNIFORMAT** | Unit standardization protocol (all SI units) |
| **Evidence Chain** | Flow: Engine→Evidence→Decision→AI→User |
| **ECO-LEGACY-001** | Critical violation: services importing from engine/ |
| **Buffer Protocol** | Zero-copy data transfer between Python and C++ |
| **Provenance Tag** | Metadata tracking evidence origin and trust level |
| **Bounded Context** | Microservices grouping by domain (replaces 73 services) |
| **Trust Level** | HIGH/MEDIUM/LOW classification of evidence reliability |
| **Import Guard** | Runtime check preventing architectural violations |

### Model Maturity Terms

| Term | Definition |
|------|------------|
| **VERIFIED** | Peer-reviewed, field-validated |
| **SCIENTIFICALLY_SUPPORTED** | Theory-backed, partially validated |
| **IMPLEMENTATION_VERIFIED** | Code matches theory, not field-validated |
| **CODE_ONLY** | Implementation exists without scientific basis |
| **STUB** | Placeholder, non-functional |

### Technology Categories

| Category | Definition |
|----------|------------|
| **CORE** | Mission-critical systems that must be maintained |
| **IMPORTANT** | Necessary systems, optimize but maintain |
| **OPTIONAL** | Useful enhancements, not essential |
| **RESEARCH** | Experimental systems, must be isolated |
| **LEGACY** | Deprecated systems, planned for removal |
| **REMOVE** | Critical violations requiring immediate action |

---

## File Naming Convention

### Reports
```
reports/eco-02/NN-DESCRIPTIVE-NAME.md
```
- NN: Two-digit sequence number (00-27)
- DESCRIPTIVE-NAME: Concise description

### ADRs
```
reports/eco-02/adr/ADR-NNN.md
```
- NNN: Three-digit sequence (001-014)

### Contracts
```
reports/eco-02/contracts/CONTRACT-NAME.md
```

### Diagrams
```
reports/eco-02/diagrams/DIAGRAM-NAME.md
```

---

## Evidence Source Reference

| Shorthand | Full Reference |
|-----------|----------------|
| ECO-01/XX | reports/eco-01/XX-FILE-NAME.md |
| ECO-00 | reports/engine-services/INVENTORY.md |
| CANON-XXX | reports/eco-01/20-CANONICAL-ASSETS.md |
| AUDIT-MODEL-XX | reports/engine-services/SCIENTIFIC-MODEL-REGISTRY.md |
| CONFLICT-XXX | reports/eco-01/24-UNKNOWN-AND-CONFLICTS.md |
| UNKNOWN-XXX | reports/eco-01/24-UNKNOWN-AND-CONFLICTS.md |
| GAP-XXX | reports/eco-01/18-RESEARCH-GAPS.md |
| ECO-LEGACY-001 | reports/eco-01/22-LEGACY-DEPENDENCY-STRATEGY.md |
| CONFLICT-XXX | reports/eco-01/24-UNKNOWN-AND-CONFLICTS.md |

---

## Acronym Reference

| Acronym | Meaning |
|---------|---------|
| API | Application Programming Interface |
| AWS | Amazon Web Services |
| CPU | Central Processing Unit |
| ET | Evapotranspiration |
| ET0 | Reference Crop Evapotranspiration |
| FAO | Food and Agriculture Organization |
| GPU | Graphics Processing Unit |
| GIS | Geographic Information System |
| GPS | Global Positioning System |
| HTTP | Hypertext Transfer Protocol |
| HTTPS | HTTP Secure |
| ISO | International Organization for Standardization |
| JSON | JavaScript Object Notation |
| NASA | National Aeronautics and Space Administration |
| NOAA | National Oceanic and Atmospheric Administration |
| RAI | Responsible AI |
| SI | Système International (metric system) |
| SQL | Structured Query Language |
| UI | User Interface |
| URL | Uniform Resource Locator |
| UTF | Unicode Transformation Format |
| WGS | World Geodetic System |

---

## Standards Referenced

| Standard | Full Name | Used For |
|----------|-----------|----------|
| FAO-56 | FAO Irrigation and Drainage Paper 56 | ET calculation |
| IEEE 754 | Standard for Floating-Point Arithmetic | Double precision |
| ISO 19115 | Geographic Information - Metadata | Spatial data |
| WGS84 | World Geodetic System 1984 | Geospatial reference |
| UNIFORMAT | (Project convention) | Unit standardization |

---

## Key References

1. **FAO-56**: Allen, R.G., et al. "Crop evapotranspiration - Guidelines for computing crop water requirements." FAO Irrigation and Drainage Paper 56, 1998.
2. **Penman**: Penman, H.F. "Natural evaporation from open water, bare soil and crops." Proceedings of the International Association of Scientific Hydrology, 1948.
3. **Hargreaves**: Hargreaves, G.H. & Samani, Z.A. "Reference crop evapotranspiration from temperature." ASAE Paper, 1985.
4. **CMIP6**: Eyring, V., et al. "An updated assessment of CMIP6." Geoscientific Model Development, 2021.
5. **MODIS**: Hall, D.K., et al. "MODIS water-vapor and temperature inversion products." IEEE Transactions on Geoscience, 2019.

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01 glossary sections*