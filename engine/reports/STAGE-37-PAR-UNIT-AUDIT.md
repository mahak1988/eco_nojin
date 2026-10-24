# Stage 37 — PAR Unit Audit

## Audit Finding

The HYRUE biomass equation requires PAR (Photosynthetically Active Radiation) in MJ/m²/day:

```
B_daily = PAR * f_IPAR * epsilon * f_water * f_temp
```

Units: MJ/m²/day × dimensionless × g/MJ × dimensionless × dimensionless = g/m²/day

The Open-Meteo weather source provides `shortwave_radiation_sum` in MJ/m²/day. Shortwave radiation includes UV + visible + NIR; PAR (~400-700 nm) is approximately 40-50% of shortwave.

## PAR Conversion Chain (VERIFIED CORRECT)

| Step | Component | Unit | Conversion |
|---|---|---|---|
| 1 | Open-Meteo `shortwave_radiation_sum` | MJ/m²/day | Raw API value |
| 2 | `build_seasonal_climate_inputs()` | MJ/m²/day → MJ/m²/day PAR | × 0.5 (DEFAULT_PAR_FRACTION) |
| 3 | `HYRUE.compute_daily()` | MJ/m²/day PAR → g/m²/day biomass | × f_IPAR × ε × f_water × f_temp |
| 4 | `HYRUE.compute()` seasonal | g/m²/day → g/m² | Sum over days |
| 5 | `HYRUE.compute()` yield | g/m² → t/ha | × HI / 100 |

## Unit Contract

New module `engine/hydroma/simulation/radiation_units.py` defines:

- `SW_MJ_M2_DAY`, `SW_KWH_M2_DAY` — shortwave units
- `PAR_MJ_M2_DAY`, `PAR_MOL_M2_DAY`, `PAR_MJ_M2_S` — PAR units
- `IPAR_MJ_M2_DAY` — intercepted PAR unit
- `KWH_TO_MJ = 3.6` — kWh to MJ conversion
- `DEFAULT_PAR_FRACTION = 0.5` — estimated PAR fraction
- `shortwave_to_par()` — validated conversion function

## Stage 35 Pilot Error (CORRECTED)

The Stage 35 pilot script used shortwave directly as PAR without ×0.5:

| Scenario | PAR source | Predicted yield | Error |
|---|---|---|---|
| Stage 35 pilot | Shortwave used as PAR (no ×0.5) | 10.899 t/ha | +63.2% |
| Stage 37 corrected | Shortwave × 0.5 → PAR | 4.807 t/ha | −28.0% |

The PAR unit correction alone explains ~50% of the previous overestimation. The remaining −28% is attributable to other uncalibrated parameters (LAI curve, EWSI weights, RUE, HI).

## Double-Conversion Guard

`convert_shortwave_to_par()` includes `already_par=True` parameter — if input is already PAR, no conversion is applied, preventing double multiplication by 0.5.

## Files

- `engine/hydroma/simulation/radiation_units.py` — new unit contract module
- `engine/hydroma/simulation/par_pipeline.py` — already correct (uses ×0.5)
- `engine/hydroma/simulation/weather_source.py` — already correct (stores shortwave in MJ/m²/day)
