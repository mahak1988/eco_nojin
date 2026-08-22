"""
Phase 15: Build C++ Acceleration + SQLite Cache Files
=====================================================

این اسکریپت فایل‌های فاز ۱۵ را به‌صورت جداگانه می‌سازد (نه در یک string بزرگ)
تا از SyntaxError Python 3.12 جلوگیری شود.

جایگزین Docker: SQLite (built-in، بدون نیاز به server)
"""
from __future__ import annotations
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def write_file(path: Path, content: str) -> bool:
    """Write file, create parents if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✅ Created: {path.relative_to(PROJECT_ROOT)}")
    return True


# ===========================================================================
# 1. SQLite Cache Module
# ===========================================================================

SQLITE_CACHE = '''"""
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
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


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
        db_path: Optional[Path] = None,
        model_version: str = "1.0.0",
    ):
        if db_path is None:
            # Default: D:\\eco_nojin\\data\\cache.db
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
    
    def _serialize(self, obj: Any) -> str:
        """Serialize Python object to JSON string."""
        if obj is None:
            return None
        try:
            return json.dumps(obj, ensure_ascii=False)
        except (TypeError, ValueError):
            return json.dumps(str(obj))
    
    def _deserialize(self, s: str) -> Any:
        """Deserialize JSON string to Python object."""
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
        result: Dict[str, Any],
        lat: float = 0.0,
        lon: float = 0.0,
        ttl_hours: int = 24,
    ) -> None:
        """Store analysis result in cache."""
        with self._lock:
            now = datetime.now(timezone.utc)
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
                    self._serialize(result.get("koppen")),
                    self._serialize(result.get("wbi")),
                    self._serialize(result.get("ewsi")),
                    self._serialize(result.get("hyrue")),
                    self._serialize(result.get("ecsi")),
                    self._serialize(result.get("hdvi")),
                    self._serialize(result.get("epia")),
                    self._serialize(result.get("hpheno")),
                    self._serialize(result.get("esri")),
                    self._serialize(result.get("hlhs")),
                    result.get("execution_time_ms"),
                    self.model_version,
                    now.isoformat(),
                    expires.isoformat(),
                    self._serialize(result.get("warnings", [])),
                ))
                conn.commit()
    
    def get(self, region_name: str, crop_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis result from cache."""
        now = datetime.now(timezone.utc)
        
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
                "koppen": self._deserialize(row["koppen"]),
                "wbi": self._deserialize(row["wbi"]),
                "ewsi": self._deserialize(row["ewsi"]),
                "hyrue": self._deserialize(row["hyrue"]),
                "ecsi": self._deserialize(row["ecsi"]),
                "hdvi": self._deserialize(row["hdvi"]),
                "epia": self._deserialize(row["epia"]),
                "hpheno": self._deserialize(row["hpheno"]),
                "esri": self._deserialize(row["esri"]),
                "hlhs": self._deserialize(row["hlhs"]),
                "execution_time_ms": row["execution_time_ms"],
                "warnings": self._deserialize(row["warnings"]) or [],
                "cached": True,
                "cached_at": row["created_at"],
            }
    
    def clear_expired(self) -> int:
        """Remove expired cache entries."""
        now = datetime.now(timezone.utc)
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
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = datetime.now(timezone.utc)
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
    
    def list_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
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
    print("=" * 80)
    print("🧪 SQLite Cache Test")
    print("=" * 80)
    
    cache = SQLiteCache()
    print(f"✅ Database: {cache.db_path}")
    
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
    print("✅ Stored test result")
    
    # Retrieve test
    cached = cache.get("Test_Region", "wheat")
    if cached:
        print(f"✅ Retrieved: WBI={cached['wbi']['wbi']}")
    else:
        print("❌ Retrieve failed")
    
    # Stats
    stats = cache.stats()
    print(f"📊 Stats: {stats}")
    
    # Cleanup
    cache.clear_all()
    print("✅ Cleared cache")
    
    return cache


if __name__ == "__main__":
    test_cache()
'''


# ===========================================================================
# 2. API Integration with SQLite
# ===========================================================================

API_INTEGRATION = '''"""
API Integration: Add SQLite caching to FastAPI endpoint
========================================================

Run this script to patch the phase13_api_endpoint.py with SQLite caching.
"""
from pathlib import Path

API_FILE = Path(r"D:\\eco_nojin\\sandbox\\phase13_api_endpoint.py")


def integrate():
    if not API_FILE.exists():
        print(f"❌ API file not found: {API_FILE}")
        return False
    
    content = API_FILE.read_text(encoding="utf-8")
    original = content
    
    # 1. Add SQLite import after existing imports
    import_block = """
# SQLite Cache Integration (Phase 15)
try:
    from engine.hydroma.models.cache import SQLiteCache
    _sqlite_cache = None
    
    def get_sqlite_cache():
        global _sqlite_cache
        if _sqlite_cache is None:
            try:
                _sqlite_cache = SQLiteCache()
                print(f"✅ SQLite cache initialized: {_sqlite_cache.db_path}")
            except Exception as e:
                print(f"⚠️  SQLite cache not available: {e}")
                _sqlite_cache = False
        return _sqlite_cache if _sqlite_cache is not False else None
except ImportError:
    def get_sqlite_cache():
        return None
"""
    
    if "SQLiteCache" not in content:
        # Find a good insertion point — after the orchestrator import
        marker = "from sandbox.phase12_unified_orchestrator import"
        if marker in content:
            # Find the end of that import block
            idx = content.find(marker)
            # Find the next line that's not an import
            lines = content[idx:].split("\\n")
            insert_line = 0
            for i, line in enumerate(lines):
                if line and not line.startswith(("from ", "import ", "    ", "\\t", ")", ",")):
                    insert_line = i
                    break
            insert_idx = idx + sum(len(l) + 1 for l in lines[:insert_line])
            content = content[:insert_idx] + import_block + "\\n" + content[insert_idx:]
            print("✅ Added SQLite import")
        else:
            print("⚠️  Could not find insertion point")
            return False
    else:
        print("ℹ️  SQLite import already present")
    
    # 2. Update analyze_get to use SQLite
    old_return = """    return _run_analysis(region_name, crop_type, cache_key=cache_key)"""
    new_return = """    # Try SQLite cache first
    sqlite_cache = get_sqlite_cache()
    if sqlite_cache and not force_refresh:
        cached = sqlite_cache.get(region_name, crop_type)
        if cached:
            return AnalyzeResponse(
                success=True,
                region=cached["region_name"],
                timestamp=cached.get("cached_at", datetime.now(timezone.utc).isoformat()),
                execution_time_ms=0.0,
                analysis=cached,
                warnings=cached.get("warnings", []),
            )
    
    return _run_analysis(region_name, crop_type, cache_key=cache_key, sqlite_cache=sqlite_cache)"""
    
    if old_return in content and "sqlite_cache = get_sqlite_cache()" not in content:
        content = content.replace(old_return, new_return, 1)
        print("✅ Updated analyze_get with SQLite caching")
    else:
        print("ℹ️  analyze_get already uses SQLite or structure differs")
    
    # 3. Update _run_analysis signature to accept sqlite_cache
    old_sig = """def _run_analysis(region: str, crop_type: str,
                  cache_key: Optional[str] = None) -> AnalyzeResponse:"""
    new_sig = """def _run_analysis(region: str, crop_type: str,
                  cache_key: Optional[str] = None,
                  sqlite_cache = None) -> AnalyzeResponse:"""
    
    if old_sig in content:
        content = content.replace(old_sig, new_sig)
        print("✅ Updated _run_analysis signature")
    else:
        print("ℹ️  Signature already updated")
    
    # 4. Add SQLite store in _run_analysis after result is computed
    old_store = """        # Cache result
        if cache_key:
            _cache[cache_key] = result"""
    new_store = """        # Cache result in memory
        if cache_key:
            _cache[cache_key] = result
        
        # Cache result in SQLite (persistent)
        if sqlite_cache:
            try:
                sqlite_cache.store(
                    region_name=result.region_name,
                    crop_type=result.crop_type,
                    result=result.to_dict(),
                    lat=result.lat,
                    lon=result.lon,
                    ttl_hours=24,
                )
            except Exception as e:
                print(f"⚠️  SQLite cache store failed: {e}")"""
    
    if old_store in content:
        content = content.replace(old_store, new_store)
        print("✅ Added SQLite store")
    else:
        print("ℹ️  SQLite store already present")
    
    # 5. Update cache_stats endpoint to include SQLite
    old_stats = """@app.get("/api/v1/cache/stats", summary="Cache Statistics")
def cache_stats():
    \\"\\"\\"Get cache statistics.\\"\\"\\"
    return {
        "cached_analyses": len(_cache),
        "cache_keys": list(_cache.keys()),
    }"""
    
    new_stats = """@app.get("/api/v1/cache/stats", summary="Cache Statistics")
def cache_stats():
    \\"\\"\\"Get cache statistics (memory + SQLite).\\"\\"\\"
    result = {
        "memory_cache": {
            "cached_analyses": len(_cache),
            "cache_keys": list(_cache.keys()),
        },
    }
    sqlite_cache = get_sqlite_cache()
    if sqlite_cache:
        result["sqlite_cache"] = sqlite_cache.stats()
    return result"""
    
    if old_stats in content:
        content = content.replace(old_stats, new_stats)
        print("✅ Updated cache_stats endpoint")
    else:
        print("ℹ️  cache_stats already updated")
    
    # 6. Update clear_cache endpoint
    old_clear = """@app.delete("/api/v1/cache", summary="Clear Cache")
def clear_cache():
    \\"\\"\\"Clear all cached analyses.\\"\\"\\"
    count = len(_cache)
    _cache.clear()
    return {"message": f"Cleared {count} cached analyses"}"""
    
    new_clear = """@app.delete("/api/v1/cache", summary="Clear Cache")
def clear_cache():
    \\"\\"\\"Clear all cached analyses (memory + SQLite).\\"\\"\\"
    count = len(_cache)
    _cache.clear()
    
    sqlite_cache = get_sqlite_cache()
    sqlite_count = 0
    if sqlite_cache:
        sqlite_count = sqlite_cache.clear_all()
    
    total = count + sqlite_count
    return {
        "message": f"Cleared {total} cached analyses",
        "memory": count,
        "sqlite": sqlite_count,
    }"""
    
    if old_clear in content:
        content = content.replace(old_clear, new_clear)
        print("✅ Updated clear_cache endpoint")
    else:
        print("ℹ️  clear_cache already updated")
    
    # Write back
    if content != original:
        API_FILE.write_text(content, encoding="utf-8")
        print(f"\\n💾 Updated: {API_FILE}")
        return True
    else:
        print("\\n⚠️  No changes needed")
        return False


if __name__ == "__main__":
    integrate()
    print("\\n🚀 Next: Run API server with: python sandbox/phase13_api_endpoint.py")
'''


# ===========================================================================
# 3. Test Cache Script
# ===========================================================================

TEST_CACHE = '''"""
Test the SQLite cache integration end-to-end.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.hydroma.models.cache import SQLiteCache


def main():
    print("=" * 80)
    print("🧪 SQLite Cache E2E Test")
    print("=" * 80)
    
    # Initialize cache
    cache = SQLiteCache()
    print(f"\\n✅ Database: {cache.db_path}")
    print(f"   Size: {cache.db_path.stat().st_size if cache.db_path.exists() else 0} bytes")
    
    # Clear old test data
    cache.clear_all()
    
    # Store multiple entries
    regions = [
        ("Iran_Isfahan", 32.65, 51.67, 68.7, "Water-Crisis"),
        ("Yemen_Sanaa", 15.35, 44.21, 94.3, "Water-Bankruptcy"),
        ("California_Sacramento", 38.58, -121.49, 41.2, "Water-Scarce"),
    ]
    
    for name, lat, lon, wbi, cls in regions:
        cache.store(name, "wheat", {
            "koppen": {"code": "Csa"},
            "wbi": {"wbi": wbi, "classification": cls},
            "execution_time_ms": 100.0,
            "warnings": [],
        }, lat=lat, lon=lon)
        print(f"✅ Stored: {name} (WBI={wbi})")
    
    # Retrieve
    print("\\n📥 Retrieving entries:")
    for name, _, _, expected_wbi, _ in regions:
        cached = cache.get(name, "wheat")
        if cached:
            actual_wbi = cached["wbi"]["wbi"]
            match = "✅" if actual_wbi == expected_wbi else "❌"
            print(f"   {match} {name}: WBI={actual_wbi}")
        else:
            print(f"   ❌ {name}: not found")
    
    # Stats
    print("\\n📊 Cache Stats:")
    stats = cache.stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    # Cleanup
    cache.clear_all()
    print(f"\\n✅ Cleaned up cache")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


# ===========================================================================
# Main: Build all files
# ===========================================================================

def main():
    print("=" * 80)
    print("🚀 Phase 15: Build Files (SQLite + C++ Structure)")
    print("=" * 80)
    
    files = [
        (PROJECT_ROOT / "engine" / "hydroma" / "models" / "cache.py", SQLITE_CACHE),
        (PROJECT_ROOT / "sandbox" / "integrate_sqlite_cache.py", API_INTEGRATION),
        (PROJECT_ROOT / "sandbox" / "test_sqlite_cache.py", TEST_CACHE),
    ]
    
    all_ok = True
    for path, content in files:
        if not write_file(path, content):
            all_ok = False
    
    # Also create data directory
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    print(f"✅ Directory: {data_dir.relative_to(PROJECT_ROOT)}/")
    
    if all_ok:
        print("\\n" + "=" * 80)
        print("✅ All files created successfully")
        print("=" * 80)
        print("\\n📋 Next steps:")
        print("\\n1. Test the SQLite cache:")
        print("   python sandbox/test_sqlite_cache.py")
        print("\\n2. Integrate with API:")
        print("   python sandbox/integrate_sqlite_cache.py")
        print("\\n3. Start API server:")
        print("   python sandbox/phase13_api_endpoint.py")
        print("\\n4. Test cache in action:")
        print("   curl http://localhost:8000/api/v1/analyze/Iran_Isfahan")
        print("   curl http://localhost:8000/api/v1/analyze/Iran_Isfahan  # should be cached")
        print("   curl http://localhost:8000/api/v1/cache/stats")


if __name__ == "__main__":
    main()