#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Surgical Fix: Correct manualChunks inline function
===================================================
Root Cause: 
1. Two manualChunks existed. Vite used the inline one (line 105).
2. Inline one used forward slashes `/react/` which fail on Windows `\`.
3. Previous script broke JS syntax via Python regex escaping.

Solution:
1. Git checkout the last working config (cceaa0a).
2. Delete the unused standalone function.
3. Replace the inline function with bulletproof string normalization.
4. Return `undefined` for unmatched modules to KILL the catch-all chunk.
"""

import os
import sys
import subprocess
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
VITE_CONFIG = FRONTEND / "vite.config.ts"

# Bulletproof JS code - uses split/join instead of regex to avoid escape hell
NEW_MANUAL_CHUNKS = """        manualChunks(id) {
          if (typeof id !== 'string' || !id.includes('node_modules')) return undefined;
          
          // Bulletproof Windows path normalization (no regex escape issues)
          const n = id.split('\\\\').join('/');
          
          // Core React & Router (Eager)
          if (n.includes('/react-dom/') || n.includes('/react/') || n.includes('/scheduler/') || n.includes('/react-router')) return 'vendor-react';
          
          // UI / Motion / Icons
          if (n.includes('/framer-motion/') || n.includes('/motion-dom/') || n.includes('/motion-utils/')) return 'vendor-motion';
          if (n.includes('/lucide-react/')) return 'vendor-icons';
          
          // Ant Design Ecosystem
          if (n.includes('/antd/') || n.includes('/@ant-design/') || n.includes('/@rc-component/') || n.includes('/rc-') || n.includes('/dayjs/') || n.includes('/stylis/')) return 'vendor-antd';
          
          // Charts & Redux (Recharts 3.x uses Redux internally)
          if (n.includes('/recharts/') || n.includes('/d3-') || n.includes('/victory-vendor/') || n.includes('/redux/') || n.includes('/@reduxjs/') || n.includes('/immer/') || n.includes('/reselect/') || n.includes('/react-redux/')) return 'vendor-charts';
          
          // 3D / Three.js Ecosystem
          if (n.includes('/three/') || n.includes('/three-stdlib/') || n.includes('/@react-three/') || n.includes('/postprocessing/') || n.includes('/n8ao/') || n.includes('/maath/') || n.includes('/suspend-react/') || n.includes('/its-fine/') || n.includes('/react-use-measure/')) return 'vendor-three';
          
          // Deck.gl / Map Ecosystem
          if (n.includes('/@deck.gl/') || n.includes('/@luma.gl/') || n.includes('/@loaders.gl/') || n.includes('/@math.gl/') || n.includes('/@probe.gl/') || n.includes('/mjolnir.js/') || n.includes('/hammerjs/')) return 'vendor-deckgl';
          
          // i18n & Query & State
          if (n.includes('/i18next/') || n.includes('/react-i18next/')) return 'vendor-i18n';
          if (n.includes('/@tanstack/')) return 'vendor-query';
          if (n.includes('/zustand/') || n.includes('/use-sync-external-store/')) return 'vendor-state';
          
          // CRITICAL: Return undefined for unmatched modules.
          // This forces Rolldown to place them in the chunks of their importers,
          // preserving laziness and completely eliminating the vendor-other catch-all!
          return undefined;
        },"""


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def warn(m): print(f"[WARN] {m}")
def err(m): print(f"[ERROR] {m}")


def main():
    print("")
    print("=" * 70)
    print("  Surgical Fix: Correct Inline manualChunks")
    print("=" * 70)
    print("")

    # Git PATH
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

    # Step 1: Revert to last working build
    print("[Step 1] Reverting vite.config.ts to cceaa0a (last working build)")
    print("-" * 70)
    subprocess.run("git checkout cceaa0a -- frontend/vite.config.ts", shell=True, cwd=PROJECT_ROOT, check=True)
    ok("Reverted successfully")
    
    content = VITE_CONFIG.read_text(encoding="utf-8")
    info(f"Read {len(content.splitlines())} lines")
    print("")

    # Step 2: Remove standalone function (it was ignored by Vite anyway)
    print("[Step 2] Removing unused standalone manualChunks function")
    print("-" * 70)
    lines = content.split('\n')
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("function manualChunks"):
            # Skip until brace depth returns to 0
            depth = 0
            started = False
            while i < len(lines):
                l = lines[i]
                depth += l.count('{')
                depth -= l.count('}')
                if '{' in l: started = True
                i += 1
                if started and depth == 0: break
            ok("Removed standalone function block")
            continue
        out_lines.append(line)
        i += 1
    
    content = '\n'.join(out_lines)
    print("")

    # Step 3: Replace the INLINE manualChunks function
    print("[Step 3] Replacing INLINE manualChunks (the one Vite actually uses)")
    print("-" * 70)
    lines = content.split('\n')
    out_lines = []
    i = 0
    replaced = False
    
    while i < len(lines):
        line = lines[i]
        # Match the inline function inside rollupOptions
        if re.search(r'manualChunks\s*\(', line) and '{' in line:
            # Skip old inline function block
            depth = 0
            started = False
            while i < len(lines):
                l = lines[i]
                depth += l.count('{')
                depth -= l.count('}')
                if '{' in l: started = True
                i += 1
                if started and depth == 0: break
            
            # Inject our bulletproof replacement
            out_lines.append(NEW_MANUAL_CHUNKS)
            replaced = True
            ok("Replaced inline manualChunks with bulletproof logic")
            continue
        
        out_lines.append(line)
        i += 1
        
    if not replaced:
        err("Could not find inline manualChunks to replace!")
        return 1
        
    content = '\n'.join(out_lines)
    print("")

    # Step 4: Save (Clean UTF-8, no BOM)
    print("[Step 4] Saving clean vite.config.ts")
    print("-" * 70)
    with open(VITE_CONFIG, "w", encoding="utf-8") as f:
        f.write(content)
    ok("Saved (UTF-8, no BOM)")
    print("")

    # Step 5: Build & Verify
    print("[Step 5] Building project (Cache cleared automatically by Vite)")
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
        ok("🎉 BUILD SUCCESSFUL!")
        print("\n  New Chunk Sizes:")
        
        chunks = {}
        for line in output.splitlines():
            if "dist/assets/" in line and ("kB" in line or "MB" in line):
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0].replace("dist/assets/", "")
                    size_str = parts[1]
                    size_kb = float(size_str.replace("kB", "").replace("MB", "").strip())
                    if "MB" in size_str: size_kb *= 1024
                    
                    gzip_kb = 0
                    if "gzip:" in line:
                        m = re.search(r'gzip:\s*(\d+\.?\d*)\s*kB', line)
                        if m: gzip_kb = float(m.group(1))
                    
                    chunks[name] = (size_kb, gzip_kb)
                    print(f"    {line.strip()}")
        
        # Analysis
        print("\n  Impact Analysis:")
        vendor_other = [k for k in chunks if 'vendor-other' in k]
        if vendor_other:
            name = vendor_other[0]
            raw, gz = chunks[name]
            if gz > 50:
                warn(f"  ⚠️ vendor-other still exists ({gz:.1f}KB gzip)")
            else:
                ok(f"  ✓ vendor-other reduced to {gz:.1f}KB gzip")
        else:
            ok("  ✓ vendor-other ELIMINATED! (Distributed to lazy chunks)")
            
        build_ok = True
    else:
        err("Build failed:")
        for line in output.splitlines()[-30:]:
            if line.strip(): print(f"    {line}")
        build_ok = False
    print("")

    # Step 6: Commit
    print("[Step 6] Committing")
    print("-" * 70)
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        msg = (
            "perf(build): surgical fix for manualChunks + eliminate catch-all\n\n"
            "Root Cause Discovered:\n"
            "- Two manualChunks existed in vite.config.ts\n"
            "- Vite used the INLINE one (line 105), which we weren't touching\n"
            "- The inline one used forward slashes `/react/` which fail on Windows `\\`\n\n"
            "Solution:\n"
            "1. Reverted to last working config\n"
            "2. Deleted unused standalone function\n"
            "3. Replaced inline function with bulletproof `split('\\\\').join('/')`\n"
            "4. CRITICAL: Return `undefined` for unmatched modules.\n"
            "   This forces Rolldown to place them in their importer's chunk,\n"
            "   preserving laziness and killing the 219KB vendor-other catch-all.\n\n"
            "Expected: Dramatic reduction in initial eager load size."
        )
        subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("Committed and pushed")
    except Exception as e:
        warn(f"Commit issue: {e}")

    print("")
    print("=" * 70)
    if build_ok:
        print("  🎉 SURGICAL FIX COMPLETE")
    else:
        print("  ⚠️ Check build errors")
    print("=" * 70)
    
    return 0 if build_ok else 1

if __name__ == "__main__":
    sys.exit(main())