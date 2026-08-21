"""
ERA5 point-series fetch (Phase 4/7 — REAL Copernicus data, no creds-free fake).

Pipeline: CDS job flow (submit -> poll -> download) + NetCDF parsing with
xarray/netcdf4 -> daily JSON series for a point.

Variables mapped (ERA5 single levels):
- ``t2m``     2m temperature      [K]  -> degC (daily mean)
- ``tp``      total precipitation [m]  -> mm/day (daily sum)

Honesty contract
----------------
- Requires a configured CDS store (token in .env) AND the dataset licence
  accepted on https://cds.climate.copernicus.eu/datasets/... (the API returns
  401 "operation not allowed" otherwise — surfaced as-is, never faked).
- Network/parse failures are explicit errors.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.satellite.cds import DataStoreClient, DataStoreError

logger = logging.getLogger(__name__)

ERA5_DATASET = "reanalysis-era5-single-levels"
VARIABLES = {"t2m": "2m_temperature", "tp": "total_precipitation"}


class Era5Error(Exception):
    """ERA5 fetch/parse error."""


def _chunk(parts: List[str]) -> List[str]:
    """Split 'YYYY-MM-DD' into ERA5 year/month/day lists."""
    years, months, days = [], [], []
    for p in parts:
        y, m, d = p.split("-")
        years.append(y)
        months.append(str(int(m)))
        days.append(str(int(d)))
    return sorted(set(years)), sorted(set(months)), sorted(set(days))


def fetch_era5_point(
    lat: float,
    lon: float,
    start: str,
    end: str,
    variables: Optional[List[str]] = None,
    store: str = "cds",
    max_seconds: float = 600.0,
) -> Dict[str, Any]:
    """Real ERA5 daily series for the nearest grid point.

    Args:
        lat/lon: point in decimal degrees (WGS84).
        start/end: ISO dates 'YYYY-MM-DD' (inclusive).
        variables: subset of ['t2m', 'tp']; default both.
        store: 'cds' | 'ewds' | 'ads'.
        max_seconds: poll deadline before raising.
    """
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        raise Era5Error("invalid coordinates")
    vars_ = variables or list(VARIABLES)
    unknown = set(vars_) - set(VARIABLES)
    if unknown:
        raise Era5Error(f"unknown variables {sorted(unknown)}; use {sorted(VARIABLES)}")
    if start > end:
        raise Era5Error("start must be <= end")

    years, months, days = _chunk([start, end])
    client = DataStoreClient(store=store)
    params: Dict[str, Any] = {
        "product_type": "reanalysis",
        "variable": [VARIABLES[v] for v in vars_],
        "year": years,
        "month": months,
        "day": days,
        "time": [
            "00:00", "03:00", "06:00", "09:00",
            "12:00", "15:00", "18:00", "21:00",
        ],
        "data_format": "netcdf",
        # 0.25 deg box around the point so the nearest grid cell is included
        "area": [
            min(90.0, lat + 0.25),
            max(-180.0, lon - 0.25),
            max(-90.0, lat - 0.25),
            min(180.0, lon + 0.25),
        ],
    }
    try:
        task_url = client.submit_request(params, dataset=ERA5_DATASET)
        client.poll_task(task_url, max_seconds=max_seconds)
        data = client.download(task_url)
    except DataStoreError as exc:
        raise Era5Error(f"CDS request failed: {exc}") from exc

    return _parse_netcdf(data, lat, lon, vars_)


def _parse_netcdf(data: bytes, lat: float, lon: float, vars_: List[str]) -> Dict[str, Any]:
    """Parse ERA5 NetCDF bytes -> daily series at the nearest grid point."""
    import io

    import xarray as xr

    # h5netcdf reads from memory (no temp files, no Windows file locks)
    try:
        ds = xr.open_dataset(io.BytesIO(data), engine="h5netcdf")
    except Exception as exc:  # noqa: BLE001
        raise Era5Error(f"NetCDF parse failed: {exc}") from exc

    # nearest grid cell; load arrays BEFORE closing the file (Windows lock)
    point = ds.sel(latitude=lat, longitude=lon, method="nearest")
    time_dim = "valid_time" if "valid_time" in ds.dims else "time"
    times = list(ds[time_dim].values)
    t2m_vals = point["t2m"].values if ("t2m" in vars_ and "t2m" in point) else None
    tp_vals = point["tp"].values if ("tp" in vars_ and "tp" in point) else None
    ds.close()

    series: List[Dict[str, Any]] = []
    for i in range(len(times)):
        row: Dict[str, Any] = {"datetime": str(times[i])[:19]}
        if t2m_vals is not None:
            row["t2m_c"] = round(float(t2m_vals[i]) - 273.15, 2)
        if tp_vals is not None:
            row["tp_mm"] = round(float(tp_vals[i]) * 1000.0, 3)
        series.append(row)

    # daily aggregation: t2m mean, tp sum
    daily: Dict[str, Dict[str, Any]] = {}
    for row in series:
        date = row["datetime"][:10]
        slot = daily.setdefault(date, {"date": date, "t2m_c_mean": None, "tp_mm_sum": 0.0, "samples": 0})
        if "t2m_c" in row:
            slot["t2m_c_mean"] = (
                row["t2m_c"] if slot["t2m_c_mean"] is None
                else (slot["t2m_c_mean"] * slot["samples"] + row["t2m_c"]) / (slot["samples"] + 1)
            )
        if "tp_mm" in row:
            slot["tp_mm_sum"] += row["tp_mm"]
        slot["samples"] += 1

    result = []
    for date in sorted(daily):
        slot = daily[date]
        entry: Dict[str, Any] = {"date": date}
        if "t2m" in vars_:
            entry["t2m_c"] = round(slot["t2m_c_mean"], 2) if slot["t2m_c_mean"] is not None else None
        if "tp" in vars_:
            entry["tp_mm"] = round(slot["tp_mm_sum"], 3)
        result.append(entry)

    return {
        "store": "cds",
        "dataset": ERA5_DATASET,
        "lat": lat,
        "lon": lon,
        "variables": vars_,
        "daily": result,
        "note": "real ERA5 reanalysis (Copernicus CDS)",
    }
