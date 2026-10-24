# Model Card: RUSLE_LS — Topographic LS Factor

## 1. Identification

| Field | Value |
|---|---|
| **model_id** | `RUSLE_LS` |
| **name** | RUSLE Topographic LS Factor |
| **version** | `1.0.0` |
| **scientific_domain** | Soil erosion |
| **intended_use** | Compute the RUSLE topographic (slope-length steepness) factor that multiplies the rainfall-runoff erosivity, soil erodibility, cover-management and support-practice factors. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|---|---|
| **governing_equations** | USDA Agriculture Handbook 703 (Renard et al. 1997), ch. 4, eqs. 4-1 to 4-4: `theta = atan(slope/100)`; `beta = (sin theta / 0.0896) / (3 sin^0.8 theta + 0.56)`; `m = beta / (1 + beta)`; `L = (lambda / 22.13)^m`; `S = 10.8 sin theta + 0.03` below 9 % slope, `16.8 sin theta - 0.50` at or above it (McCool et al. 1987); `LS = L * S`. |
| **equation_conventions** | The slope is entered as a percentage; `lambda` is the slope length in metres; 22.13 m is the standard RUSLE plot length. The result is a dimensionless multiplier on the soil-loss unit of the model consuming it (t/ha/yr). |
| **assumptions** | (1) A single representative slope length and gradient for the plot. (2) The 9 % steepness branch is a published discontinuity the model reproduces rather than smooths. |
| **applicability_domain** | `slope_length_m > 0` and `slope_percent >= 0`. Beyond long slopes the published guidance subdivides the profile, which the model does not do. |

---

## 3. Input / Output Schema

| Field | Value |
|---|---|
| **input_schema** | `slope_length_m` (float, m, > 0), `slope_percent` (float, %, >= 0) |
| **output_schema** | `ls_factor` (float, dimensionless), `ls_factor_inputs`, `data_source`, `units` |
| **units** | Slope in metres; steepness as a percentage; the factor itself dimensionless. |

---

## 9. Implementation & Traceability

| Field | Value |
|---|---|
| **implementation_status** | Production — the native kernel `engine/cpp_core/src/erosion.cpp::ls_factor` is the canonical implementation, dispatched through `engine/hydroma/cpp_bridge.py` with a Python twin in `engine/cpp_core/src/erosion_python.cpp`; the gateway route is `engine/gateway/model_dispatcher.py::_route_canon_007_rusle_ls`. |
| **verification_status** | Verified — the AH-703 equations are evaluated independently in `engine/validation/RUSLE_LS.md` and reproduced to floating-point round-off over six cases spanning 1 – 25 % slope and 10 – 200 m length. |
| **validation_status** | **VALIDATED_METHOD** — validated against the published USDA Agriculture Handbook 703 chapter 4 equations with the evidence record `engine/validation/RUSLE_LS.md`, whose reference values are re-derived independently of the engine in `engine/validation/test_validation_records.py`. Only the topographic factor is credited; RUSLE_SOIL_LOSS remains unvalidated. |
| **provenance** | `data_source: "modelled"`; `model: "Renard et al. 1997 / McCool et al. 1987"`; `computed: True` |
| **validation_record** | `engine/validation/RUSLE_LS.md` |
| **unit_tests** | `engine/validation/test_validation_records.py`, `engine/tests/test_card_code_agreement.py::TestCanon007RusleLs` |
