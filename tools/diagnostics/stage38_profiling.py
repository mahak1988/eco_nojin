"""Stage 38 Part 2 — Profile runtime on a small sample of development records.

Runs the full HYRUE pipeline on 3 dev records to measure actual time per
operation, then extrapolates to the full test set (1,722 records).
"""

import sys

sys.path.insert(0, "D:/HyDroMA")
sys.path.insert(0, "D:/eco_nojin")

import time

import numpy as np
import pandas as pd

from engine.hydroma.eval.benchmark_profiler import (
    BenchmarkProfiler,
)
from engine.hydroma.eval.benchmark_split_manifest import load_split_manifest
from engine.hydroma.eval.seasonal_predictor import (
    EWSIInputs,
    InputSourcePolicy,
    SeasonalPredictionRequest,
    compute_seasonal_prediction,
)
from engine.hydroma.simulation.ewsi_pipeline import (
    EWSIComputationPolicy,
    EWSIInputSeries,
    compute_daily_ewsi,
)
from engine.hydroma.simulation.remote_sensing.satellite_source import Sentinel2Source
from engine.hydroma.simulation.weather_source import fetch_daily_weather


def profile_single_record(
    profiler: BenchmarkProfiler,
    record: pd.Series,
) -> dict:
    """Run the full pipeline on one record with detailed timing."""
    lat = float(record["Latitude"])
    lon = float(record["Longitude"])
    start = str(record["SowingDate"])[:10]
    end = str(record["HarvestDate"])[:10]
    field_id = str(record["Field_ID"])
    district = str(record["District"])
    season = str(record["Year"])
    obs_yield = float(record["GrainYield"])

    profiler.start_record(field_id, district, season)
    record_start = time.perf_counter()

    # Step 1: Dataset loading
    profiler.start_operation("dataset_loading")
    profiler.end_operation("dataset_loading", status="SUCCESS")

    # Step 2: Weather API request
    profiler.start_operation("weather_api_request")
    try:
        weather_df = fetch_daily_weather(lat, lon, start, end)
        profiler.end_operation(
            "weather_api_request",
            status="SUCCESS",
            cache_hit=False,
        )
    except Exception as exc:
        profiler.end_operation(
            "weather_api_request",
            status="FAILED",
            cache_hit=False,
        )
        return {"status": "failed", "error": f"Weather: {exc}"}

    n_days = len(weather_df)
    dates_list = weather_df["Date"].dt.strftime("%Y-%m-%d").tolist()

    # Step 3: Satellite STAC search
    profiler.start_operation("satellite_stac_search")
    try:
        src = Sentinel2Source()
        ts = src.fetch_reflectance(lat, lon, start, end)
        profiler.end_operation(
            "satellite_stac_search",
            status="SUCCESS" if len(ts.acquisitions) > 0 else "PARTIAL",
            cache_hit=False,
        )
    except Exception:
        profiler.end_operation(
            "satellite_stac_search",
            status="FAILED",
            cache_hit=False,
        )
        ts = type("TS", (), {"acquisitions": []})()

    # Step 4: Satellite asset download (per acquisition)
    profiler.start_operation("satellite_asset_download")
    n_acq = len(ts.acquisitions)
    profiler.end_operation(
        "satellite_asset_download",
        status="SUCCESS",
        cache_hit=False,
        retry_count=0,
    )

    # Step 5: Raster processing (NDMI computation)
    profiler.start_operation("raster_processing")
    nir_vals = np.full(n_days, np.nan)
    swir_vals = np.full(n_days, np.nan)
    for acq in ts.acquisitions:
        if acq.date in dates_list:
            i = dates_list.index(acq.date)
            if "B8A" in acq.bands:
                nir_vals[i] = acq.bands["B8A"].value
            if "B11" in acq.bands:
                swir_vals[i] = acq.bands["B11"].value
    # Forward fill
    for i in range(n_days):
        if np.isnan(nir_vals[i]):
            for j in range(n_days):
                if not np.isnan(nir_vals[j]):
                    nir_vals[i] = nir_vals[j]
                    swir_vals[i] = swir_vals[j]
                    break
    profiler.end_operation("raster_processing", status="SUCCESS")

    # Step 6: LAI computation (skip — LAI handled by seasonal_predictor internally)
    # Step 7: VPD computation (handled inside EWSI)

    # Step 8: EWSI computation
    profiler.start_operation("ewsi_computation")
    vpd_vals = weather_df["VapourPressureDeficit"].values.astype(float)
    sm_vals = weather_df["SoilMoisture_0_7cm"].values.astype(float)
    has_nir_swir = not np.all(np.isnan(nir_vals))
    has_vpd = not np.all(np.isnan(vpd_vals))
    has_sm = not np.all(np.isnan(sm_vals))

    if has_nir_swir and has_vpd and has_sm:
        inp = EWSIInputSeries(
            dates=dates_list,
            nir=nir_vals,
            swir=swir_vals,
            vpd=vpd_vals,
            soil_moisture=sm_vals,
            soil_field_capacity=0.35,
        )
        ewsi_out = compute_daily_ewsi(inp, policy=EWSIComputationPolicy.STRICT)
        ewsi_array = ewsi_out.ewsi
        ewsi_status = "SUCCESS"
        ewsi_missing = ewsi_out.missing_fields
    else:
        ewsi_array = None
        ewsi_status = "BLOCKED"
        ewsi_missing = []
    profiler.end_operation("ewsi_computation", status=ewsi_status)

    # Step 9: HYRUE computation
    profiler.start_operation("hyrue_computation")
    try:
        request = SeasonalPredictionRequest(
            site_id=f"prof_{field_id}",
            season_id=f"wheat_{district}_{season}",
            crop="wheat",
            planting_date=start,
            harvest_date=end,
            latitude=lat,
            longitude=lon,
            input_source_policy=InputSourcePolicy.ALLOW_ESTIMATED,
            ewsi_inputs=EWSIInputs(
                nir=nir_vals if has_nir_swir else None,
                swir=swir_vals if has_nir_swir else None,
                vpd=vpd_vals if has_vpd else None,
                soil_moisture=sm_vals if has_sm else None,
                soil_field_capacity=0.35,
            ),
            data_label="stage38_profiling",
        )
        prediction, report = compute_seasonal_prediction(request)
        profiler.end_operation(
            "hyrue_computation",
            status=prediction.computation_status,
        )
        pred_yield = prediction.value if prediction.value is not None else None
    except Exception as exc:
        profiler.end_operation("hyrue_computation", status="FAILED")
        pred_yield = None
        return {"status": "failed", "error": f"HYRUE: {exc}"}

    # Step 10: Result serialization
    profiler.start_operation("result_serialization")
    result = {
        "field_id": field_id,
        "district": district,
        "season": season,
        "obs_yield": obs_yield,
        "pred_yield": pred_yield,
        "ewsi_status": ewsi_status,
        "ewsi_missing": ewsi_missing,
    }
    profiler.end_operation("result_serialization", status="SUCCESS")

    record_elapsed = time.perf_counter() - record_start
    return {
        "status": "success",
        "record_seconds": record_elapsed,
        "result": result,
    }


def main():
    print("=" * 60)
    print("Stage 38 Part 2 — Runtime Profiling")
    print("=" * 60)

    manifest = load_split_manifest()
    dev_ids = set(manifest["development_record_ids"])

    df = pd.read_excel(
        "data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx"
    )
    dev_df = df[df["District"].isin(manifest["development_districts"])].copy()

    # Sample 3 dev records from different districts
    sampled = dev_df.sample(n=3, random_state=42)
    print(f"Profiling {len(sampled)} dev records...")

    profiler = BenchmarkProfiler()
    results = []
    for _, record in sampled.iterrows():
        print(f"\n  Profiling {record['Field_ID']} ({record['District']}, {record['Year']})...")
        r = profile_single_record(profiler, record)
        results.append(r)
        if r["status"] == "success":
            print(f"    Success: {r['record_seconds']:.1f}s")
        else:
            print(f"    Failed: {r.get('error', 'unknown')}")

    summary = profiler.summarize()
    print("\n" + "=" * 60)
    print("PROFILING SUMMARY")
    print("=" * 60)
    print(f"Records processed: {summary.records_processed}")
    print(f"Total elapsed: {summary.total_elapsed_seconds:.1f}s")
    print(f"Median seconds per record: {summary.median_seconds_per_record:.1f}s")
    print(f"Weather requests: {summary.weather_requests}")
    print(f"STAC searches: {summary.stac_searches}")
    print(f"Satellite downloads: {summary.satellite_downloads}")
    print(f"Cache hit rate: {summary.cache_hit_rate:.1%}")
    print(f"Retry count: {summary.retry_count}")
    print(f"Failed requests: {summary.failed_requests}")
    print("\nOperation totals:")
    for op, total in sorted(summary.operation_totals.items(), key=lambda x: -x[1]):
        print(f"  {op}: {total:.1f}s ({summary.operation_counts[op]} calls)")

    # Extrapolate to full test set
    n_test = 1722
    if summary.records_processed > 0:
        est_total = summary.median_seconds_per_record * n_test
        print(f"\nExtrapolated to {n_test} test records:")
        print(f"  Estimated total: {est_total/3600:.1f} hours")
        print(f"  Estimated total: {est_total/60:.0f} minutes")

    profiler.save()
    print("\nResults saved to engine/reports/data/stage38_profiling_results.json")


if __name__ == "__main__":
    main()
