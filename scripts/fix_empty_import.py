#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Empty Import Statement in WeatherControls.tsx
====================================================
Problem: Line 4 has "import { , ApiOutlined, ...}" - leading comma
Solution: Rewrite the import line with proper syntax
"""

import os
import sys
import subprocess
import re
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
    print("  Fix: Empty Import Statement")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Read file
    print("[Step 1] Reading WeatherControls.tsx")
    print("-" * 70)
    
    content = WEATHER_CONTROLS.read_text(encoding="utf-8")
    lines = content.split('\n')
    info(f"Read {len(lines)} lines")
    print("")

    # Step 2: Find and fix the import line
    print("[Step 2] Fixing import statement")
    print("-" * 70)
    
    # Show current line 4
    info(f"Current line 4: {lines[3][:80]}...")
    
    # Find the import line
    import_line_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('import {') and '@ant-design/icons' in line:
            import_line_idx = i
            break
    
    if import_line_idx == -1:
        err("Could not find import line!")
        return 1
    
    # Extract all icon names from the current line
    import_match = re.search(r'import\s+\{([^}]+)\}\s+from', lines[import_line_idx])
    
    if not import_match:
        err("Could not parse import statement!")
        return 1
    
    imports_str = import_match.group(1)
    
    # Split by comma and clean up
    raw_imports = [imp.strip() for imp in imports_str.split(',')]
    
    # Filter out empty strings and duplicates
    valid_imports = []
    seen = set()
    
    for imp in raw_imports:
        imp = imp.strip()
        if not imp:
            continue  # Skip empty
        
        # Handle "ThunderboltOutlined as FloodIcon"
        if ' as ' in imp:
            base = imp.split(' as ')[0].strip()
            if base not in seen:
                seen.add(base)
                valid_imports.append(imp)
        else:
            if imp not in seen:
                seen.add(imp)
                valid_imports.append(imp)
    
    # Sort alphabetically
    valid_imports.sort()
    
    # Rebuild the import line
    new_imports_str = ', '.join(valid_imports)
    new_import_line = f'import {{ {new_imports_str} }} from "@ant-design/icons";'
    
    info(f"New import line: {new_import_line[:80]}...")
    
    # Replace the line
    lines[import_line_idx] = new_import_line
    
    ok(f"Fixed import line (line {import_line_idx + 1})")
    print("")

    # Step 3: Save
    print("[Step 3] Saving WeatherControls.tsx")
    print("-" * 70)
    
    new_content = '\n'.join(lines)
    WEATHER_CONTROLS.write_text(new_content, encoding="utf-8")
    ok("Saved")
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
                if any(k in line for k in ["vendor", "index", "HyDroMaCenter", "cinematic"]):
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
                "fix(syntax): fix empty import in WeatherControls.tsx\\n\\n"
                "Problem:\\n"
                "- Import line had leading comma: 'import { , ApiOutlined, ...}'\\n"
                "- Build failed with Unexpected token error\\n\\n"
                "Solution:\\n"
                "- Extracted all valid icon names\\n"
                "- Removed empty strings and duplicates\\n"
                "- Rebuilt import line with proper syntax\\n\\n"
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