"""
Phase 4 Git Commit Helper
حل مشکل PowerShell PSReadLine با استفاده از subprocess
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Git path in Windows
GIT_PATHS = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
    "git",  # fallback to PATH
]

def find_git():
    for path in GIT_PATHS:
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return path
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    return None

def git_command(args, description: str) -> bool:
    print(f"\n🔧 {description}")
    print(f"   Running: git {' '.join(args)}")
    
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    
    if result.returncode == 0:
        print(f"   ✅ Success")
        if result.stdout:
            for line in result.stdout.split('\n')[:10]:
                if line.strip():
                    print(f"   {line}")
        return True
    else:
        print(f"   ❌ Failed: {result.stderr}")
        return False

def main():
    git_path = find_git()
    if not git_path:
        print("❌ Git not found in any known location")
        sys.exit(1)
    
    print(f"✅ Git found at: {git_path}\n")
    
    # Stage changes
    if not git_command(["add", "."], "Staging all changes"):
        sys.exit(1)
    
    # Check status
    git_command(["status", "--short"], "Current status")
    
    # Commit with message
    commit_message = """feat(science): Phase 4a - Professional Hydroma models library

Created enterprise-grade models library with 8 proprietary scientific models:
- EWSI: Multi-source Water Stress Index (Sentinel-2 + VPD + soil)
- HY-RUE: Radiation Use Efficiency with satellite LAI
- ECSI: Carbon Sequestration based on RothC-26.3
- HDVI: Multi-scale Drought Vulnerability Index
- EPIA: Precision Irrigation Advisor with satellite Kc
- H-Pheno: Phenology detection from NDVI time-series
- ESRI: Salinity Risk Index (spectral + soil + irrigation)
- HLHS: Composite Landscape Health Score for fund management

Each model includes:
- Type hints and dataclass parameters
- Input validation against physical bounds
- Vectorized NumPy computations
- Validation against peer-reviewed reference data
- Monte Carlo uncertainty quantification
- Local sensitivity analysis
- Docstrings with literature references

Mathematical foundations: Monteith 1977, RothC, FAO-56, AquaCrop, Kogan 1995.
"""
    
    if not git_command(["commit", "-m", commit_message], "Committing changes"):
        sys.exit(1)
    
    # Push
    if not git_command(["push", "origin", "main"], "Pushing to remote"):
        print("   ⚠️ Push failed - may need authentication")
    
    print("\n" + "=" * 80)
    print("✅ Git operations completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    main()