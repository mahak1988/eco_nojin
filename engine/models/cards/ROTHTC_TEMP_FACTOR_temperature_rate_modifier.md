# Model Card: ROTHTC_TEMP_FACTOR — RothC Temperature Rate Modifier

## 1. Identification

| Field | Value |
|---|---|
| **model_id** | `ROTHTC_TEMP_FACTOR` |
| **name** | RothC Temperature Rate Modifier |
| **version** | `1.0.0` |
| **scientific_domain** | Soil carbon turnover |
| **intended_use** | Report the RothC-26.3 temperature rate modifier that multiplies the compartment rate constants, for a mean monthly air temperature. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|---|---|
| **governing_equations** | Coleman, K., Prout, J.M. & Milne, A.E., *RothC — A Model for the Turnover of Carbon in Soil*, Rothamsted Research, section 1.6.1, equation (1): `RM_Tmp = 47.91 / (1 + e^(106.06 / (T + 18.27)))`, with T the average monthly air temperature in degrees Celsius. The official Fortran, Python and R releases additionally hard-zero the modifier below -5 C, which this implementation reproduces. |
| **equation_conventions** | The factor is dimensionless and multiplies the compartment rate constant k directly. It is monotonically increasing with **no optimum and no supra-optimal decline**, so it legitimately exceeds 1.0; 47.91 is the constant that normalises it to exactly 1.0 at T = 9.291 C, the Rothamsted mean annual temperature marked on Figure 2 of the model description. |
| **assumptions** | (1) The equation is calibrated over roughly -10 to 40 C; extrapolating the exponential outside that range gives values the calibration cannot support. (2) The -5 C guard is a numerical guard from the official code, not a value in the published equation. |
| **applicability_domain** | All T at or above -5 C. At T = -18.27 C the exponent's denominator crosses zero and the equation is undefined; the guard means the implementation never evaluates it. |

---

## 3. Input / Output Schema

| Field | Value |
|---|---|
| **input_schema** | `temperature` (float, C) |
| **output_schema** | `value` (float, dimensionless), `units` |
| **units** | Temperature in C; the modifier dimensionless. |

---

## 9. Implementation & Traceability

| Field | Value |
|---|---|
| **implementation_status** | Production — implemented in `engine/hydroma/simulation/runners/rothc_runner.py::temp_factor`, dispatched by the gateway route `engine/gateway/model_dispatcher.py::_rothc_gateway_out`. |
| **verification_status** | Verified — the implementation reproduces equation (1) and the official low-temperature guard bit-for-bit over eight comparison cases that include every published tabulated check point and the 9.291 C normalisation; see `engine/validation/ROTHTC_TEMP_FACTOR.md`. |
| **validation_status** | **VALIDATED_METHOD** — validated against the published RothC-26.3 section 1.6.1 equation (1) with the evidence record `engine/validation/ROTHTC_TEMP_FACTOR.md`, whose reference values are re-derived independently of the engine in `engine/validation/test_validation_records.py`. Only the temperature modifier is credited; the other three RothC rate modifiers, the pool rates and the steady state remain unvalidated. |
| **provenance** | `data_source: "computed"`; `model: "RothC-26.3 (Coleman, Prout & Milne 2024)"`; `computed: True` |
| **validation_record** | `engine/validation/ROTHTC_TEMP_FACTOR.md` |
| **unit_tests** | `engine/validation/test_validation_records.py`, `engine/strict_tests/test_s20_simulation_validation.py::TestRothcSocLaws` |
