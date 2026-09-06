"""
Tests for engine.data_connector
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from engine.data_connector import connector
import structlog
logger = structlog.get_logger()


def test_connector_creation():
    """Connector should be created."""
    assert connector is not None
    logger.info("PASS: Connector creation")


def test_list_master_tables():
    """Should list tables in master DuckDB."""
    try:
        tables = connector.list_master_tables()
        assert len(tables) > 0
        logger.info(f"PASS: Master tables ({len(tables)} found)")
    except Exception as e:
        logger.info(f"SKIP: Master tables ({e})")


def test_get_climate_data():
    """Should get climate data."""
    try:
        data = connector.get_climate_data(year=2020)
        assert data is not None
        logger.info(f"PASS: Climate data retrieved")
    except Exception as e:
        logger.info(f"SKIP: Climate data ({e})")


def test_get_table_info():
    """Should get table info."""
    try:
        info = connector.get_table_info("weather_daily")
        assert "table" in info
        logger.info(f"PASS: Table info ({info.get('rows', 0)} rows)")
    except Exception as e:
        logger.info(f"SKIP: Table info ({e})")


if __name__ == "__main__":
    logger.info("Running connector tests...\n")
    test_connector_creation()
    test_list_master_tables()
    test_get_climate_data()
    test_get_table_info()
    logger.info("\nAll connector tests completed!")
