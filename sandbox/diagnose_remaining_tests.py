"""
Final Diagnostic + Fix for 6 Remaining Test Failures
=====================================================
Reads the actual test files, understands expectations, and fixes implementation.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(r"D:\eco_nojin")


def read_file(path):
    """Read file content."""
    p = PROJECT_ROOT / path
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


def diagnose_tests():
    """Read all test files and extract test case details."""
    print("=" * 70)
    print("🔍 DIAGNOSTIC: Reading test files...")
    print("=" * 70)

    # 1. Read capability tests
    cap_test = read_file("engine/land/tests/test_capability.py")
    if cap_test:
        print("\n📄 test_capability.py content:")
        print("-" * 40)
        print(cap_test)
        print("-" * 40)

    # 2. Read terrain tests
    terrain_test = read_file("engine/land/tests/test_terrain.py")
    if terrain_test:
        print("\n📄 test_terrain.py content:")
        print("-" * 40)
        print(terrain_test)
        print("-" * 40)

    # 3. Read comprehensive tests (just the failing parts)
    comp_test = read_file("engine/land/tests/test_land_comprehensive.py")
    if comp_test:
        # Extract arid test
        arid_match = re.search(
            r'def test_arid_land_climate_limitation.*?(?=\n    def |\nclass |\Z)',
            comp_test, re.DOTALL
        )
        if arid_match:
            print("\n📄 test_arid_land_climate_limitation:")
            print("-" * 40)
            print(arid_match.group())
            print("-" * 40)

    # 4. Read current capability.py
    cap_impl = read_file("engine/land/capability.py")
    if cap_impl:
        print("\n📄 Current capability.py (_upgrade_class method):")
        print("-" * 40)
        # Find _upgrade_class
        upgrade_match = re.search(
            r'def _upgrade_class.*?(?=\n    def |\nclass |\Z)',
            cap_impl, re.DOTALL
        )
        if upgrade_match:
            print(upgrade_match.group())
        print("-" * 40)

    # 5. Read current terrain_analysis.py thresholds
    terrain_impl = read_file("engine/land/terrain_analysis.py")
    if terrain_impl:
        print("\n📄 Current TERRAIN_THRESHOLDS:")
        print("-" * 40)
        thresh_match = re.search(
            r'TERRAIN_THRESHOLDS = \{[^}]+\}',
            terrain_impl, re.DOTALL
        )
        if thresh_match:
            print(thresh_match.group())
        print("-" * 40)


if __name__ == "__main__":
    diagnose_tests()