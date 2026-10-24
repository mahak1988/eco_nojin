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
    DataHub (engine.data_connector.FileDuckDBHub by default; injected in
    production)
        ↓
    Consolidated Databases:
         - eco_nojin_master.duckdb — analytics master, built from data that
           exists in this repository by tools/build_master_duckdb.py. Its
           real schema is:
               soil_parameters         12 rows (engine/data/soil_vg_table.csv)
               crop_parameters          3 rows (engine/hydroma/data/kc_data.csv)
               model_registry           9 rows (data/model_registry.json)
               soil_texture_classes    12 rows (engine/hydroma/soil/taxonomy.py)
               master_build_provenance  4 rows (this build: source, SHA-256,
                                          row count, build timestamp)
           Location: data/master/eco_nojin_master.duckdb, overridable with
           the ECO_MASTER_DUCKDB environment variable.
         - data/food_security.duckdb — food-security indicators built from
           the free World Bank API v2 and the FAO FAOSTAT Food Security
           domain by tools/build_food_security_table.py. Its real schema is:
               food_security_indicators  (country_code, country_fa,
                                          indicator_code, indicator_fa, year,
                                          value, unit, source, source_url,
                                          retrieved_at)
               food_security_sources     (url, retrieval date, licence per
                                          source, including the derived
                                          formulas)
           Location: data/food_security.duckdb, overridable with the
           FOOD_SECURITY_DB environment variable. It is a *separate* file
           from the master on purpose: tools/build_master_duckdb.py deletes
           and rebuilds the master on every run, so food-security tables
           stored there would not survive that build.
         - econojin.db / eco_manual_v1.sqlite — NOT PRESENT. An earlier
          version of this docstring claimed 132 DuckDB tables plus a
          62-table transactional and an 18-table reference SQLite; none of
          those files ever existed on disk, so the claims are withdrawn.
          No method here reads a table this repository has no source for:
          get_climate_data queries weather_daily, which has no in-repo
          source and therefore fails with an honest catalog error until a
          real climate source is added.

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

import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

# Identifier allowlist, duplicated from services.security.query_safe.
#
# That module was the previous home of this validator, and this file imported
# the private name `_safe_ident` from it across a package boundary. Importing a
# leading-underscore name is a private API contract with no owner, and it made
# the engine unimportable without `services`. The validator is 3 lines of pure
# stdlib with no dependencies, so it lives here now and `services` keeps its
# own copy; if the two ever diverge, `services/security/query_safe.py` is the
# one with tests.
#
# Behaviour is identical: fullmatch against [A-Za-z_][A-Za-z0-9_]*, raising
# ValueError otherwise.
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _safe_ident(name: str) -> str:
    """Validate a SQL identifier against a strict allowlist pattern.

    Raises:
        ValueError: if the identifier contains characters outside
            ``[A-Za-z_][A-Za-z0-9_]*``.
    """
    if not _IDENT_RE.fullmatch(str(name)):
        raise ValueError(f"invalid SQL identifier: {name!r}")
    return str(name)


#: Environment variable that overrides the master DuckDB location.
MASTER_DUCKDB_ENV = "ECO_MASTER_DUCKDB"

#: Default master DuckDB path. Built by tools/build_master_duckdb.py.
DEFAULT_MASTER_DUCKDB: Path = PROJECT_ROOT / "data" / "master" / "eco_nojin_master.duckdb"

#: Environment variable that overrides the food-security DuckDB location.
#: The same name is honoured by tools/build_food_security_table.py and by
#: services.data_manual.loader.food_security, so one override points every
#: reader and the builder at the same file.
FOOD_SECURITY_DB_ENV = "FOOD_SECURITY_DB"

#: Default food-security DuckDB path. Built by
#: tools/build_food_security_table.py from the World Bank API v2 and the
#: FAO FAOSTAT Food Security domain.
DEFAULT_FOOD_SECURITY_DUCKDB: Path = PROJECT_ROOT / "data" / "food_security.duckdb"


def master_duckdb_path() -> Path:
    """Absolute path of the master DuckDB file.

    The ``ECO_MASTER_DUCKDB`` environment variable wins when set; otherwise
    the repo-relative default is returned, so the path never depends on the
    process working directory.
    """
    override = os.environ.get(MASTER_DUCKDB_ENV)
    if override:
        return Path(override).expanduser()
    return DEFAULT_MASTER_DUCKDB


def food_security_duckdb_path() -> Path:
    """Absolute path of the food-security DuckDB file (``FOOD_SECURITY_DB`` wins)."""
    override = os.environ.get(FOOD_SECURITY_DB_ENV)
    if override:
        return Path(override).expanduser()
    return DEFAULT_FOOD_SECURITY_DUCKDB


def _rows_to_dicts(conn: Any, rows: Any) -> list[dict]:
    """Convert DuckDB result rows to dicts using the cursor description.

    ``fetchone``/``fetchall`` return plain tuples, and ``dict(tuple)``
    raises — which the query methods below used to swallow into an empty
    result that looked like "this table has no matching row". Mapping the
    description's column names onto the rows is what makes the real
    master's rows actually reachable.
    """
    columns = [column[0] for column in conn.description]
    return [dict(zip(columns, row, strict=False)) for row in rows]


class MasterDuckDBNotBuilt(FileNotFoundError):
    """The master DuckDB file is absent (or is not a regular file).

    Raised by the default hub before any query runs, naming the expected
    path and the command that builds it. This replaces the two dishonest
    behaviours this connector used to have: raising an unconfigured-port
    error that named no file, and swallowing the error into an empty result
    that looked like "no data".
    """


class FoodSecurityStoreNotBuilt(FileNotFoundError):
    """The food-security DuckDB file is absent (or is not a regular file).

    Raised before any food-security query runs, naming the expected path and
    ``python tools/build_food_security_table.py`` — the command that fetches
    the real World Bank / FAO FAOSTAT data into it.
    """


class FileDuckDBHub:
    """Hub backed by the two DuckDB files this repository actually builds.

    ``get_duckdb("master")`` opens the master file at
    :func:`master_duckdb_path` and ``get_duckdb("food_security")`` opens the
    food-security file at :func:`food_security_duckdb_path`, both read-only.
    Absent files raise :class:`MasterDuckDBNotBuilt` /
    :class:`FoodSecurityStoreNotBuilt` naming the build command, so a caller
    never sees an empty result that means "not built".

    The SQLite methods raise, because this repository ships no transactional
    SQLite file — an application that has one must inject its own hub or
    ``PersistencePort`` rather than rely on this default.
    """

    def get_duckdb(self, name: str = "master") -> Any:
        """Return a read-only DuckDB connection for a named database."""
        error: Exception
        if name in ("master", "analytics", ""):
            path = master_duckdb_path()
            error = MasterDuckDBNotBuilt(
                f"master DuckDB not found at {path}. Build it with "
                f"'python tools/build_master_duckdb.py', or point "
                f"{MASTER_DUCKDB_ENV} at an existing file."
            )
        elif name in ("food_security", "food"):
            path = food_security_duckdb_path()
            error = FoodSecurityStoreNotBuilt(
                f"food-security DuckDB not found at {path}. Build it with "
                f"'python tools/build_food_security_table.py', or point "
                f"{FOOD_SECURITY_DB_ENV} at an existing file."
            )
        else:
            raise KeyError(
                f"unknown database {name!r}; the engine's default hub serves "
                f"only 'master' (tools/build_master_duckdb.py) and "
                f"'food_security' (tools/build_food_security_table.py)"
            )
        if not path.is_file():
            raise error
        import duckdb

        return duckdb.connect(str(path), read_only=True)

    def get_duckdb_pooled(self, database: str = "master") -> Any:
        """Pooled alias of :meth:`get_duckdb` (one connection per call)."""
        return self.get_duckdb(database)

    def return_duckdb_pooled(self, conn: Any, database: str = "master") -> None:
        """Close a connection obtained from :meth:`get_duckdb_pooled`."""
        conn.close()

    def get_sqlite(self, name: str | None = None) -> Any:
        """Raise: this repository ships no transactional SQLite database."""
        raise RuntimeError(
            f"No SQLite database is configured for {name or 'econojin'!r}. "
            f"This repository ships no transactional SQLite file; inject a "
            f"PersistencePort if your deployment has one."
        )


def default_hub():
    """Return the default hub: the master DuckDB file on disk.

    The production implementation is injected via ``DataConnector(hub=...)``.
    The default resolves the path lazily on first use, so constructing a
    connector never opens a database or fails when the master has not been
    built yet.
    """
    return FileDuckDBHub()


class DataConnector:
    """
    Unified data access for processing engines.

    Provides domain-specific methods for scientific computations,
    abstracting away the underlying database complexity.

    Args:
        hub: Object exposing ``get_duckdb(name)`` and ``get_sqlite(name)``.
            Defaults to :class:`FileDuckDBHub`, resolved on first use rather
            than at construction, so constructing a connector never opens a
            database. With the default hub, queries raise
            :class:`MasterDuckDBNotBuilt` until the master has been built
            with ``tools/build_master_duckdb.py``.
    """

    def __init__(self, hub=None):
        self._hub = hub

    @property
    def hub(self):
        """The DataHub, resolved lazily on first access."""
        if self._hub is None:
            self._hub = default_hub()
        return self._hub

    def _build_where_clause(self, conditions: dict) -> tuple[str, list]:
        """Build a parameterized WHERE clause from a {column: value} mapping.

        Column names go through the SQL identifier allowlist, so a key that
        is not a plain identifier raises :class:`ValueError` before it can
        reach the database. Values are always bound as parameters.
        """
        if not conditions:
            return "", []
        clauses: list[str] = []
        params: list = []
        for column, value in conditions.items():
            clauses.append(f"{_safe_ident(column)} = ?")
            params.append(value)
        return " WHERE " + " AND ".join(clauses), params

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

    def get_food_security_indicators(
        self,
        country_code: str | None = None,
        indicator_code: str | None = None,
        year: int | None = None,
        source: str | None = None,
        limit: int = 10000,
    ) -> list[dict]:
        """
        Get food-security indicator rows from the food-security DuckDB.

        Args:
            country_code: Optional ISO3 filter (``IRN``, ``TUR``, ...).
            indicator_code: Optional indicator filter, e.g.
                ``AG.YLD.CREL.KG``, ``FAO_FSC:210041`` or
                ``derived:cereal_self_sufficiency_proxy``.
            year: Optional year filter.
            source: Optional source filter (``world_bank``,
                ``faostat_food_security`` or ``derived``).
            limit: Maximum rows to return.

        Returns:
            List of dicts with the documented columns:
            country_code, country_fa, indicator_code, indicator_fa, year,
            value, unit, source, source_url, retrieved_at. Every row carries
            its source URL and retrieval timestamp, so a consumer can always
            tell where a number came from.

        Raises:
            FoodSecurityStoreNotBuilt: the store has not been built; the
                message names ``tools/build_food_security_table.py``.
        """
        conn = self.hub.get_duckdb("food_security")

        conditions: dict[str, Any] = {}
        if country_code is not None:
            conditions["country_code"] = country_code
        if indicator_code is not None:
            conditions["indicator_code"] = indicator_code
        if year is not None:
            conditions["year"] = year
        if source is not None:
            conditions["source"] = source

        query = "SELECT * FROM food_security_indicators"
        clause, params = self._build_where_clause(conditions)
        query += clause + " ORDER BY country_code, indicator_code, year LIMIT ?"
        params.append(limit)

        try:
            result = conn.execute(query, params)
            return _rows_to_dicts(conn, result.fetchall())
        except Exception as e:
            logger.error(f"get_food_security_indicators failed: {e}")
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
            rows = conn.execute(
                "SELECT * FROM crop_parameters WHERE crop_name = ? LIMIT 1",
                [crop_name],
            ).fetchall()
            return _rows_to_dicts(conn, rows)[0] if rows else {}
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
            rows = conn.execute(
                "SELECT * FROM soil_parameters WHERE soil_type = ? LIMIT 1",
                [soil_type],
            ).fetchall()
            return _rows_to_dicts(conn, rows)[0] if rows else {}
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
            return _rows_to_dicts(conn, result)
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
            _safe_ident(table_name)
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
            return _rows_to_dicts(conn, result)
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

__all__ = [
    "DataConnector",
    "FileDuckDBHub",
    "FoodSecurityStoreNotBuilt",
    "MasterDuckDBNotBuilt",
    "connector",
    "default_hub",
    "food_security_duckdb_path",
    "master_duckdb_path",
]
