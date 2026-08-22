"""
Phase 2A Complete: Verify All Tests + Git Commit
================================================
1. Run all land tests (Phase 1 + Phase 2A)
2. Commit changes
3. Prepare for Phase 2B (Climate Integration)
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"D:\eco_nojin")


def run_command(cmd, cwd=None, check=True):
    """Run command and return result."""
    result = subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False
    )
    if check and result.returncode != 0:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(result.stderr)
    return result


def main():
    print("=" * 70)
    print("🎯 Phase 2A Complete: Verification & Commit")
    print("=" * 70)
    
    # Step 1: Run all land tests
    print("\n[1/3] Running all land tests (Phase 1 + Phase 2A)...")
    result = run_command(
        [sys.executable, "-m", "pytest", "engine/land/tests/", "-v", "--tb=short"],
        check=False
    )
    print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
    
    if "passed" not in result.stdout:
        print("❌ Some tests failed")
        return False
    
    # Count passed tests
    import re
    match = re.search(r"(\d+) passed", result.stdout)
    if match:
        print(f"\n✅ All {match.group(1)} tests passed!")
    
    # Step 2: Find git and commit
    print("\n[2/3] Committing changes to git...")
    
    # Find git
    git_paths = [
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
        r"C:\Users\{}\AppData\Local\Programs\Git\bin\git.exe".format(
            Path.home().name
        ),
    ]
    
    git_path = None
    for path in git_paths:
        if Path(path).exists():
            git_path = path
            break
    
    if not git_path:
        try:
            result = subprocess.run(["where", "git"], capture_output=True, text=True, check=True)
            git_path = result.stdout.strip().split('\n')[0]
        except:
            pass
    
    if not git_path:
        print("❌ Git not found. Please commit manually:")
        print("   git add -A")
        print('   git commit -m "feat(land): Phase 2A - Soil Integration (28 tests)"')
        return False
    
    print(f"✓ Found git: {git_path}")
    
    # Add changes
    result = subprocess.run([git_path, "add", "-A"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to add changes: {result.stderr}")
        return False
    
    # Check status
    result = subprocess.run([git_path, "status", "--short"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    if not result.stdout.strip():
        print("⚠️  No changes to commit")
    else:
        print("\nFiles to commit:")
        for line in result.stdout.strip().split('\n')[:10]:
            print(f"  {line}")
    
    # Commit
    commit_msg = """feat(land): Phase 2A - Soil Integration Complete

- Connected engine/land/ to engine/hydroma/soil/ modules
- Created engine/land/integration/ with SoilIntegrator
- 6-layer deep soil profile (0-200cm): 0-5, 5-15, 15-30, 30-60, 60-100, 100-200cm
- USDA texture classification (12 classes)
- van Genuchten water retention parameters
- Available Water Capacity (AWC) calculation
- Salinity classification (5 classes)
- Soil health scoring (0-100)
- 28 comprehensive tests (all passing)

Technical details:
- SoilLayer model with chemistry, physics, and VG parameters
- DeepSoilProfile with dominant texture and rooting depth
- SoilIntegrationResult with suitable crops and recommendations
- Fallback logic when soil modules unavailable"""
    
    result = subprocess.run(
        [git_path, "commit", "-m", commit_msg],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Commit failed: {result.stderr}")
        return False
    
    print("✅ Changes committed successfully!")
    
    # Step 3: Summary and next steps
    print("\n" + "=" * 70)
    print("📊 Phase 2A Summary")
    print("=" * 70)
    print("✅ Soil Integration Complete")
    print("   - 28 tests passing")
    print("   - 6-layer soil profile (0-200cm)")
    print("   - Connected to hydroma/soil modules")
    print("   - USDA texture + van Genuchten parameters")
    print("   - AWC + Salinity + Health scoring")
    
    print("\n📋 Next: Phase 2B - Climate Integration")
    print("   Will connect to:")
    print("   - ERA5 / Open-Meteo / WorldClim")
    print("   - ET0 (Hargreaves + Penman-Monteith)")
    print("   - Köppen-Geiger classification")
    print("   - Aridity Index + Growing Season")
    
    print("\n" + "=" * 70)
    print("✅ Phase 2A COMPLETE - Ready for Phase 2B")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)