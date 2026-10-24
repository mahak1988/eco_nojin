# Stage 37 — Runtime Integrity

## Problem

Python could not import from `engine.hydroma.models.*` or `engine.hydroma.simulation.*` even though PowerShell `ls` and `glob` showed the directories existed.

## Root Cause

Two directories existed under `engine/`:

| Directory | Name | Contents |
|---|---|---|
| `engine/hydroma/` | 'hydrama' (with 'a') | Only `eval/` subdirectory (empty shell) |
| `engine/hydroma/` | 'hydroma' (with 'o') | Full code: `models/`, `simulation/`, `eval/`, and 60+ other subdirectories |

All Python imports used `engine.hydroma.*` (matching AGENTS.md and the project name HYDROMA → hydrama), but the actual code was in `engine.hydroma.*` (with 'o').

## Fix

1. Renamed `engine/hydroma/` → `engine/hydrama_wrong/`
2. Renamed `engine/hydroma/` → `engine/hydroma/`
3. Moved Stage 36 Stage files from `hydrama_wrong/eval/` to `hydrama/eval/`
4. Removed `hydrama_wrong/`
5. Replaced all `engine.hydroma.` → `engine.hydroma.` in 295 Python files across the entire repo

## Verification

All 12 critical imports succeed:

| Module | Status |
|---|---|
| `engine.hydroma.models.hyrue` | ✅ |
| `engine.hydroma.models.ewsi` | ✅ |
| `engine.hydroma.simulation.weather_source` | ✅ |
| `engine.hydroma.simulation.ewsi_pipeline` | ✅ |
| `engine.hydroma.simulation.par_pipeline` | ✅ |
| `engine.hydroma.simulation.lai_model` | ✅ |
| `engine.hydroma.eval.seasonal_predictor` | ✅ |
| `engine.hydroma.eval.benchmark_split_manifest` | ✅ |
| `engine.hydroma.eval.calibration_parameter_registry` | ✅ |
| `engine.hydroma.eval.pilot_error_analysis` | ✅ |
| `engine.hydroma.eval.hyrue_calibration` | ✅ |
| `engine.hydroma.eval.hyrue_uncertainty_analysis` | ✅ |

Import guard: **0 violations** (1,383 files scanned).

## Files Modified

- `engine/hydroma/` — directory renamed from `hydroma/`
- `engine/hydrama_wrong/` — removed (was old `hydrama/`)
- 295 Python files — `engine.hydroma.` → `engine.hydroma.` import fix
- `tools/diagnostics/stage37_runtime_diagnostic.py` — new diagnostic tool
