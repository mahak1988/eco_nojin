"""Eco Nojin Database Initialization - Single Script."""
from __future__ import annotations
import structlog

logger = structlog.get_logger()

import json
import sys
from pathlib import Path
from uuid import uuid4


# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = Path("D:/eco_nojin/data/eco_nojin.duckdb")
PROJECT_NAME = "Eco Nojin"


# ============================================================
# SCHEMA DEFINITIONS
# ============================================================

TABLES = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            role VARCHAR(50) DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT current_timestamp,
            updated_at TIMESTAMP DEFAULT current_timestamp
        )
    """,

    "projects": """
        CREATE TABLE IF NOT EXISTS projects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            owner_id UUID,
            region_name VARCHAR(255),
            area_ha DOUBLE,
            created_at TIMESTAMP DEFAULT current_timestamp,
            updated_at TIMESTAMP DEFAULT current_timestamp
        )
    """,

    "land_units": """
        CREATE TABLE IF NOT EXISTS land_units (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID,
            name VARCHAR(255) NOT NULL,
            code VARCHAR(50),
            geom GEOMETRY,
            centroid GEOMETRY,
            area_ha DOUBLE,
            land_use VARCHAR(50),
            soil_type VARCHAR(100),
            slope_class VARCHAR(20),
            elevation_min DOUBLE,
            elevation_max DOUBLE,
            aspect_dominant VARCHAR(10),
            created_at TIMESTAMP DEFAULT current_timestamp,
            updated_at TIMESTAMP DEFAULT current_timestamp
        )
    """,

    "watersheds": """
        CREATE TABLE IF NOT EXISTS watersheds (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID,
            parent_id UUID,
            name VARCHAR(255),
            code VARCHAR(50),
            order_number INTEGER,
            geom GEOMETRY,
            outlet_point GEOMETRY,
            area_ha DOUBLE,
            curve_number_avg DOUBLE,
            time_of_concentration_hours DOUBLE,
            avg_slope_percent DOUBLE,
            created_at TIMESTAMP DEFAULT current_timestamp
        )
    """,

    "soil_profiles": """
        CREATE TABLE IF NOT EXISTS soil_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            land_unit_id UUID,
            sample_point GEOMETRY,
            depth_cm DOUBLE,
            sand_percent DOUBLE,
            silt_percent DOUBLE,
            clay_percent DOUBLE,
            texture_class VARCHAR(50),
            ph DOUBLE,
            ec_ds_m DOUBLE,
            organic_carbon_percent DOUBLE,
            nitrogen_ppm DOUBLE,
            phosphorus_ppm DOUBLE,
            potassium_ppm DOUBLE,
            bulk_density DOUBLE,
            field_capacity DOUBLE,
            wilting_point DOUBLE,
            saturation DOUBLE,
            theta_r DOUBLE,
            theta_s DOUBLE,
            alpha DOUBLE,
            n_param DOUBLE,
            ks DOUBLE,
            sample_date DATE,
            created_at TIMESTAMP DEFAULT current_timestamp
        )
    """,

    "climate_stations": """
        CREATE TABLE IF NOT EXISTS climate_stations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID,
            name VARCHAR(255),
            station_id VARCHAR(100),
            location GEOMETRY,
            elevation_m DOUBLE,
            source VARCHAR(50),
            created_at TIMESTAMP DEFAULT current_timestamp
        )
    """,

    "climate_daily": """
        CREATE TABLE IF NOT EXISTS climate_daily (
            id BIGINT,
            station_id UUID,
            date DATE NOT NULL,
            temp_min_c DOUBLE,
            temp_max_c DOUBLE,
            temp_avg_c DOUBLE,
            precipitation_mm DOUBLE,
            wind_speed_ms DOUBLE,
            relative_humidity DOUBLE,
            solar_radiation_mj_m2 DOUBLE,
            et0_mm DOUBLE
        )
    """,

    "satellite_observations": """
        CREATE TABLE IF NOT EXISTS satellite_observations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            land_unit_id UUID,
            satellite VARCHAR(50),
            product VARCHAR(100),
            acquisition_date DATE,
            ndvi DOUBLE,
            evi DOUBLE,
            ndwi DOUBLE,
            lai DOUBLE,
            soil_moisture_index DOUBLE,
            cloud_cover_percent DOUBLE,
            quality_score DOUBLE,
            raster_path VARCHAR(500),
            created_at TIMESTAMP DEFAULT current_timestamp
        )
    """,

    "crop_plans": """
        CREATE TABLE IF NOT EXISTS crop_plans (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            land_unit_id UUID,
            crop_name VARCHAR(100),
            variety VARCHAR(100),
            planting_date DATE,
            harvest_date DATE,
            irrigation_type VARCHAR(50),
            fertilization_plan VARCHAR,
            expected_yield_ton_ha DOUBLE,
            water_requirement_mm DOUBLE,
            season VARCHAR(20),
            year INTEGER,
            created_at TIMESTAMP DEFAULT current_timestamp
        )
    """,

    "simulation_runs": """
        CREATE TABLE IF NOT EXISTS simulation_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID,
            land_unit_id UUID,
            model_name VARCHAR(50),
            model_version VARCHAR(20),
            scenario_name VARCHAR(100),
            parameters VARCHAR,
            start_date DATE,
            end_date DATE,
            time_step VARCHAR(20),
            status VARCHAR(20),
            result_summary VARCHAR,
            output_path VARCHAR(500),
            execution_time_seconds DOUBLE,
            created_at TIMESTAMP DEFAULT current_timestamp,
            completed_at TIMESTAMP
        )
    """,

    "mrv_observations": """
        CREATE TABLE IF NOT EXISTS mrv_observations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            land_unit_id UUID,
            observation_type VARCHAR(50),
            observer VARCHAR(100),
            observation_date DATE,
            location GEOMETRY,
            measurements VARCHAR,
            verified BOOLEAN DEFAULT FALSE,
            verified_by VARCHAR(100),
            verified_at TIMESTAMP,
            photos_urls VARCHAR,
            notes TEXT,
            created_at TIMESTAMP DEFAULT current_timestamp
        )
    """,

    "carbon_credits": """
        CREATE TABLE IF NOT EXISTS carbon_credits (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID,
            land_unit_id UUID,
            baseline_tco2e DOUBLE,
            actual_tco2e DOUBLE,
            sequestered_tco2e DOUBLE,
            verification_standard VARCHAR(50),
            verification_date DATE,
            certificate_id VARCHAR(100),
            period_start DATE,
            period_end DATE,
            created_at TIMESTAMP DEFAULT current_timestamp
        )
    """,
}


INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
    "CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id)",
    "CREATE INDEX IF NOT EXISTS idx_land_units_project ON land_units(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_watersheds_project ON watersheds(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_soil_land_unit ON soil_profiles(land_unit_id)",
    "CREATE INDEX IF NOT EXISTS idx_climate_station_date ON climate_daily(station_id, date)",
    "CREATE INDEX IF NOT EXISTS idx_satellite_land_date ON satellite_observations(land_unit_id, acquisition_date)",
    "CREATE INDEX IF NOT EXISTS idx_simulation_project ON simulation_runs(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_simulation_land ON simulation_runs(land_unit_id)",
]


# ============================================================
# MAIN FUNCTIONS
# ============================================================

def connect_db():
    """Connect to DuckDB and load spatial extension."""
    import duckdb

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))

    try:
        conn.execute("INSTALL spatial;")
        conn.execute("LOAD spatial;")
    except Exception as e:
        logger.warning(f"Warning: spatial extension issue: {e}")

    return conn


def create_schema(conn):
    """Create all tables and indexes."""
    logger.info("\n[1/3] Creating schema...")

    # Create tables
    for table_name, ddl in TABLES.items():
        try:
            conn.execute(ddl)
            logger.info(f"  [OK] {table_name}")
        except Exception as e:
            logger.info(f"  [FAIL] {table_name}: {e}")

    # Create indexes
    logger.info("  Creating indexes...")
    for idx_sql in INDEXES:
        try:
            conn.execute(idx_sql)
        except Exception as e:
            logger.warning(f"  [WARN] Index: {e}")

    # Verify
    result = conn.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).fetchall()

    logger.info(f"\n  Created {len(result)} tables:")
    for row in result:
        logger.info(f"    - {row[0]}")


def insert_test_data(conn):
    """Insert test data."""
    logger.info("\n[2/3] Inserting test data...")

    from shapely.geometry import Polygon, Point

    # Create test user
    user_id = uuid4()
    conn.execute(
        "INSERT INTO users (id, email, password_hash, full_name, role) VALUES (?, ?, ?, ?, ?)",
        [str(user_id), "admin@econojin.io", "hashed_pw", "Admin User", "admin"]
    )
    logger.info("  [OK] User: admin@econojin.io")

    # Create test project
    project_id = uuid4()
    conn.execute(
        "INSERT INTO projects (id, name, description, owner_id, region_name, area_ha) VALUES (?, ?, ?, ?, ?, ?)",
        [str(project_id), "Test Pilot Project", "Development project",
         str(user_id), "Test Region", 1000.0]
    )
    logger.info(f"  [OK] Project: {project_id}")

    # Create land units
    land_units = [
        ("Plot A - North Field", Polygon([
            (51.0, 35.0), (51.1, 35.0), (51.1, 35.1), (51.0, 35.1), (51.0, 35.0)
        ]), 123.45, "agriculture", "gentle"),
        ("Plot B - South Rangeland", Polygon([
            (51.2, 35.2), (51.3, 35.2), (51.3, 35.3), (51.2, 35.3), (51.2, 35.2)
        ]), 87.6, "rangeland", "steep"),
    ]

    land_unit_ids = []
    for name, geom, area, use, slope in land_units:
        lu_id = uuid4()
        conn.execute("""
            INSERT INTO land_units (id, project_id, name, geom, area_ha, land_use, slope_class)
            VALUES (?, ?, ?, ST_GeomFromText(?), ?, ?, ?)
        """, [
            str(lu_id), str(project_id), name, geom.wkt, area, use, slope
        ])
        land_unit_ids.append(lu_id)
        logger.info(f"  [OK] Land Unit: {name}")

    # Create soil profiles
    for lu_id in land_unit_ids:
        profile_id = uuid4()
        conn.execute("""
            INSERT INTO soil_profiles (
                id, land_unit_id, sample_point, depth_cm,
                sand_percent, silt_percent, clay_percent, texture_class,
                ph, organic_carbon_percent, sample_date
            ) VALUES (?, ?, ST_GeomFromText(?), ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            str(profile_id), str(lu_id), Point(51.05, 35.05).wkt, 30.0,
            40.0, 35.0, 25.0, "loam", 7.2, 1.5, "2026-01-15"
        ])

    logger.info(f"  [OK] Soil profiles: {len(land_unit_ids)}")

    # Create test simulation run
    sim_id = uuid4()
    conn.execute("""
        INSERT INTO simulation_runs (
            id, project_id, land_unit_id, model_name, scenario_name,
            parameters, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        str(sim_id), str(project_id), str(land_unit_ids[0]),
        "SWAT+", "Baseline_2026",
        json.dumps({"time_step": "daily", "start": "2026-01-01"}),
        "pending"
    ])
    logger.info("  [OK] Simulation run: SWAT+ Baseline_2026")

    return project_id, land_unit_ids


def verify_data(conn):
    """Verify data and run spatial queries."""
    logger.info("\n[3/3] Verification...")

    # Count records
    tables_to_check = ["users", "projects", "land_units", "soil_profiles", "simulation_runs"]
    for table in tables_to_check:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        logger.info(f"  [OK] {table}: {count}")

    # Spatial query
    logger.info("\n  Spatial query test:")
    results = conn.execute("""
        SELECT name, area_ha,
               ST_Area(geom) AS calc_area,
               ST_X(ST_Centroid(geom)) AS lon,
               ST_Y(ST_Centroid(geom)) AS lat
        FROM land_units
        ORDER BY area_ha DESC
    """).fetchall()

    for r in results:
        logger.info(f"    - {r[0]}: {r[1]:.2f} ha (center: {r[3]:.4f}, {r[4]:.4f})")


def main():
    logger.info("=" * 60)
    logger.info(f"{PROJECT_NAME} Database Initialization")
    logger.info("=" * 60)

    # Remove old database
    if DB_PATH.exists():
        logger.info(f"Removing old database: {DB_PATH}")
        DB_PATH.unlink()

    # Connect
    conn = connect_db()
    logger.info(f"Connected to: {DB_PATH}")

    try:
        create_schema(conn)
        project_id, land_unit_ids = insert_test_data(conn)
        verify_data(conn)

        logger.info("\n" + "=" * 60)
        logger.info("[SUCCESS] Database initialization complete!")
        logger.info("=" * 60)
        logger.info(f"Database: {DB_PATH}")
        logger.info(f"Project ID: {project_id}")
        logger.info(f"Land Units: {len(land_unit_ids)}")
        logger.info("\nReady for Phase 1.4: Map Generation Engine")

    except Exception as e:
        logger.error(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
