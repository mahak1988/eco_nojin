"""Test DuckDB Spatial as PostGIS alternative."""
import structlog

logger = structlog.get_logger()
import duckdb
from pathlib import Path

DB_PATH = Path("D:/eco_nojin/data/eco_nojin.duckdb")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def test_spatial():
    logger.info("=== Testing DuckDB Spatial ===")
    conn = duckdb.connect(str(DB_PATH))
    
    # Install and load spatial
    conn.execute("INSTALL spatial;")
    conn.execute("LOAD spatial;")
    logger.info("✅ Spatial extension loaded")
    
    # Test basic spatial operations
    result = conn.execute("""
        SELECT 
            ST_GeomFromText('POINT(51.3890 35.6892)') AS tehran,
            ST_Buffer(ST_GeomFromText('POINT(51.3890 35.6892)'), 0.1) AS buffer,
            ST_Area(ST_Buffer(ST_GeomFromText('POINT(51.3890 35.6892)'), 0.1)) AS area
    """).fetchall()
    logger.info(f"✅ Point operations: {len(result)} results")
    
    # Create spatial table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test_land_units (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            area_ha DOUBLE,
            geom GEOMETRY
        )
    """)
    logger.info("✅ Spatial table created")
    
    # Insert test data
    conn.execute("""
        INSERT OR REPLACE INTO test_land_units VALUES
            (1, 'Plot A', 15.5, ST_GeomFromText('POLYGON((51.0 35.0, 51.1 35.0, 51.1 35.1, 51.0 35.1, 51.0 35.0))')),
            (2, 'Plot B', 8.2, ST_GeomFromText('POLYGON((51.2 35.2, 51.3 35.2, 51.3 35.3, 51.2 35.3, 51.2 35.2))'))
    """)
    logger.info("✅ Test data inserted")
    
    # Test spatial query
    result = conn.execute("""
        SELECT name, area_ha, ST_Area(geom) AS calc_area
        FROM test_land_units
    """).fetchall()
    logger.info(f"✅ Spatial query: {result}")
    
    conn.close()
    logger.info("\n🎉 DuckDB Spatial is ready as PostGIS alternative!")

if __name__ == "__main__":
    test_spatial()
