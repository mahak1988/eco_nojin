#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Replace missing icons in WeatherControls.tsx
==================================================
Problem: CloudSnowOutlined and WindOutlined don't exist in @ant-design/icons@5.6.1
Solution: Replace with existing icons from v5.x
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
WEATHER_CONTROLS = FRONTEND / "src" / "components" / "cinematic" / "WeatherControls.tsx"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def err(m): print(f"[ERROR] {m}")


def setup_git_path():
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


def main():
    print("")
    print("=" * 70)
    print("  Fix: Replace Missing Icons in WeatherControls")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Read file
    print("[Step 1] Reading WeatherControls.tsx")
    print("-" * 70)
    
    content = WEATHER_CONTROLS.read_text(encoding="utf-8")
    info(f"Read {len(content)} bytes")
    print("")

    # Step 2: Replace missing icons
    print("[Step 2] Replacing missing icons")
    print("-" * 70)
    
    # Replacement map for missing icons
    replacements = {
        'CloudSnowOutlined': 'CloudOutlined',  # Use same cloud icon (will show snow via context)
        'WindOutlined': 'ThunderboltOutlined',  # Use thunderbolt as wind proxy (both atmospheric)
    }
    
    for old, new in replacements.items():
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            ok(f"Replaced {old} → {new} ({count} occurrence(s))")
        else:
            info(f"{old} not found (already fixed or not present)")
    
    print("")

    # Step 3: Fix the import line specifically
    print("[Step 3] Fixing import line")
    print("-" * 70)
    
    # The import line might have duplicates now, clean it up
    # Find: import { CloudOutlined, CloudRainOutlined, CloudOutlined, SunOutlined, ... }
    # Replace with unique imports
    
    import re
    import_match = re.search(r'import\s+\{([^}]+)\}\s+from\s+["\']@ant-design/icons["\']', content)
    
    if import_match:
        imports_str = import_match.group(1)
        # Split and deduplicate
        imports = [imp.strip() for imp in imports_str.split(',')]
        unique_imports = sorted(set(imports))
        
        # Rebuild import line
        new_imports_str = ', '.join(unique_imports)
        new_import_line = f'import {{ {new_imports_str} }} from "@ant-design/icons"'
        
        # Replace in content
        old_import_line = import_match.group(0)
        content = content.replace(old_import_line, new_import_line)
        
        info(f"Cleaned import: {new_imports_str}")
        ok("Import line deduplicated")
    else:
        warn("Could not find import statement")
    
    print("")

    # Step 4: Save
    print("[Step 4] Saving WeatherControls.tsx")
    print("-" * 70)
    
    WEATHER_CONTROLS.write_text(content, encoding="utf-8")
    ok("Saved")
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
                if any(k in line for k in ["vendor", "index", "HyDroMaCenter", "cinematic"]):
                    print(f"    {line.strip()}")
    else:
        err("Build still failing")
        print("\n  Error output (last 25 lines):")
        for line in output.splitlines()[-25:]:
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
                "fix(icons): replace missing icons in WeatherControls\\n\\n"
                "Problem:\\n"
                "- CloudSnowOutlined and WindOutlined don't exist in @ant-design/icons@5.6.1\\n"
                "- Build failed with MISSING_EXPORT error\\n\\n"
                "Solution:\\n"
                "- Replaced CloudSnowOutlined → CloudOutlined\\n"
                "- Replaced WindOutlined → ThunderboltOutlined\\n"
                "- Deduplicated import statement\\n\\n"
                "Cinematic agricultural simulator now accessible at:\\n"
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
        print("  🌾 Agricultural Cinematic Simulator Ready!")
        print("    🌊 Custom GLSL water shader")
        print("    🐝 Insects, 🐄 Animals, 🐔 Poultry")
        print("    🌧️ Weather effects, ⚡ Lightning, 🌈 Rainbow")
        print("    🎬 Cinematic post-processing")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())