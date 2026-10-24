# Stage 41 — Limitations

## What the test set does and does not evaluate

| Question | Answer |
|---|---|
| Are the three test districts disjoint from the development districts? | **Yes.** The seven development districts (Bihar and eastern UP) and the three test districts (Buxar, Muzaffarpur, Rohtas) share no records; the split manifest defines the partition and the leakage guard is asserted before the calibration. |
| Do the test districts have enough climate and management diversity? | **Partly.** Three districts in one agro-ecological zone of one state. They differ in yield level and in bias sign, but they do not span the climatic or management range of Indian wheat. |
| Are the CIMMYT coordinates precise enough for satellite evaluation? | **Yes for the 20 m Sentinel-2 pixel.** The coordinates are field-level; the satellite value is a single 20 m pixel at that point. The limitation is temporal, not spatial. |
| Are the weather and satellite data comparable across districts? | **Mostly.** All three districts use the same ERA5 source and the same Sentinel-2 collection; a small number of records fall back to NASA POWER, and those are identified per record. |
| Are the results stable across seasons? | **No.** Performance varies by season and the bias changes sign between seasons. |
| Are the test results enough to generalise to other regions? | **No.** Three spatial clusters cannot support a generalisation claim. |

## Spatial generalisation uncertainty

The district-level cluster bootstrap is reported in the benchmark
summary. Its limitation is structural, not statistical: with three
clusters the bootstrap distribution is the distribution of three draws,
so the 2.5th and 97.5th percentiles sit close to the extreme
resamples. The interval is reported with that caveat and **must not be
read as a confidence statement about generalisation to other regions**.

The uncertainty budget also excludes the calibration component (the
bootstrap runs on the frozen model, not on the calibration) and the
input component (remote-sensing, weather and observation uncertainty).
The reported interval therefore **understates** the total uncertainty.

## Sampling

The Stage 40 evaluation used a 450-record stratified sample; Stage 41
evaluates the complete 1722-record test
frame. The sample was drawn proportionally within district × season
strata with a floor per stratum, so it is representative by design; the
side-by-side comparison in `STAGE-41-BASELINE-VS-CALIBRATED.md`
quantifies how representative it was in practice.

## What remains open

| Item | Status |
|---|---|
| ε / HI collinearity | Open - only their product is identifiable from yield data |
| LAI model validation | Open - the GDD sigmoid is documented as a placeholder, not a validated crop model |
| EWSI weighting provenance | Open - weights and anchors are project defaults |
| Thermal response width | Open - the 8 °C Gaussian width has no source and was never a free parameter |
| Operational baseline | Absent - the repository has no operational forecast to compare against |
| Second external dataset | Absent - every result here comes from one dataset in one region |
| Field-level yield drivers | Not represented by any input (management, soil, pests) |
