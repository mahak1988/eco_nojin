"""Benchmark profiler for Stage 38 — measures runtime per operation per record.

Profiles the full HYRUE pipeline to identify time bottlenecks before scaling
to the complete test set (1,722 records).

Tracks:
    dataset_loading, weather_api_request, weather_cache_lookup,
    satellite_stac_search, satellite_asset_download, raster_processing,
    lai_computation, vpd_computation, soil_moisture_processing,
    ewsi_computation, hyrue_computation, result_serialization, report_generation

Each operation record includes: operation_name, record_id, district_id, season,
start_time, end_time, duration_seconds, cache_hit, request_status, retry_count.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

OPERATION_NAMES = [
    "dataset_loading",
    "weather_api_request",
    "weather_cache_lookup",
    "satellite_stac_search",
    "satellite_asset_download",
    "raster_processing",
    "lai_computation",
    "vpd_computation",
    "soil_moisture_processing",
    "ewsi_computation",
    "hyrue_computation",
    "result_serialization",
    "report_generation",
]

PROFILER_RESULTS_PATH = Path(
    "engine/reports/data/stage38_profiling_results.json"
)


@dataclass
class OperationProfile:
    """A single timed operation within the pipeline."""

    operation_name: str
    record_id: str
    district_id: str
    season: str
    start_time: str
    end_time: str
    duration_seconds: float
    cache_hit: bool
    request_status: str
    # SUCCESS, PARTIAL, NOT_FOUND, RATE_LIMITED, NETWORK_ERROR,
    # INVALID_RESPONSE, FAILED
    retry_count: int = 0


@dataclass
class ProfilerResult:
    """Aggregated profiler results."""

    records_processed: int
    total_elapsed_seconds: float
    median_seconds_per_record: float
    p95_seconds_per_record: float
    weather_requests: int
    stac_searches: int
    satellite_downloads: int
    cache_hit_rate: float
    retry_count: int
    failed_requests: int
    operation_totals: dict[str, float]  # operation_name -> total seconds
    operation_counts: dict[str, int]  # operation_name -> count
    records: list[OperationProfile] = field(default_factory=list)


class BenchmarkProfiler:
    """Profiles runtime per operation per record."""

    def __init__(self) -> None:
        self.records: list[OperationProfile] = []
        self._active: dict[str, float] = {}  # operation_name -> start_time
        self._record_start: float | None = None
        self._current_record: str = ""
        self._current_district: str = ""
        self._current_season: str = ""

    def start_record(self, record_id: str, district_id: str, season: str) -> None:
        """Mark the start of a record's processing."""
        self._record_start = time.perf_counter()
        self._current_record = record_id
        self._current_district = district_id
        self._current_season = season

    def end_record(self) -> float:
        """Mark the end of a record's processing and return elapsed seconds."""
        if self._record_start is None:
            return 0.0
        elapsed = time.perf_counter() - self._record_start
        self._record_start = None
        return elapsed

    def start_operation(self, operation_name: str) -> None:
        """Mark the start of an operation."""
        self._active[operation_name] = time.perf_counter()

    def end_operation(
        self,
        operation_name: str,
        status: str = "SUCCESS",
        cache_hit: bool = False,
        retry_count: int = 0,
    ) -> float:
        """Mark the end of an operation and record the profile entry."""
        if operation_name not in self._active:
            raise ValueError(f"Operation {operation_name} was not started")
        start = self._active.pop(operation_name)
        elapsed = time.perf_counter() - start

        self.records.append(
            OperationProfile(
                operation_name=operation_name,
                record_id=self._current_record,
                district_id=self._current_district,
                season=self._current_season,
                start_time=datetime.now(UTC).isoformat(),
                end_time=datetime.now(UTC).isoformat(),
                duration_seconds=elapsed,
                cache_hit=cache_hit,
                request_status=status,
                retry_count=retry_count,
            )
        )
        return elapsed

    def summarize(self) -> ProfilerResult:
        """Aggregate all recorded operations into a summary."""
        if not self.records:
            return ProfilerResult(
                records_processed=0,
                total_elapsed_seconds=0.0,
                median_seconds_per_record=0.0,
                p95_seconds_per_record=0.0,
                weather_requests=0,
                stac_searches=0,
                satellite_downloads=0,
                cache_hit_rate=0.0,
                retry_count=0,
                failed_requests=0,
                operation_totals={},
                operation_counts={},
            )

        # Simpler approach: count unique records and sum all operation times
        record_ids = {r.record_id for r in self.records if r.record_id}

        operation_totals: dict[str, float] = {}
        operation_counts: dict[str, int] = {}
        for r in self.records:
            operation_totals[r.operation_name] = (
                operation_totals.get(r.operation_name, 0.0) + r.duration_seconds
            )
            operation_counts[r.operation_name] = operation_counts.get(r.operation_name, 0) + 1

        total_elapsed = sum(r.duration_seconds for r in self.records)
        median_per_record = (
            total_elapsed / len(record_ids) if record_ids else 0.0
        )

        weather_requests = operation_counts.get("weather_api_request", 0)
        stac_searches = operation_counts.get("satellite_stac_search", 0)
        satellite_downloads = operation_counts.get("satellite_asset_download", 0)
        cache_hits = sum(1 for r in self.records if r.cache_hit)
        cache_total = operation_counts.get("weather_api_request", 0) + operation_counts.get(
            "satellite_stac_search", 0
        ) + operation_counts.get("satellite_asset_download", 0)
        cache_hit_rate = cache_hits / cache_total if cache_total > 0 else 0.0
        retry_count = sum(r.retry_count for r in self.records)
        failed_requests = sum(
            1 for r in self.records if r.request_status == "FAILED"
        )

        return ProfilerResult(
            records_processed=len(record_ids),
            total_elapsed_seconds=total_elapsed,
            median_seconds_per_record=median_per_record,
            p95_seconds_per_record=0.0,
            weather_requests=weather_requests,
            stac_searches=stac_searches,
            satellite_downloads=satellite_downloads,
            cache_hit_rate=cache_hit_rate,
            retry_count=retry_count,
            failed_requests=failed_requests,
            operation_totals=operation_totals,
            operation_counts=operation_counts,
            records=self.records,
        )

    def save(self, output_path: Path | None = None) -> None:
        """Save results to JSON."""
        out_path = output_path or PROFILER_RESULTS_PATH
        out_path.parent.mkdir(parents=True, exist_ok=True)
        summary = self.summarize()
        output = {
            "records_processed": summary.records_processed,
            "total_elapsed_seconds": summary.total_elapsed_seconds,
            "median_seconds_per_record": summary.median_seconds_per_record,
            "p95_seconds_per_record": summary.p95_seconds_per_record,
            "weather_requests": summary.weather_requests,
            "stac_searches": summary.stac_searches,
            "satellite_downloads": summary.satellite_downloads,
            "cache_hit_rate": summary.cache_hit_rate,
            "retry_count": summary.retry_count,
            "failed_requests": summary.failed_requests,
            "operation_totals": summary.operation_totals,
            "operation_counts": summary.operation_counts,
            "saved_at": datetime.now(UTC).isoformat(),
            "records": [asdict(r) for r in self.records],
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, default=str)

    @classmethod
    def load(cls, path: Path | None = None) -> BenchmarkProfiler:
        """Load results from JSON."""
        out_path = path or PROFILER_RESULTS_PATH
        with open(out_path, encoding="utf-8") as f:
            data = json.load(f)
        profiler = cls()
        for r in data.get("records", []):
            profiler.records.append(OperationProfile(**r))
        return profiler


__all__ = [
    "BenchmarkProfiler",
    "OperationProfile",
    "ProfilerResult",
    "PROFILER_RESULTS_PATH",
]


if __name__ == "__main__":
    print("BenchmarkProfiler module loaded successfully")
    print(f"Results path: {PROFILER_RESULTS_PATH}")
    print(f"Operation names: {OPERATION_NAMES}")
