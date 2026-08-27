"""Climate motor — CMIP6 (SSP) scenarios via Open-Meteo Climate API (free,
no registration) for 30-year risk analysis vs an observed ERA5 baseline.

Real data: Open-Meteo reanalysis (ERA5) for the baseline period and CMIP6
model output for the scenario period (SSP126/SSP245/SSP370/SSP585).
Outputs are honest computed deltas + a transparent drought-risk projection.
"""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/era5"
CLIMATE_URL = "https://climate-api.open-meteo.com/v1/climate"

SCENARIOS = ["SSP126", "SSP245", "SSP370", "SSP585"]


def _daily_series(url: str, params: Dict[str, Any]) -> Dict[str, List[Any]]:
    r = httpx.get(url, params=params, timeout=90)
    r.raise_for_status()
    d = r.json()["daily"]
    return {
        "time": d["time"],
        "tmean": [float(x or 0.0) for x in d["temperature_2m_mean"]],
        "precip": [float(x or 0.0) for x in d["precipitation_sum"]],
    }


def _monthly_mean(values: List[float]) -> List[float]:
    out: List[float] = []
    for i in range(0, len(values) - 27, 30):
        chunk = values[i : i + 30]
        out.append(sum(chunk) / len(chunk))
    return out


def _monthly_sum(values: List[float]) -> List[float]:
    out: List[float] = []
    for i in range(0, len(values) - 27, 30):
        chunk = values[i : i + 30]
        out.append(sum(chunk))
    return out


def _stats(values: List[float]) -> Dict[str, float]:
    n = len(values)
    if n == 0:
        return {"mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": round(sum(values) / n, 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
    }


def run_climate(
    lat: float,
    lon: float,
    scenario: str = "SSP245",
    baseline_start: str = "2015-01-01",
    baseline_end: str = "2024-12-31",
    future_start: str = "2040-01-01",
    future_end: str = "2049-12-31",
) -> Dict[str, Any]:
    if scenario not in SCENARIOS:
        return {"status": "error", "error": f"scenario must be one of {SCENARIOS}"}

    base = _daily_series(
        ARCHIVE_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": baseline_start,
            "end_date": baseline_end,
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "UTC",
        },
    )
    fut = _daily_series(
        CLIMATE_URL,
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": future_start,
            "end_date": future_end,
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "UTC",
            "models": "CMCC_CM2_VHR4",
            "scenarios": scenario,
        },
    )

    bt, bp = _monthly_mean(base["tmean"]), _monthly_sum(base["precip"])
    ft, fp = _monthly_mean(fut["tmean"]), _monthly_sum(fut["precip"])

    delta_t = round(sum(ft) / len(ft) - sum(bt) / len(bt), 2)
    base_p = sum(bp) / len(bp)
    fut_p = sum(fp) / len(fp)
    delta_p = round(fut_p - base_p, 1)
    p_change_pct = round((fut_p - base_p) / base_p * 100, 1) if base_p else None

    dry_months_base = sum(1 for v in bp if v < 10)
    dry_months_fut = sum(1 for v in fp if v < 10)

    return {
        "status": "ok",
        "data_mode": "real_climate_model",
        "source": "Open-Meteo Climate API (CMIP6, free) + ERA5 baseline",
        "location": {"lat": lat, "lon": lon},
        "scenario": scenario,
        "periods": {
            "baseline": {"start": baseline_start, "end": baseline_end},
            "future": {"start": future_start, "end": future_end, "years": (int(future_end[:4]) - int(future_start[:4])) + 1},
        },
        "baseline": {"tmean_c": _stats(bt), "precip_mm_month": _stats(bp), "dry_months_pct": round(dry_months_base / len(bp) * 100, 1)},
        "future": {"tmean_c": _stats(ft), "precip_mm_month": _stats(fp), "dry_months_pct": round(dry_months_fut / len(fp) * 100, 1)},
        "delta": {
            "tmean_c": delta_t,
            "precip_mm_month": delta_p,
            "precip_change_pct": p_change_pct,
            "dry_months_pct_point_change": round(dry_months_fut / len(fp) * 100 - dry_months_base / len(bp) * 100, 1),
        },
        "risk_30y": {
            "heat_risk": "high" if delta_t >= 3 else ("moderate" if delta_t >= 1.5 else "low"),
            "drought_risk": "high" if (p_change_pct or 0) <= -15 else ("moderate" if (p_change_pct or 0) <= -5 else "low"),
            "note": "پیش‌بینی ساده مبتنی بر دلتای دما/بارش مدل CMIP6 — تحلیل قطعی نیازمند آبشار مدل‌های هیدرولوژیک است.",
        },
        "note": f"سناریوی {scenario} از CMIP6 (مدل CMCC-CM2-VHR4)؛ داده واقعی و رایگان بدون ثبت‌نام. "
        f"سرویس Open-Meteo Climate در حال حاضر تا سال ۲۰۴۹ داده می‌دهد — با گسترش سرویس، پنجره به ۳۰ سال کامل می‌رسد.",
    }
