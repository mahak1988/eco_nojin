# Stage 39 — Parameter Identifiability

## Question

If the development-set calibration were executed, could the estimated
parameters be interpreted physically? Or would the optimisation simply
find *a* combination that happens to fit the development set?

## The Structural Problem

HYRUE's seasonal yield is a product of terms that all scale the same
biomass:

```
Y = (sum_d PAR_d * f_IPAR(LAI_d) * f_water(EWSI_d) * f_temp(T_d)) * epsilon * HI
```

`epsilon` (radiation use efficiency) and `HI` (harvest index) are
**multiplicative constants** applied to the same seasonal biomass sum.
For any non-zero biomass:

```
epsilon' = epsilon * r   and   HI' = HI / r
```

produce an **identical** prediction for every record, for any `r > 0`.
The two parameters are perfectly collinear: only their product
`epsilon * HI` is identifiable from yield data.

The same applies to the EWSI weights, the LAI curve amplitude
(`lai_max`), and the temperature-response width
(`thermal_gaussian_width`) when the canopy is not stressed: they all
rescale the same biomass.

## Identifiability Table

| Parameter | Identifiable from yield data? | Reason |
|---|---|---|
| `epsilon * HI` (product only) | **Yes** | Sets the overall yield scale |
| `epsilon` alone | **No** | Perfectly collinear with `HI` |
| `HI` alone | **No** | Perfectly collinear with `epsilon` |
| `k` (light extinction) | **Partly** | Shaped by the LAI curve, confounded with `lai_max` |
| `lai_max` | **No** | Confounded with `k` and with the LAI source itself |
| `t_opt` | **Moderately** | Distinguishable only where temperature stress binds |
| `t_min`, `t_max` | **No** | Rarely binding in this climate; no gradient information |
| `thermal_gaussian_width` | **No** | Collinear with `t_opt` for a narrow temperature range |
| `ewsi_weight_ndmi` | **No** | Collinear with the other two weights (sum = 1) and with `f_water` amplitude |
| `ewsi_weight_vpd` | **No** | Same |
| `ewsi_weight_soil` | **No** | Same |
| `ndmi_ref`, `ndmi_crit` | **No** | Only two of the three affect the transform; the third is degenerate |
| `soil_field_capacity` | **No** | Scales the soil stress term |

## Consequence for the Calibration Design

Only a small number of parameter combinations are identifiable. The
calibration must therefore:

1. **Freeze** the parameters that carry independent scientific backing
   (`epsilon` and `HI` at their literature values, or one of them with
   the other fixed).
2. **Freeze** the EWSI weights at their initial values unless a
   development-set fit demonstrates a stable, cross-validated
   improvement, and then report them as *performance-calibrated* rather
   than as physiologically validated coefficients.
3. Estimate at most one or two parameters at a time, with leave-one-
   district-out cross-validation to check stability.

## Recommended Calibration Design (for Stage 40)

**Step 1 — scale parameters.** With `HI` fixed at 0.45, fit `epsilon` on
the development set. The product `epsilon * HI` is what matters, so
report it as such.

**Step 2 — light interception.** With `epsilon` fixed, fit `k` (and only
`k`) using leave-one-district-out validation.

**Step 3 — thermal response.** Fit `t_opt` only if the temperature
stress term shows real variation in the development set (i.e. if
`f_temp` is not saturated at 0 or 1 for most days).

**Step 4 — EWSI weights.** Treat as a *single* simplex direction
parameter (2 degrees of freedom) and accept them only if
leave-one-district-out RMSE improves consistently. If accepted, they
must be described as calibrated against observed grain yield — a
performance calibration — and explicitly not as physiologically
validated weights.

**Step 5 — freeze and evaluate.** Write the final parameter set with the
calibration method, dataset, record IDs, seed and version recorded.

## Free Parameters Recommended

| Free parameter | Fixed during its fit |
|---|---|
| `epsilon` | `HI` = 0.45, all others at defaults |
| `k` | `epsilon` from step 1, all others at defaults |
| `t_opt` (optional) | `epsilon`, `k` from previous steps |

Maximum three free parameters at any one time, against ~3,967
development records — a ratio of roughly 1:1,300, which is
conservative.

## Current State

No calibration was executed in Stage 39, so this document specifies the
design rather than reporting estimates. The frozen model carries
defaults for every parameter, and every parameter's status field
(`calibratable` / `uncalibrated` / `fixed`) records that.

## Conclusion

A "calibrate everything" approach on this model would produce numbers
that look like measurements but are not identifiable. The scientifically
honest procedure is to estimate the small number of combinations the data
can actually support, and to report the rest as fixed assumptions.
