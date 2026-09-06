"""Read-only loader for the shared manual reference dataset (eco_manual_v1).

Every model, motor and service can use this single import point:

    from services.data_manual import manual

    df = manual.weather_daily(site_id=12, start="2002-03-01", end="2002-10-30")
    sites = manual.sites()
    kc = manual.crop_water_params(species_id="wheat")

Storage notes:
    - SQLite file: data/manual/eco_manual_v1.sqlite  (budget <= 10 MB)
    - metric columns are stored as INTEGER x10  (lat/lon x1000);
      this loader converts them back to float transparently.
    - override location with env var MANUAL_DATA_DB if needed.
"""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

_PROJECT = Path(__file__).resolve().parents[2]
_DEFAULT_DB = _PROJECT / "data" / "manual" / "eco_manual_v1.sqlite"

SCALED_X10 = {
    "tmax_c", "tmin_c", "tmean_c", "precip_mm", "et0_mm", "gdd_base10",
    "tmax_avg_c", "tmin_avg_c", "tavg_c", "rad_mj_m2", "rh_pct", "rh_mean_pct",
    "wind_ms", "dtr_c", "sunshine_h_day", "aridity_index_p_et0",
    "tmax_normal_c", "tmin_normal_c", "tmean_normal_c", "precip_normal_mm",
    "et0_normal_mm", "kc_ini", "kc_mid", "kc_end", "root_depth_m",
    "theta_fc_cm3cm3", "theta_wp_cm3cm3", "awc_cm3cm3", "ksat_mm_hr",
    "bulk_density_gcm3", "organic_carbon_pct", "annual_rain_normal_mm",
    "rain_cv_pct", "yield_t_ha", "pou_pct", "des_kcal_cap_day",
    "protein_g_cap_day", "delta_t_deg_c", "delta_precip_pct",
    "delta_t_extreme_deg", "elevation_m",
}
SCALED_X1000 = {"lat", "lon"}


def db_path() -> Path:
    override = os.getenv("MANUAL_DATA_DB")
    return Path(override) if override else _DEFAULT_DB


def _rescale(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if col in SCALED_X10:
            df[col] = df[col] / 10.0
        elif col in SCALED_X1000:
            df[col] = df[col] / 1000.0
    return df


def _query(table: str, where: str = "", params: tuple = (), order: str = "") -> pd.DataFrame:
    """Execute a SELECT on the manual SQLite database with safe identifier handling.

    The table name is validated against ``_safe_ident`` before interpolation
    so that user-supplied identifiers cannot inject SQL.  Values are always
    bound through ``params``.
    """
    from services.security.query_safe import _safe_ident
    safe_table = _safe_ident(table)
    sql = "SELECT * FROM " + safe_table
    if where:
        sql += where
    if order:
        sql += " ORDER BY " + order
    path = db_path()
    if not path.exists():
        raise FileNotFoundError(
            "manual dataset not found at " + str(path) + "; run scripts/import_manual_data.py"
        )
    con = sqlite3.connect("file:" + path.as_posix() + "?mode=ro", uri=True)
    try:
        df = pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()
    return _rescale(df)


def _where(conditions: dict[str, Any]) -> tuple[str, tuple]:
    clauses = ['"' + k + '" = ?' for k, v in conditions.items() if v is not None]
    params = tuple(v for v in conditions.values() if v is not None)
    return (" WHERE " + " AND ".join(clauses) if clauses else ""), params


# ----------------------------------------------------------------- accessors

def sites() -> pd.DataFrame:
    return _query("sites", order="site_id")


def site(site_id: int) -> pd.DataFrame:
    return _query("sites", where=" WHERE site_id = ?", params=(site_id,))


def weather_daily(site_id: int, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    where = " WHERE site_id = ?"
    params = (site_id,)
    if start:
        where += " AND date >= ?"
        params += (start,)
    if end:
        where += " AND date <= ?"
        params += (end,)
    return _query("weather_daily", where=where, params=params, order="date")


def weather_annual(site_id: int | None = None) -> pd.DataFrame:
    w, p = _where({"site_id": site_id})
    return _query("weather_annual", where=w, params=p, order="site_id, year")


def climate_normals(site_id: int | None = None) -> pd.DataFrame:
    w, p = _where({"site_id": site_id})
    return _query("climate_normals", where=w, params=p, order="site_id, month")


def climate_monthly(site_id: int, year: int | None = None) -> pd.DataFrame:
    w, p = _where({"site_id": site_id, "year": year})
    return _query("climate_monthly_300sites", where=w, params=p, order="year, month")


def crop_water_params(species_id: str | None = None) -> pd.DataFrame:
    w, p = _where({"species_id": species_id})
    return _query("crop_water_params", where=w, params=p)


def crop_calendar(province: str | None = None, crop_fa: str | None = None) -> pd.DataFrame:
    w, p = _where({"province": province, "crop_fa": crop_fa})
    return _query("crop_calendar_iran", where=w, params=p, order="province, crop_fa")


def soil_regions(province: str | None = None) -> pd.DataFrame:
    w, p = _where({"province": province})
    return _query("soil_hydraulic_regions", where=w, params=p)


def production_faostat(item_fa: str | None = None, country_fa: str | None = None) -> pd.DataFrame:
    w, p = _where({"item_fa": item_fa, "country_fa": country_fa})
    return _query("production_faostat", where=w, params=p, order="year")


def iran_provincial(province: str | None = None, crop_fa: str | None = None) -> pd.DataFrame:
    w, p = _where({"province": province, "crop_fa": crop_fa})
    return _query("iran_provincial_agriculture", where=w, params=p, order="year")


def food_security(country_fa: str | None = None) -> pd.DataFrame:
    w, p = _where({"country_fa": country_fa})
    return _query("food_security_indicators", where=w, params=p, order="year")


def water_resources() -> pd.DataFrame:
    return _query("water_resources_aquastat", order="year")


def disasters(country_fa: str | None = None) -> pd.DataFrame:
    w, p = _where({"country_fa": country_fa})
    return _query("climate_disasters", where=w, params=p, order="year")


def climate_projections(region_fa: str | None = None) -> pd.DataFrame:
    w, p = _where({"region_fa": region_fa})
    return _query("climate_projections", where=w, params=p)


def species_map(species_id: str | None = None) -> pd.DataFrame:
    w, p = _where({"species_id": species_id})
    return _query("species_crop_map", where=w, params=p)


def data_dictionary(sheet: str | None = None) -> pd.DataFrame:
    w, p = _where({"sheet": sheet})
    return _query("meta_dictionary", where=w, params=p)


def status() -> dict[str, Any]:
    """Existence, size and table inventory — for health checks."""
    path = db_path()
    if not path.exists():
        return {"exists": False, "path": str(path)}
    db_uri = "file:" + path.as_posix() + "?mode=ro"
    con = sqlite3.connect(db_uri, uri=True)
    try:
        tables = [
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]
        from services.security.query_safe import _safe_ident
        counts = {}
        for t in tables:
            safe_t = _safe_ident(t)
            counts[t] = con.execute(
                "SELECT COUNT(*) FROM '" + safe_t + "'"
            ).fetchone()[0]
    finally:
        con.close()
    return {
        "exists": True,
        "path": str(path),
        "size_mb": round(path.stat().st_size / 1e6, 2),
        "tables": counts,
    }
