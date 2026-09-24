"""
engine.data_connector
=====================

Processing Engine Data Connector for Eco Nojin.

This module connects all processing engines and scientific motors
to the consolidated DataHub, providing a unified data access layer.

Architecture:
    Processing Engine (Hydroma, Simulation, MRV)
        ↓
    DataConnector (this module)
        ↓
    DataHub (database.hub)
        ↓
    Consolidated Databases:
        - eco_nojin_master.duckdb (analytics, 132 tables)
        - econojin.db (transactional, 62 tables)
        - eco_manual_v1.sqlite (reference, 18 tables)

Usage:
    from engine.data_connector import connector

    # Get climate data from master DuckDB
    df = connector.get_climate_data(station_id=123, year=2020)

    # Get user data from transactional DB
    user = connector.get_user(user_id="abc")

    # Get scientific reference data
    crop_params = connector.get_crop_parameters("wheat")

Author: Eco Nojin Architecture Team
"""

import sys
from pathlib import Path
from typing import Any, Optional

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
import pandas as pd

from database.hub import hub
from services.security.query_safe import (
    safe_execute,
    safe_dynamic_select,
    build_where_clause,
    _safe_ident,
)

logger = logging.getLogger(__name__)


class DataConnector:
    """
    Unified data access for processing engines.

    Provides domain-specific methods for scientific computations,
    abstracting away the underlying database complexity.
    """

    def __init__(self):
        self.hub = hub

    # ── DuckDB (Analytics) Methods ──────────────────────────────

    def get_climate_data(
        self,
        station_id: int | None = None,
        year: int | None = None,
        limit: int = 10000,
    ) -> Any:
        """
        Get climate data from master DuckDB.

        Args:
            station_id: Optional station ID filter
            year: Optional year filter
            limit: Maximum rows to return

        Returns:
            pandas DataFrame with climate data
        """
        conn = self.hub.get_duckdb("master")

        conditions = {}
        if station_id is not None:
            conditions["site_id"] = station_id
        if year is not None:
            conditions["year"] = year

        query = "SELECT * FROM weather_daily"
        clause, params = self._build_where_clause(conditions)
        query += clause + " LIMIT ?"
        params.append(limit)

        try:
            result = conn.execute(query, params)
            return result.fetchdf()
        except Exception as e:
            logger.error(f"get_climate_data failed: {e}")
            raise
        finally:
            conn.close()

    def get_crop_parameters(self, crop_name: str) -> dict:
        """
        Get crop parameters from master DuckDB.

        Args:
            crop_name: Crop name to lookup

        Returns:
            Dictionary with crop parameters
        """
        conn = self.hub.get_duckdb("master")
        try:
            result = conn.execute(
                "SELECT * FROM crop_parameters WHERE crop_name = ? LIMIT 1",
                [crop_name],
            ).fetchone()
            if result:
                return dict(result)
            return {}
        except Exception as e:
            logger.error(f"get_crop_parameters failed: {e}")
            return {}
        finally:
            conn.close()

    def get_soil_parameters(self, soil_type: str) -> dict:
        """
        Get soil parameters from master DuckDB.

        Args:
            soil_type: Soil type to lookup

        Returns:
            Dictionary with soil parameters
        """
        conn = self.hub.get_duckdb("master")
        try:
            result = conn.execute(
                "SELECT * FROM soil_parameters WHERE soil_type = ? LIMIT 1",
                [soil_type],
            ).fetchone()
            if result:
                return dict(result)
            return {}
        except Exception as e:
            logger.error(f"get_soil_parameters failed: {e}")
            return {}
        finally:
            conn.close()

    def get_elevation_data(self, lat: float, lon: float, radius_km: float = 5.0) -> list:
        """
        Get elevation data around a point.

        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers

        Returns:
            List of elevation points
        """
        conn = self.hub.get_duckdb("master")
        try:
            result = conn.execute(
                """
                SELECT lat, lon, elevation
                FROM elevation_grid
                WHERE lat BETWEEN ? - ?/111.0 AND ? + ?/111.0
                  AND lon BETWEEN ? - ?/(111.0 * COS(RADIANS(?))) AND ? + ?/(111.0 * COS(RADIANS(?)))
                LIMIT 10000
                """,
                [lat, lat, radius_km, radius_km, lon, lon, radius_km, radius_km, lat, lat],
            ).fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"get_elevation_data failed: {e}")
            return []
        finally:
            conn.close()

    # ── SQLite (Transactional) Methods ──────────────────────────

    def get_user(self, user_id: str) -> dict | None:
        """
        Get user from transactional SQLite.

        Args:
            user_id: User ID

        Returns:
            User dict or None
        """
        conn = self.hub.get_sqlite()
        try:
            result = conn.execute(
                "SELECT * FROM users WHERE id = ? LIMIT 1",
                [user_id],
            ).fetchone()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"get_user failed: {e}")
            return None
        finally:
            conn.close()

    def get_farm(self, farm_id: int) -> dict | None:
        """
        Get farm from transactional SQLite.

        Args:
            farm_id: Farm ID

        Returns:
            Farm dict or None
        """
        conn = self.hub.get_sqlite()
        try:
            result = conn.execute(
                "SELECT * FROM farms WHERE id = ? LIMIT 1",
                [farm_id],
            ).fetchone()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"get_farm failed: {e}")
            return None
        finally:
            conn.close()

    def list_farms(self, user_id: str) -> list[dict]:
        """
        List farms for a user.

        Args:
            user_id: User ID

        Returns:
            List of farm dicts
        """
        conn = self.hub.get_sqlite()
        try:
            result = conn.execute(
                "SELECT * FROM farms WHERE user_id = ?",
                [user_id],
            ).fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"list_farms failed: {e}")
            return []
        finally:
            conn.close()

    # ── Reference Data (Manual) Methods ─────────────────────────

    def get_crop_parameters_manual(self, crop_name: str) -> dict:
        """
        Get crop parameters from manual reference SQLite.

        Args:
            crop_name: Crop name

        Returns:
            Dictionary with crop parameters
        """
        conn = self.hub.get_sqlite("manual")
        try:
            result = conn.execute(
                "SELECT * FROM crop_parameters WHERE crop_name = ? LIMIT 1",
                [crop_name],
            ).fetchone()
            return dict(result) if result else {}
        except Exception as e:
            logger.error(f"get_crop_parameters_manual failed: {e}")
            return {}
        finally:
            conn.close()

    def get_soil_parameters_manual(self, soil_type: str) -> dict:
        """
        Get soil parameters from manual reference SQLite.

        Args:
            soil_type: Soil type

        Returns:
            Dictionary with soil parameters
        """
        conn = self.hub.get_sqlite("manual")
        try:
            result = conn.execute(
                "SELECT * FROM soil_parameters WHERE soil_type = ? LIMIT 1",
                [soil_type],
            ).fetchone()
            return dict(result) if result else {}
        except Exception as e:
            logger.error(f"get_soil_parameters_manual failed: {e}")
            return {}
        finally:
            conn.close()

    # ── DataHub Methods ─────────────────────────────────────────

    def get_table_list(self, db_key: str = "master") -> list[str]:
        """
        List tables in a DataHub database.

        Args:
            db_key: Database key (master, transactional, manual)

        Returns:
            List of table names
        """
        conn = self.hub.get_duckdb(db_key)
        try:
            result = conn.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'main'
                ORDER BY table_name
                """
            ).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"get_table_list failed: {e}")
            return []
        finally:
            conn.close()

    def get_table_info(self, table_name: str, db_key: str = "master") -> dict:
        """
        Get schema information for a table.

        Args:
            table_name: Table name
            db_key: Database key

        Returns:
            Dictionary with table info
        """
        conn = self.hub.get_duckdb(db_key)
        try:
            safe_table = _safe_ident(table_name)
            columns = conn.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = ?
                ORDER BY ordinal_position
                """,
                [table_name],
            ).fetchall()

            row_count = conn.execute(
                'SELECT COUNT(*) FROM "' + _safe_ident(table_name) + '"'
            ).fetchone()[0]

            return {
                "table": table_name,
                "columns": [{"name": c[0], "type": c[1]} for c in columns],
                "rows": row_count,
            }
        except Exception as e:
            logger.error(f"get_table_info failed: {e}")
            return {"table": table_name, "error": str(e)}
        finally:
            conn.close()

    def query_master(
        self,
        query: str,
        params: list | None = None,
    ) -> list[dict]:
        """
        Execute a parameterized query on master DuckDB.

        Args:
            query: SQL query with ? placeholders
            params: Parameters to bind

        Returns:
            List of result dicts
        """
        conn = self.hub.get_duckdb("master")
        try:
            result = conn.execute(query, params or []).fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"query_master failed: {e}")
            raise
        finally:
            conn.close()

    def query_transactional(
        self,
        query: str,
        params: list | None = None,
    ) -> list[dict]:
        """
        Execute a parameterized query on transactional SQLite.

        Args:
            query: SQL query with ? placeholders
            params: Parameters to bind

        Returns:
            List of result dicts
        """
        conn = self.hub.get_sqlite()
        try:
            result = conn.execute(query, params or []).fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"query_transactional failed: {e}")
            raise
        finally:
            conn.close()


# Global connector instance
connector = DataConnector()

__all__ = ["DataConnector", "connector"]