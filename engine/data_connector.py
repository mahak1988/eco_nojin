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
import re
from pathlib import Path
from typing import Optional, Any, Dict, List
from contextlib import contextmanager

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.hub import hub
from services.security.query_safe import _safe_ident

import logging
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
        params = []
        if station_id is not None:
            conditions.append("site_id = ?")
            params.append(station_id)
        if year is not None:
            conditions.append("year = ?")
            params.append(year)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        query = """
            SELECT * FROM weather_daily
            %s
            LIMIT 10000
        """ % where_clause

        try:
            return conn.execute(query, params).fetchdf()
        except Exception:
            return conn.execute(query, params).fetchall()
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
            logger.info(f"Warning: get_crop_parameters failed: {e}")
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


    def _extract_table_names(self, query: str) -> set[str]:
        """Extract table names referenced in a SELECT/WITH query (best-effort).

        Uses a simple regex to identify tokens following FROM and JOIN keywords.
        This is not a full SQL parser but is sufficient for whitelist checks
        when combined with a strict identifier allowlist.
        """
        text = query
        pattern = re.compile(
            r"\b(?:FROM|JOIN)\s+(?:`?\"?([A-Za-z_][A-Za-z0-9_]*)\`?\"?\.)?(?:`?\"?([A-Za-z_][A-Za-z0-9_]*)\`?\"?|\`?\"?([A-Za-z_][A-Za-z0-9_]*)\`?\"?)",
            re.IGNORECASE,
        )
        names: set[str] = set()
        for match in pattern.finditer(text):
            for group in match.groups():
                if group:
                    names.add(group.lower())
        return names

    def _sanitize_sql(self, query: str) -> str:
        """
        Sanitize SQL query to prevent injection attacks.

        Security measures:
        - Only SELECT/WITH statements allowed
        - Dangerous keywords (DROP, DELETE, etc.) are blocked
        - SQL comments (--, /*, ;) are not allowed
        - Table names MUST appear in the analytics whitelist
          (defence-in-depth on top of the keyword blacklist)
        """
        if not isinstance(query, str):
            raise ValueError("query must be a string")
        if len(query) > 10_000:
            raise ValueError("query too long")
        query_upper = query.upper().strip()

        # Block dangerous keywords (defence-in-depth on top of whitelist)
        dangerous_keywords = [
            'DROP TABLE', 'DROP DATABASE', 'DELETE FROM',
            'UPDATE ', 'INSERT INTO', 'ALTER TABLE',
            'TRUNCATE', 'CREATE TABLE', 'CREATE DATABASE',
            'GRANT', 'REVOKE', 'EXECUTE', 'EXEC(',
            'XP_CMDSHELL', 'INFORMATION_SCHEMA',
            'WAITFOR DELAY', 'UNION SELECT',
            'SHUTDOWN', 'LOAD_FILE', 'INTO OUTFILE',
            'INTO DUMPFILE', 'PG_SLEEP', 'PG_CATALOG',
        ]

        for keyword in dangerous_keywords:
            if keyword in query_upper:
                logger.warning("SQL injection attempt blocked: %s in query", keyword)
                raise ValueError(
                    f"Dangerous SQL statement detected: {keyword}. "
                    "Only SELECT queries are allowed in analytics."
                )

        # Block comment-based injection
        if '--' in query or '/*' in query or ';' in query:
            logger.warning("SQL injection attempt blocked: comment/semicolon detected")
            raise ValueError(
                "SQL comments (;, --, /*) are not allowed in analytics queries. "
                "Use parameterized queries instead."
            )

        # Only SELECT/WITH allowed
        if not query_upper.startswith('SELECT') and not query_upper.startswith('WITH'):
            raise ValueError(
                "Only SELECT/WITH queries are allowed in execute_analytics_query"
            )

        # Whitelist tables referenced in the query
        tables = self._extract_table_names(query)
        unknown = tables - self.ALLOWED_ANALYTICS_TABLES
        if unknown:
            logger.warning(
                "Analytics query references non-whitelisted tables: %s",
                ", ".join(sorted(unknown)),
            )
            raise ValueError(
                f"Table(s) not in analytics whitelist: {sorted(unknown)}. "
                "Allowed: " + ", ".join(sorted(self.ALLOWED_ANALYTICS_TABLES))
            )

        return query

    # Whitelist of tables available to ad-hoc analytics queries on master DuckDB.
    # Restricting to these is safer than a keyword blacklist alone.
    ALLOWED_ANALYTICS_TABLES: set[str] = {
        "weather_daily",
        "climate_normals_monthly",
        "crop_water_parameters",
        "ref_sites",
        "ref_soils",
        "ref_species",
        "ref_climate_requirements",
        "ref_crop_calendar",
        "ref_indices_registry",
        "ref_decision_engine",
        "data_weather_daily",
        "data_weather_history_annual",
        "climate_disasters",
        "v_all_indices",
        "v_crop_climate_matrix",
        "v_drought_indices",
    }


    def execute_analytics_query(self, query: str) -> Any:
        """
        Execute arbitrary analytics query on master DuckDB.
        
        Security:
        - Query is sanitized BEFORE execution to prevent SQL injection
        - Only SELECT/WITH statements allowed
        - Dangerous keywords (DROP, DELETE, etc.) are blocked
        
        Args:
            query: SQL query (must be SELECT or WITH statement)
        
        Returns:
            Query result as pandas DataFrame or list of tuples
        """
        # STEP 1: SQL Injection Protection (BEFORE getting connection)
        try:
            query = self._sanitize_sql(query)
        except ValueError as e:
            import logging
            logging.getLogger(__name__).error(f"SQL injection attempt blocked: {e}")
            raise
        
        # STEP 2: Get connection
        conn = self.hub.get_duckdb("master")
        
        # STEP 3: Execute query
        try:
            return conn.execute(query).fetchdf()
        except Exception as e:
            # Fallback to fetchall for non-SELECT queries
            try:
                return conn.execute(query).fetchall()
            except Exception as e2:
                import logging
                logging.getLogger(__name__).error(f"Query execution failed: {e2}")
                raise


    def get_crop_calendar(self, province: Optional[str] = None) -> List[Dict]:
        """Get crop calendar data from manual SQLite."""

        # SQL Injection Protection
        try:
            query = self._sanitize_sql(query)
        except ValueError as e:
            logger.error(f"SQL injection attempt blocked: {e}")
            raise

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
            columns = conn.execute("\n                SELECT column_name, data_type\n                FROM information_schema.columns\n                WHERE table_name = '{}'\n                ORDER BY ordinal_position\n            ".format(_safe_ident(table_name))).fetchall()

            row_count = conn.execute(
                'SELECT COUNT(*) FROM "{}"'.format(_safe_ident(table_name))
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
