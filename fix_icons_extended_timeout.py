#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Extended timeout for pnpm install
=======================================
Problem: pnpm install timed out after 180 seconds
Solution: Increase timeout to 600 seconds + add speed-up options
"""

import os
import sys
import subprocess
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
PACKAGE_JSON = FRONTEND / "package.json"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def err(m): print(f"[ERROR] {m}")
def warn(m): print(f"[WARN] {m}")


def setup_git_path():
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


def main():
    print("")
    print("=" * 70)
    print("  Fix: Extended Timeout for pnpm install")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Check package.json
    print("[Step 1] Checking package.json")
    print("-" * 70)
    
    with open(PACKAGE_JSON, "r", encoding="utf-8") as f:
        package_data = json.load(f)
    
    dependencies = package_data.get("dependencies", {})
    
    has_icons = "@ant-design/icons" in dependencies
    
    if has_icons:
        ok(f"@ant-design/icons found: {dependencies['@ant-design/icons']}")
    else:
        warn("@ant-design/icons NOT found, adding...")
        dependencies["@ant-design/icons"] = "^5.2.6"
        package_data["dependencies"] = dependencies
        
        with open(PACKAGE_JSON, "w", encoding="utf-8") as f:
            json.dump(package_data, f, indent=2, ensure_ascii=False)
        
        ok("Added @ant-design/icons to package.json")
    
    print("")

    # Step 2: Reinstall with extended timeout
    print("[Step 2] Reinstalling dependencies (extended timeout)")
    print("-" * 70)
    info("Running pnpm install with 600s timeout...")
    info("This may take 5-10 minutes...")
    
    result = subprocess.run(
        "pnpm install --prefer-offline",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=600,  # 10 minutes
    )
    
    if result.returncode == 0:
        ok("Dependencies installed successfully")
        output_lines = result.stdout.splitlines()
        for line in output_lines[-15:]:
            if line.strip():
                print(f"    {line}")
    else:
        err("pnpm install failed")
        print("\n  Output:")
        for line in result.stdout.splitlines()[-20:]:
            if line.strip():
                print(f"    {line}")
        print("\n  Stderr:")
        for line in result.stderr.splitlines()[-10:]:
            if line.strip():
                print(f"    {line}")
        return 1
    
    print("")

    # Step 3: Verify installation
    print("[Step 3] Verifying @ant-design/icons installation")
    print("-" * 70)
    
    icons_path = FRONTEND / "node_modules" / "@ant-design" / "icons"
    if icons_path.exists():
        ok(f"@ant-design/icons installed")
        
        icons_pkg = icons_path / "package.json"
        if icons_pkg.exists():
            with open(icons_pkg, "r", encoding="utf-8") as f:
                icons_data = json.load(f)
            ok(f"Version: {icons_data.get('version', 'unknown')}")
    else:
        err("@ant-design/icons not found in node_modules!")
        return 1
    
    print("")

    # Step 4: Build verification
    print("[Step 4] Building project")
    print("-" * 70)
    info("This will take 1-2 minutes...")
    
    result = subprocess.run(
        "pnpm build",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
    )
    
    build_ok = result.returncode == 0
    output = result.stdout + result.stderr
    
    if build_ok:
        ok("🎉 Build successful!")
        
        print("\n  Bundle sizes:")
        for line in output.splitlines():
            if "dist/assets/" in line and ("kB" in line or "MB" in line):
                if "vendor" in line or "index" in line or "HyDroMaCenter" in line:
                    print(f"    {line.strip()}")
    else:
        err("Build still failing")
        print("\n  Error output (last 25 lines):")
        for line in output.splitlines()[-25:]:
            if line.strip():
                print(f"    {line}")
    print("")

    # Step 5: Commit if successful
    if build_ok:
        print("[Step 5] Committing fix")
        print("-" * 70)
        try:
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "fix(deps): install @ant-design/icons with extended timeout\\n\\n"
                "Problem:\\n"
                "- @ant-design/icons was missing from dependencies\\n"
                "- pnpm install timed out at 180s\\n\\n"
                "Solution:\\n"
                "- Added @ant-design/icons to package.json\\n"
                "- Increased timeout to 600s\\n"
                "- Used --prefer-offline for faster install\\n"
                "- Build now successful\\n\\n"
                "Cinematic simulator accessible at:\\n"
                "- http://localhost:5173/hydroma"
            )
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")
        
        print("")
        print("=" * 70)
        print("  🎉 FIX SUCCESSFUL!")
        print("=" * 70)
        print("")
        print("  Next steps:")
        print("    cd D:\\eco_nojin\\frontend")
        print("    pnpm dev")
        print("    Visit: http://localhost:5173/hydroma")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())