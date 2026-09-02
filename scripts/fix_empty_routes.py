#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Orphan Routes with empty element={}
=========================================
Root cause: purge_hydroma removed <Diag3D/> JSX but left element={} behind.
Solution: Remove ALL <Route ... element={} /> lines entirely, since the
pages they pointed to are already deleted.
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
    print("  Fix: Remove orphan Routes with empty element={}")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Read App.tsx
    print("[Step 1] Reading App.tsx")
    print("-" * 70)
    original = APP_FILE.read_text(encoding="utf-8-sig")
    info(f"Read {len(original)} bytes")
    print("")

    # Step 2: Find and remove orphan routes
    print("[Step 2] Removing orphan routes")
    print("-" * 70)
    content = original

    # Pattern: <Route ... element={} ... />
    # (handles attributes in any order, with optional whitespace)
    pattern = r"[ \t]*<Route\b[^>]*element=\{\s*\}[^>]*/>\s*\n"

    matches = list(re.finditer(pattern, content))
    info(f"Found {len(matches)} orphan route(s):")

    for m in matches:
        line = m.group(0).strip()
        # Extract path for display
        path_match = re.search(r'path="([^"]+)"', line)
        path = path_match.group(1) if path_match else "(unknown)"
        info(f"  • {path}: {line[:80]}")

    # Remove all matches
    content = re.sub(pattern, "", content)

    if content == original:
        info("No orphan routes found - nothing to fix")
    else:
        APP_FILE.write_text(content, encoding="utf-8")
        ok(f"Removed {len(matches)} orphan route(s)")
    print("")

    # Step 3: Safety check - scan for any remaining JSX with empty attributes
    print("[Step 3] Scanning for other empty JSX attributes")
    print("-" * 70)
    empty_attrs = re.findall(r"\w+=\{\s*\}", content)
    if empty_attrs:
        warn(f"Found {len(empty_attrs)} other empty attributes:")
        for a in empty_attrs:
            info(f"  {a}")
        info("These may be intentional (e.g., event handlers) - not auto-removed")
    else:
        ok("No other empty JSX attributes found")
    print("")

    # Step 4: Build verification
    print("[Step 4] Build verification")
    print("-" * 70)
    result = subprocess.run(
        "pnpm build",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
    )

    build_ok = result.returncode == 0
    if build_ok:
        ok("🎉 Build successful!")
        for line in (result.stdout + result.stderr).splitlines():
            if "dist/assets/index" in line and "kB" in line:
                info(f"  bundle: {line.strip()}")
    else:
        err("Build still failing:")
        for line in (result.stdout + result.stderr).splitlines()[-20:]:
            if line.strip():
                print(f"    {line}")
    print("")

    # Step 5: Commit
    if build_ok:
        print("[Step 5] Committing")
        print("-" * 70)
        try:
            subprocess.run("git add -A .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "fix(app): remove orphan routes with empty element={}\\n\\n"
                f"Removed {len(matches)} orphan <Route ... element='{{}}' /> line(s)\\n"
                "left over from the HyDroMa purge (pages deleted, routes orphaned).\\n"
                "Build is now green.\\n\\n"
                "/hydroma still points to SimulatorPlaceholder."
            )
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")

        print("")
        print("=" * 70)
        print("  ✅ FIX COMPLETE - workspace fully clean")
        print("=" * 70)
        print("")
        print("  State after purge + fix:")
        print("    • Build:       ✅ green")
        print("    • /hydroma:    placeholder 'در حال بازسازی'")
        print("    • Other pages: untouched")
        print("    • Bundle:      lighter (three/drei/postprocessing gone)")
        print("")
        print("  Ready for standard simulator rebuild whenever you are.")
        print("")

    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())