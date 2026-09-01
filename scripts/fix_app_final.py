#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Fix: Remove orphan tags in App.tsx
==========================================
Problem: After <Route path="/hydroma"> there are 4 orphan lines:
  </Routes>
  </ProtectedRoute>
  }
  />
These must be removed to fix the JSX nesting.
"""

import os
import sys
import subprocess
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
APP_FILE = FRONTEND / "src" / "App.tsx"


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
    print("  Final Fix: Remove Orphan Tags in App.tsx")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Read file
    print("[Step 1] Reading App.tsx")
    print("-" * 70)
    content = APP_FILE.read_text(encoding="utf-8")
    lines = content.split('\n')
    info(f"Total lines: {len(lines)}")
    print("")

    # Step 2: Find the orphan section
    print("[Step 2] Finding orphan tags")
    print("-" * 70)
    
    # Look for the pattern:
    # <Route path="/hydroma" element={...} />
    #                 </Routes>
    #                 </ProtectedRoute>
    #               }
    #             />
    #             <Route path="/dashboard"
    
    hydroma_line_idx = -1
    for i, line in enumerate(lines):
        if 'path="/hydroma"' in line and 'CinematicSimulator' in line:
            hydroma_line_idx = i
            break
    
    if hydroma_line_idx == -1:
        err("Could not find /hydroma route!")
        return 1
    
    info(f"Found /hydroma route at line {hydroma_line_idx + 1}")
    
    # Check next 5 lines for the orphan pattern
    orphan_start = -1
    orphan_end = -1
    
    for i in range(hydroma_line_idx + 1, min(hydroma_line_idx + 10, len(lines))):
        stripped = lines[i].strip()
        
        # Check if this is an orphan line
        if stripped == '</Routes>':
            orphan_start = i
            info(f"  Found orphan </Routes> at line {i + 1}")
        elif stripped == '</ProtectedRoute>' and orphan_start != -1:
            info(f"  Found orphan </ProtectedRoute> at line {i + 1}")
        elif stripped == '}' and orphan_start != -1:
            info(f"  Found orphan '}}' at line {i + 1}")
        elif stripped == '/>' and orphan_start != -1:
            orphan_end = i
            info(f"  Found orphan '/>' at line {i + 1}")
            break
        elif stripped.startswith('<Route') and orphan_start != -1:
            # We hit the next Route without finding '/>' - adjust
            orphan_end = i - 1
            break
    
    if orphan_start == -1 or orphan_end == -1:
        info("No orphan pattern found - trying alternative fix")
        
        # Alternative: just look for </Routes> followed by </ProtectedRoute>
        for i in range(len(lines) - 1):
            if lines[i].strip() == '</Routes>' and i + 1 < len(lines):
                if lines[i + 1].strip() == '</ProtectedRoute>':
                    orphan_start = i
                    # Find end of orphan block
                    for j in range(i + 2, min(i + 5, len(lines))):
                        if lines[j].strip() in ['}', '/>']:
                            if lines[j].strip() == '/>':
                                orphan_end = j
                                break
                    if orphan_end == -1:
                        orphan_end = i + 3
                    info(f"Found orphan block: lines {i+1} to {orphan_end+1}")
                    break
        
        if orphan_start == -1:
            err("Could not find orphan pattern")
            return 1
    
    print("")

    # Step 3: Remove orphan lines
    print("[Step 3] Removing orphan lines")
    print("-" * 70)
    
    info(f"Removing lines {orphan_start + 1} to {orphan_end + 1}")
    
    # Show what we're removing
    print("  Lines to remove:")
    for i in range(orphan_start, orphan_end + 1):
        print(f"    {i+1}: {lines[i]}")
    
    # Remove the lines
    del lines[orphan_start:orphan_end + 1]
    
    new_content = '\n'.join(lines)
    APP_FILE.write_text(new_content, encoding="utf-8")
    ok(f"Removed {orphan_end - orphan_start + 1} orphan lines")
    print("")

    # Step 4: Verify structure
    print("[Step 4] Verifying JSX structure")
    print("-" * 70)
    
    routes_open = new_content.count('<Routes')
    routes_close = new_content.count('</Routes>')
    protected_open = new_content.count('<ProtectedRoute')
    protected_close = new_content.count('</ProtectedRoute>')
    
    info(f"<Routes>: {routes_open} open, {routes_close} close")
    info(f"<ProtectedRoute>: {protected_open} open, {protected_close} close")
    
    if routes_open != routes_close:
        err(f"Mismatch: {routes_open} vs {routes_close}")
    else:
        ok("Routes tags balanced")
    
    if protected_open != protected_close:
        err(f"Mismatch: {protected_open} vs {protected_close}")
    else:
        ok("ProtectedRoute tags balanced")
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
    
    if build_ok:
        ok("🎉 Build successful!")
        
        # Show bundle size
        output = result.stdout + result.stderr
        print("\n  Bundle sizes:")
        for line in output.splitlines():
            if "dist/assets/" in line and ("kB" in line or "MB" in line):
                print(f"    {line.strip()}")
    else:
        err("Build still failing")
        output = result.stdout + result.stderr
        print("\n  Error output:")
        for line in output.splitlines()[-25:]:
            if line.strip():
                print(f"    {line}")
    print("")

    # Step 6: Commit
    if build_ok:
        print("[Step 6] Committing fix")
        print("-" * 70)
        try:
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "fix(jsx): remove orphan tags in App.tsx\\n\\n"
                "Problem:\\n"
                "- After /hydroma route there were 4 orphan lines:\\n"
                "  </Routes>\\n"
                "  </ProtectedRoute>\\n"
                "  }\\n"
                "  />\\n"
                "- These caused JSX nesting error\\n\\n"
                "Solution:\\n"
                "- Removed orphan lines\\n"
                "- Build now successful\\n"
                "- /hydroma route now works correctly\\n\\n"
                "Cinematic agricultural simulator accessible at:\\n"
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
        print("  Run: cd D:\\eco_nojin\\frontend")
        print("       pnpm dev")
        print("")
        print("  Then visit: http://localhost:5173/hydroma")
        print("")
        print("  🌾 Agricultural Cinematic Simulator Features:")
        print("    🐝 Insects (bees, ladybugs, locusts)")
        print("    🐄 Domestic animals (cows, sheep, horses)")
        print("    🐔 Poultry (chickens, ducks)")
        print("    🌊 Flood simulation")
        print("    💧 Irrigation systems (sprinklers + drip)")
        print("    ⛲ Well system")
        print("    🏞️ River with flowing water shader")
        print("    🏖️ Coastline with waves")
        print("    🏗️ Watershed engineering (check dams + terraces)")
        print("    🚜 Plowing trails with tractor")
        print("")
        print("  🌤️ Weather effects:")
        print("    ☀️ Day/Dawn/Dusk/Night with dynamic lighting")
        print("    🌧️ Rain, ❄️ Snow, 🌪️ Dust storms, 🔥 Drought")
        print("    ⚡ Lightning in storms")
        print("    🌈 Rainbow after rain")
        print("    🦋 Butterflies, 🐦 Birds, 🌌 Aurora, 🪲 Fireflies")
        print("    🎬 Cinematic post-processing (Bloom, SSAO, DoF, Vignette)")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())