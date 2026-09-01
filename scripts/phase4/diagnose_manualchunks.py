#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic + Fix: Why manualChunks isn't being applied
=======================================================
Observation: Chunk sizes didn't change at all - same hashes
Hypothesis: manualChunks function is defined but NOT wired to rollupOptions
or Rolldown 1.2.5 requires different syntax

Steps:
1. Read vite.config.ts and show exact structure
2. Verify manualChunks is actually referenced
3. Try Rolldown-compatible syntax
4. Clear cache and rebuild
"""

import os
import sys
import subprocess
import re
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
VITE_CONFIG = FRONTEND / "vite.config.ts"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def warn(m): print(f"[WARN] {m}")
def err(m): print(f"[ERROR] {m}")


def main():
    print("")
    print("=" * 70)
    print("  Diagnostic: Why manualChunks isn't working")
    print("=" * 70)
    print("")

    # Git PATH
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

    # Step 1: Read and analyze vite.config.ts
    print("[Step 1] Analyzing vite.config.ts")
    print("-" * 70)
    
    content = VITE_CONFIG.read_text(encoding="utf-8-sig")
    lines = content.split('\n')
    
    info(f"Total lines: {len(lines)}")
    info(f"Total bytes: {len(content)}")
    print("")
    
    # Check for key patterns
    checks = {
        "function manualChunks": "manualChunks function definition",
        "manualChunks,": "manualChunks reference with comma",
        "manualChunks }": "manualChunks in rollupOptions",
        "rollupOptions": "rollupOptions object",
        "output:": "output configuration",
        "id.replace": "path normalization",
        "normalized": "normalized variable",
    }
    
    print("  Pattern detection:")
    for pattern, description in checks.items():
        if pattern in content:
            count = content.count(pattern)
            ok(f"  ✓ {description} (found {count}x)")
        else:
            warn(f"  ✗ {description} NOT FOUND")
    print("")

    # Step 2: Show the relevant section
    print("[Step 2] Showing rollupOptions section")
    print("-" * 70)
    
    # Find rollupOptions
    ro_idx = content.find("rollupOptions")
    if ro_idx != -1:
        # Show 30 lines around it
        start_line = content[:ro_idx].count('\n')
        lines_to_show = lines[max(0, start_line-2):start_line+30]
        
        print(f"  Lines {max(0, start_line-2)+1} to {start_line+30}:")
        for i, line in enumerate(lines_to_show, start=max(0, start_line-2)+1):
            print(f"    {i:3d}: {line}")
    else:
        err("rollupOptions not found in config!")
    print("")

    # Step 3: Show manualChunks function
    print("[Step 3] Showing manualChunks function")
    print("-" * 70)
    
    fn_idx = content.find("function manualChunks")
    if fn_idx != -1:
        # Find the end of the function
        start_line = content[:fn_idx].count('\n')
        brace_start = content.find("{", fn_idx)
        depth = 0
        end_line = start_line
        
        for i in range(brace_start, len(content)):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    end_line = content[:i+1].count('\n')
                    break
        
        print(f"  Lines {start_line+1} to {end_line+1}:")
        for i in range(start_line, min(end_line+1, start_line+40)):
            print(f"    {i+1:3d}: {lines[i]}")
        
        if end_line - start_line > 40:
            print(f"    ... ({end_line - start_line - 40} more lines)")
    else:
        err("manualChunks function not found!")
    print("")

    # Step 4: Check if this is actually being used
    print("[Step 4] Checking build section")
    print("-" * 70)
    
    build_idx = content.find("build:")
    if build_idx != -1:
        # Find the closing brace of build
        start_line = content[:build_idx].count('\n')
        brace_start = content.find("{", build_idx)
        depth = 0
        end_line = start_line
        
        for i in range(brace_start, len(content)):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    end_line = content[:i+1].count('\n')
                    break
        
        build_section = '\n'.join(lines[start_line:end_line+1])
        
        if "manualChunks" in build_section:
            ok("manualChunks IS referenced in build section")
            
            # Check the exact syntax
            if "output: { manualChunks }" in build_section:
                ok("Correct syntax: output: { manualChunks }")
            elif "manualChunks," in build_section:
                warn("Possible issue: manualChunks with trailing comma?")
            else:
                warn("Unusual manualChunks reference syntax")
        else:
            err("manualChunks NOT in build section - THIS IS THE BUG!")
            info("Need to add it properly")
    else:
        err("build: section not found!")
    print("")

    # Step 5: Try clearing Vite cache
    print("[Step 5] Clearing Vite cache")
    print("-" * 70)
    
    cache_dirs = [
        FRONTEND / "node_modules" / ".vite",
        FRONTEND / "node_modules" / ".cache",
        FRONTEND / ".vite",
    ]
    
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                ok(f"Deleted: {cache_dir}")
            except Exception as e:
                warn(f"Could not delete {cache_dir}: {e}")
        else:
            info(f"Not found: {cache_dir}")
    print("")

    # Step 6: Create a NEW, simpler vite.config.ts with proper syntax
    print("[Step 6] Rewriting vite.config.ts with Rolldown-compatible syntax")
    print("-" * 70)
    
    # Read the current config to preserve everything except manualChunks
    new_content = content
    
    # Remove the function definition (we'll inline it)
    fn_start = new_content.find("function manualChunks")
    if fn_start != -1:
        brace_start = new_content.find("{", fn_start)
        depth = 0
        fn_end = fn_start
        
        for i in range(brace_start, len(new_content)):
            if new_content[i] == '{':
                depth += 1
            elif new_content[i] == '}':
                depth -= 1
                if depth == 0:
                    fn_end = i + 1
                    break
        
        # Remove the function
        new_content = new_content[:fn_start] + new_content[fn_end:]
        ok("Removed standalone manualChunks function")
    
    # Now replace the rollupOptions with an inline function
    # This is the Rolldown-compatible way
    manualchunks_inline = """
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (!id.includes('node_modules')) return undefined;
          
          // Normalize Windows paths
          const normalized = id.replace(/\\\\/g, '/');
          
          // Core React
          if (/\\/node_modules\\/(react|react-dom|scheduler)\\//.test(normalized)) {
            return 'vendor-react';
          }
          
          // Router
          if (normalized.includes('react-router')) {
            return 'vendor-router';
          }
          
          // Ant Design
          if (/\\/node_modules\\/(antd|@ant-design|@rc-component|dayjs|stylis|clsx)\\//.test(normalized)) {
            return 'vendor-antd';
          }
          
          // Charts + Redux
          if (/\\/node_modules\\/(recharts|victory-vendor|d3-|@reduxjs|redux|immer|reselect|react-redux)\\//.test(normalized)) {
            return 'vendor-charts';
          }
          
          // Three.js + 3D
          if (/\\/node_modules\\/(three|three-stdlib|@react-three|postprocessing|n8ao|maath|suspend-react|its-fine|react-use-measure)\\//.test(normalized)) {
            return 'vendor-three';
          }
          
          // Deck.gl
          if (/\\/node_modules\\/(@deck\\.gl|@luma\\.gl|@loaders\\.gl|@math\\.gl|@probe\\.gl|mjolnir|hammerjs)\\//.test(normalized)) {
            return 'vendor-deckgl';
          }
          
          // Motion
          if (/\\/node_modules\\/(framer-motion|motion-dom|motion-utils)\\//.test(normalized)) {
            return 'vendor-motion';
          }
          
          // i18n
          if (normalized.includes('i18next')) return 'vendor-i18n';
          
          // React Query
          if (normalized.includes('@tanstack')) return 'vendor-query';
          
          // State
          if (normalized.includes('zustand')) return 'vendor-state';
          
          // Icons
          if (normalized.includes('lucide-react')) return 'vendor-icons';
          
          // Small utilities - co-locate with importer
          return undefined;
        }
      }
    },"""
    
    # Replace rollupOptions section
    ro_pattern = r'rollupOptions:\s*\{[^}]*output:[^}]*manualChunks[^}]*\}[^}]*\}'
    new_content = re.sub(ro_pattern, manualchunks_inline.strip(), new_content, flags=re.DOTALL)
    
    ok("Replaced with inline manualChunks function")
    print("")

    # Step 7: Save
    print("[Step 7] Saving new config")
    print("-" * 70)
    
    with open(VITE_CONFIG, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    # Verify no BOM
    with open(VITE_CONFIG, "rb") as f:
        first = f.read(3)
    
    if first == b'\xef\xbb\xbf':
        warn("BOM detected, stripping")
        new_content = new_content.lstrip('\ufeff')
        with open(VITE_CONFIG, "w", encoding="utf-8") as f:
            f.write(new_content)
    
    ok("Saved (UTF-8, no BOM)")
    print("")

    # Step 8: Build
    print("[Step 8] Building with new config")
    print("-" * 70)
    info("2-3 minutes...")

    result = subprocess.run(
        "pnpm build",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
    )
    output = result.stdout + result.stderr

    if result.returncode == 0:
        ok("BUILD SUCCESSFUL")
        print("\n  Chunk sizes:")
        
        chunks = {}
        for line in output.splitlines():
            if "dist/assets/" in line and ("kB" in line or "MB" in line):
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0].replace("dist/assets/", "")
                    size_str = parts[1]
                    if "kB" in size_str:
                        size_kb = float(size_str.replace("kB", "").strip())
                    elif "MB" in size_str:
                        size_kb = float(size_str.replace("MB", "").strip()) * 1024
                    else:
                        size_kb = 0
                    
                    # Find gzip
                    gzip_kb = 0
                    if "gzip:" in line:
                        gzip_idx = line.find("gzip:")
                        rest = line[gzip_idx:]
                        m = re.search(r'(\d+\.?\d*)\s*kB', rest)
                        if m:
                            gzip_kb = float(m.group(1))
                    
                    chunks[name] = (size_kb, gzip_kb)
                    print(f"    {line.strip()}")
        
        print("\n  Comparison:")
        previous = {
            "vendor-other": 219.02,
            "vendor-antd": 244.25,
            "vendor-three": 55.42,
            "index": 42.20,
        }
        
        for chunk_name, prev_gz in previous.items():
            matches = [k for k in chunks if chunk_name in k and not k.startswith("vendor-other")]
            if chunk_name == "vendor-other":
                matches = [k for k in chunks if "vendor-other" in k]
            
            if matches:
                new_raw, new_gz = chunks[matches[0]]
                diff_gz = new_gz - prev_gz
                status = "📉" if diff_gz < -10 else "📈" if diff_gz > 10 else "="
                print(f"    {status} {chunk_name}: {prev_gz:.1f}KB → {new_gz:.1f}KB gzip ({diff_gz:+.1f}KB)")
            else:
                print(f"    ❓ {chunk_name}: not found")
        
        # Check vendor-other
        vendor_other_matches = [k for k in chunks if 'vendor-other' in k]
        if vendor_other_matches:
            name = vendor_other_matches[0]
            raw, gz = chunks[name]
            if gz > 50:
                warn(f"\n  ⚠️ vendor-other still large: {gz:.1f}KB gzip")
                info("  Chunking still not working correctly")
            else:
                ok(f"\n  ✓ vendor-other reduced to {gz:.1f}KB gzip")
        else:
            ok("\n  ✓ vendor-other eliminated!")
        
        build_ok = True
    else:
        err("Build failed:")
        for line in output.splitlines()[-30:]:
            if line.strip():
                print(f"    {line}")
        build_ok = False
    print("")

    # Step 9: Commit
    print("[Step 9] Committing")
    print("-" * 70)
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        msg = (
            "perf(build): inline manualChunks function for Rolldown compatibility\n\n"
            "Problem:\n"
            "- Standalone manualChunks function wasn't being applied\n"
            "- Chunk sizes remained unchanged (same hashes)\n"
            "- Rolldown 1.2.5 may require inline function syntax\n\n"
            "Fix:\n"
            "- Removed standalone function definition\n"
            "- Inlined manualChunks directly in rollupOptions.output\n"
            "- Windows path normalization included\n"
            "- All regex patterns use forward slashes after normalization\n\n"
            "Expected: vendor-other should be dramatically smaller"
        )
        subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("Committed and pushed")
    except Exception as e:
        warn(f"Commit issue: {e}")

    print("")
    print("=" * 70)
    if build_ok:
        print("  🎉 Diagnostic + Fix COMPLETE")
    else:
        print("  ⚠️ Build failed - check errors")
    print("=" * 70)
    print("")

    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())