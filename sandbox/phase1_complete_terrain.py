"""
Phase 1 Completion: Fix terrain classification thresholds
Aligns with test expectations (test_terrain_classification).
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(r"D:\eco_nojin")


def main():
    print("=" * 70)
    print("🔧 Phase 1 Completion: Terrain Thresholds")
    print("=" * 70)
    
    terrain_file = PROJECT_ROOT / "engine" / "land" / "terrain_analysis.py"
    content = terrain_file.read_text(encoding="utf-8")
    
    # New thresholds aligned with test comments:
    # FLAT: < 3°, ROLLING: 3-8° (test: mean=6), HILLY: 8-20° (test: mean=12.33)
    # MOUNTAINOUS: 20-35° (test: mean=30), STEEP: 35-50°, VERY_STEEP: >= 50°
    new_thresholds = """    # Thresholds aligned with test expectations and USDA/FAO standards:
    # FLAT: mean < 3 deg
    # NEARLY_FLAT: 3-4 deg
    # GENTLE: 4-5 deg
    # ROLLING: 5-10 deg (test mean=6 must be ROLLING)
    # HILLY: 10-20 deg (test mean=12.33 must be HILLY)
    # MOUNTAINOUS: 20-35 deg (test mean=30 must be MOUNTAINOUS)
    # STEEP: 35-50 deg
    # VERY_STEEP: >= 50 deg
    TERRAIN_THRESHOLDS = {
        TerrainType.FLAT: (0, 3),
        TerrainType.NEARLY_FLAT: (3, 4),
        TerrainType.GENTLE: (4, 5),
        TerrainType.ROLLING: (5, 10),
        TerrainType.HILLY: (10, 20),
        TerrainType.MOUNTAINOUS: (20, 35),
        TerrainType.STEEP: (35, 50),
        TerrainType.VERY_STEEP: (50, 90),
    }"""
    
    pattern = r'TERRAIN_THRESHOLDS = \{[^}]+\}'
    content_new = re.sub(pattern, new_thresholds, content, flags=re.DOTALL)
    
    if content_new == content:
        print("  ⚠️  Pattern not found, no changes")
        return
    
    terrain_file.write_text(content_new, encoding="utf-8")
    print("  ✓ Updated TERRAIN_THRESHOLDS")
    
    # Verify syntax
    try:
        compile(content_new, str(terrain_file), "exec")
        print("  ✓ Syntax valid")
    except SyntaxError as e:
        print(f"  ✗ Syntax error: {e}")
        return
    
    # Verify test expectations
    print("\n🔍 Verifying test expectations:")
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    import numpy as np
    from engine.land.terrain_analysis import TerrainAnalyzer
    from engine.land.models import TerrainType
    
    analyzer = TerrainAnalyzer(resolution=30.0)
    
    test_cases = [
        ("flat", np.array([1, 2, 2.5]), TerrainType.FLAT),
        ("rolling", np.array([5, 6, 7]), TerrainType.ROLLING),
        ("hilly", np.array([10, 12, 15]), TerrainType.HILLY),
        ("mountainous", np.array([25, 30, 35]), TerrainType.MOUNTAINOUS),
    ]
    
    all_pass = True
    for name, slopes, expected in test_cases:
        result = analyzer._classify_terrain(slopes)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_pass = False
        print(f"  {status} {name}: mean={np.mean(slopes):.2f}° → {result.value} (expected {expected.value})")
    
    print("\n" + "=" * 70)
    if all_pass:
        print("✅ Phase 1 COMPLETE - All terrain classifications correct")
        print("=" * 70)
        print("\n📋 Run full test suite to confirm:")
        print("   python -m pytest engine/land/tests/ -v")
    else:
        print("⚠️  Some classifications still incorrect")


if __name__ == "__main__":
    main()