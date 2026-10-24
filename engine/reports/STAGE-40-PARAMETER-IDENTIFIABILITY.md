# Stage 40 — Parameter Identifiability

## The structural problem

HYRUE's seasonal yield is

```
Y = ( Σ_d PAR_d · f_IPAR(LAI_d) · ε · f_water(EWSI_d) · f_temp(T_d) ) · HI / 100
```

Two facts about this expression determine what the data can identify.

**1. ε and HI are perfectly collinear.**
Both are multiplicative constants applied *after* the daily sum. For any
`r > 0`:

```
ε' = ε · r      and      HI' = HI / r
```

give **identical** predictions for every record, for every input. No
amount of yield data can separate them. Only the product `ε · HI` is
identifiable from grain yield.

**2. Several other parameters are confounded with each other or with the
inputs.**

| Confounding group | Members | Consequence |
|---|---|---|
| Scale | ε, HI | Only the product is identifiable |
| Canopy light interception | k, lai_max, the LAI series itself | k and lai_max trade off against the LAI source |
| Thermal response | t_opt, the hard-coded Gaussian width (8 °C) | Only their combination is meaningful; the width cannot be fitted at all (hard-coded twice in the implementation) |
| EWSI composition | the three weights (sum = 1), the EWSI anchors, the EWSI amplitude | The weights are 2 free directions that trade against each other and against the anchors |

## Consequence for the calibration design

The response is **not** simply "fit fewer parameters". It is:

1. **Fix the parameters that carry independent scientific backing**, and
   state clearly that fixing them is a *modelling decision*, not a
   proof that their individual values are known.
2. **Fit only the parameter whose effect the data can actually
   constrain.** For the first calibrated model that is `ε` alone, with
   `HI` held at its documented value.
3. **Report the fitted quantity as the product** where that is what the
   data supports, so the reader is not misled into believing that ε
   alone was determined.

## What was fixed, and why

| Parameter | Class | Rationale |
|---|---|---|
| `hi` | FIXED (0.45) | Perfectly collinear with ε. The wheat preset from the literature is the most defensible single choice. **This is a modelling decision, not a claim that the true harvest index is 0.45 for these fields.** |
| `shortwave_to_par_factor` | FIXED (0.5) | A unit conversion, not a model parameter. Fitting it would let a unit assumption absorb a model error. |
| `ndmi_ref`, `ndmi_crit` | INSUFFICIENT_DATA | No published source for wheat in eastern India. Fitting them to grain yield would convert an unvalidated assumption into a dataset-specific value while removing the ability to distinguish a real signal from an artefact. |
| `vpd_low`, `vpd_high` | INSUFFICIENT_DATA | Same reasoning. |
| `soil_field_capacity` | INSUFFICIENT_DATA | Not site-specific; no measurement available for the CIMMYT fields. |
| `thermal_gaussian_width` | INSUFFICIENT_DATA | Hard-coded in the implementation; cannot be fitted without a code change. |
| `t_min`, `t_max` | INSUFFICIENT_DATA | Rarely binding in this climate; no gradient information. |
| `k`, `lai_max` | WEAKLY_IDENTIFIABLE | Confounded with the LAI source. Not freed in the first model. |
| `t_opt` | WEAKLY_IDENTIFIABLE | Confounded with the Gaussian width and the season length. Not freed in the first model. |
| EWSI weights | WEAKLY_IDENTIFIABLE | Two free directions that trade against each other. Not freed in the first model. |
| **`ε`** | **CALIBRATABLE** | The one parameter the data can constrain, given HI fixed. |

## The free parameter

`ε` is bounded to **1.0 – 4.0 g/MJ IPAR**, fixed in the registry
*before* any fitting. The bound is a physical/literature range for
wheat, not a range chosen from the observed fit quality.

The objective is RMSE on development-district records.

## The structural insight that makes calibration feasible

Because ε and HI are applied after the daily sum, the seasonal integral

```
S = Σ_d ( PAR_d · f_IPAR(LAI_d) · f_water(EWSI_d) · f_temp(T_d) )
```

is independent of both, and for any candidate (ε, HI):

```
Y = ε · S · HI / 100
```

Caching `S` per record makes every (ε, HI) evaluation **instant**. The
expensive part — weather acquisition, satellite acquisition, EWSI
computation — is done **once** per record, and the entire parameter
sweep is then arithmetic. This is implemented in
`engine/hydroma/eval/identifiability_calibration.py`.

Without this, a calibration over ~3,900 development records would
require a full pipeline pass per candidate parameter set.

## If the weights are ever fitted

Should a later stage fit the EWSI weights against grain yield, the
report must state that the weights are **calibrated against observed
yield** — a *performance* calibration — and must not describe them as
physiologically validated coefficients. The same applies to any
parameter released from the `WEAKLY_IDENTIFIABLE` class.

## Open identifiability questions for Stage 41

1. Is the LAI series informative enough to separate `k` from `lai_max`?
   Requires a development set with genuine LAI variation (currently
   every record uses the same GDD-model curve, so `k` and `lai_max` are
   only identifiable as a joint effect).
2. Does the EWSI amplitude (the weights and anchors jointly) explain
   variance beyond what `ε` absorbs? If the EWSI amplitude and `ε`
   are also collinear, the EWSI index carries no independently
   identifiable signal in yield data, and that is a scientific finding
   worth reporting rather than hiding.
3. Can the thermal response be separated from the season length? The
   Gaussian width is hard-coded, so `t_opt` is only interpretable
   jointly with it.
