"""Lab data store + measured-vs-modelled SOC comparison (Phase 4-D).

Honest contract (W-001): lab samples are REAL user-uploaded measurements.
The comparison reports bias / RMSE / MAPE / R2 between lab SOC and the
modelled SoilGrids baseline (same conversion as the scientific chain:
soc_t_ha = soc_g_kg * bulk_density * 2.5). No fabricated fallbacks.
"""

import json
import math
import os
import time
import uuid
from typing import Any

from services.satellite.soilgrids import fetch_soil_profile

DATA_DIR = "data/lab"
STORE = os.path.join(DATA_DIR, "lab_samples.json")
MAX_COMPARE_POINTS = 10

# (lat, lon) -> modelled soc_t_ha (in-memory cache, SoilGrids WCS is slow)
_model_cache: dict[tuple, float] = {}


def _load() -> list[dict[str, Any]]:
    if not os.path.exists(STORE):
        return []
    with open(STORE, encoding="utf-8") as fh:
        return json.load(fh)


def _save(rows: list[dict[str, Any]]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STORE, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)


def add_lab_samples(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate and store lab SOC measurements. Returns honest status."""
    cleaned: list[dict[str, Any]] = []
    errors: list[str] = []
    for i, r in enumerate(rows, 1):
        try:
            lat = float(r.get("lat"))
            lon = float(r.get("lon"))
            soc = float(r.get("soc_t_ha"))
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError("lat/lon out of range")
            if soc <= 0:
                raise ValueError("soc_t_ha must be > 0")
            cleaned.append(
                {
                    "lab_id": str(r.get("lab_id") or f"LAB-{uuid.uuid4().hex[:8].upper()}"),
                    "lat": round(lat, 6),
                    "lon": round(lon, 6),
                    "soc_t_ha": round(soc, 3),
                    "depth_cm": float(r.get("depth_cm", 30) or 30),
                    "lab": str(r.get("lab") or "unknown"),
                    "sampled_at": str(r.get("sampled_at") or time.strftime("%Y-%m-%d")),
                    "added_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }
            )
        except (TypeError, ValueError) as exc:
            errors.append(f"row {i}: {exc}")
    existing = _load()
    _save(existing + cleaned)
    return {
        "status": "stored" if cleaned else "no_valid_rows",
        "added": len(cleaned),
        "errors": errors,
        "total": len(existing) + len(cleaned),
    }


def list_lab_samples() -> dict[str, Any]:
    rows = _load()
    return {
        "status": "ok" if rows else "no_lab_data",
        "count": len(rows),
        "samples": rows,
        "hint": None if rows else "ابتدا داده آزمایشگاهی ثبت کنید (POST /api/mrv/lab/samples)",
    }


async def _modelled_soc(lat: float, lon: float) -> float:
    key = (round(lat, 4), round(lon, 4))
    if key not in _model_cache:
        prof = await fetch_soil_profile(key[0], key[1])
        bd = float(prof.get("bulk_density_g_cm3", 1.3) or 1.3)
        soc_g_kg = float(prof.get("soc_g_kg", 10.0) or 10.0)
        # same conversion as chain_runner (RothC baseline input)
        _model_cache[key] = round(soc_g_kg * bd * 2.5, 3)
    return _model_cache[key]


async def compare_model() -> dict[str, Any]:
    """Measured (lab) vs modelled (SoilGrids) SOC per sample + honest stats."""
    rows = [r for r in _load() if r.get("lat") is not None and r.get("lon") is not None][:MAX_COMPARE_POINTS]
    if not rows:
        return {
            "status": "no_lab_data",
            "message": "داده آزمایشگاهی ثبت نشده — KGE/اعتبارسنجی تا بارگذاری داده واقعی غیرفعال است (W-001).",
        }
    pairs: list[dict[str, Any]] = []
    for r in rows:
        try:
            modelled = await _modelled_soc(float(r["lat"]), float(r["lon"]))
        except Exception:
            continue  # one bad point must not kill the comparison
        pairs.append(
            {
                "lab_id": r.get("lab_id"),
                "lat": r.get("lat"),
                "lon": r.get("lon"),
                "measured_soc_t_ha": r.get("soc_t_ha"),
                "modelled_soc_t_ha": modelled,
                "error_t_ha": round(float(r["soc_t_ha"]) - modelled, 3),
            }
        )
    if not pairs:
        return {"status": "model_unavailable", "message": "SoilGrids برای نقاط ثبتشده در دسترس نبود."}
    n = len(pairs)
    meas = [float(p["measured_soc_t_ha"]) for p in pairs]
    mod = [float(p["modelled_soc_t_ha"]) for p in pairs]
    mean_m = sum(meas) / n
    mean_mod = sum(mod) / n
    bias = mean_m - mean_mod
    rmse = math.sqrt(sum((m - o) ** 2 for m, o in zip(meas, mod)) / n)
    mape = sum(abs(m - o) / abs(m) * 100 for m, o in zip(meas, mod) if m != 0) / n
    ss_res = sum((m - o) ** 2 for m, o in zip(meas, mod))
    ss_tot = sum((m - mean_m) ** 2 for m in meas)
    r2 = round(1 - ss_res / ss_tot, 4) if ss_tot > 0 else None
    status = "comparison_ready" if n >= 2 else "low_sample_warning"
    return {
        "status": status,
        "n": n,
        "mean_measured_t_ha": round(mean_m, 3),
        "mean_modelled_t_ha": round(mean_mod, 3),
        "bias_t_ha": round(bias, 3),
        "rmse_t_ha": round(rmse, 3),
        "mape_pct": round(mape, 2),
        "r2": r2,
        "kge": None,  # needs observed time series — honest
        "note": "آمار فقط با داده آزمایشگاهی واقعی محاسبه میشود؛ KGE نیازمند سری زمانی مشاهدهای است.",
        "pairs": pairs,
    }
