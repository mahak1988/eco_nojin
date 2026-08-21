# 19 — Phase 7 Kickoff: Scientific Model Core (22 models)

> Status: **phase 7 started** — 22 real models callable via API with
> fidelity badges; 8 numeric conformance tests green. 330 backend tests.

## 1. Goal

Scientific breadth + computational speed: every model callable from the API
with an honest fidelity badge (official / simplified / experimental),
numerical conformance tests, and a public catalog page.

## 2. What shipped

### `services/models/registry.py`
- 22 model specs, each wrapping a REAL implemented function (no stubs):
  ET0 (Hargreaves), runoff, check-dam/trench/half-moon designs,
  crop yield + comparison (AquaCrop-style), climate projections,
  IPCC biomass (above/below ground), **RothC 5-pool**, **Farquhar
  photosynthesis**, quantum efficiency (experimental), project carbon
  sequestration (VM0042-aligned), soil health index, pedotransfer (Saxton &
  Rawls), salinity class + leaching requirement (FAO), **van Genuchten**
  retention, AWC by texture, **RUSLE** erosion.
- Fidelity counts: official 9, simplified 11, experimental 2.
- `run_model(slug, params)` — validates required/typed params, executes,
  returns `{slug, fidelity, result, executed_ms}`; errors are explicit
  (ValueError → 400), never silent fallbacks.

### API (`/api/v1/models*`, public — science is open)
- `GET /api/v1/models` — list + fidelity_counts.
- `GET /api/v1/models/{slug}` — detail with params.
- `POST /api/v1/models/{slug}/run` — validated execution.

### Frontend `/models`
- ModelCatalog: 22 cards with fidelity badges (رسمی/سادهشده/آزمایشی),
  expandable parameter forms (defaults pre-filled from registry), live run
  with JSON result panel; honest error display.

## 3. Phase 7 acceptance criteria (master plan) — status

| Criterion | Status |
|---|---|
| 22 models callable from API with fidelity badge | ✅ 22 + API + catalog |
| 5 numerical conformance tests green | ✅ 8 conformance checks |
| RothC 5-pool, Farquhar, van Genuchten, RUSLE present | ✅ |
| PINN surrogate (PyTorch) 100–1000× faster | ⏳ next |
| C++20 parity for hot paths | ⏳ cpp_core exists; bridging next |
| Model card (limits/validity domain) | ⏳ Phase 9 (card template in catalog) |

## 4. Next steps (Phase 7 remainder)
1. Model cards (validity domain + limitations per model) — frontend only.
2. PINN surrogate training scaffold (PyTorch) for real-time bot/USSD answers.
3. C++20 numeric parity for hot paths via `engine/cpp_core` bridge.

## 5. Model cards + PINN scaffold (this session)

### Model cards (validity domain + limitations)
- `MODEL_CARDS` in the registry: every one of the 22 models now carries an
  honest validity domain and limitation note (e.g. ET0 "daily, semi-arid;
  large error in windy/humid conditions"). Exposed via the API and rendered
  in `/models` catalog cards.

### PINN surrogate scaffold
- `services/models/pinn_surrogate.py` — optional PyTorch: without torch the
  module imports cleanly and reports `available=False` (honest); with torch,
  a small MLP + training loop (`fit`) is ready for surrogate training.
- Tests: `tests/test_pinn.py` (3; 2 skipped without torch).

### CDS (ERA5) client
- `services/satellite/cds.py` — job-flow REST client for the Climate Data
  Store (see docs 16 §6).

## 6. Copernicus data stores (CDS / EWDS / ADS) + SEPAL

All three Copernicus stores share the same free key flow (register →
open the "how-to-api" page → copy the UID + API key shown there):
- CDS  — ERA5 reanalysis — https://cds.climate.copernicus.eu/how-to-api
- EWDS — weather store   — https://ewds.climate.copernicus.eu/how-to-api
- ADS  — CAMS air quality — https://ads.atmosphere.copernicus.eu/how-to-api

`services/satellite/cds.py` → `DataStoreClient(store="cds|ewds|ads")`
(submit → poll → download, plain httpx, basic auth uid:key). Env:
`CDS_UID/CDS_API_KEY`, `EWDS_UID/EWDS_API_KEY`, `ADS_UID/ADS_API_KEY`
(key links live in `.env` comments and in the status payload).

SEPAL (https://sepal.io) — FAO EO platform: **no API key**; web login via
Google/GitHub; automation uses a login token. `SEPAL_BASE_URL` set.

Endpoints:
- `GET /api/v1/satellite/stores/status` — all stores + SEPAL, honest flags
- `GET /api/v1/satellite/cds/status` — backward-compatible CDS only

Tests: `tests/test_cds.py` (10).

## 7. C++20 parity for hot paths (acceptance item)

Built and verified:
- `engine/cpp_core/bindings/c_api.cpp` — extern "C" surface over the
  existing C++20 kernels (ET0 Hargreaves, extraterrestrial radiation,
  van Genuchten), compiled to `hydroma_core.dll` with MSVC 2019 /O2
  (script in the file header; `build_v1.bat` pattern).
- `services/models/cpp_bridge.py` — ctypes loader (env `HYDROMA_CORE_DLL`
  or repo default). Honest `available` flag; kernels raise
  `CppBridgeUnavailable` when the DLL is missing (no silent Python fallback).
- `GET /api/v1/models/cpp-status` — capability + which kernels are bridged.
- Numeric parity verified: C++ vs Python registry results agree to
  rel 1e-9 for `et0_hargreaves` and `van_genuchten_theta`
  (`tests/test_cpp_bridge.py`, 5 tests; skip when DLL absent).
- UI: `/models` catalog shows a C++20 engine badge.

Build command (from engine/cpp_core):
```
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\
      VC\Auxiliary\Build\vcvars64.bat"
cl /nologo /std:c++20 /O2 /EHsc /LD /Iinclude bindings\c_api.cpp ^
   src\climate.cpp src\soil.cpp /Fe:hydroma_core.dll
```

## 8. PINN surrogate — LIVE (PyTorch installed)

`pip install torch` (2.13.0) is now present in the venv, so the surrogate
scaffold is ACTIVE:
- `services/models/pinn_surrogate.py` — `available=True`; MLP + `fit()` loop.
- `tests/test_pinn.py` — 3 tests pass (toy sin(x) surrogate converges,
  loss < 0.5; predict shape).
- `GET /api/v1/models/pinn-status` — honest capability report.
Next: train a production surrogate (e.g. crop yield vs AquaCrop inputs)
for millisecond answers in the bot/USSD path.

## 9. ERA5 real-data pipeline (Phase 7 wrap)

`services/satellite/era5_fetch.py` — real ERA5 daily series for a point:
- CDS job flow (submit -> poll -> download) + NetCDF parse via **h5netcdf**
  (in-memory, no Windows file locks).
- Variables: t2m (daily mean, C), tp (daily sum, mm).
- `POST /api/v1/satellite/era5/series?lat=&lon=&start=&end=&variables=`
  (variables comma-separated, optional).
- Errors are honest: missing licence -> 401 "operation not allowed" from
  CDS is surfaced; bad coordinates/unknown variables -> 400.
- Tests: `tests/test_era5.py` (7: parse, nearest-point, daily agg, mocked
  pipeline, store-error surfacing).

Auth model for the new CDS (2025+): single personal-access token
(`key:<uuid>`), **Bearer** header; the old uid:key Basic scheme is kept
behind `CDS_AUTH=basic`. Endpoint path is the OGC-style
`/retrieve/v1/processes/{dataset}/execution`.

### App-start fixes this session
- `main.py`: added missing `import os` (crash: `NameError: os` in lifespan).
- `main.py`: `load_dotenv()` at import time so satellite clients see .env
  (pydantic-settings alone does not populate os.environ).
- `globals.css`: `scroll-behavior: smooth` now respects
  `prefers-reduced-motion`.
