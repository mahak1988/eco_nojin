"""Resumable benchmark runner for Stage 38/39.

Processes CIMMYT test-district records one at a time with persistent state,
allowing execution to be paused and resumed without losing progress.

Each record is processed through the full pipeline:
1. Fetch weather data from Open-Meteo ERA5-Land
2. Fetch satellite data from Planetary Computer STAC (if available)
3. Compute EWSI from NDMI + VPD + soil moisture
4. Run HYRUE seasonal computation

Execution statuses:
    PENDING   - Record queued for processing
    RUNNING   - Record currently being processed
    COMPUTED  - Record successfully processed with all inputs
    PARTIAL_INPUTS - Record processed with missing/incomplete inputs
    BLOCKED   - Record cannot be processed (missing critical inputs)
    FAILED    - Record processing encountered an error

No synthetic data is ever used. Failed records are recorded with their
error reason and excluded from metrics computation.

Weather API responses are cached via ScientificCache for cross-run
persistence.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from engine.hydroma.eval.benchmark_split_manifest import load_split_manifest
from engine.hydroma.eval.seasonal_predictor import (
    EWSIInputs,
    InputSourcePolicy,
    SeasonalPredictionRequest,
    compute_seasonal_prediction,
)
from engine.hydroma.simulation.data_cache import ScientificCache
from engine.hydroma.simulation.ewsi_pipeline import (
    EWSIComputationPolicy,
    EWSIInputSeries,
    compute_daily_ewsi,
)
from engine.hydroma.simulation.remote_sensing.satellite_source import Sentinel2Source
from engine.hydroma.simulation.weather_source import fetch_daily_weather

RUNNER_DB_PATH = Path("engine/reports/data/stage39_runner.sqlite")
RUNNER_RESULTS_PATH = Path("engine/reports/data/stage39_benchmark_results.jsonl")
RUNNER_MANIFEST_PATH = Path("engine/reports/data/stage39_run_manifest.json")

#: Terminal execution statuses.
TERMINAL_STATUSES = frozenset(
    {"COMPUTED", "PARTIAL_INPUTS", "BLOCKED", "FAILED", "SKIPPED_DUPLICATE"}
)

#: Statuses that mean a record was successfully processed (has output).
SUCCESS_STATUSES = frozenset({"COMPUTED", "PARTIAL_INPUTS"})


@dataclass
class RecordResult:
    """Result of processing a single benchmark record."""

    record_id: str
    district_id: str
    season: str
    latitude: float
    longitude: float
    planting_date: str
    harvest_date: str
    observed_yield: float
    predicted_yield: float | None
    absolute_error: float | None
    relative_error_percent: float | None
    execution_status: str  # COMPUTED, PARTIAL_INPUTS, BLOCKED, FAILED
    computation_mode: str  # seasonal, legacy_constant, daily
    input_quality_status: str  # complete, partial, unavailable
    weather_coverage: float  # fraction of days with weather data (0-1)
    satellite_coverage: float  # fraction of days with satellite data (0-1)
    lai_status: str  # observed, estimated, missing
    par_status: str  # observed, estimated, missing
    ewsi_status: str  # observed, estimated, missing
    model_version: str = "2.0.0"
    failure_reason: str | None = None
    processing_seconds: float | None = None
    cache_hits: int = 0
    api_calls: int = 0
    ewsi_provenance: dict[str, Any] | None = None
    par_provenance: str | None = None
    #: Hash of the model code that produced this prediction.  Results from
    #: different model versions must never be mixed, so this travels with
    #: every record.
    model_code_hash: str | None = None
    #: Hash of the resolved inputs (weather, LAI, EWSI, parameters).  A
    #: rerun with the same inputs and model must reproduce the same output.
    data_hash: str | None = None
    #: Number of valid Sentinel-2 acquisitions with usable NIR/SWIR.
    satellite_acquisition_count: int = 0
    #: Number of days with valid weather rows.
    weather_valid_days: int = 0
    #: Provenance of the weather and satellite inputs.
    weather_provenance: dict[str, Any] | None = None
    satellite_provenance: dict[str, Any] | None = None
    #: Whether the record's weather came from the primary source or a
    #: fallback (``estimated`` marks a fallback).
    weather_source: str | None = None
    #: Prediction from the baseline parameter set, computed in the same
    #: pass from the *same* inputs as ``predicted_yield``.  This makes the
    #: baseline/calibrated comparison exactly like-for-like: same weather,
    #: same LAI, same EWSI, same PAR, same code path.
    baseline_predicted_yield: float | None = None
    baseline_error: float | None = None
    baseline_absolute_error: float | None = None
    baseline_relative_error_percent: float | None = None
    #: Where this record's inputs came from: the CIMMYT eastern-India
    #: wheat field-trial yields for the test districts, with the daily
    #: inputs resolved by the engine pipeline (ERA5 weather, Sentinel-2
    #: L2A, GDD LAI).
    data_source: str = "cimmyt_wheat_test_districts"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@contextmanager
def _sqlite_connection(path: Path):
    """Open a SQLite connection that is always closed.

    ``with sqlite3.connect(...)`` commits but does not close, which leaves
    the file locked on Windows and prevents temporary directories from
    being removed.
    """
    conn = sqlite3.connect(path)
    try:
        yield conn
    finally:
        conn.close()


class ResumableBenchmarkRunner:
    """Processes test-district records with persistent state and resumability.

    Uses SQLite to track execution state so that:
    - Completed records are not reprocessed
    - Execution can be paused and resumed
    - Failed records are tracked with their error reason
    - Progress is persisted incrementally (JSONL + SQLite)

    Weather API responses are cached via ScientificCache for cross-run
    persistence.
    """

    def __init__(
        self,
        db_path: Path | None = None,
        results_path: Path | None = None,
        manifest_path: Path | None = None,
        cache: ScientificCache | None = None,
        hyrue_params: Any | None = None,
        run_id: str = "stage39",
        data_label: str = "stage39_benchmark",
        shard_index: int = 0,
        shard_count: int = 1,
        record_ids: list[str] | None = None,
        model_code_hash: str | None = None,
        baseline_params: Any | None = None,
    ) -> None:
        self.db_path = db_path or RUNNER_DB_PATH
        self.results_path = results_path or RUNNER_RESULTS_PATH
        self.manifest_path = manifest_path or RUNNER_MANIFEST_PATH
        self.cache = cache or ScientificCache()
        #: Explicit HYRUE parameters for the run.  ``None`` means the crop
        #: preset is used (the uncalibrated baseline).  Supplying a parameter
        #: set evaluates that exact, frozen model and is recorded in the
        #: run manifest.
        self.hyrue_params = hyrue_params
        #: Run identity, recorded in the manifest and in every record.
        self.run_id = run_id
        self.data_label = data_label
        #: Optional sink for the resolved daily inputs of each processed
        #: record.  Calibration tooling uses this to fit parameters against
        #: the exact input basis the benchmark evaluates on.
        self.input_sink: list[dict[str, Any]] | None = None
        #: Shard assignment for parallel execution.  Shard ``i`` of ``n``
        #: processes every ``n``-th record, so the shards are disjoint and
        #: each covers the same districts and seasons.
        if shard_count < 1:
            raise ValueError("shard_count must be >= 1")
        if not 0 <= shard_index < shard_count:
            raise ValueError("shard_index must be in [0, shard_count)")
        self.shard_index = shard_index
        self.shard_count = shard_count
        #: Optional explicit record set.  When given, only these
        #: ``Field_ID`` values are processed.  This is how a documented
        #: stratified sample of the test set is evaluated.
        self.record_ids = set(record_ids) if record_ids is not None else None
        #: Hash of the model code that produced these results.  Recorded on
        #: every record so that results from different model versions can
        #: never be silently mixed.
        self.model_code_hash = model_code_hash
        #: Optional baseline parameter set.  When supplied, every record
        #: gets a second prediction from the *same* resolved inputs, which
        #: is what makes the baseline/calibrated comparison like-for-like.
        self.baseline_params = baseline_params
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Create runner state tables."""
        with _sqlite_connection(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS record_state (
                    record_id TEXT PRIMARY KEY,
                    district_id TEXT NOT NULL,
                    season TEXT NOT NULL,
                    status TEXT NOT NULL,
                    processed_at TEXT,
                    failure_reason TEXT,
                    processing_seconds REAL,
                    cache_hits INTEGER DEFAULT 0,
                    api_calls INTEGER DEFAULT 0
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_record_status "
                "ON record_state(status)"
            )
            conn.commit()

    def _is_processed(self, record_id: str) -> bool:
        """Check if a record has already reached a terminal status."""
        with _sqlite_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT status FROM record_state WHERE record_id = ?",
                (record_id,),
            ).fetchone()
            return row is not None and row[0] in TERMINAL_STATUSES

    def _get_processed_ids(self) -> set[str]:
        """Get all record IDs that have reached terminal status."""
        with _sqlite_connection(self.db_path) as conn:
            placeholders = ",".join("?" * len(TERMINAL_STATUSES))
            rows = conn.execute(
                f"SELECT record_id FROM record_state WHERE status IN ({placeholders})",
                tuple(TERMINAL_STATUSES),
            ).fetchall()
            return {row[0] for row in rows}

    def _save_record_state(
        self,
        record_id: str,
        district_id: str,
        season: str,
        status: str,
        failure_reason: str | None = None,
        processing_seconds: float | None = None,
        cache_hits: int = 0,
        api_calls: int = 0,
    ) -> None:
        """Persist record execution state to SQLite."""
        processed_at = datetime.now(UTC).isoformat()
        with _sqlite_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO record_state
                (record_id, district_id, season, status, processed_at,
                 failure_reason, processing_seconds, cache_hits, api_calls)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id, district_id, season, status, processed_at,
                    failure_reason, processing_seconds, cache_hits, api_calls,
                ),
            )
            conn.commit()

    def _append_result(self, result: RecordResult) -> None:
        """Append a record result to the JSONL file."""
        with open(self.results_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result.to_dict(), default=str) + "\n")

    def load_test_records(self) -> pd.DataFrame:
        """Load all test-district records from CIMMYT dataset."""
        manifest = load_split_manifest()
        df = pd.read_excel(
            "data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx"
        )
        test_df = df[df["District"].isin(manifest["test_districts"])].copy()
        return test_df

    def process_record(self, record: pd.Series) -> RecordResult:
        """Process a single test record through the full pipeline:
        weather -> satellite -> EWSI -> HYRUE seasonal."""
        lat = float(record["Latitude"])
        lon = float(record["Longitude"])
        start = str(record["SowingDate"])[:10]
        end = str(record["HarvestDate"])[:10]
        field_id = str(record["Field_ID"])
        district = str(record["District"])
        season = str(record["Year"])
        obs_yield = float(record["GrainYield"])

        cache_hits = 0
        api_calls = 0
        record_start = time.perf_counter()
        weather_source = "open_meteo_era5"
        weather_provenance: dict[str, Any] | None = None
        satellite_provenance: dict[str, Any] | None = None
        satellite_acquisition_count = 0

        # --- Step 1: Fetch weather data ---
        try:
            weather_df = fetch_daily_weather(lat, lon, start, end)
            api_calls += 1
            n_days = len(weather_df)
        except Exception as exc:
            return RecordResult(
                record_id=field_id,
                district_id=district,
                season=season,
                latitude=lat,
                longitude=lon,
                planting_date=start,
                harvest_date=end,
                observed_yield=obs_yield,
                predicted_yield=None,
                absolute_error=None,
                relative_error_percent=None,
                execution_status="BLOCKED",
                computation_mode="unknown",
                input_quality_status="unavailable",
                weather_coverage=0.0,
                satellite_coverage=0.0,
                lai_status="missing",
                par_status="missing",
                ewsi_status="missing",
                failure_reason=f"Weather fetch failed: {exc}",
            )

        dates_list = weather_df["Date"].dt.strftime("%Y-%m-%d").tolist()
        vpd_vals = weather_df["VapourPressureDeficit"].values.astype(float)
        sm_vals = weather_df["SoilMoisture_0_7cm"].values.astype(float)
        weather_df["ShortwaveRadiation"].values.astype(float)

        weather_coverage = (
            float(weather_df["VapourPressureDeficit"].notna().mean())
            if n_days > 0 else 0.0
        )
        weather_valid_days = int(
            weather_df["VapourPressureDeficit"].notna().sum()
        ) if n_days > 0 else 0
        # The weather source falls back from Open-Meteo ERA5 to NASA POWER on
        # timeout; a fallback record is not data-equivalent to an ERA5 record
        # and must be identifiable in the results.
        weather_source = str(
            getattr(weather_df, "attrs", {}).get("source", "open_meteo_era5")
        )
        weather_provenance = {
            "source": weather_source,
            "rows": int(n_days),
            "valid_days": weather_valid_days,
            "vpd_coverage": weather_coverage,
        }

        # --- Step 2: Fetch satellite data (Sentinel-2 NIR/SWIR) ---
        nir_vals = np.full(n_days, np.nan)
        swir_vals = np.full(n_days, np.nan)
        satellite_coverage = 0.0
        valid_sat_days = 0

        try:
            src = Sentinel2Source()
            ts = src.fetch_reflectance(lat, lon, start, end)
            api_calls += 1

            for acq in ts.acquisitions:
                if acq.date in dates_list:
                    i = dates_list.index(acq.date)
                    if "B8A" in acq.bands:
                        nir_vals[i] = float(acq.bands["B8A"].value)
                        valid_sat_days += 1
                    if "B11" in acq.bands:
                        swir_vals[i] = float(acq.bands["B11"].value)
                        valid_sat_days += 1

            # Number of acquisitions that carry a usable NIR/SWIR pair.
            satellite_acquisition_count = sum(
                1
                for acq in ts.acquisitions
                if "B8A" in acq.bands and "B11" in acq.bands
            )
            satellite_provenance = {
                "source": "sentinel2_l2a",
                "acquisitions_total": len(ts.acquisitions),
                "acquisitions_with_nir_swir": satellite_acquisition_count,
                "season_days": int(n_days),
            }

            # Forward fill missing NDMI
            for i in range(n_days):
                if np.isnan(nir_vals[i]):
                    for j in range(n_days):
                        if not np.isnan(nir_vals[j]):
                            nir_vals[i] = nir_vals[j]
                            swir_vals[i] = swir_vals[j]
                            break

            satellite_coverage = valid_sat_days / (2 * n_days) if n_days > 0 else 0.0
        except Exception as exc:
            # Satellite fetch failed - EWSI will use allow_estimated with VPD+SM only
            satellite_provenance = {"source": "sentinel2_l2a", "error": str(exc)}

        # --- Step 3: Compute EWSI ---
        has_nir_swir = not np.all(np.isnan(nir_vals))
        has_vpd = not np.all(np.isnan(vpd_vals))
        has_sm = not np.all(np.isnan(sm_vals))

        ewsi_status = "missing"
        ewsi_array = None
        ewsi_provenance = None

        if has_nir_swir or has_vpd or has_sm:
            try:
                inp = EWSIInputSeries(
                    dates=dates_list,
                    nir=nir_vals if has_nir_swir else None,
                    swir=swir_vals if has_nir_swir else None,
                    vpd=vpd_vals if has_vpd else None,
                    soil_moisture=sm_vals if has_sm else None,
                    soil_field_capacity=0.35,
                )
                ewsi_out = compute_daily_ewsi(
                    inp, policy=EWSIComputationPolicy.ALLOW_ESTIMATED
                )
                ewsi_array = ewsi_out.ewsi
                ewsi_status = (
                    "observed" if not ewsi_out.missing_fields else "estimated"
                )
                ewsi_provenance = {
                    "source_model": "EWSI",
                    "quality_status": ewsi_out.quality_status,
                    "scientific_status": ewsi_out.scientific_status,
                    "method": ewsi_out.method,
                    "weights": ewsi_out.weights,
                    "missing_fields": ewsi_out.missing_fields,
                    "computation_policy": ewsi_out.computation_policy,
                }
            except Exception:
                ewsi_status = "failed"
        elif has_vpd or has_sm:
            ewsi_status = "estimated"
        else:
            ewsi_status = "missing"

        # --- Step 4: LAI status (resolved by the predictor) ---
        lai_status = "missing"

        # --- Step 5: PAR status ---
        par_status = "estimated" if weather_coverage > 0 else "missing"

        # --- Step 6: Run HYRUE seasonal ---
        predicted_yield = None
        execution_status = "BLOCKED"
        failure_reason = None
        data_hash: str | None = None
        report_lai_provenance: Any = None
        baseline_predicted_yield: float | None = None
        resolved_inputs: list[dict[str, Any]] = []

        if ewsi_array is not None:
            try:
                request = SeasonalPredictionRequest(
                    site_id=f"bench_{field_id}",
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
                    data_label=self.data_label,
                    hyrue_params=self.hyrue_params,
                )
                try:
                    prediction, report = compute_seasonal_prediction(
                        request,
                        input_sink=(
                            resolved_inputs if self.input_sink is not None else None
                        ),
                    )
                finally:
                    if self.input_sink is not None:
                        self.input_sink.extend(
                            {"record_id": field_id, **resolved_input}
                            for resolved_input in resolved_inputs
                        )
                predicted_yield = prediction.value
                # ``PredictionResult.computation_status`` is one of
                # computed / partial / fail_closed / not_attempted; map it
                # onto the benchmark execution statuses.
                computation_mode = prediction.computation_status
                if computation_mode == "computed":
                    execution_status = "COMPUTED"
                elif computation_mode == "partial":
                    execution_status = "PARTIAL_INPUTS"
                elif computation_mode in ("fail_closed", "not_attempted"):
                    execution_status = "FAILED"
                else:
                    execution_status = "PARTIAL_INPUTS"
                input_quality = prediction.input_quality
                # The predictor records a hash of the resolved inputs; it is
                # the reproducibility handle for this record.
                repro = getattr(report, "reproducibility", None) or {}
                if isinstance(repro, dict):
                    data_hash = repro.get("data_hash")
                report_lai_provenance = (
                    report.input_provenance.get("lai")
                    if isinstance(getattr(report, "input_provenance", None), dict)
                    else None
                )
                # The predictor resolves LAI itself (observed > NDVI > GDD
                # model); record which route was actually used.
                if isinstance(report_lai_provenance, dict):
                    q = str(report_lai_provenance.get("quality_status", ""))
                    lai_status = {
                        "observed": "observed",
                        "model_generated": "estimated",
                        "model_estimate": "estimated",
                        "empirical": "estimated",
                    }.get(q, "estimated" if q else "missing")
                else:
                    lai_status = "estimated"

                # --- Baseline prediction from the SAME inputs ---
                # Re-uses the identical resolved weather, LAI, EWSI and PAR,
                # so the baseline/calibrated comparison cannot be confounded
                # by input differences between the two versions.
                if self.baseline_params is not None:
                    try:
                        baseline_request = SeasonalPredictionRequest(
                            site_id=f"bench_{field_id}",
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
                            data_label=self.data_label,
                            hyrue_params=self.baseline_params,
                        )
                        baseline_prediction, _ = compute_seasonal_prediction(
                            baseline_request
                        )
                        baseline_predicted_yield = baseline_prediction.value
                    except Exception:
                        baseline_predicted_yield = None
            except Exception as exc:
                execution_status = "FAILED"
                failure_reason = f"HYRUE computation failed: {exc}"
                computation_mode = "unknown"
                input_quality = "unavailable"
        else:
            execution_status = "BLOCKED"
            failure_reason = (
                "EWSI not available (missing NDMI, VPD, or soil moisture)"
            )
            computation_mode = "unknown"
            input_quality = "unavailable"

        # Compute errors
        absolute_error = None
        relative_error_percent = None
        if predicted_yield is not None:
            absolute_error = predicted_yield - obs_yield
            relative_error_percent = (
                (predicted_yield - obs_yield) / obs_yield * 100
                if obs_yield != 0 else None
            )
        baseline_error = None
        baseline_absolute_error = None
        baseline_relative_error_percent = None
        if baseline_predicted_yield is not None:
            baseline_error = baseline_predicted_yield - obs_yield
            baseline_absolute_error = abs(baseline_error)
            baseline_relative_error_percent = (
                baseline_error / obs_yield * 100 if obs_yield != 0 else None
            )

        return RecordResult(
            record_id=field_id,
            district_id=district,
            season=season,
            latitude=lat,
            longitude=lon,
            planting_date=start,
            harvest_date=end,
            observed_yield=obs_yield,
            predicted_yield=predicted_yield,
            absolute_error=absolute_error,
            relative_error_percent=relative_error_percent,
            execution_status=execution_status,
            computation_mode=computation_mode,
            input_quality_status=input_quality,
            weather_coverage=weather_coverage,
            satellite_coverage=satellite_coverage,
            lai_status=lai_status,
            par_status=par_status,
            ewsi_status=ewsi_status,
            model_version="2.0.0",
            failure_reason=failure_reason,
            processing_seconds=time.perf_counter() - record_start,
            cache_hits=cache_hits,
            api_calls=api_calls,
            ewsi_provenance=ewsi_provenance,
            par_provenance=par_status,
            model_code_hash=self.model_code_hash,
            data_hash=data_hash,
            satellite_acquisition_count=satellite_acquisition_count,
            weather_valid_days=weather_valid_days,
            weather_provenance=weather_provenance,
            satellite_provenance=satellite_provenance,
            weather_source=weather_source,
            baseline_predicted_yield=baseline_predicted_yield,
            baseline_error=baseline_error,
            baseline_absolute_error=baseline_absolute_error,
            baseline_relative_error_percent=baseline_relative_error_percent,
        )

    def run(
        self,
        max_records: int | None = None,
        skip_processed: bool = True,
    ) -> dict[str, Any]:
        """Run the benchmark on all test-district records.

        Args:
            max_records: Maximum number of records to process (None = all).
            skip_processed: Skip records already in terminal state.

        Returns:
            Summary dictionary with execution statistics.
        """
        test_df = self.load_test_records()
        processed_ids = self._get_processed_ids() if skip_processed else set()

        records_to_process = test_df[~test_df["Field_ID"].isin(processed_ids)]
        if self.record_ids is not None:
            records_to_process = records_to_process[
                records_to_process["Field_ID"].astype(str).isin(self.record_ids)
            ]
        if max_records is not None:
            records_to_process = records_to_process.head(max_records)
        if self.shard_count > 1:
            # Deterministic interleave so every shard covers the same set of
            # districts and seasons.  Each shard owns its own state database
            # and results file, so shards never contend for the same rows.
            records_to_process = records_to_process.iloc[
                self.shard_index :: self.shard_count
            ]

        total = len(records_to_process)
        print(f"Benchmark runner: {total} records to process")
        print(f"Already processed: {len(processed_ids)}")

        completed = 0
        partial = 0
        blocked = 0
        failed = 0

        for _, record in records_to_process.iterrows():
            record_id = str(record["Field_ID"])
            print(f"\nProcessing {record_id} ({record['District']}, {record['Year']})")

            start_time = time.perf_counter()
            self._save_record_state(
                record_id, str(record["District"]), str(record["Year"]),
                "RUNNING",
            )

            try:
                result = self.process_record(record)
                elapsed = time.perf_counter() - start_time

                # Update state
                self._save_record_state(
                    record_id, str(record["District"]), str(record["Year"]),
                    result.execution_status,
                    failure_reason=result.failure_reason,
                    processing_seconds=elapsed,
                    cache_hits=result.cache_hits,
                    api_calls=result.api_calls,
                )
                self._append_result(result)

                if result.execution_status in SUCCESS_STATUSES:
                    completed += 1
                elif result.execution_status == "BLOCKED":
                    blocked += 1
                elif result.execution_status == "FAILED":
                    failed += 1

                print(f"  {result.execution_status} ({elapsed:.1f}s)")
                if result.predicted_yield is not None:
                    print(f"    Predicted: {result.predicted_yield:.3f} "
                          f"Observed: {result.observed_yield:.3f} "
                          f"Error: {result.absolute_error:+.3f}")

            except Exception as exc:
                elapsed = time.perf_counter() - start_time
                self._save_record_state(
                    record_id, str(record["District"]), str(record["Year"]),
                    "FAILED",
                    failure_reason=str(exc),
                    processing_seconds=elapsed,
                )
                # A record that could not be processed is still a record
                # of the benchmark: it is written to the results file so
                # that the aggregate counts match the manifest.
                self._append_result(
                    RecordResult(
                        record_id=record_id,
                        district_id=str(record["District"]),
                        season=str(record["Year"]),
                        latitude=float(record["Latitude"]),
                        longitude=float(record["Longitude"]),
                        planting_date=str(record["SowingDate"])[:10],
                        harvest_date=str(record["HarvestDate"])[:10],
                        observed_yield=float(record["GrainYield"]),
                        predicted_yield=None,
                        absolute_error=None,
                        relative_error_percent=None,
                        execution_status="FAILED",
                        computation_mode="unknown",
                        input_quality_status="unavailable",
                        weather_coverage=0.0,
                        satellite_coverage=0.0,
                        lai_status="missing",
                        par_status="missing",
                        ewsi_status="missing",
                        failure_reason=str(exc),
                        processing_seconds=elapsed,
                    )
                )
                failed += 1
                print(f"  FAILED ({elapsed:.1f}s): {exc}")

        # Write manifest
        summary = {
            "run_id": f"{self.run_id}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            "total_records_to_process": total,
            "already_processed": len(processed_ids),
            "completed": completed,
            "partial": partial,
            "blocked": blocked,
            "failed": failed,
            "test_districts": manifest_test_districts(),
            "test_record_count": load_split_manifest()["test_record_count"],
            "created_at": datetime.now(UTC).isoformat(),
            "db_path": str(self.db_path),
            "results_path": str(self.results_path),
            "data_label": self.data_label,
            "model_parameters": (
                {
                    "epsilon": float(self.hyrue_params.epsilon),
                    "k": float(self.hyrue_params.k),
                    "hi": float(self.hyrue_params.hi),
                    "lai_max": float(self.hyrue_params.lai_max),
                    "t_opt": float(self.hyrue_params.t_opt),
                    "t_min": float(self.hyrue_params.t_min),
                    "t_max": float(self.hyrue_params.t_max),
                }
                if self.hyrue_params is not None
                else None
            ),
            "model_parameters_note": (
                "Explicit frozen parameter set used for every record."
                if self.hyrue_params is not None
                else "None supplied: the crop preset is used (uncalibrated baseline)."
            ),
        }
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        print("\n" + "=" * 60)
        print("BENCHMARK RUNNER SUMMARY")
        print("=" * 60)
        print(f"Records to process: {total}")
        print(f"Already processed: {len(processed_ids)}")
        print(f"Completed: {completed}")
        print(f"Partial: {partial}")
        print(f"Blocked: {blocked}")
        print(f"Failed: {failed}")
        print(f"\nManifest saved to: {self.manifest_path}")
        print(f"Results saved to: {self.results_path}")
        print(f"State DB: {self.db_path}")

        return summary


def manifest_test_districts() -> list[str]:
    """Get test district names from the split manifest."""
    manifest = load_split_manifest()
    return manifest["test_districts"]


__all__ = [
    "ResumableBenchmarkRunner",
    "RecordResult",
    "RUNNER_DB_PATH",
    "RUNNER_RESULTS_PATH",
    "RUNNER_MANIFEST_PATH",
    "TERMINAL_STATUSES",
    "SUCCESS_STATUSES",
]
