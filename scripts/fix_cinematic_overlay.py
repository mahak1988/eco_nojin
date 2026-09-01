#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix String Literal Error in CinematicOverlay.tsx
==================================================
Problem: Single quotes inside single-quoted string
Solution: Use template literals (backticks)
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
    print("  Fix String Literal in CinematicOverlay.tsx")
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

    # Step 2: Show problematic area
    print("[Step 2] Lines 20-35 (around the error)")
    print("-" * 70)
    
    for i in range(19, min(35, len(lines))):
        marker = " >>>" if i == 26 else "    "
        print(f"{marker} {i+1:3d}: {lines[i]}")
    
    print("")

    # Step 3: Fix the issue
    print("[Step 3] Fixing string literal")
    print("-" * 70)
    
    # Find the problematic line and fix it
    fixed = False
    
    for i, line in enumerate(lines):
        if "backgroundImage:" in line and "data:image/svg+xml" in line:
            # Check if it uses single quotes
            if "backgroundImage: 'url(" in line:
                # Replace single quotes with backticks
                lines[i] = line.replace("backgroundImage: 'url(", "backgroundImage: `url(").replace(")',", ")',")
                ok(f"Fixed line {i+1}: Changed single quotes to backticks")
                fixed = True
                break
    
    if not fixed:
        info("Pattern not found, trying alternative fix...")
        
        # Alternative: Replace the entire line
        for i, line in enumerate(lines):
            if "backgroundImage:" in line and "svg" in line:
                # Replace with a simpler version using backticks
                new_line = '''          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,'''
                lines[i] = new_line
                ok(f"Replaced line {i+1} with template literal")
                fixed = True
                break
    
    if fixed:
        # Save file
        new_content = '\n'.join(lines)
        OVERLAY_FILE.write_text(new_content, encoding="utf-8")
        ok("Saved CinematicOverlay.tsx")
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

        # Step 5: Commit
        if build_ok:
            print("[Step 5] Committing fix")
            print("-" * 70)
            try:
                subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
                msg = (
                    "fix(cinematic): fix string literal in CinematicOverlay.tsx\\n\\n"
                    "Problem:\\n"
                    "- Single quotes inside single-quoted string caused parse error\\n"
                    "- Line 27: backgroundImage: 'url(\\\"data:...viewBox='0 0 200 200'...)\\n\\n"
                    "Solution:\\n"
                    "- Changed to template literal (backticks)\\n"
                    "- Build now successful\\n\\n"
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
            print("  🌾 Agricultural Cinematic Simulator Ready!")
            print("")
    else:
        err("Could not apply fix")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())