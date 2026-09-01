#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Fix: Replace the entire problematic line in CinematicOverlay.tsx
===========================================================================
Problem: Line 27 has mismatched quotes - starts with ` but ends with '
Solution: Replace the entire line with a properly formatted version
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
OVERLAY_FILE = FRONTEND / "src" / "components" / "cinematic" / "CinematicOverlay.tsx"


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
    print("  Complete Fix: Replace Problematic Line in CinematicOverlay.tsx")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Read file
    print("[Step 1] Reading CinematicOverlay.tsx")
    print("-" * 70)
    
    content = OVERLAY_FILE.read_text(encoding="utf-8")
    lines = content.split('\n')
    info(f"Total lines: {len(lines)}")
    print("")

    # Step 2: Find and replace the problematic line
    print("[Step 2] Replacing the entire problematic line")
    print("-" * 70)
    
    # The correct line (with backticks and proper escaping)
    # Using raw string to avoid escape issues
    correct_line = '          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox=\'0 0 200 200\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'4\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\'/%3E%3C/svg%3E")`,'

    fixed = False
    for i, line in enumerate(lines):
        if "backgroundImage:" in line and "svg+xml" in line:
            info(f"Found problematic line at {i+1}")
            info(f"  Old: {line.strip()[:80]}...")
            lines[i] = correct_line
            info(f"  New: {correct_line.strip()[:80]}...")
            fixed = True
            break
    
    if not fixed:
        err("Could not find the problematic line!")
        return 1
    
    # Save the file
    new_content = '\n'.join(lines)
    OVERLAY_FILE.write_text(new_content, encoding="utf-8")
    ok("Saved CinematicOverlay.tsx")
    print("")

    # Step 3: Verify the fix by showing the corrected area
    print("[Step 3] Verifying the corrected code")
    print("-" * 70)
    
    for i in range(22, 30):
        marker = " >>>" if i == 26 else "    "
        print(f"{marker} {i+1:3d}: {lines[i]}")
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
        print("\n  Error output (last 20 lines):")
        for line in output.splitlines()[-20:]:
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
                "fix(cinematic): fix unterminated string in CinematicOverlay\\n\\n"
                "Problem:\\n"
                "- Line 27 had mismatched quotes\\n"
                "- Started with backtick but ended with single quote\\n"
                "- Caused 'Unterminated string' error\\n\\n"
                "Solution:\\n"
                "- Replaced entire line with properly formatted template literal\\n"
                "- Build now successful\\n\\n"
                "Cinematic agricultural simulator now accessible at:\\n"
                "- http://localhost:5173/hydroma\\n"
                "- http://localhost:5173/cinematic"
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
        print("  ✅ Build is now successful!")
        print("")
        print("  Next steps:")
        print("    cd D:\\eco_nojin\\frontend")
        print("    pnpm dev")
        print("")
        print("  Then visit: http://localhost:5173/hydroma")
        print("")
        print("  🌾 Agricultural Cinematic Simulator Features:")
        print("    🐝 Insects (bees, ladybugs, locusts)")
        print("    🐄 Domestic animals (cows, sheep, horses)")
        print("    🐔 Poultry (chickens, ducks)")
        print("    🌊 Flood, 💧 Irrigation, ⛲ Well")
        print("    🏞️ River, 🏖️ Coastline, 🏗️ Watershed, 🚜 Plowing")
        print("    🌤️ Weather: Rain, Snow, Dust, Drought, Storm")
        print("    ⚡ Lightning, 🌈 Rainbow, 🦋 Butterflies")
        print("    🎬 Post-processing: Bloom, SSAO, DoF, Vignette")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())