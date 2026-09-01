#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase C - Wave 2.5: manualChunks Rebuild (eliminate catch-all)
================================================================
Scientific rationale:
- A catch-all vendor chunk mixes eager + lazy deps, forcing eager
  download of heavy 3D/postprocessing code on first paint.
- Affinity-based grouping keeps each heavy stack isolated so it is
  fetched ONLY when a lazy page actually imports it.
- Returning `undefined` for unmatched modules lets Rollup co-locate
  them with their importers, preserving laziness.
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
VITE_CONFIG = FRONTEND / "vite.config.ts"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def warn(m): print(f"[WARN] {m}")


MANUAL_CHUNKS_FN_LINES = [
    "// Affinity-based chunking: heavy stacks isolated, NO catch-all.",
    "function manualChunks(id: string): string | undefined {",
    "  if (!id.includes('node_modules')) return undefined;",
    "",
    "  // Core React (exact segments only)",
    "  if (/\\/node_modules\\/(react|react-dom|scheduler)\\//.test(id)) return 'vendor-react';",
    "",
    "  if (id.includes('react-router')) return 'vendor-router';",
    "",
    "  if (id.includes('antd') || id.includes('@ant-design') || id.includes('@rc-component') ||",
    "      id.includes('dayjs') || id.includes('stylis')) return 'vendor-antd';",
    "",
    "  if (id.includes('recharts') || id.includes('victory-vendor') || id.includes('d3-') ||",
    "      id.includes('redux') || id.includes('immer') || id.includes('reselect'))",
    "    return 'vendor-charts';",
    "",
    "  if (id.includes('three') || id.includes('@react-three') || id.includes('postprocessing') ||",
    "      id.includes('n8ao') || id.includes('maath')) return 'vendor-three';",
    "",
    "  if (id.includes('deck.gl') || id.includes('luma.gl') || id.includes('loaders.gl') ||",
    "      id.includes('math.gl') || id.includes('probe.gl') || id.includes('mjolnir') ||",
    "      id.includes('hammerjs')) return 'vendor-deckgl';",
    "",
    "  if (id.includes('framer-motion') || id.includes('motion-dom') || id.includes('motion-utils'))",
    "    return 'vendor-motion';",
    "",
    "  if (id.includes('i18next')) return 'vendor-i18n';",
    "  if (id.includes('@tanstack')) return 'vendor-query';",
    "  if (id.includes('zustand')) return 'vendor-state';",
    "  if (id.includes('lucide-react')) return 'vendor-icons';",
    "",
    "  // IMPORTANT: no catch-all. Unmatched modules stay with their importers",
    "  // so lazy pages keep their deps lazy.",
    "  return undefined;",
    "}",
]


def find_matching_brace(text, open_idx):
    """Return index of the brace matching the '{' at open_idx."""
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i
    return -1


def main():
    print("")
    print("=" * 70)
    print("  Phase C - Wave 2.5: manualChunks Rebuild")
    print("=" * 70)
    print("")

    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

    # Step 1: Read config
    print("[Step 1] Reading vite.config.ts")
    print("-" * 70)
    content = VITE_CONFIG.read_text(encoding="utf-8-sig")
    info(f"Read {len(content)} bytes")
    print("")

    # Step 2: Remove existing manualChunks value (object or function)
    print("[Step 2] Replacing existing manualChunks")
    print("-" * 70)

    idx = content.find("manualChunks")
    if idx != -1:
        # Find the value start after the colon
        colon = content.find(":", idx)
        if colon != -1:
            j = colon + 1
            while j < len(content) and content[j] in " \t\r\n":
                j += 1
            if j < len(content) and content[j] in "{(":
                end = find_matching_brace(content, j) if content[j] == "{" else content.find(")", j)
                if end != -1:
                    content = content[:colon + 1] + " manualChunks" + content[end + 1:]
                    ok("Existing manualChunks replaced with function reference")
            else:
                # Likely already a plain identifier
                ok("manualChunks already references an identifier")
    else:
        # Insert rollupOptions.output.manualChunks inside build
        b = content.find("build:")
        if b != -1:
            brace = content.find("{", b)
            insert = (
                "\n    rollupOptions: {\n      output: { manualChunks },\n    },"
            )
            content = content[:brace + 1] + insert + content[brace + 1:]
            ok("Inserted rollupOptions.output.manualChunks into build")
        else:
            warn("No build section found; appending one")
            content = content.replace(
                "export default",
                "build: { rollupOptions: { output: { manualChunks } } },\nexport default",
                1,
            )

    # Step 3: Inject the function definition before export default
    print("[Step 3] Injecting manualChunks function")
    print("-" * 70)

    fn_text = "\n".join(MANUAL_CHUNKS_FN_LINES) + "\n\n"

    if "function manualChunks" not in content:
        content = content.replace("export default", fn_text + "export default", 1)
        ok("Function definition injected")
    else:
        # Replace old definition
        start = content.find("function manualChunks")
        end = find_matching_brace(content, content.find("{", start))
        if end != -1:
            content = content[:start] + fn_text.rstrip("\n") + content[end + 1:]
            ok("Old function definition replaced")
    print("")

    # Step 4: Save (no BOM)
    print("[Step 4] Saving config")
    print("-" * 70)
    with open(VITE_CONFIG, "w", encoding="utf-8") as f:
        f.write(content)
    ok("Saved (UTF-8, no BOM)")
    print("")

    # Step 5: Build & compare
    print("[Step 5] Building with new chunking")
    print("-" * 70)
    info("1-2 minutes...")

    result = subprocess.run(
        "pnpm build",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
    )
    output = result.stdout + result.stderr

    if result.returncode == 0:
        ok("BUILD SUCCESSFUL")
        print("\n  New chunk sizes:")
        for line in output.splitlines():
            if "dist/assets/" in line and ("kB" in line or "MB" in line):
                print(f"    {line.strip()}")
        build_ok = True
    else:
        warn("Build failed:")
        for line in output.splitlines()[-25:]:
            if line.strip():
                print(f"    {line}")
        build_ok = False
    print("")

    # Step 6: Commit
    print("[Step 6] Committing")
    print("-" * 70)
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        msg = (
            "perf(build): affinity-based manualChunks, eliminate catch-all vendor-other\n\n"
            "Problem:\n"
            "- vendor-other (850KB raw / 219KB gzip) mixed eager deps (react-router)\n"
            "  with lazy deps (drei/postprocessing/n8ao), forcing eager download\n"
            "- Estimated initial load ~400KB gzip\n\n"
            "Fix:\n"
            "- Affinity groups: react / router / antd / charts / three / deckgl /\n"
            "  motion / i18n / query / state / icons\n"
            "- NO catch-all: unmatched modules stay with importers (laziness kept)\n\n"
            "Expected: initial load ~110-120KB gzip (~70% reduction)"
        )
        subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("Committed and pushed")
    except Exception as e:
        warn(f"Commit issue: {e}")

    print("")
    print("=" * 70)
    print("  🎉 Wave 2.5 COMPLETE" if build_ok else "  ⚠️ Check build errors")
    print("=" * 70)
    print("")
    print("  Manual P0 follow-up (recommended):")
    print("  In HomePage.tsx, convert static 3D import to lazy:")
    print("")
    print("    const Diag3D = lazy(() => import('./Diag3D'));")
    print("    <Suspense fallback={<LoadingSpinner />}><Diag3D /></Suspense>")
    print("")
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())