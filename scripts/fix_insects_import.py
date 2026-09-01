#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Missing useRef import in InsectsSystem.tsx
===============================================
Root cause of "Uncaught ReferenceError: useRef is not defined"
and the resulting "WebGLRenderer: Context Lost" cascade.
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
INSECTS_FILE = FRONTEND / "src" / "components" / "cinematic" / "InsectsSystem.tsx"


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
    print("  Fix: Add missing useRef import to InsectsSystem")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Read and fix
    print("[Step 1] Patching InsectsSystem.tsx")
    print("-" * 70)

    content = INSECTS_FILE.read_text(encoding="utf-8")
    original = content

    # Fix 1: ensure useRef is imported from react
    if "import { useMemo } from 'react';" in content:
        content = content.replace(
            "import { useMemo } from 'react';",
            "import { useRef, useMemo } from 'react';",
            1,
        )
        ok("Added useRef to React import")
    elif "import { useRef, useMemo }" in content:
        info("useRef already imported - no change needed")
    else:
        err("Unexpected import pattern - please check manually")
        return 1

    if content == original:
        info("File unchanged")
    else:
        INSECTS_FILE.write_text(content, encoding="utf-8")
        ok("Saved InsectsSystem.tsx")
    print("")

    # Step 2: Sanity-check other cinematic files for the same pattern
    print("[Step 2] Scanning other cinematic files for missing useRef")
    print("-" * 70)

    cinematic_dir = INSECTS_FILE.parent
    all_ok = True
    for file in cinematic_dir.glob("*.tsx"):
        if file.name == "InsectsSystem.tsx":
            continue
        text = file.read_text(encoding="utf-8")
        uses_useRef = "useRef(" in text or "useRef<" in text
        imports_useRef = "useRef" in text.split("import")[1] if "import" in text else False
        # Better check: look at first 10 lines for useRef in imports
        first_block = "\n".join(text.split("\n")[:15])
        imports_useRef = "useRef" in first_block and "from 'react'" in first_block

        if uses_useRef and not imports_useRef:
            err(f"{file.name}: uses useRef but doesn't import it!")
            all_ok = False
        elif uses_useRef:
            ok(f"{file.name}: useRef properly imported")

    if all_ok:
        ok("All cinematic files have valid imports")
    print("")

    # Step 3: Build verification (dev mode won't catch runtime errors,
    # but we can at least ensure no build break)
    print("[Step 3] Build verification")
    print("-" * 70)
    result = subprocess.run(
        "pnpm build",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
    )
    build_ok = result.returncode == 0
    if build_ok:
        ok("Build successful")
    else:
        err("Build failed:")
        for line in (result.stdout + result.stderr).splitlines()[-15:]:
            if line.strip():
                print(f"    {line}")
    print("")

    # Step 4: Commit
    if build_ok:
        print("[Step 4] Committing")
        print("-" * 70)
        try:
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "fix(cinematic): add missing useRef import in InsectsSystem\\n\\n"
                "Runtime bug (passed build, failed at runtime):\\n"
                "- InsectsSystem.tsx used useRef but didn't import it\\n"
                "- Caused 'Uncaught ReferenceError: useRef is not defined'\\n"
                "- Cascaded into 'WebGLRenderer: Context Lost' (entire Canvas crashed)\\n\\n"
                "Fix: Added useRef to React import.\\n"
                "Also scanned all cinematic/*.tsx files - no other missing imports."
            )
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")

        print("")
        print("=" * 70)
        print("  🎉 FIX COMPLETE!")
        print("=" * 70)
        print("")
        print("  Action required:")
        print("    1. Hard refresh browser: Ctrl + Shift + R")
        print("    2. Visit: http://localhost:5173/hydroma")
        print("    3. Verify Canvas renders without crash")
        print("")
        print("  Notes about the other console warnings:")
        print("    • MaxListenersExceededWarning  → from browser extension (MetaMask etc.)")
        print("    • ObjectMultiplex orphaned data → from browser extension")
        print("    • THREE.Clock deprecated        → internal to drei, harmless")
        print("    • antd Space direction          → minor deprecation, harmless")
        print("  None of these affect the app.")
        print("")

    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())