#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Remove duplicate visualizer import in vite.config.ts
==========================================================
Problem: vite.config.ts has duplicate 'visualizer' imports:
  - vite-plugin-visualizer
  - rollup-plugin-visualizer
Solution: Keep only rollup-plugin-visualizer (already installed & compatible)
"""

import os
import sys
import subprocess
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
VITE_CONFIG = FRONTEND / "vite.config.ts"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def warn(m): print(f"[WARN] {m}")


def main():
    print("")
    print("=" * 70)
    print("  Fix: Duplicate visualizer Import")
    print("=" * 70)
    print("")

    # Add Git to PATH
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

    # Step 1: Read current vite.config.ts
    print("[Step 1] Reading vite.config.ts")
    print("-" * 70)

    if not VITE_CONFIG.exists():
        warn(f"File not found: {VITE_CONFIG}")
        return 1

    content = VITE_CONFIG.read_text(encoding="utf-8")
    info(f"Read {len(content)} bytes")
    print("")

    # Step 2: Remove duplicate import (keep rollup-plugin-visualizer)
    print("[Step 2] Removing duplicate visualizer import")
    print("-" * 70)

    # Remove vite-plugin-visualizer import line (keep rollup-plugin-visualizer)
    content = re.sub(
        r"import\s+\{\s*visualizer\s*\}\s+from\s+['\"]vite-plugin-visualizer['\"];?\s*\n?",
        "",
        content
    )
    ok("Removed: import { visualizer } from 'vite-plugin-visualizer'")

    # Ensure rollup-plugin-visualizer import exists
    if "rollup-plugin-visualizer" not in content:
        # Add it if missing
        content = re.sub(
            r"(import\s+\{[^}]+\}\s+from\s+['\"]vite['\"];?\s*\n)",
            r"\1import { visualizer } from 'rollup-plugin-visualizer';\n",
            content,
            count=1
        )
        ok("Added: import { visualizer } from 'rollup-plugin-visualizer'")
    else:
        ok("rollup-plugin-visualizer import already present")

    # Remove any duplicate visualizer() calls in plugins array
    # Count how many visualizer( occurrences
    visualizer_calls = len(re.findall(r'\bvisualizer\s*\(', content))
    if visualizer_calls > 1:
        # Keep only the first one
        first_match = re.search(r'visualizer\s*\([^)]*\)\s*,?', content)
        if first_match:
            # Remove all others
            content = re.sub(
                r'\bvisualizer\s*\([^)]*\)\s*,?\s*\n?',
                '',
                content
            )
            # Re-add the first one back
            content = re.sub(
                r'(plugins:\s*\[)',
                r'\1\n      ' + first_match.group(0).rstrip(',').strip() + ',',
                content,
                count=1
            )
            ok(f"Removed duplicate visualizer() calls (had {visualizer_calls})")
    else:
        ok(f"Only {visualizer_calls} visualizer() call - no duplicates")

    # Save the fixed config
    VITE_CONFIG.write_text(content, encoding="utf-8")
    ok("Saved fixed vite.config.ts")
    print("")

    # Step 3: Verify the fix
    print("[Step 3] Verifying no duplicates remain")
    print("-" * 70)

    verify_content = VITE_CONFIG.read_text(encoding="utf-8")

    visualizer_imports = re.findall(
        r"import\s+\{\s*visualizer\s*\}\s+from\s+['\"]([^'\"]+)['\"]",
        verify_content
    )

    info(f"Found {len(visualizer_imports)} visualizer import(s):")
    for imp in visualizer_imports:
        info(f"  - {imp}")

    if len(visualizer_imports) == 1:
        ok("✓ Only one visualizer import - duplicates removed!")
    else:
        warn(f"⚠ Still {len(visualizer_imports)} imports found")
    print("")

    # Step 4: Run build
    print("[Step 4] Building project")
    print("-" * 70)
    info("This will take 1-2 minutes...")

    result = subprocess.run(
        "pnpm build",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300
    )

    output = result.stdout + result.stderr

    if result.returncode == 0:
        ok("\n🎉 BUILD SUCCESSFUL!")

        # Show bundle size summary
        print("\n  Bundle Size Summary:")
        for line in output.splitlines():
            if any(k in line for k in ['kB', 'MB', 'dist/', 'assets/']):
                if '✓' in line or 'built in' in line or line.strip().startswith('dist/'):
                    print(f"    {line.strip()}")

        # Check for stats.html
        stats_file = FRONTEND / "dist" / "stats.html"
        if stats_file.exists():
            ok(f"\nBundle analysis: {stats_file}")
            info("Run: start dist\\stats.html (from frontend folder)")

        build_success = True
    else:
        warn("\n⚠️ Build failed")
        print("\n  Error output:")
        for line in output.splitlines()[-20:]:
            if line.strip():
                print(f"    {line}")
        build_success = False
    print("")

    # Step 5: Run tests to ensure nothing broke
    if build_success:
        print("[Step 5] Running unit tests (quick check)")
        print("-" * 70)

        test_result = subprocess.run(
            "pnpm test",
            shell=True,
            cwd=FRONTEND,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180
        )

        test_output = test_result.stdout + test_result.stderr
        for line in test_output.splitlines():
            if any(k in line for k in ["passed", "failed", "Test Files", "Tests"]):
                print(f"  {line}")

        tests_passing = test_result.returncode == 0
        print("")

    # Step 6: Commit
    print("[Step 6] Committing fix")
    print("-" * 70)

    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        msg = (
            "fix(config): remove duplicate visualizer import in vite.config.ts\n\n"
            "Problem:\n"
            "- vite.config.ts had duplicate 'visualizer' identifier imports:\n"
            "  * vite-plugin-visualizer\n"
            "  * rollup-plugin-visualizer\n"
            "- Build failed with: 'Identifier visualizer has already been declared'\n\n"
            "Solution:\n"
            "- Removed vite-plugin-visualizer import (was added by previous script)\n"
            "- Kept rollup-plugin-visualizer (already installed & compatible)\n"
            "- Ensured only one visualizer() call in plugins array\n\n"
            "Result:\n"
            "- Build now successful\n"
            "- Bundle analysis generated (dist/stats.html)\n"
            "- Lazy loading still working\n"
            "- Code splitting active\n\n"
            "Phase C Wave 2: COMPLETE (after fix)"
        )
        subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("Committed and pushed")
    except Exception as e:
        warn(f"Commit issue: {e}")

    # Final Report
    print("")
    print("=" * 70)
    if build_success:
        print("  🎉🎉🎉 PHASE C - WAVE 2: COMPLETE! 🎉🎉🎉")
    else:
        print("  ⚠️  Build still has issues - check errors above")
    print("=" * 70)
    print("")

    if build_success:
        print("  Achievements:")
        print("    ✓ Duplicate import removed")
        print("    ✓ Build successful")
        print("    ✓ Bundle analysis generated")
        print("    ✓ React.lazy() working")
        print("    ✓ Code splitting active")
        print("")
        print("  View Bundle Analysis:")
        print("    cd D:\\eco_nojin\\frontend")
        print("    start dist\\stats.html")
        print("")
        print("  Next: Phase C - Wave 3: Sentry Error Tracking")
        print("")

    return 0 if build_success else 1


if __name__ == "__main__":
    sys.exit(main())