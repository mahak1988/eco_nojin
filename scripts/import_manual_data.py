r"""Inject the manual Excel dataset into a compact shared SQLite for all models.

Source : D:\eco_nojin\<manual-excel folder>  (v1.0 workbook + supplementary)
Target : D:\eco_nojin\data\manual\eco_manual_v1.sqlite  (budget: <= 10 MB)
Design : metric columns stored as scaled INTEGER (x10); loaders convert back.
Run    : .venv\Scripts\python.exe scripts\import_manual_data.py
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\eco_nojin")
OUT_DIR = ROOT / "data" / "manual"
OUT = OUT_DIR / "eco_manual_v1.sqlite"
MARKER = "eco_nojin_platform_history_v1.0.xlsx"


def find_source_dir() -> Path:
    """Locate the manual-data folder by its marker file (no hardcoded unicode)."""
    for d in ROOT.iterdir():
        if d.is_dir() and (d / MARKER).exists():
            return d
    raise FileNotFoundError(f"folder containing {MARKER} not found under {ROOT}")


BASE = find_source_dir()
V10 = BASE / MARKER
CLIMATE = BASE / "01-03_climate_history_2000_2024.xlsx"
SPECIES = BASE / "06_species_crop_group_map.xlsx"

SCALE10 = {
    "tmax_c", "tmin_c", "tmean_c", "precip_mm", "et0_mm", "gdd_base10",
    "tmax_avg_c", "tmin_avg_c", "tavg_c", "rad_mj_m2", "rh_pct", "rh_mean_pct",
    "wind_ms", "dtr_c", "sunshine_h_day", "aridity_index_p_et0",
    "tmax_normal_c", "tmin_normal_c", "tmean_normal_c", "precip_normal_mm",
    "et0_normal_mm", "kc_ini", "kc_mid", "kc_end", "root_depth_m",
    "theta_fc_cm3cm3", "theta_wp_cm3cm3", "awc_cm3cm3", "ksat_mm_hr",
    "bulk_density_gcm3", "organic_carbon_pct", "annual_rain_normal_mm",
    "rain_cv_pct", "yield_t_ha", "pou_pct", "des_kcal_cap_day",
    "protein_g_cap_day", "delta_t_deg_c", "delta_precip_pct",
    "delta_t_extreme_deg", "lat", "lon", "elevation_m",
}


FACTORS = {'lat': 1000, 'lon': 1000}


def enc(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col in SCALE10 and pd.api.types.is_numeric_dtype(out[col]):
            f = FACTORS.get(col, 10)
            out[col] = (out[col] * f).round().astype('Int64')
    return out


def create_sqlite(con: sqlite3.Connection, name: str, df: pd.DataFrame) -> int:
    cols = []
    for c in df.columns:
        s = df[c]
        if pd.api.types.is_integer_dtype(s):
            cols.append(f'"{c}" INTEGER')
        elif pd.api.types.is_float_dtype(s):
            cols.append(f'"{c}" REAL')
        else:
            cols.append(f'"{c}" TEXT')
    con.execute(f'CREATE TABLE "{name}" ({", ".join(cols)})')
    rows = []
    for rec in df.itertuples(index=False, name=None):
        row = tuple(
            None if pd.isna(v) else (v.item() if hasattr(v, "item") else v)
            for v in rec
        )
        rows.append(row)
    placeholders = ",".join("?" * len(df.columns))
    con.executemany(f'INSERT INTO "{name}" VALUES ({placeholders})', rows)
    return len(rows)


def read_sheet(path: Path, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    return df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    con = sqlite3.connect(OUT)
    con.execute("PRAGMA page_size=8192")
    total = 0

    jobs = [
        (V10, "Sites_Master", "sites", True),
        (V10, "Weather_History_Annual", "weather_annual", True),
        (V10, "Climate_Normals_Monthly", "climate_normals", True),
        (V10, "Weather_Daily", "weather_daily", True),
        (V10, "Crop_Water_Parameters", "crop_water_params", True),
        (V10, "Crop_Calendar_Iran", "crop_calendar_iran", False),
        (V10, "Soil_Hydraulic_Regions", "soil_hydraulic_regions", True),
        (V10, "Production_Faostat", "production_faostat", True),
        (V10, "Iran_Provincial_Agriculture", "iran_provincial_agriculture", True),
        (V10, "Food_Security_Indicators", "food_security_indicators", True),
        (V10, "Water_Resources_Aquastat", "water_resources_aquastat", False),
        (V10, "Climate_Disasters", "climate_disasters", False),
        (V10, "Climate_Projections", "climate_projections", True),
        (V10, "Data_Dictionary", "meta_dictionary", False),
        (V10, "Sources_Notes", "meta_sources", False),
        (CLIMATE, "Monthly_2000_2024", "climate_monthly_300sites", True),
        (SPECIES, "SpeciesMap", "species_crop_map", False),
    ]

    for path, sheet, table, scaled in jobs:
        df = read_sheet(path, sheet)
        if table == "climate_monthly_300sites":
            df = df.drop(columns=["country", "admin1"], errors="ignore")  # joinable via sites
        if scaled:
            df = enc(df)
        n = create_sqlite(con, table, df)
        total += n
        print(f"  {table:32s} {n:>7,} rows x {df.shape[1]} cols", flush=True)

    con.execute("CREATE TABLE meta_info (key TEXT PRIMARY KEY, value TEXT)")
    con.executemany(
        "INSERT INTO meta_info VALUES (?, ?)",
        [
            ("version", "1.0"),
            ("built", datetime.now().isoformat(timespec="seconds")),
            ("source_folder", BASE.name),
            ("note", "scaled INTEGER columns are x10; divide by 10 in loaders"),
            ("budget_mb", "10"),
        ],
    )
    con.commit()
    con.execute("VACUUM")
    size_mb = OUT.stat().st_size / 1e6
    con.close()
    print(f"TOTAL rows: {total:,}")
    print(f"DB SIZE: {size_mb:.2f} MB  (budget 10 MB) -> {'OK' if size_mb <= 10 else 'OVER BUDGET'}")


if __name__ == "__main__":
    main()
