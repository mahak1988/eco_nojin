"""
SQLite Cache for Analysis Results
=================================

جایگزین PostgreSQL: SQLite بدون نیاز به Docker یا server

Features:
- Built-in (Python استاندارد، بدون install)
- File-based (cache.db)
- TTL support
- Thread-safe
- Production-ready (Instagram, WhatsApp, Firefox از SQLite استفاده می‌کنند)
"""
import structlog

logger = structlog.get_logger()
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


class SQLiteCache:
    """
    SQLite-based cache for analysis results.
    
    Usage:
        cache = SQLiteCache()  # default: cache.db in project root
        cache.store("Iran_Isfahan", "wheat", result_dict)
        result = cache.get("Iran_Isfahan", "wheat")
        cache.clear_expired()
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS analysis_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_name TEXT NOT NULL,
        crop_type TEXT NOT NULL,
        lat REAL,
        lon REAL,
        koppen TEXT,
        wbi TEXT,
        ewsi TEXT,
        hyrue TEXT,
        ecsi TEXT,
        hdvi TEXT,
        epia TEXT,
        hpheno TEXT,
        esri TEXT,
        hlhs TEXT,
        execution_time_ms REAL,
        model_version TEXT,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        warnings TEXT,
        UNIQUE(region_name, crop_type, model_version)
    );
    
    CREATE INDEX IF NOT EXISTS idx_region ON analysis_cache(region_name, crop_type);
    CREATE INDEX IF NOT EXISTS idx_expires ON analysis_cache(expires_at);
    """

    def __init__(
        self,
        db_path: Path | None = None,
        model_version: str = "1.0.0",
    ):
        if db_path is None:
            # Default: D:\eco_nojin\data\cache.db
            db_path = Path(__file__).parent.parent.parent / "data" / "cache.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.model_version = model_version
        self._lock = threading.Lock()

        # Initialize schema
        with self._connect() as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        """Create a connection with WAL mode for better concurrency."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30,
            check_same_thread=False,
        )
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _Integerize(self, obj: Any) -> str:
        """Serialize Python object to JSON string."""
        if obj is None:
            return None
        try:
            return json.dumps(obj, ensure_ascii=False)
        except (TypeError, ValueError):
            return json.dumps(str(obj))

    def _deIntegerize(self, s: str) -> Any:
        """DeIntegerize JSON string to Python object."""
        if s is None:
            return None
        try:
            return json.loads(s)
        except (json.JSONDecodeError, TypeError):
            return None

    def store(
        self,
        region_name: str,
        crop_type: str,
        result: dict[str, Any],
        lat: float = 0.0,
        lon: float = 0.0,
        ttl_hours: int = 24,
    ) -> None:
        """Store analysis result in cache."""
        with self._lock:
            now = datetime.now(UTC)
            expires = now + timedelta(hours=ttl_hours)

            with self._connect() as conn:
                sql = """
                    INSERT OR REPLACE INTO analysis_cache
                    (region_name, crop_type, lat, lon,
                     koppen, wbi, ewsi, hyrue, ecsi, hdvi,
                     epia, hpheno, esri, hlhs,
                     execution_time_ms, model_version,
                     created_at, expires_at, warnings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                conn.execute(sql, (
                    region_name, crop_type, lat, lon,
                    self._Integerize(result.get("koppen")),
                    self._Integerize(result.get("wbi")),
                    self._Integerize(result.get("ewsi")),
                    self._Integerize(result.get("hyrue")),
                    self._Integerize(result.get("ecsi")),
                    self._Integerize(result.get("hdvi")),
                    self._Integerize(result.get("epia")),
                    self._Integerize(result.get("hpheno")),
                    self._Integerize(result.get("esri")),
                    self._Integerize(result.get("hlhs")),
                    result.get("execution_time_ms"),
                    self.model_version,
                    now.isoformat(),
                    expires.isoformat(),
                    self._Integerize(result.get("warnings", [])),
                ))
                conn.commit()

    def get(self, region_name: str, crop_type: str) -> dict[str, Any] | None:
        """Retrieve analysis result from cache."""
        now = datetime.now(UTC)

        with self._connect() as conn:
            cur = conn.execute("""
                SELECT * FROM analysis_cache
                WHERE region_name = ? AND crop_type = ? AND model_version = ?
                LIMIT 1
            """, (region_name, crop_type, self.model_version))

            row = cur.fetchone()
            if not row:
                return None

            # Check expiration
            expires_at = datetime.fromisoformat(row["expires_at"])
            if expires_at < now:
                conn.execute(
                    "DELETE FROM analysis_cache WHERE id = ?",
                    (row["id"],)
                )
                conn.commit()
                return None

            return {
                "region_name": row["region_name"],
                "crop_type": row["crop_type"],
                "lat": row["lat"],
                "lon": row["lon"],
                "koppen": self._deIntegerize(row["koppen"]),
                "wbi": self._deIntegerize(row["wbi"]),
                "ewsi": self._deIntegerize(row["ewsi"]),
                "hyrue": self._deIntegerize(row["hyrue"]),
                "ecsi": self._deIntegerize(row["ecsi"]),
                "hdvi": self._deIntegerize(row["hdvi"]),
                "epia": self._deIntegerize(row["epia"]),
                "hpheno": self._deIntegerize(row["hpheno"]),
                "esri": self._deIntegerize(row["esri"]),
                "hlhs": self._deIntegerize(row["hlhs"]),
                "execution_time_ms": row["execution_time_ms"],
                "warnings": self._deIntegerize(row["warnings"]) or [],
                "cached": True,
                "cached_at": row["created_at"],
            }

    def clear_expired(self) -> int:
        """Remove expired cache entries."""
        now = datetime.now(UTC)
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM analysis_cache WHERE expires_at < ?",
                (now.isoformat(),)
            )
            conn.commit()
            return cur.rowcount

    def clear_all(self) -> int:
        """Clear all cache entries."""
        with self._lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM analysis_cache")
            conn.commit()
            return cur.rowcount

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        now = datetime.now(UTC)
        with self._connect() as conn:
            cur = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN expires_at < ? THEN 1 ELSE 0 END) as expired
                FROM analysis_cache
            """, (now.isoformat(),))
            row = cur.fetchone()

            return {
                "backend": "sqlite",
                "db_path": str(self.db_path),
                "db_size_mb": round(self.db_path.stat().st_size / 1024 / 1024, 2) if self.db_path.exists() else 0,
                "total_entries": row["total"],
                "expired_entries": row["expired"],
                "active_entries": row["total"] - row["expired"],
                "model_version": self.model_version,
            }

    def list_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        """List all cache entries."""
        with self._connect() as conn:
            cur = conn.execute("""
                SELECT region_name, crop_type, model_version, created_at, expires_at
                FROM analysis_cache
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]


def test_cache():
    """Test the SQLite cache."""
    logger.info("=" * 80)
    logger.info("🧪 SQLite Cache Test")
    logger.info("=" * 80)

    cache = SQLiteCache()
    logger.info(f"✅ Database: {cache.db_path}")

    # Store test
    test_result = {
        "koppen": {"code": "Csa", "description": "Mediterranean"},
        "wbi": {"wbi": 68.7, "classification": "Water-Crisis"},
        "ewsi": {"mean": 0.62},
        "hyrue": {"yield_t_ha": 6.91},
        "ecsi": {"delta_soc": 0.88},
        "hdvi": {"hdvi": 2.32},
        "epia": {"recommendation": "Irrigate 5mm"},
        "hpheno": {"los_days": 160},
        "esri": {"mean_esri": 0.15},
        "hlhs": {"hlhs": 54.4},
        "execution_time_ms": 100.0,
        "warnings": [],
    }

    cache.store("Test_Region", "wheat", test_result, lat=32.65, lon=51.67)
    logger.info("✅ Stored test result")

    # Retrieve test
    cached = cache.get("Test_Region", "wheat")
    if cached:
        logger.info(f"✅ Retrieved: WBI={cached['wbi']['wbi']}")
    else:
        logger.info("❌ Retrieve failed")

    # Stats
    stats = cache.stats()
    logger.info(f"📊 Stats: {stats}")

    # Cleanup
    cache.clear_all()
    logger.info("✅ Cleared cache")

    return cache


if __name__ == "__main__":
    test_cache()
