"""
Fix Git Commit for Windows PowerShell
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"D:\eco_nojin")


def find_git():
    """Find git executable on Windows"""
    git_paths = [
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
    ]
    for path in git_paths:
        if Path(path).exists():
            return path
    
    # Try where git
    result = subprocess.run(["where", "git"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip().split('\n')[0]
    
    return None


def main():
    print("=" * 70)
    print("📦 COMMITTING PHASE 2 (Soil + Climate) COMPLETE")
    print("=" * 70)
    
    git_path = find_git()
    if not git_path:
        print("❌ Git not found. Please commit manually:")
        print("   git add -A")
        print('   git commit -m "feat(land): Phase 2 - Soil & Climate Integration"')
        return 1
    
    print(f"✓ Found git: {git_path}")
    
    # Add all changes
    print("\n[1/3] Adding changes...")
    result = subprocess.run(
        [git_path, "add", "-A"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"❌ Failed: {result.stderr}")
        return 1
    print("✓ Changes staged")
    
    # Status
    print("\n[2/3] Checking status...")
    result = subprocess.run(
        [git_path, "status", "--short"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    
    if result.stdout.strip():
        print("Files to commit:")
        for line in result.stdout.strip().split('\n')[:15]:
            print(f"  {line}")
    else:
        print("⚠️  No changes to commit")
    
    # Commit
    print("\n[3/3] Committing...")
    commit_msg = """feat(land): Phase 2 Complete - Soil & Climate Integration

Phase 2A - Soil Integration (28 tests):
- Connected engine/land/ to engine/hydroma/soil/ modules
- 6-layer deep soil profile (0-200cm)
- USDA texture classification + van Genuchten parameters
- AWC calculation + Salinity + Soil Health scoring

Phase 2B - Climate Integration (47 tests):
- Köppen-Geiger classification (KGCv5)
- ET0 (Hargreaves + Penman-Monteith)
- Aridity Index + Growing Season calculation
- Open-Meteo integration

Phase 2C - Comprehensive Land Analysis (15 tests):
- Combined Soil + Climate + Land Capability
- Land Use Recommendations
- Crop Suitability Scoring (6 major crops)

Phase 2D - Scientific Motors Hub (18 tests):
- Unified API for CropAdvisor, IrrigationScheduler, RUSLE, RothC
- Graceful degradation

Total: 108 new tests passing (159 total)
"""
    
    result = subprocess.run(
        [git_path, "commit", "-m", commit_msg],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"❌ Commit failed: {result.stderr}")
        return 1
    
    print("✅ Phase 2 committed successfully!")
    
    # Show log
    result = subprocess.run(
        [git_path, "log", "--oneline", "-3"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    print("\n📋 Recent commits:")
    print(result.stdout)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())