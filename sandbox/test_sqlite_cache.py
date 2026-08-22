"""
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
    print(f"\n✅ Database: {cache.db_path}")
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
    print("\n📥 Retrieving entries:")
    for name, _, _, expected_wbi, _ in regions:
        cached = cache.get(name, "wheat")
        if cached:
            actual_wbi = cached["wbi"]["wbi"]
            match = "✅" if actual_wbi == expected_wbi else "❌"
            print(f"   {match} {name}: WBI={actual_wbi}")
        else:
            print(f"   ❌ {name}: not found")
    
    # Stats
    print("\n📊 Cache Stats:")
    stats = cache.stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    # Cleanup
    cache.clear_all()
    print(f"\n✅ Cleaned up cache")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
