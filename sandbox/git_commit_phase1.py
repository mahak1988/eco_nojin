"""
Git Commit Phase 1 - Complete Land Intelligence
================================================
Finds git executable and commits Phase 1 changes.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"D:\eco_nojin")


def find_git():
    """Find git executable path."""
    # Common git paths on Windows
    possible_paths = [
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
        r"C:\Users\{}\AppData\Local\Programs\Git\bin\git.exe".format(
            Path.home().name
        ),
    ]
    
    for git_path in possible_paths:
        if Path(git_path).exists():
            return git_path
    
    # Try which on Windows
    try:
        result = subprocess.run(
            ["where", "git"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n')[0]
    except subprocess.CalledProcessError:
        pass
    
    return None


def run_git_command(git_path, args, cwd=None):
    """Run a git command."""
    cmd = [git_path] + args
    result = subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    return result


def main():
    print("=" * 70)
    print("🔨 Git Commit - Phase 1 Complete")
    print("=" * 70)
    
    # Find git
    git_path = find_git()
    if not git_path:
        print("❌ Git not found!")
        print("\n📋 Please install Git from: https://git-scm.com/download/win")
        print("   Then run: refreshenv (if using Chocolatey) or restart PowerShell")
        return False
    
    print(f"✓ Found git: {git_path}")
    
    # Check if we're in a git repository
    result = run_git_command(git_path, ["rev-parse", "--git-dir"])
    if result.returncode != 0:
        print("❌ Not a git repository!")
        print("\n📋 Initialize git repository:")
        print("   git init")
        return False
    
    print("✓ Git repository found")
    
    # Add all changes
    print("\n[1/3] Adding changes...")
    result = run_git_command(git_path, ["add", "-A"])
    if result.returncode != 0:
        print(f"❌ Failed to add changes: {result.stderr}")
        return False
    print("✓ All changes added")
    
    # Check status
    print("\n[2/3] Checking status...")
    result = run_git_command(git_path, ["status", "--short"])
    if result.stdout.strip():
        print("Files to commit:")
        for line in result.stdout.strip().split('\n')[:10]:  # Show first 10
            print(f"  {line}")
        if len(result.stdout.strip().split('\n')) > 10:
            print(f"  ... and {len(result.stdout.strip().split('\n')) - 10} more")
    else:
        print("⚠️  No changes to commit")
        return True
    
    # Commit
    print("\n[3/3] Committing...")
    commit_message = """feat(land): Complete Phase 1 - Land Intelligence Module

- 51 tests passing (100%)
- Enhanced models: 8 TerrainTypes, 7 SlopeClasses, 8 CapabilityClasses
- D8 drainage analysis with Strahler ordering & Horton bifurcation
- USDA Land Capability Classification
- Reference data: 26 countries, 8 regions, 29 cities in SQLite
- Terrain analysis with TWI, TPI, curvature, landform classification

Technical details:
- Pydantic V2 models with validation
- NumPy-based slope/aspect calculations
- Strahler stream ordering algorithm
- Topographic Wetness Index (TWI)
- Topographic Position Index (TPI)
- Vector Ruggedness Measure (VRM)
- 7-class terrain classification (FLAT to VERY_STEEP)
- 8-class capability system (CLASS_I to CLASS_VIII)"""
    
    result = run_git_command(git_path, ["commit", "-m", commit_message])
    if result.returncode != 0:
        print(f"❌ Commit failed: {result.stderr}")
        return False
    
    print("✓ Changes committed successfully!")
    print("\n" + "=" * 70)
    print("✅ Phase 1 COMPLETE - All changes committed to git")
    print("=" * 70)
    
    # Show log
    print("\n📋 Latest commit:")
    result = run_git_command(git_path, ["log", "--oneline", "-1"])
    print(result.stdout)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)