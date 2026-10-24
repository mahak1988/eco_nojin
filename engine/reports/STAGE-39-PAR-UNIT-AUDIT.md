# Stage 39 — PAR Unit Audit

## Audit Scope

Every stage of the radiation chain was traced from data acquisition to
seasonal yield:

```
Open-Meteo shortwave_radiation_sum (MJ/m^2/day)
  -> weather_source._build_dataframe            (stores as ShortwaveRadiation)
  -> par_pipeline.convert_shortwave_to_par     (x 0.5, documented as estimated)
  -> par_pipeline.build_seasonal_climate_inputs -> SeasonalClimateInputs.par
  -> HYRUE.compute -> B_daily = PAR * f_IPAR * epsilon * f_water * f_temp
  -> B_season -> Y_t_ha = B_season * HI / 100
```

## Variable Definitions

| Variable | Meaning | Unit used in code |
|---|---|---|
| Shortwave radiation | Total downward shortwave at the surface (300-3000 nm) | MJ/m²/day |
| PAR | Photosynthetically Active Radiation (400-700 nm) | MJ/m²/day |
| IPAR | PAR intercepted by the canopy | MJ/m²/day |
| ε (epsilon) | Radiation use efficiency | g/MJ IPAR |
| B_day | Daily biomass production | g/m²/day |

**Shortwave ≠ PAR.** PAR is the fraction of shortwave falling in the
400-700 nm band. Using shortwave directly as PAR overestimates the
radiation input.

## Stage 35 Pilot Error — Source

The Stage 35 pilot script used the raw `ShortwaveRadiation` column as PAR
without applying the 0.5 conversion:

```python
par_vals = w['ShortwaveRadiation'].values.astype(float)   # ~2x too large
```

This was a defect in the Stage 35 pilot script, **not** in the library
code. `par_pipeline.build_seasonal_climate_inputs()` has always applied
`convert_shortwave_to_par()` with `frac_par=0.5`.

Effect on the pilot record (Buxar, 2016-17):

| Variant | Predicted yield | Error |
|---|---|---|
| Stage 35: shortwave used as PAR | 10.899 t/ha | +63.2% |
| Stage 37: shortwave x 0.5 -> PAR | 4.807 t/ha | −28.0% |

## Unit Contract

New module `engine/hydroma/simulation/radiation_units.py` defines the
canonical units and conversions:

| Symbol | Value | Meaning |
|---|---|---|
| `DEFAULT_PAR_FRACTION` | 0.5 | PAR fraction of shortwave |
| `KWH_TO_MJ` | 3.6 | kWh/m²/day -> MJ/m²/day |
| `MJ_PER_MOL_PAR` | 0.217 | MJ per mol PAR photons |

### Conversions provided

* `shortwave_to_par(sw_value, sw_unit, par_fraction, already_par)` —
  normalises the unit, applies the fraction, and **skips the conversion
  entirely when `already_par=True`** so a PAR input is never halved twice.
* `kwh_to_mj()` / `mj_to_kwh()`
* `par_energy_to_mol()` / `par_mol_to_energy()` — these two use an
  assumed mean photon energy and are therefore recorded as *estimated*,
  never silently applied.

### Verified behaviour

| Input | Expected | Verified |
|---|---|---|
| 10 MJ/m²/day shortwave | 5 MJ/m²/day PAR | PASS |
| 1 kWh/m²/day shortwave | 1.8 MJ/m²/day PAR | PASS |
| 5 MJ/m²/day already PAR | 5 MJ/m²/day (unchanged) | PASS |
| unknown unit | ValueError | PASS |
| PAR fraction outside (0,1] | ValueError | PASS |

## Scientific Status of the 0.5 Factor

`DEFAULT_PAR_FRACTION = 0.5` is an **approximation**, not a measured
parameter for any specific site. It follows the widely used agricultural
meteorology assumption (Monteith & Unsworth 2013; FAO-56 uses 0.5 in the
absence of spectral data). The true fraction varies with atmospheric
composition, solar zenith angle and aerosol loading.

Provenance is therefore recorded as `estimated`, and the frozen model
config lists `par_conversion_status: "estimated"`.

## Double-Conversion Audit

| Risk | Mitigation | Verified |
|---|---|---|
| kWh->MJ applied twice | `shortwave_to_par()` normalises to MJ once, then applies the PAR fraction | PASS |
| shortwave->PAR applied twice | `already_par=True` short-circuits the fraction | PASS |
| PAR input halved | `already_par` parameter | PASS |
| transformed data cached under the wrong label | Satellite cache stores the *sampled reflectance*, never a PAR value; the cache key includes the source product and processing level | PASS |
| value re-transformed in another module | `HYRUE` consumes `SeasonalClimateInputs.par` as MJ/m²/day and never re-derives it | PASS |

## Mass Balance Check

```
IPAR  = PAR x f_IPAR                            [MJ/m^2/day]
B_day = IPAR x epsilon x f_water x f_temp        [g/m^2/day]
```

With PAR in MJ/m²/day and epsilon in g/MJ, the product is g/m²/day. The
seasonal sum is g/m²; multiplying by dimensionless HI gives g/m² of
grain; dividing by 100 gives t/ha. The chain is dimensionally closed.

## Conclusion

The PAR unit chain is correct and now has an explicit, tested contract.
The remaining −28% pilot error is **not** a unit error: it comes from
uncalibrated parameters (ε, HI, EWSI weights/anchors) and from LAI
representation. Those are addressed by the calibration protocol, not by
further unit manipulation.
