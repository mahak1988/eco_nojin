"""Persistent scientific cache for weather and satellite data.

Provides SQLite-backed disk cache for external data sources to avoid
redundant API calls during benchmark execution. Cache keys incorporate
all parameters that affect the result to ensure correctness.

Cache entries store:
- Raw API responses (weather JSON, STAC search results)
- Processed data (downloaded assets, computed values)
- Provenance metadata (source, version, timestamp)
- Status (SUCCESS, PARTIAL, FAILED, NOT_FOUND, RATE_LIMITED, NETWORK_ERROR)

Cache is never used to store synthetic data as if it were real.
All entries are tagged with their source and quality status.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

#: Valid cache entry statuses.
CACHE_STATUSES = frozenset(
    {
        "SUCCESS",
        "PARTIAL",
        "NOT_FOUND",
        "RATE_LIMITED",
        "NETWORK_ERROR",
        "INVALID_RESPONSE",
        "FAILED",
    }
)

CACHE_DB_PATH = Path("engine/reports/data/stage38_cache.sqlite")


def _make_key(*parts: str) -> str:
    """Create a deterministic SHA-256 cache key from string parts."""
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class ScientificCache:
    """SQLite-backed persistent cache for external scientific data sources.

    Cache keys incorporate provider, endpoint, parameters, coordinates,
    date range, variable list, and unit contract version to ensure that
    different queries never collide.

    Cache entries are never overwritten with synthetic data. Failed
    responses are cached with their error status so that repeated calls
    don't re-attempt known failures (within TTL).
    """

    def __init__(self, db_path: Path | None = None, ttl_seconds: int = 86400) -> None:
        self.db_path = db_path or CACHE_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection that the caller must close."""
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Create cache tables if they don't exist."""
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    params_hash TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    start_date TEXT,
                    end_date TEXT,
                    variables TEXT,
                    unit_contract_version TEXT,
                    source_api_version TEXT,
                    status TEXT NOT NULL,
                    response_json TEXT,
                    fetched_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_expires "
                "ON cache_entries(expires_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_status "
                "ON cache_entries(status)"
            )
            conn.commit()
        finally:
            conn.close()

    def _make_provider_key(
        self,
        provider: str,
        endpoint: str,
        latitude: float | None,
        longitude: float | None,
        start_date: str | None,
        end_date: str | None,
        variables: list[str] | None,
        unit_contract_version: str | None,
    ) -> str:
        """Build a cache key from all parameters that affect the result."""
        return _make_key(
            provider,
            endpoint,
            str(latitude) if latitude is not None else "null",
            str(longitude) if longitude is not None else "null",
            start_date or "null",
            end_date or "null",
            ",".join(sorted(variables)) if variables else "null",
            unit_contract_version or "null",
        )

    def get(
        self,
        provider: str,
        endpoint: str,
        latitude: float | None = None,
        longitude: float | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        variables: list[str] | None = None,
        unit_contract_version: str | None = None,
        source_api_version: str | None = None,
    ) -> dict[str, Any] | None:
        """Retrieve a cache entry if present and not expired.

        Returns None if no entry exists or the entry has expired.
        Expired entries are deleted on retrieval.
        """
        key = self._make_provider_key(
            provider, endpoint, latitude, longitude, start_date, end_date,
            variables, unit_contract_version,
        )
        now = datetime.now(UTC).isoformat()
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT status, response_json, retry_count, expires_at
                FROM cache_entries WHERE key = ?
                """,
                (key,),
            ).fetchone()
            if row is None:
                return None
            status, response_json, retry_count, expires_at = row
            if now >= expires_at:
                conn.execute(
                    "DELETE FROM cache_entries WHERE key = ?", (key,)
                )
                conn.commit()
                return None
            try:
                data = json.loads(response_json) if response_json else {}
            except json.JSONDecodeError:
                data = {}
            return {
                "key": key,
                "status": status,
                "data": data,
                "retry_count": retry_count,
                "provider": provider,
                "endpoint": endpoint,
            }
        finally:
            conn.close()

    def put(
        self,
        provider: str,
        endpoint: str,
        status: str,
        latitude: float | None = None,
        longitude: float | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        variables: list[str] | None = None,
        unit_contract_version: str | None = None,
        source_api_version: str | None = None,
        response_json: dict[str, Any] | None = None,
        retry_count: int = 0,
    ) -> None:
        """Store a cache entry.

        Args:
            provider: Data provider name (e.g. "Open-Meteo", "Planetary Computer").
            endpoint: API endpoint or data source identifier.
            status: One of SUCCESS, PARTIAL, NOT_FOUND, RATE_LIMITED,
                NETWORK_ERROR, INVALID_RESPONSE, FAILED.
            latitude: Site latitude (WGS84 decimal degrees).
            longitude: Site longitude (WGS84 decimal degrees).
            start_date: Inclusive start date (ISO YYYY-MM-DD).
            end_date: Inclusive end date (ISO YYYY-MM-DD).
            variables: List of requested variables.
            unit_contract_version: Version of the unit contract used.
            source_api_version: Version of the source API.
            response_json: Parsed JSON response (or None).
            retry_count: Number of retries attempted.
        """
        if status not in CACHE_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of {sorted(CACHE_STATUSES)}"
            )

        key = self._make_provider_key(
            provider, endpoint, latitude, longitude, start_date, end_date,
            variables, unit_contract_version,
        )
        now = datetime.now(UTC).isoformat()
        expires = datetime.now(UTC) + timedelta(seconds=self.ttl_seconds)
        expires_iso = expires.isoformat()

        response_json_str = (
            json.dumps(response_json, sort_keys=True) if response_json is not None
            else None
        )

        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache_entries
                (key, provider, endpoint, params_hash, latitude, longitude,
                 start_date, end_date, variables, unit_contract_version,
                 source_api_version, status, response_json, fetched_at,
                 expires_at, retry_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key, provider, endpoint, key,
                    latitude, longitude, start_date, end_date,
                    json.dumps(sorted(variables)) if variables else None,
                    unit_contract_version,
                    source_api_version,
                    status,
                    response_json_str,
                    now,
                    expires_iso,
                    retry_count,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, key: str) -> bool:
        """Delete a cache entry. Returns True if the entry existed."""
        conn = self._connect()
        try:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE key = ?", (key,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def clear_expired(self) -> int:
        """Remove all expired cache entries. Returns count removed."""
        now = datetime.now(UTC).isoformat()
        conn = self._connect()
        try:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE expires_at < ?", (now,)
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        conn = self._connect()
        try:
            total = conn.execute(
                "SELECT COUNT(*) FROM cache_entries"
            ).fetchone()[0]
            by_status = dict(
                conn.execute(
                    "SELECT status, COUNT(*) FROM cache_entries GROUP BY status"
                ).fetchall()
            )
            expired = conn.execute(
                "SELECT COUNT(*) FROM cache_entries WHERE expires_at < ?",
                (datetime.now(UTC).isoformat(),),
            ).fetchone()[0]
        finally:
            conn.close()
        return {
            "total_entries": total,
            "by_status": dict(by_status),
            "expired_entries": expired,
        }


__all__ = [
    "ScientificCache",
    "CACHE_STATUSES",
    "CACHE_DB_PATH",
]
