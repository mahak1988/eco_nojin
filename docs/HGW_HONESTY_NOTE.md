# Hydroma Global Watchdog — Honesty Note

**Version:** Phase 6b (August 2026)
**Authors:** EcoNojin Scientific Council

## Scientific Status

The Hydroma Global Watchdog (HGW) provides probabilistic scientific
assessments of water security, climate vulnerability, and recovery
potential for regions worldwide. All outputs carry uncertainty and
must be interpreted with caution.

## Validated Outputs ✓

These metrics have been validated against peer-reviewed literature
and external sources (WRI Aqueduct, FAO AQUASTAT, IPCC):

- **Water Bankruptcy Index (WBI):** Rankings align with WRI Aqueduct 4.0
- **WEF Nexus Risk (WERI):** Captures compounding stress correctly
- **Climate-induced Conflict Risk (CRI):** Based on Mach et al. (2019) Nature
- **Ecosystem Recovery Potential (ERPI):** Order-of-magnitude realistic
- **Prescriptive Recovery (PRSP):** Evidence-based, context-aware

## Known Limitations ⚠️

### Köppen-Geiger Classification
Current implementation uses approximate monthly data presets.
This can misclassify border regions (e.g., Sudan, Yemen, Netherlands).

**Planned resolution (Phase 7):** Direct connection to WorldClim
(1991-2020 monthly normals) will provide definitive classification.

### Time-to-Bankruptcy Estimates
These are **order-of-magnitude estimates** (typical range: ±60% of
central value). They should NOT be interpreted as deterministic
predictions. Many factors (technological innovation, policy change,
international aid) can significantly alter trajectories.

### Conflict Risk
Based on Mach et al. (2019) — climate accounts for only 3-20% of
conflict variance. Conflict is driven by many factors (governance,
ethnic tensions, historical grievances) beyond climate.

## Usage Guidelines

### For Policy Makers
HGW serves as a **decision-support tool**, not a decision-maker.
All recommendations require:
1. Local validation by domain experts
2. Socio-economic and cultural context consideration
3. Stakeholder engagement
4. Continuous monitoring and adaptation

### For Researchers
All methodologies are documented with peer-reviewed references.
Users are encouraged to:
- Validate outputs against local data
- Report discrepancies to improve models
- Contribute to the open-source implementation

## Disclaimer

Outputs from HGW are probabilistic scientific assessments. They
carry inherent uncertainty and should never be used as sole basis
for policy decisions. The EcoNojin team accepts no liability for
decisions made based on HGW outputs without proper validation.

## References

- Beck et al. (2018) Scientific Data — Köppen-Geiger maps
- Mach et al. (2019) Nature — Climate as conflict risk factor
- Rigaud et al. (2018) World Bank Groundswell — Climate migration
- IPCC AR6 (2021-2023) — Mitigation pathways
- WRI Aqueduct 4.0 — Water risk atlas
- Peel et al. (2007) HESS — Köppen-Geiger reference