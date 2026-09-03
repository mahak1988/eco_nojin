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
from typing import Optional, Any, Dict, List
from contextlib import contextmanager

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.hub import hub


class DataConnector:
    """
    Unified data access for processing engines.
    
    Provides domain-specific methods for scientific computations,
    abstracting away the underlying database complexity.
    """

    def __init__(self):
        self.hub = hub

    # ── DuckDB (Analytics) Methods ──────────────────────────────

    def get_climate_data(self, station_id: Optional[int] = None,
                        year: Optional[int] = None) -> Any:
        """
        Get climate data from master DuckDB.
        
        Args:
            station_id: Optional station ID filter
            year: Optional year filter
        
        Returns:
            pandas DataFrame with climate data
        """
        conn = self.hub.get_duckdb("master")

        conditions = []
        if station_id is not None:
            conditions.append(f"site_id = {station_id}")
        if year is not None:
            conditions.append(f"year = {year}")

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT * FROM weather_daily
            {where_clause}
            LIMIT 10000
        """

        try:
            return conn.execute(query).fetchdf()
        except Exception:
            return conn.execute(query).fetchall()
        finally:
            conn.close()

    def get_crop_parameters(self, crop_name: str) -> Dict:
        """
        Get crop water parameters from master DuckDB.
        
        Args:
            crop_name: Name of the crop
        
        Returns:
            Dictionary with crop parameters
        """
        conn = self.hub.get_duckdb("master")

        # Try with parameterized query first, fallback to direct if columns differ
        queries = [
            ("SELECT * FROM crop_water_parameters WHERE LOWER(species_id) = LOWER(?)", [crop_name]),
            ("SELECT * FROM crop_water_parameters WHERE LOWER(scientific_name) LIKE ?", [f"%{crop_name}%"]),
            ("SELECT * FROM crop_water_parameters LIMIT 1", []),  # fallback: get any record
        ]

        try:
            for query, params in queries:
                result = conn.execute(query, params).fetchone()
                if result:
                    if hasattr(result, "keys"):
                        return dict(result)
                    # Convert Row tuple to dict using column names
                    cols = [desc[0] for desc in conn.description]
                    return dict(zip(cols, result))
            return {}
        except Exception as e:
            print(f"Warning: get_crop_parameters failed: {e}")
            return {}
        finally:
            conn.close()

    def get_climate_normals(self, station_id: int) -> List[Dict]:
        """Get monthly climate normals for a station."""
        conn = self.hub.get_duckdb("master")

        try:
            results = conn.execute("""
                SELECT * FROM climate_normals_monthly
                WHERE site_id = ?
                ORDER BY month
            """, [station_id]).fetchall()
            return [dict(r) if hasattr(r, "keys") else r for r in results]
        except Exception:
            return []
        finally:
            conn.close()

    def execute_analytics_query(self, query: str) -> Any:
        """Execute arbitrary analytics query on master DuckDB."""
        conn = self.hub.get_duckdb("master")
        try:
            return conn.execute(query).fetchdf()
        except Exception:
            return conn.execute(query).fetchall()
        finally:
            conn.close()

    # ── SQLite (Manual Reference) Methods ───────────────────────

    def get_crop_calendar(self, province: Optional[str] = None) -> List[Dict]:
        """Get crop calendar data from manual SQLite."""
        conn = self.hub.get_sqlite("manual")

        try:
            cursor = conn.cursor()
            if province:
                cursor.execute(
                    "SELECT * FROM crop_calendar_iran WHERE province = ?",
                    (province,)
                )
            else:
                cursor.execute("SELECT * FROM crop_calendar_iran")

            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_climate_disasters(self, country: Optional[str] = None) -> List[Dict]:
        """Get climate disaster records from manual SQLite."""
        conn = self.hub.get_sqlite("manual")

        try:
            cursor = conn.cursor()
            if country:
                cursor.execute(
                    "SELECT * FROM climate_disasters WHERE country_fa = ?",
                    (country,)
                )
            else:
                cursor.execute("SELECT * FROM climate_disasters")

            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception:
            return []
        finally:
            conn.close()

    # ── SQLAlchemy (Transactional) Methods ──────────────────────

    @contextmanager
    def get_session(self):
        """Get a database session for transactional operations."""
        with self.hub.get_session() as session:
            yield session

    def get_user(self, user_id: str) -> Optional[Any]:
        """Get user by ID from transactional database."""
        try:
            from database.models import User
            with self.hub.get_session() as session:
                return session.query(User).filter_by(id=user_id).first()
        except Exception:
            return None

    def get_land_profile(self, land_id: str) -> Optional[Any]:
        """Get land profile by ID."""
        try:
            from database.models import LandProfile
            with self.hub.get_session() as session:
                return session.query(LandProfile).filter_by(id=land_id).first()
        except Exception:
            return None

    # ── Metadata Methods ───────────────────────────────────────

    def list_master_tables(self) -> List[str]:
        """List all tables in master DuckDB."""
        conn = self.hub.get_duckdb("master")
        try:
            result = conn.execute("""
                SELECT table_name 
                FROM information_schema.tables
                WHERE table_schema = 'main'
                ORDER BY table_name
            """).fetchall()
            return [row[0] for row in result]
        except Exception:
            return []
        finally:
            conn.close()

    def get_table_info(self, table_name: str) -> Dict:
        """Get schema information for a table in master DuckDB."""
        conn = self.hub.get_duckdb("master")
        try:
            columns = conn.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """).fetchall()

            row_count = conn.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]

            return {
                "table": table_name,
                "columns": [{"name": c[0], "type": c[1]} for c in columns],
                "rows": row_count
            }
        except Exception as e:
            return {"table": table_name, "error": str(e)}
        finally:
            conn.close()


# Global connector instance
connector = DataConnector()

__all__ = ["DataConnector", "connector"]
