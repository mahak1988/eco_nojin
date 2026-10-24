# Stage 40 — Equation and Unit Audit

## Scope

The actual HYRUE equations were extracted from the code (not from a
specification) and checked for dimensional consistency before any
calibration was attempted. Files audited:

| File | Role |
|---|---|
| `engine/hydroma/models/hyrue.py` | f_IPAR, f_water, f_temp, daily biomass, seasonal yield |
| `engine/hydroma/simulation/radiation_units.py` | radiation unit contract (Stage 37) |
| `engine/hydroma/simulation/par_pipeline.py` | SW → PAR conversion, seasonal input assembly |
| `engine/hydroma/simulation/weather_source.py` | raw shortwave acquisition, unit labels |
| `engine/hydroma/simulation/lai_model.py` | GDD-based LAI |
| `engine/hydroma/simulation/ewsi_pipeline.py` | EWSI composite and stress transforms |
| `engine/hydroma/eval/hyrue_calibration.py` | calibration entry point |

## 2.1 — Radiation Contract

### Chain as implemented

```
Open-Meteo / NASA POWER  shortwave_radiation_sum   [MJ/m^2/day]
        |  weather_source._build_dataframe  (column "ShortwaveRadiation")
        v
par_pipeline.convert_shortwave_to_par(sw, frac_par=0.5)   [MJ/m^2/day PAR]
        |  status="estimated"
        v
SeasonalClimateInputs.par
        |  HYRUE.compute_daily:  apar = par * f_ipar
        v
IPAR                                                     [MJ/m^2/day]
```

### Checks

| Check | Result | Evidence |
|---|---|---|
| Input unit declared | PASS | Open-Meteo `shortwave_radiation_sum` is MJ/m²/day; the Open-Meteo daily block is unit-labelled `MJ/m^2` |
| Conversion applied exactly once | PASS | `convert_shortwave_to_par` is the only conversion point; `SeasonalClimateInputs.par` is consumed directly by `HYRUE.compute_daily`; the `already_par` flag in `radiation_units.shortwave_to_par` short-circuits a second application |
| kWh → MJ handled | PASS | `KWH_TO_MJ = 3.6` in `radiation_units`; `convert_shortwave_to_par` normalises to MJ before applying the fraction |
| Daily shortwave matched to daily biomass | PASS | `SeasonalClimateInputs.par` is a per-day array; `HYRUE.compute` in seasonal mode sums `B_day` element-wise |
| Missing inputs not silently zeroed | PASS | `build_seasonal_climate_inputs` records missing fields; `compute_hyrue_seasonal` raises `WeatherUnavailable` when required inputs are absent; `fetch_daily_weather` raises `WeatherUnavailable` when all three sources fail (no synthetic fallback exists) |
| Fraction provenance | PASS | `PARConversionSpec.status = "estimated"`, `frac_par = 0.5`, `coeff_source` recorded; the frozen config carries `par_conversion_status: "estimated"` |

### Verdict

The radiation chain is dimensionally closed and free of double
conversion. The 0.5 factor is an **estimate** (Monteith & Unsworth 2013
ch. 9; FAO-56 default), not a measurement, and is labelled as such.

## 2.2 — Light Interception

### As implemented (`HYRUE.f_ipar`)

```python
canopy = np.clip(lai, 0, lai_max) if lai_max is not None else np.clip(lai, 0, 20)
return 1 - np.exp(-k * canopy)
```

`lai_max` is consumed (the code comment records that it was previously a
dead parameter).

### Checks

| Check | Result |
|---|---|
| Form matches `f_IPAR = 1 - exp(-k·LAI_eff)` | PASS |
| `LAI_eff = min(LAI, LAI_max)` applied | PASS |
| `f_IPAR ∈ [0, 1]` | PASS — `k > 0`, `canopy ≥ 0` |
| `lai_max` has physical backing | PARTIAL — it is a canopy ceiling (m²/m²), not a fitted parameter. It is treated as `WEAKLY_IDENTIFIABLE` in the registry, not calibrated |
| Negative LAI handled | PASS — clipped to 0 |

## 2.3 — Biomass Production

### As implemented (`HYRUE.compute_daily`)

```python
f_ipar  = self.f_ipar(lai_arr, self.params.k, self.params.lai_max)
f_water = 1 - ewsi_arr
t_clipped = np.where(t_below | t_above, self.params.t_opt, t_as_arr)
f_temp = np.exp(-(((t_clipped - self.params.t_opt) / 8) ** 2))
f_temp = np.where(t_below | t_above, 0.0, f_temp)
apar    = par_arr * f_ipar
biomass = apar * self.params.epsilon * f_water * f_temp
```

### As implemented (`HYRUE.compute`, seasonal mode)

```python
B_total = sum(B_day)
Y       = B_total * HI / 100      # g/m^2 -> t/ha
```

### Dimensional chain

| Term | Unit |
|---|---|
| PAR | MJ m⁻² day⁻¹ |
| f_IPAR | dimensionless |
| IPAR = PAR × f_IPAR | MJ m⁻² day⁻¹ |
| ε (epsilon) | g MJ⁻¹ IPAR |
| f_water, f_temp | dimensionless |
| B_day | g m⁻² day⁻¹ |
| B_season = Σ B_day | g m⁻² |
| Y = B_season × HI / 100 | t ha⁻¹ |

**The chain is dimensionally closed.** ε is in g/MJ IPAR and multiplies an
MJ/m²/day quantity, yielding g/m²/day. The `/100` converts g/m² to
t/ha. No unit error is present, and none needs to be repaired before
calibration.

### The structural insight used by the calibration

`epsilon` and `HI` are both **multiplicative constants applied after the
daily sum**. Therefore

```
S = Σ_d ( PAR_d · f_IPAR_d · f_water_d · f_temp_d )
B_season = ε · S
Y = ε · S · HI / 100
```

`S` is independent of both. Caching `S` per record makes every
(ε, HI) evaluation instant, which is what makes an
identifiability-constrained calibration feasible at all. This is used by
`engine/hydroma/eval/identifiability_calibration.py`.

## 2.4 — Water and Temperature Factors

### f_water

```python
f_water = 1 - ewsi_arr
```

| Check | Result |
|---|---|
| Direction | PASS — EWSI is a *stress* index (0 = no stress, 1 = severe), so its complement is the growth multiplier |
| Range | PASS — EWSI ∈ [0, 1] ⇒ f_water ∈ [0, 1] |
| EWSI definition consistent | PASS — `engine/hydroma/models/ewsi.py` documents the same interpretation |
| Provenance preserved | PASS — `ewsi_provenance` carries component statuses, weights and missing fields into `PredictionResult` |

### f_temp

```python
f_temp = exp(-(((T - T_opt) / 8) ** 2))     # width hard-coded to 8
f_temp = 0 outside [t_min, t_max]
```

| Check | Result |
|---|---|
| Form matches the Gaussian | PASS |
| Range | PASS — f_temp ∈ [0, 1]; exactly 0 outside the cardinal window |
| Cardinal temperatures | PASS — `t_min`/`t_max` are honoured, so 60 °C gives no growth rather than a small non-zero stress |
| **Gaussian width is hard-coded** | **RECORDED DEFECT** — the width 8 °C appears *twice* (`stress_temperature` and `compute_daily`) and has no source. It cannot be calibrated without a code change, and the two copies must be kept in sync by hand |
| Width × T_opt confounding | The width and T_opt trade off against each other; only their combination is meaningful, so neither is separately identifiable |

### LAI source

`LAIModel` is GDD-based. The LAI curve amplitude is confounded with `k`
and with `lai_max`; the model therefore treats the LAI source as a
fixed assumption, not a free parameter.

## 2.5 — Parameters in the Code vs. the Registry

| Code parameter | Code default | Wheat preset | Registry class |
|---|---|---|---|
| epsilon | 2.5 | 2.2 | CALIBRATABLE (1.0–4.0) |
| hi | 0.45 | 0.45 | FIXED (0.2–0.6) |
| k | 0.65 | 0.65 (inherited) | WEAKLY_IDENTIFIABLE (0.3–1.0) |
| lai_max | 6.0 | 6.0 (inherited) | WEAKLY_IDENTIFIABLE (3.0–8.0) |
| t_opt | 25.0 | 20.0 | WEAKLY_IDENTIFIABLE (10.0–30.0) |
| t_min | 5.0 | 5.0 (inherited) | INSUFFICIENT_DATA (0.0–10.0) |
| t_max | 35.0 | 35.0 (inherited) | INSUFFICIENT_DATA (30.0–45.0) |
| thermal_gaussian_width | 8 (hard-coded) | 8 | INSUFFICIENT_DATA (3.0–15.0) |
| ewsi weights | 0.4/0.3/0.3 | same | WEAKLY_IDENTIFIABLE |
| ndmi_ref / ndmi_crit | 0.3 / −0.2 | same | INSUFFICIENT_DATA |
| vpd_low / vpd_high | 0.5 / 4.0 | same | INSUFFICIENT_DATA |
| soil_field_capacity | 0.35 | same | INSUFFICIENT_DATA |
| shortwave_to_par_factor | 0.5 | same | FIXED (unit conversion) |

The crop presets supply only `epsilon`, `hi` and `t_opt`; `k`, `lai_max`,
`t_min` and `t_max` fall back to the generic defaults for every crop. The
code records this explicitly.

## 2.6 — Defects Found

| Defect | Severity | Effect on calibration |
|---|---|---|
| Gaussian width 8 °C hard-coded in two places, no source | Medium | Width cannot be calibrated; `t_opt` is only identifiable jointly with it |
| `t_min`/`t_max`/`lai_max`/`k` have no per-crop source | Low | Fixed assumptions; not fitted |
| `k`, `lai_max`, LAI amplitude mutually confounded | Medium | Treated as `WEAKLY_IDENTIFIABLE`, not freely fitted |
| ε and HI perfectly collinear | High | Only the product is identifiable; HI held fixed |

**No unit error, no double conversion, and no biomass-definition
mismatch was found.** The calibration therefore proceeds against a
structurally sound model, and any improvement it achieves will reflect
parameter values rather than a repaired equation.

## 2.7 — Pre-Calibration Checklist

| Item | Status |
|---|---|
| Radiation chain dimensionally closed | PASS |
| Conversion applied once | PASS |
| Biomass definition consistent with HI | PASS |
| Missing inputs not zero-filled | PASS |
| ε unit consistent with IPAR unit | PASS |
| Parameters classified with bounds fixed in advance | PASS |
| Identifiability constraint defined | PASS — HI fixed, ε free |
| Leakage guard on every calibration entry point | PASS |
