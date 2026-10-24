# Stage 40 — Limitations

These are the limits of what Stage 40 established. They are stated
plainly so that nothing in the reports can be read as more than it is.

## Scope

| Limit | Detail |
|---|---|
| One dataset | CIMMYT eastern-India wheat, one region, six seasons (2016-17 to 2021-22) |
| Three test districts | Buxar, Muzaffarpur, Rohtas - the whole test set is three clusters |
| A sample, not the full test set | 450 evaluated of 450 sampled |
| One free parameter | `epsilon`; `HI` fixed at 0.45 |
| One model | HYRUE; no other crop model was compared |
| One metric family | RMSE, MAE, bias, R², MAPE - no skill score against an operational forecast |

## Model limitations that remain open

| Item | Why it matters |
|---|---|
| `epsilon` and `HI` are perfectly collinear | Only their product is identifiable from yield data; the fitted `epsilon` is a scale, not a measurement |
| The objective is nearly flat over the grid | Many `epsilon` values fit the data almost equally well; the value is one point on a plateau |
| The thermal response has a hard-coded 8 °C Gaussian width | No source; the width was never a free parameter |
| LAI is model-generated for every record | The GDD curve is assumed, not observed; `k` and `lai_max` cannot be separated |
| EWSI weights and anchors are project defaults | The fitted `epsilon` may have absorbed an EWSI amplitude error |
| Soil moisture is ERA5-Land reanalysis at ~9 km | Field capacity 0.35 m³/m³ is a default |
| Satellite NDMI is one 20 m pixel per field | Most season days have no observation and are forward-filled |
| Observation uncertainty is not propagated | The reported intervals understate the total uncertainty |

## Evaluation limitations

| Item | Detail |
|---|---|
| Three spatial clusters | The district-level bootstrap has three clusters; its 2.5th and 97.5th percentiles are close to the extreme resamples |
| Calibration uncertainty not in the interval | The bootstrap runs on the frozen model, not the calibration |
| Input uncertainty not in the interval | Remote-sensing, weather and observation uncertainty excluded |
| The test set was used once | It has now been looked at. A stage that adjusts the model to these numbers has consumed it |
| The API path can fall back | The weather source falls back from Open-Meteo ERA5 to NASA POWER on timeout |

## What would be needed to lift the status

1. **Observed LAI** (or a published EWSI weighting) to break the
   `epsilon`/`HI` degeneracy and the LAI confound.
2. **A second dataset** in a different agro-climatic zone.
3. **The full 1,722-record test set**, or an explicit statement that the
   sample is sufficient.
4. **A nested bootstrap** that resamples the calibration inside the
   interval computation.
5. **A second external dataset** to separate "this model works" from
   "this model works in Bihar".
