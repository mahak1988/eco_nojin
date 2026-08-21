# 32. Phase 3 Sprint 2 (Part 2) — Real Weather & SWAT+ Runner

**Date:** 2026-08-17 | **Status:** Active | **Class:** Technical
**Basis:** Doc 31 (sprint 2 part 1).

> This commit delivers: a real-weather source (Open-Meteo + FAO-56
> Hargreaves ET0) with optional chain wiring, and a SWAT+ runner
> (binary subprocess + output.hru parser).

## 1) Real Weather — `simulation/weather_source.py`
- **Open-Meteo Archive API** (free, no key): daily Tmin/Tmax/precipitation.
- **FAO-56 Hargreaves ET0** computed locally:
  `ET0 = 0.0023·Ra·(Tmean+17.8)·√(Tmax−Tmin)` with standard solar geometry
  (Ra from latitude and day of year).
- Output uses the aquacrop 3.x column order:
  `MinTemp, MaxTemp, Precipitation, ReferenceET, Date`.
- Network failure → explicit `WeatherUnavailable`; fallback to synthetic
  weather **only with a `synthetic (fallback)` label + error message**.

**Chain wiring:** `ChainInputs.lat/lon/use_real_weather` — when enabled the
orchestrator fetches real weather for the planting→harvest window and
records `weather_source="open-meteo (real)"` in the aquacrop output.

## 2) SWAT+ Runner — `simulation/runners/swat_runner.py`
- Runs the SWAT+ binary via subprocess (in the project dir, text-I/O
  convention).
- **output.hru parser** by column name (case-insensitive): AREA, RUNOFF,
  SEDYLD → basin aggregates: `area_ha`, `runoff_mm` (area-weighted),
  `sedyld_t` (sum of sedyld × area).
- **Honesty:** the operator must supply the binary (download from
  swat.tamu.edu); when missing, `SwatUnavailable` with a clear message —
  no fabricated fallback.
- Tests: parser with a real fixture, error paths, and the success path with
  a mocked subprocess.

## 3) Tests
- 18 new tests (weather 9: Hargreaves, fetch, errors, window; SWAT 6;
  orchestrator real-weather 2 + honest fallback).
- Full suite: **483 passed**.

## 4) Next
- Obtain the SWAT+ binary and build a sample project for field validation
  of the parser;
- RothC reference validation with official data;
- ERA5 via CDS (optional, replaces Open-Meteo for longer series);
- wire chain outputs to the MRV dashboard.
