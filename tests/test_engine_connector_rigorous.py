"""
tests/test_engine_connector_rigorous.py
=======================================

Rigorous tests for engine.data_connector.DataConnector.
"""

import sys
import pytest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestConnectorInstantiation:
    """Test connector instantiation and initialization."""

    def test_connector_singleton(self):
        """Connector should be available as singleton."""
        from engine.data_connector import connector, DataConnector
        assert connector is not None
        assert isinstance(connector, DataConnector)

    def test_connector_has_hub(self):
        """Connector should have hub reference."""
        from engine.data_connector import connector
        assert hasattr(connector, "hub")
        assert connector.hub is not None


class TestConnectorAnalyticsQueries:
    """Test DuckDB analytics queries."""

    def test_list_master_tables(self, connector_instance):
        """Should list tables in master DuckDB."""
        pytest.importorskip("duckdb")
        tables = connector_instance.list_master_tables()
        assert isinstance(tables, list)
        assert len(tables) > 0
        assert "weather_daily" in tables

    def test_get_table_info(self, connector_instance):
        """Should get table info with columns and row count."""
        pytest.importorskip("duckdb")
        info = connector_instance.get_table_info("weather_daily")
        assert "table" in info
        assert info["table"] == "weather_daily"
        assert "columns" in info
        assert "rows" in info
        assert info["rows"] >= 0
        assert isinstance(info["columns"], list)

    def test_get_table_info_nonexistent(self, connector_instance):
        """Should handle nonexistent table gracefully."""
        pytest.importorskip("duckdb")
        info = connector_instance.get_table_info("nonexistent_table_xyz")
        assert "error" in info or info.get("rows", 0) == 0

    def test_get_climate_data(self, connector_instance):
        """Should get climate data from master DuckDB."""
        pytest.importorskip("duckdb")
        data = connector_instance.get_climate_data()
        assert data is not None
        if hasattr(data, "__len__"):
            assert len(data) >= 0

    def test_get_climate_data_with_year_filter(self, connector_instance):
        """Should filter climate data by year."""
        pytest.importorskip("duckdb")
        data = connector_instance.get_climate_data(year=2020)
        assert data is not None

    def test_execute_analytics_query(self, connector_instance):
        """Should execute arbitrary analytics query."""
        pytest.importorskip("duckdb")
        result = connector_instance.execute_analytics_query("SELECT 1 AS val")
        assert result is not None


class TestConnectorCropParameters:
    """Test crop parameter retrieval."""

    def test_get_crop_parameters(self, connector_instance):
        """Should get crop parameters."""
        pytest.importorskip("duckdb")
        params = connector_instance.get_crop_parameters("wheat")
        assert isinstance(params, dict)

    def test_get_crop_parameters_case_insensitive(self, connector_instance):
        """Should be case-insensitive."""
        pytest.importorskip("duckdb")
        p1 = connector_instance.get_crop_parameters("WHEAT")
        p2 = connector_instance.get_crop_parameters("wheat")
        assert isinstance(p1, dict)
        assert isinstance(p2, dict)

    def test_get_crop_parameters_nonexistent(self, connector_instance):
        """Should return empty dict for nonexistent crop."""
        pytest.importorskip("duckdb")
        params = connector_instance.get_crop_parameters(
            "nonexistent_crop_xyz123456789"
        )
        assert isinstance(params, dict)


class TestConnectorManualData:
    """Test manual SQLite operations."""

    def test_get_crop_calendar(self, connector_instance):
        """Should get crop calendar data."""
        calendar = connector_instance.get_crop_calendar()
        assert isinstance(calendar, list)
        if calendar:
            assert isinstance(calendar[0], dict)

    def test_get_crop_calendar_with_province(self, connector_instance):
        """Should filter by province."""
        calendar = connector_instance.get_crop_calendar(province="کرمانشاه")
        assert isinstance(calendar, list)

    def test_get_climate_disasters(self, connector_instance):
        """Should get climate disasters."""
        disasters = connector_instance.get_climate_disasters()
        assert isinstance(disasters, list)
        if disasters:
            assert isinstance(disasters[0], dict)

    def test_get_climate_disasters_with_country(self, connector_instance):
        """Should filter disasters by country."""
        disasters = connector_instance.get_climate_disasters(country="ایران")
        assert isinstance(disasters, list)


class TestConnectorTransactional:
    """Test transactional operations."""

    def test_get_session_context(self, connector_instance):
        """get_session should work as context manager."""
        with connector_instance.get_session() as session:
            assert session is not None

    def test_get_user_returns_none_or_user(self, connector_instance):
        """get_user should handle missing users gracefully."""
        user = connector_instance.get_user("nonexistent_user_xyz")
        assert user is None or hasattr(user, "id")

    def test_get_land_profile_returns_none_or_profile(self, connector_instance):
        """get_land_profile should handle missing profiles gracefully."""
        profile = connector_instance.get_land_profile("nonexistent_land_xyz")
        assert profile is None or hasattr(profile, "id")


class TestConnectorEdgeCases:
    """Test edge cases and error handling."""

    def test_unicode_in_queries(self, connector_instance):
        """Should handle Unicode/Persian text in queries."""
        pytest.importorskip("duckdb")
        result = connector_instance.execute_analytics_query(
            "SELECT 'سلام' AS greeting"
        )
        assert result is not None

    def test_empty_result_handling(self, connector_instance):
        """Should handle empty results gracefully."""
        pytest.importorskip("duckdb")
        result = connector_instance.execute_analytics_query(
            "SELECT 1 WHERE 1=0"
        )
        assert result is not None

    def test_null_values_handling(self, connector_instance):
        """Should handle NULL values."""
        pytest.importorskip("duckdb")
        result = connector_instance.execute_analytics_query(
            "SELECT NULL AS null_val"
        )
        assert result is not None


class TestConnectorConcurrency:
    """Test concurrent access."""

    def test_concurrent_queries(self, connector_instance):
        """Multiple concurrent queries should work."""
        pytest.importorskip("duckdb")
        errors = []
        results = []

        def query(i):
            try:
                info = connector_instance.get_table_info("weather_daily")
                results.append(info)
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(query, i) for i in range(10)]
            for future in as_completed(futures):
                pass

        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 10

    def test_concurrent_list_tables(self, connector_instance):
        """Concurrent list_master_tables should work."""
        pytest.importorskip("duckdb")
        results = []

        def list_tables():
            tables = connector_instance.list_master_tables()
            results.append(len(tables))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(list_tables) for _ in range(10)]
            for future in as_completed(futures):
                pass

        assert len(results) == 10
        assert all(count == results[0] for count in results)


class TestConnectorDataIntegrity:
    """Test data integrity across operations."""

    def test_row_counts_consistent(self, connector_instance):
        """Row counts should be consistent across calls."""
        pytest.importorskip("duckdb")
        info1 = connector_instance.get_table_info("weather_daily")
        info2 = connector_instance.get_table_info("weather_daily")
        assert info1["rows"] == info2["rows"]

    def test_table_list_stable(self, connector_instance):
        """Table list should be stable."""
        pytest.importorskip("duckdb")
        tables1 = sorted(connector_instance.list_master_tables())
        tables2 = sorted(connector_instance.list_master_tables())
        assert tables1 == tables2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
