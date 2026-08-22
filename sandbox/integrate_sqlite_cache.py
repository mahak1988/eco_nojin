"""
API Integration: Add SQLite caching to FastAPI endpoint
========================================================

Run this script to patch the phase13_api_endpoint.py with SQLite caching.
"""
from pathlib import Path

API_FILE = Path(r"D:\eco_nojin\sandbox\phase13_api_endpoint.py")


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
            lines = content[idx:].split("\n")
            insert_line = 0
            for i, line in enumerate(lines):
                if line and not line.startswith(("from ", "import ", "    ", "\t", ")", ",")):
                    insert_line = i
                    break
            insert_idx = idx + sum(len(l) + 1 for l in lines[:insert_line])
            content = content[:insert_idx] + import_block + "\n" + content[insert_idx:]
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
    \"\"\"Get cache statistics.\"\"\"
    return {
        "cached_analyses": len(_cache),
        "cache_keys": list(_cache.keys()),
    }"""
    
    new_stats = """@app.get("/api/v1/cache/stats", summary="Cache Statistics")
def cache_stats():
    \"\"\"Get cache statistics (memory + SQLite).\"\"\"
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
    \"\"\"Clear all cached analyses.\"\"\"
    count = len(_cache)
    _cache.clear()
    return {"message": f"Cleared {count} cached analyses"}"""
    
    new_clear = """@app.delete("/api/v1/cache", summary="Clear Cache")
def clear_cache():
    \"\"\"Clear all cached analyses (memory + SQLite).\"\"\"
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
        print(f"\n💾 Updated: {API_FILE}")
        return True
    else:
        print("\n⚠️  No changes needed")
        return False


if __name__ == "__main__":
    integrate()
    print("\n🚀 Next: Run API server with: python sandbox/phase13_api_endpoint.py")
