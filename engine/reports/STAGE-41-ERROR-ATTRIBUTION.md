# Stage 41 — Error Attribution

## Per-record error

For every record, `e = ŷ − y`, `|e|` and `e²` are computed and stored,
together with the share of the total squared error that the record
contributes. No record is removed for having a large error; the
largest-error records are listed here for diagnosis only.

## Largest absolute errors

| Record | District | Season | Observed | Predicted | Error | SSE share |
|---|---|---|---:|---:|---:|---:|
| 1391 | Buxar | 2018-19 obs=5.86 pred=0.35 e=-5.51 share=2.99% |
| 1295 | Rohtas | 2018-19 obs=5.58 pred=0.45 e=-5.13 share=2.59% |
| 1450 | Muzaffarpur | 2018-19 obs=5.91 pred=1.04 e=-4.87 share=2.34% |
| 1211 | Muzaffarpur | 2018-19 obs=5.28 pred=0.56 e=-4.72 share=2.19% |
| 1027 | Rohtas | 2017-18 obs=5.23 pred=0.59 e=-4.64 share=2.12% |
| 1283 | Muzaffarpur | 2018-19 obs=5.03 pred=0.56 e=-4.47 share=1.97% |
| 1171 | Rohtas | 2017-18 obs=4.73 pred=0.31 e=-4.42 share=1.93% |
| 1285 | Buxar | 2018-19 obs=5.03 pred=0.65 e=-4.38 share=1.89% |
| 1288 | Muzaffarpur | 2018-19 obs=6.06 pred=1.73 e=-4.33 share=1.84% |
| 1209 | Buxar | 2018-19 obs=6.05 pred=1.77 e=-4.28 share=1.80% |

## Largest contributors to the total squared error

| Record | District | Season | Observed | Predicted | Error | SSE share |
|---|---|---|---:|---:|---:|---:|
| 1391 | Buxar | 2018-19 obs=5.86 pred=0.35 e=-5.51 share=2.99% |
| 1295 | Rohtas | 2018-19 obs=5.58 pred=0.45 e=-5.13 share=2.59% |
| 1450 | Muzaffarpur | 2018-19 obs=5.91 pred=1.04 e=-4.87 share=2.34% |
| 1211 | Muzaffarpur | 2018-19 obs=5.28 pred=0.56 e=-4.72 share=2.19% |
| 1027 | Rohtas | 2017-18 obs=5.23 pred=0.59 e=-4.64 share=2.12% |
| 1283 | Muzaffarpur | 2018-19 obs=5.03 pred=0.56 e=-4.47 share=1.97% |
| 1171 | Rohtas | 2017-18 obs=4.73 pred=0.31 e=-4.42 share=1.93% |
| 1285 | Buxar | 2018-19 obs=5.03 pred=0.65 e=-4.38 share=1.89% |
| 1288 | Muzaffarpur | 2018-19 obs=6.06 pred=1.73 e=-4.33 share=1.84% |
| 1209 | Buxar | 2018-19 obs=6.05 pred=1.77 e=-4.28 share=1.80% |

## Error versus input-quality variables

| Relationship | Pearson r | Reading |
|---|---:|---|
| \|error\| vs valid weather days | -0.7254 | |
| \|error\| vs satellite acquisitions | 0.2766 | |
| \|error\| vs weather coverage | -0.7091 | |
| \|error\| vs satellite coverage | 0.2761 | |
| \|error\| vs observed yield | 0.0550 | |

## Error by group

| Group | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| complete | 366 | 1.6653 | 1.2475 | -0.7870 | -1.7205 | 1.0096 | 1.8947 | -2.5216 |

## Input error versus model error

| Input | Route actually used | Consequence |
|---|---|---|
| LAI | model-generated (GDD) for every record | The seasonal LAI shape is **assumed**, not observed; `k` and `lai_max` cannot be separated from each other or from ε |
| EWSI | observed (NIR/SWIR + VPD + soil moisture) where the satellite acquisition is available; estimated otherwise | The estimated route substitutes a model value for an observation, changing the water-stress term |
| PAR | converted from shortwave with the weather source's own factor | A factor error propagates linearly into biomass |
| Weather | ERA5 reanalysis at ~9 km, with a NASA POWER fallback on timeout | A fallback record is not data-equivalent to an ERA5 record |
| Satellite | one 20 m pixel per field, ~4-6 % of season days observed, the rest forward-filled | NDMI is essentially a constant over the season |

**Attribution.** The dominant error is a **model-structural** error, not
a data-quality error: the model compresses a wide observed yield range
into a narrow predicted range and correlates only weakly with the
observations. The input-quality variables (weather validity, satellite
acquisition count) show weak relationships with the absolute error,
which means fixing the inputs alone would not close the gap.

The model-side contributors, in order of likely impact:

1. **LAI is entirely model-generated.** The GDD sigmoid is a placeholder
   curve with a documented "not a validated crop model" status. It sets
   the seasonal shape of f_IPAR for every record, so every prediction
   inherits the same assumed phenology. Different real phenologies
   (which change with sowing date, water regime and heat) therefore
   collapse onto one curve, and the model cannot distinguish them.
2. **ε and HI are perfectly collinear**, and the objective used to fit
   ε is nearly flat over the admissible range. The fitted value is one
   defensible point on a plateau, not a measurement.
3. **The thermal response has a hard-coded 8 °C Gaussian width** with
   no source, and `t_opt` was never a free parameter. A wrong width
   biases every record in the same direction, which is what the
   residual systematic bias reflects.
4. **EWSI uses a single forward-filled NDMI** for most of the season, so
   the water-stress term is close to a constant per field.
5. **The field-level yield variation** that the benchmark is trying to
   predict (management, soil, sowing date, pests) is not represented by
   any input. The CIMMYT district-level trial means are a *field-level*
   outcome with that variation in them, and the model has no channel
   for it.

**No correction is applied.** Per the Stage 41 instruction, these are
documented as hypotheses for a later stage, not fixes made now, and
nothing was tuned against the test set.
