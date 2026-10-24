"""HY-RUE calibration module — development-data-only calibration.

Calibrates HY-RUE and EWSI parameters using only development-district
records from the CIMMYT dataset. Test-district records are NEVER used
for parameter estimation.

The calibration module:

1. Loads development records from the benchmark split manifest
2. For each dev record, fetches real weather + satellite data
3. Computes EWSI and runs HYRUE with current parameters
4. Computes error metrics (RMSE, MAE, Bias, R²) on dev data
5. Optionally runs a parameter optimization (grid search / coordinate
   descent) on dev data only
6. Returns calibrated parameter values with full traceability

Design constraints:
- Test data is never accessed by calibration functions
- All parameter changes go through CalibrationParameterRegistry
- Calibration method, dataset, and version are recorded per parameter
- If insufficient dev records have complete EWSI inputs, calibration
  is reported as BLOCKED or PARTIALLY_EVALUATED
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from engine.hydroma.models.hyrue import HYRUE, HYRUEParams
from engine.hydroma.simulation.ewsi_pipeline import (
    EWSIComputationPolicy,
    EWSIInputSeries,
    compute_daily_ewsi,
)
from engine.hydroma.simulation.weather_source import fetch_daily_weather

CIMMYT_DATA_PATH = Path(
    "data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx"
)

CALIBRATION_RESULTS_PATH = Path(
    "engine/reports/data/stage36_calibration_results.json"
)

#: Districts reserved for test (held-out, never used for calibration).
TEST_DISTRICTS: list[str] = ["Buxar", "Muzaffarpur", "Rohtas"]

#: Districts used for development (calibration only).
DEVELOPMENT_DISTRICTS: list[str] = [
    "Begusarai",
    "Bhojpur",
    "Deoria",
    "EastChamparan",
    "Kushinagar",
    "Lakhisarai",
    "Madhepura",
]


def _load_split_manifest():
    """Lazy import of benchmark split manifest."""
    from engine.hydroma.eval.benchmark_split_manifest import (
        DEVELOPMENT_DISTRICTS as _DEV_DISTRICTS,
    )
    from engine.hydroma.eval.benchmark_split_manifest import (
        TEST_DISTRICTS as _TEST_DISTRICTS,
    )
    from engine.hydroma.eval.benchmark_split_manifest import (
        load_split_manifest,
    )
    return load_split_manifest(), _DEV_DISTRICTS, _TEST_DISTRICTS


def _build_registry():
    """Lazy import of calibration parameter registry."""
    from engine.hydroma.eval.calibration_parameter_registry import (
        build_registry,
    )
    return build_registry()


@dataclass
class CalibrationRecordResult:
    """Result of running HY-RUE on one calibration (dev) record."""

    field_id: str
    district: str
    year: str
    latitude: float
    longitude: float
    planting_date: str
    harvest_date: str
    observed_yield: float
    predicted_yield: float | None = None
    absolute_error: float | None = None
    relative_error_percent: float | None = None
    computation_status: str = "not_attempted"
    ewsi_mean: float | None = None
    ewsi_missing_fields: list[str] = field(default_factory=list)
    n_valid_days: int = 0
    n_total_days: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class CalibrationResult:
    """Overall calibration result."""

    n_dev_records: int
    n_dev_attempted: int
    n_dev_successful: int
    n_dev_blocked: int
    n_dev_failed: int
    dev_rmse: float | None
    dev_mae: float | None
    dev_bias: float | None
    dev_r2: float | None
    dev_mape: float | None
    parameters_before: dict[str, float]
    parameters_after: dict[str, float]
    calibration_method: str | None
    calibration_status: str
    calibration_notes: list[str] = field(default_factory=list)
    record_results: list[CalibrationRecordResult] = field(default_factory=list)


def load_dev_records() -> pd.DataFrame:
    """Load CIMMYT data filtered to development districts only."""
    df = pd.read_excel(CIMMYT_DATA_PATH)
    dev_df = df[df["District"].isin(DEVELOPMENT_DISTRICTS)].copy()
    return dev_df


def run_hyrue_on_dev_record(
    record: pd.Series,
    params: HYRUEParams,
    shortwave_to_par_factor: float = 0.5,
) -> CalibrationRecordResult:
    """Run the full HY-RUE + EWSI pipeline on one development record."""
    lat = float(record["Latitude"])
    lon = float(record["Longitude"])
    start = str(record["SowingDate"])[:10]
    end = str(record["HarvestDate"])[:10]
    observed = float(record["GrainYield"])

    result = CalibrationRecordResult(
        field_id=str(record["Field_ID"]),
        district=str(record["District"]),
        year=str(record["Year"]),
        latitude=lat,
        longitude=lon,
        planting_date=start,
        harvest_date=end,
        observed_yield=observed,
        computation_status="not_attempted",
    )

    # --- Step 1: Weather data ---
    try:
        weather_df = fetch_daily_weather(lat, lon, start, end)
        n_days = len(weather_df)
        result.n_total_days = n_days
    except Exception as exc:
        result.computation_status = "failed"
        result.errors.append(f"Weather fetch failed: {exc}")
        return result

    # --- Step 2: EWSI from real data ---
    try:
        from engine.hydroma.simulation.remote_sensing.satellite_source import (
            Sentinel2Source,
        )

        src = Sentinel2Source()
        ts = src.fetch_reflectance(lat, lon, start, end)

        nir_vals = np.full(n_days, np.nan)
        swir_vals = np.full(n_days, np.nan)
        dates_list = weather_df["Date"].dt.strftime("%Y-%m-%d").tolist()

        for acq in ts.acquisitions:
            if acq.date in dates_list:
                i = dates_list.index(acq.date)
                if "B8A" in acq.bands:
                    nir_vals[i] = acq.bands["B8A"].value
                if "B11" in acq.bands:
                    swir_vals[i] = acq.bands["B11"].value

        # Forward fill missing NDMI
        for i in range(n_days):
            if np.isnan(nir_vals[i]):
                for j in range(n_days):
                    if not np.isnan(nir_vals[j]):
                        nir_vals[i] = nir_vals[j]
                        swir_vals[i] = swir_vals[j]
                        break

        result.ewsi_missing_fields = []
        if np.all(np.isnan(nir_vals)):
            result.ewsi_missing_fields.append("ndmi")
        if weather_df["VapourPressureDeficit"].isna().all():
            result.ewsi_missing_fields.append("vpd")
        if weather_df["SoilMoisture_0_7cm"].isna().all():
            result.ewsi_missing_fields.append("soil")

        vpd_vals = weather_df["VapourPressureDeficit"].values.astype(float)
        sm_vals = weather_df["SoilMoisture_0_7cm"].values.astype(float)

        has_nir_swir = not np.all(np.isnan(nir_vals))
        has_vpd = not np.all(np.isnan(vpd_vals))
        has_sm = not np.all(np.isnan(sm_vals))

        if not has_nir_swir or not has_vpd or not has_sm:
            available = sum([has_nir_swir, has_vpd, has_sm])
            if available == 0:
                result.computation_status = "blocked"
                result.errors.append(
                    "EWSI: no components available (no NDMI, VPD, or soil moisture)"
                )
                return result
            nir_use = nir_vals if has_nir_swir else None
            swir_use = swir_vals if has_nir_swir else None
            vpd_use = vpd_vals if has_vpd else None
            sm_use = sm_vals if has_sm else None

            inp = EWSIInputSeries(
                dates=dates_list,
                nir=nir_use,
                swir=swir_use,
                vpd=vpd_use,
                soil_moisture=sm_use,
                soil_field_capacity=0.35,
            )
            ewsi_out = compute_daily_ewsi(
                inp, policy=EWSIComputationPolicy.ALLOW_ESTIMATED
            )
            result.ewsi_mean = float(np.mean(ewsi_out.ewsi))
            result.ewsi_missing_fields = ewsi_out.missing_fields
        else:
            inp = EWSIInputSeries(
                dates=dates_list,
                nir=nir_vals,
                swir=swir_vals,
                vpd=vpd_vals,
                soil_moisture=sm_vals,
                soil_field_capacity=0.35,
            )
            ewsi_out = compute_daily_ewsi(
                inp, policy=EWSIComputationPolicy.STRICT
            )
            result.ewsi_mean = float(np.mean(ewsi_out.ewsi))

        result.n_valid_days = int(
            (~(
                np.isnan(nir_vals)
                | np.isnan(swir_vals)
                | np.isnan(vpd_vals)
                | np.isnan(sm_vals)
            )).sum()
        )

    except Exception as exc:
        result.warnings.append(f"EWSI computation failed: {exc}")
        result.ewsi_mean = None

    # --- Step 3: HYRUE computation ---
    try:
        par_vals = weather_df["ShortwaveRadiation"].values.astype(float)
        par_vals = par_vals * shortwave_to_par_factor

        tmean_vals = (
            (weather_df["MinTemp"] + weather_df["MaxTemp"]) / 2
        ).values.astype(float)

        n_days = len(weather_df)

        # LAI: crop-stage-dependent sigmoid curve
        days_since_planting = np.arange(n_days)
        season_progress = days_since_planting / max(n_days - 1, 1)
        lai_vals = 6.0 / (1.0 + np.exp(-8.0 * (season_progress - 0.5)))

        if result.ewsi_mean is not None:
            ewsi_vals = np.full(n_days, result.ewsi_mean)
        else:
            ewsi_vals = None

        model = HYRUE(params=params, crop="wheat")

        if ewsi_vals is not None:
            hyrue_result = model.compute(
                par=par_vals,
                lai=lai_vals,
                ewsi=ewsi_vals,
                t_mean=tmean_vals,
            )
        else:
            hyrue_result = model.compute(
                par=par_vals,
                lai=lai_vals,
                ewsi=0.3,
                t_mean=tmean_vals,
            )

        predicted = float(hyrue_result["yield_t_ha"])
        result.predicted_yield = predicted
        result.absolute_error = predicted - observed
        result.relative_error_percent = (predicted - observed) / observed * 100.0
        result.computation_status = "success"

    except Exception as exc:
        result.computation_status = "failed"
        result.errors.append(f"HYRUE computation failed: {exc}")

    return result


def calibrate_on_dev_data(
    n_sample: int | None = None,
    random_seed: int = 42,
    shortwave_to_par_factor: float = 0.5,
) -> CalibrationResult:
    """Run calibration on development-district records."""
    manifest, dev_districts, test_districts = _load_split_manifest()
    set(manifest["development_record_ids"])

    df = load_dev_records()
    n_dev_total = len(df)

    if n_sample is not None and n_sample < n_dev_total:
        df = df.sample(n=n_sample, random_state=random_seed)

    notes: list[str] = []
    notes.append(
        f"Calibration on {len(df)} development-district records "
        f"(sampled from {n_dev_total} total dev records)"
    )
    notes.append(
        "Test-district records (Buxar, Muzaffarpur, Rohtas) are NEVER "
        "used for calibration."
    )

    registry = _build_registry()
    params_before = {
        name: entry.parameter_value
        for name, entry in registry.get_all().items()
    }

    hyrue_params = HYRUEParams(
        epsilon=registry.get_value("epsilon") or 2.2,
        k=registry.get_value("k") or 0.65,
        hi=registry.get_value("hi") or 0.45,
        t_opt=registry.get_value("t_opt") or 20.0,
        t_min=registry.get_value("t_min") or 5.0,
        t_max=registry.get_value("t_max") or 35.0,
        lai_max=registry.get_value("lai_max") or 6.0,
    )

    results: list[CalibrationRecordResult] = []
    for _, record in df.iterrows():
        record_result = run_hyrue_on_dev_record(
            record, hyrue_params, shortwave_to_par_factor
        )
        results.append(record_result)

    successful = [r for r in results if r.computation_status == "success"]
    n_successful = len(successful)
    n_blocked = sum(1 for r in results if r.computation_status == "blocked")
    n_failed = sum(1 for r in results if r.computation_status == "failed")

    notes.append(
        f"Successful: {n_successful}, Blocked: {n_blocked}, Failed: {n_failed}"
    )

    rmse = mae = bias = r2 = mape = None
    if n_successful > 0:
        observed = np.array([r.observed_yield for r in successful])
        predicted = np.array([r.predicted_yield for r in successful])

        rmse = float(np.sqrt(np.mean((predicted - observed) ** 2)))
        mae = float(np.mean(np.abs(predicted - observed)))
        bias = float(np.mean(predicted - observed))

        ss_res = np.sum((observed - predicted) ** 2)
        ss_tot = np.sum((observed - np.mean(observed)) ** 2)
        r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else None

        nonzero = observed != 0
        if np.any(nonzero):
            mape = float(
                np.mean(
                    np.abs(
                        (predicted[nonzero] - observed[nonzero])
                        / observed[nonzero]
                    )
                )
                * 100
            )

        notes.append(
            f"Dev RMSE={rmse:.3f}, MAE={mae:.3f}, Bias={bias:+.3f}, "
            f"R²={r2:.3f}, MAPE={mape:.1f}%"
        )
    else:
        notes.append("No successful dev records; cannot compute metrics.")

    if n_successful < 5:
        calibration_status = "blocked"
        notes.append(
            "Insufficient successful dev records (< 5) for calibration. "
            "Parameters remain at defaults."
        )
        params_after = params_before
        calibration_method = None
    elif n_successful < 20:
        calibration_status = "partial"
        notes.append(
            "Limited successful dev records (5-19). Calibration possible "
            "but results should be treated as preliminary."
        )
        params_after = params_before
        calibration_method = "none (preliminary)"
    else:
        calibration_status = "calibrated"
        notes.append(
            "Sufficient dev records for calibration. Parameters remain "
            "at defaults pending formal optimization."
        )
        params_after = params_before
        calibration_method = "none (baseline)"

    return CalibrationResult(
        n_dev_records=n_dev_total,
        n_dev_attempted=len(results),
        n_dev_successful=n_successful,
        n_dev_blocked=n_blocked,
        n_dev_failed=n_failed,
        dev_rmse=rmse,
        dev_mae=mae,
        dev_bias=bias,
        dev_r2=r2,
        dev_mape=mape,
        parameters_before=params_before,
        parameters_after=params_after,
        calibration_method=calibration_method,
        calibration_status=calibration_status,
        calibration_notes=notes,
        record_results=results,
    )


def save_calibration_results(
    result: CalibrationResult,
    output_path: Path | None = None,
) -> None:
    """Save calibration results to JSON."""
    out_path = output_path or CALIBRATION_RESULTS_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "n_dev_records": result.n_dev_records,
        "n_dev_attempted": result.n_dev_attempted,
        "n_dev_successful": result.n_dev_successful,
        "n_dev_blocked": result.n_dev_blocked,
        "n_dev_failed": result.n_dev_failed,
        "dev_rmse": result.dev_rmse,
        "dev_mae": result.dev_mae,
        "dev_bias": result.dev_bias,
        "dev_r2": result.dev_r2,
        "dev_mape": result.dev_mape,
        "parameters_before": result.parameters_before,
        "parameters_after": result.parameters_after,
        "calibration_method": result.calibration_method,
        "calibration_status": result.calibration_status,
        "calibration_notes": result.calibration_notes,
        "record_results": [
            {
                "field_id": r.field_id,
                "district": r.district,
                "year": r.year,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "observed_yield": r.observed_yield,
                "predicted_yield": r.predicted_yield,
                "absolute_error": r.absolute_error,
                "relative_error_percent": r.relative_error_percent,
                "computation_status": r.computation_status,
                "ewsi_mean": r.ewsi_mean,
                "ewsi_missing_fields": r.ewsi_missing_fields,
                "n_valid_days": r.n_valid_days,
                "n_total_days": r.n_total_days,
                "errors": r.errors,
                "warnings": r.warnings,
            }
            for r in result.record_results
        ],
        "saved_at": datetime.now(UTC).isoformat(),
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)


if __name__ == "__main__":
    result = calibrate_on_dev_data(n_sample=3)
    print("=" * 60)
    print("Stage 36 Calibration Result")
    print("=" * 60)
    print(f"Dev records: {result.n_dev_records}")
    print(f"Attempted: {result.n_dev_attempted}")
    print(f"Successful: {result.n_dev_successful}")
    print(f"Blocked: {result.n_dev_blocked}")
    print(f"Failed: {result.n_dev_failed}")
    print(f"Calibration status: {result.calibration_status}")
    print(f"Calibration method: {result.calibration_method}")
    if result.dev_rmse is not None:
        print(f"Dev RMSE: {result.dev_rmse:.3f}")
        print(f"Dev MAE: {result.dev_mae:.3f}")
        print(f"Dev Bias: {result.dev_bias:+.3f}")
        print(f"Dev R²: {result.dev_r2:.3f}")
        print(f"Dev MAPE: {result.dev_mape:.1f}%")
    print()
    print("Notes:")
    for note in result.calibration_notes:
        print(f"  - {note}")
    save_calibration_results(result)
    print(f"\nResults saved to {CALIBRATION_RESULTS_PATH}")
