# Stage 41 — Input Quality Analysis

## Status of each input

| Input | Status | Count | Consequence |
|---|---|---:|---|


**LAI.** Every record uses the model-generated (GDD) route. No record in
the test set has an observed LAI series, so the seasonal LAI shape is
assumed for all of them. This is the single largest structural input
limitation.

## EWSI

| Status | Count | Consequence |
|---|---:|---|


## PAR

| Status | Count | Consequence |
|---|---:|---|


## Weather source

| Source | Count | Consequence |
|---|---:|---|


A fallback record is not data-equivalent to a primary record and is
identified so that it can be excluded or weighted in a later analysis.

## Metrics by input quality

| Input quality | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| complete | 366 | 1.6653 | 1.2475 | -0.7870 | -1.7205 | 1.0096 | 1.8947 | -2.5216 |

## Metrics by LAI status

| LAI status | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| estimated | 366 | 1.6653 | 1.2475 | -0.7870 | -1.7205 | 1.0096 | 1.8947 | -2.5216 |

## Metrics by EWSI status

| EWSI status | n | Cal RMSE | Cal MAE | Cal Bias | Cal R² | Mean-ref RMSE | Base RMSE | Base R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| estimated | 97 | 2.4617 | 1.9225 | -1.7821 | -5.5067 | 0.9789 | 2.6458 | -6.5168 |
| observed | 269 | 1.2602 | 1.0042 | -0.4282 | -0.5300 | 1.0205 | 1.5362 | -1.2737 |

## Separating incomplete inputs from model error

| Rule | Result |
|---|---|
| Records with a prediction | 366 of 1722 |
| Records dropped from the metric set | 1356 |

Incomplete or failed records are **not** deleted: they are counted by
status and written to `failed_records.jsonl`. The metrics are computed
on the records that produced a prediction, and the count of records
without one is stated above so the reader can see exactly what the
metrics cover.
