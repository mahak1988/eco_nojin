"""
Populate Land Database with Reference Data
==========================================

Creates database tables and populates with reference data:
- countries, regions, cities
- terrain_classifications, drainage_standards

Run: python sandbox/populate_land_database.py
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path BEFORE any project imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "land_reference.db"


def create_tables(conn: sqlite3.Connection):
    """Create database tables."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            name_fa TEXT,
            continent TEXT NOT NULL,
            capital_lat REAL,
            capital_lon REAL,
            area_km2 REAL,
            population INTEGER,
            dominant_climate TEXT,
            currency TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            name_fa TEXT,
            country_code TEXT NOT NULL,
            center_lat REAL,
            center_lon REAL,
            area_km2 REAL,
            population INTEGER,
            elevation_mean_m REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (country_code) REFERENCES countries(code)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_fa TEXT,
            country_code TEXT NOT NULL,
            region_code TEXT,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            population INTEGER,
            elevation_m REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (country_code) REFERENCES countries(code)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS terrain_classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            slope_min_deg REAL NOT NULL,
            slope_max_deg REAL NOT NULL,
            description TEXT,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drainage_standards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            density_min_km_km2 REAL NOT NULL,
            density_max_km_km2 REAL NOT NULL,
            description TEXT,
            typical_geology TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS land_profiles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            country TEXT,
            region TEXT,
            city TEXT,
            location_lat REAL NOT NULL,
            location_lon REAL NOT NULL,
            area_hectares REAL,
            boundary_geojson TEXT,
            dem_source TEXT,
            dem_resolution_m REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT
        )
    """)

    conn.commit()
    print("✓ Tables created")


def populate_countries(conn: sqlite3.Connection):
    """Populate countries table."""
    from engine.land.reference.data import COUNTRIES
    cursor = conn.cursor()
    for country in COUNTRIES:
        cursor.execute("""
            INSERT OR REPLACE INTO countries 
            (code, name, name_fa, continent, capital_lat, capital_lon,
             area_km2, population, dominant_climate, currency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            country.code, country.name, country.name_fa,
            country.continent.value, country.capital_lat, country.capital_lon,
            country.area_km2, country.population,
            country.dominant_climate, country.currency
        ))
    conn.commit()
    print(f"✓ Populated {len(COUNTRIES)} countries")


def populate_regions(conn: sqlite3.Connection):
    """Populate regions table."""
    from engine.land.reference.data import REGIONS
    cursor = conn.cursor()
    for region in REGIONS:
        cursor.execute("""
            INSERT OR REPLACE INTO regions
            (code, name, name_fa, country_code, center_lat, center_lon,
             area_km2, population, elevation_mean_m)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            region.code, region.name, region.name_fa, region.country_code,
            region.center_lat, region.center_lon,
            region.area_km2, region.population, region.elevation_mean_m
        ))
    conn.commit()
    print(f"✓ Populated {len(REGIONS)} regions")


def populate_cities(conn: sqlite3.Connection):
    """Populate cities table."""
    from engine.land.reference.data import CITIES
    cursor = conn.cursor()
    for city in CITIES:
        cursor.execute("""
            INSERT OR REPLACE INTO cities
            (name, name_fa, country_code, region_code, lat, lon,
             population, elevation_m)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            city.name, city.name_fa, city.country_code, city.region_code,
            city.lat, city.lon, city.population, city.elevation_m
        ))
    conn.commit()
    print(f"✓ Populated {len(CITIES)} cities")


def populate_terrain_classifications(conn: sqlite3.Connection):
    """Populate terrain classifications table."""
    from engine.land.reference.data import TERRAIN_CLASSIFICATIONS
    cursor = conn.cursor()
    for tc in TERRAIN_CLASSIFICATIONS:
        cursor.execute("""
            INSERT OR REPLACE INTO terrain_classifications
            (code, name, slope_min_deg, slope_max_deg, description, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            tc.code, tc.name, tc.slope_min_deg, tc.slope_max_deg,
            tc.description, tc.source
        ))
    conn.commit()
    print(f"✓ Populated {len(TERRAIN_CLASSIFICATIONS)} terrain classifications")


def populate_drainage_standards(conn: sqlite3.Connection):
    """Populate drainage standards table."""
    from engine.land.reference.data import DRAINAGE_STANDARDS
    cursor = conn.cursor()
    for ds in DRAINAGE_STANDARDS:
        cursor.execute("""
            INSERT OR REPLACE INTO drainage_standards
            (code, name, density_min_km_km2, density_max_km_km2,
             description, typical_geology)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ds.code, ds.name, ds.density_min_km_km2, ds.density_max_km_km2,
            ds.description, ds.typical_geology
        ))
    conn.commit()
    print(f"✓ Populated {len(DRAINAGE_STANDARDS)} drainage standards")


def verify_data(conn: sqlite3.Connection):
    """Verify populated data."""
    cursor = conn.cursor()
    tables = [
        "countries", "regions", "cities",
        "terrain_classifications", "drainage_standards", "land_profiles"
    ]
    print("\n📊 Data verification:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  - {table}: {count} records")

    cursor.execute(
        "SELECT name, name_fa, dominant_climate "
        "FROM countries WHERE code = 'IR'"
    )
    iran = cursor.fetchone()
    if iran:
        print(f"\n  - Iran: {iran[0]} ({iran[1]}), climate: {iran[2]}")


def main():
    print("=" * 70)
    print("🗄️  Land Database Population")
    print("=" * 70)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    print(f"✓ Connected to: {DB_PATH}")

    try:
        print("\n[1/6] Creating tables...")
        create_tables(conn)

        print("\n[2/6] Populating countries...")
        populate_countries(conn)

        print("\n[3/6] Populating regions...")
        populate_regions(conn)

        print("\n[4/6] Populating cities...")
        populate_cities(conn)

        print("\n[5/6] Populating standards...")
        populate_terrain_classifications(conn)
        populate_drainage_standards(conn)

        print("\n[6/6] Verifying data...")
        verify_data(conn)

        print("\n" + "=" * 70)
        print("✅ Database populated successfully!")
        print("=" * 70)
        print(f"\n📁 Database: {DB_PATH}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
