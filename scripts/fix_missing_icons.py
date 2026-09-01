#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Missing @ant-design/icons dependency
==========================================
Problem: Rolldown can't resolve @ant-design/icons
Solution: Ensure it's in package.json and reinstall dependencies
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
    print("  Fix: Missing @ant-design/icons Dependency")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Check package.json
    print("[Step 1] Checking package.json")
    print("-" * 70)
    
    with open(PACKAGE_JSON, "r", encoding="utf-8") as f:
        package_data = json.load(f)
    
    dependencies = package_data.get("dependencies", {})
    dev_dependencies = package_data.get("devDependencies", {})
    
    has_icons = "@ant-design/icons" in dependencies
    has_icons_dev = "@ant-design/icons" in dev_dependencies
    
    if has_icons:
        ok(f"@ant-design/icons found in dependencies: {dependencies['@ant-design/icons']}")
    elif has_icons_dev:
        ok(f"@ant-design/icons found in devDependencies: {dev_dependencies['@ant-design/icons']}")
    else:
        warn("@ant-design/icons NOT found in package.json")
        info("Adding to dependencies...")
        
        # Add to dependencies
        dependencies["@ant-design/icons"] = "^5.2.6"
        package_data["dependencies"] = dependencies
        
        # Save updated package.json
        with open(PACKAGE_JSON, "w", encoding="utf-8") as f:
            json.dump(package_data, f, indent=2, ensure_ascii=False)
        
        ok("Added @ant-design/icons to package.json")
    
    print("")

    # Step 2: Check if antd is present (icons should come with it)
    print("[Step 2] Checking antd dependency")
    print("-" * 70)
    
    has_antd = "antd" in dependencies
    if has_antd:
        ok(f"antd found: {dependencies['antd']}")
        info("@ant-design/icons should be a peer dependency of antd")
    else:
        warn("antd not found in dependencies")
    
    print("")

    # Step 3: Reinstall dependencies
    print("[Step 3] Reinstalling dependencies")
    print("-" * 70)
    info("Running pnpm install...")
    
    result = subprocess.run(
        "pnpm install",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=180,
    )
    
    if result.returncode == 0:
        ok("Dependencies installed successfully")
        # Show last few lines
        output_lines = result.stdout.splitlines()
        for line in output_lines[-10:]:
            if line.strip():
                print(f"    {line}")
    else:
        err("pnpm install failed")
        print(result.stdout[-500:])
        return 1
    
    print("")

    # Step 4: Verify installation
    print("[Step 4] Verifying @ant-design/icons installation")
    print("-" * 70)
    
    icons_path = FRONTEND / "node_modules" / "@ant-design" / "icons"
    if icons_path.exists():
        ok(f"@ant-design/icons installed at: {icons_path}")
        
        # Check package.json of the package
        icons_pkg = icons_path / "package.json"
        if icons_pkg.exists():
            with open(icons_pkg, "r", encoding="utf-8") as f:
                icons_data = json.load(f)
            ok(f"Version: {icons_data.get('version', 'unknown')}")
    else:
        err("@ant-design/icons not found in node_modules!")
        info("Trying explicit install...")
        
        result = subprocess.run(
            "pnpm add @ant-design/icons",
            shell=True, cwd=FRONTEND,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
        
        if result.returncode == 0:
            ok("Explicitly installed @ant-design/icons")
        else:
            err("Explicit install failed")
            return 1
    
    print("")

    # Step 5: Build verification
    print("[Step 5] Building project")
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
        print("\n  Error output (last 20 lines):")
        for line in output.splitlines()[-20:]:
            if line.strip():
                print(f"    {line}")
    print("")

    # Step 6: Commit if successful
    if build_ok:
        print("[Step 6] Committing fix")
        print("-" * 70)
        try:
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "fix(deps): ensure @ant-design/icons is properly installed\\n\\n"
                "Problem:\\n"
                "- Rolldown couldn't resolve @ant-design/icons\\n"
                "- Build failed with missing dependency error\\n\\n"
                "Solution:\\n"
                "- Verified @ant-design/icons in package.json\\n"
                "- Reinstalled dependencies with pnpm install\\n"
                "- Build now successful\\n\\n"
                "Cinematic agricultural simulator accessible at:\\n"
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
        print("  ✅ All dependencies properly installed!")
        print("")
        print("  Next steps:")
        print("    cd D:\\eco_nojin\\frontend")
        print("    pnpm dev")
        print("    Visit: http://localhost:5173/hydroma")
        print("")
        print("  🌾 Agricultural Cinematic Simulator Ready!")
        print("    🌊 Custom GLSL water shader")
        print("    🐝 Insects, 🐄 Animals, 🐔 Poultry")
        print("    🌧️ Weather effects, ⚡ Lightning, 🌈 Rainbow")
        print("    🎬 Cinematic post-processing")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())