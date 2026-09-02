#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Dynamic admin/index.ts (corrected regex + subdirectory handling)
======================================================================
"""

import os
import sys
import subprocess
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
SRC = FRONTEND / "src"


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
    print("  Fix: Dynamic admin/index.ts (v2 - corrected)")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Scan actual files in admin directory
    print("[Step 1] Scanning src/pages/admin/")
    print("-" * 70)
    
    admin_dir = SRC / "pages" / "admin"
    
    if not admin_dir.exists():
        err("Directory src/pages/admin/ does not exist!")
        return 1
    
    # Find all .tsx and .ts files (excluding index files)
    tsx_files = list(admin_dir.glob("*.tsx")) + list(admin_dir.glob("*.ts"))
    tsx_files = [f for f in tsx_files if f.stem != "index"]
    
    # Find subdirectories with index files
    subdirs = []
    for subdir in admin_dir.iterdir():
        if subdir.is_dir():
            index_files = list(subdir.glob("index.ts*"))
            if index_files:
                subdirs.append(subdir.name)
    
    info(f"Found {len(tsx_files)} direct files:")
    for f in sorted(tsx_files):
        info(f"  ✓ {f.name}")
    
    info(f"Found {len(subdirs)} subdirectories:")
    for s in sorted(subdirs):
        info(f"  ✓ {s}/")
    
    print("")

    # Step 2: Generate barrel file dynamically
    print("[Step 2] Generating admin/index.ts")
    print("-" * 70)
    
    exports = []
    
    # Direct files (default exports)
    for f in sorted(tsx_files):
        name = f.stem
        # Skip non-component files
        if name in ["styles", "types", "utils", "constants"]:
            continue
        exports.append(f"export {{ default as {name} }} from './{name}';")
    
    # Subdirectories (export * from)
    for subdir in sorted(subdirs):
        exports.append(f"export * from './{subdir}';")
    
    # Build the file content
    content = "// Auto-generated barrel file - exports only verified files\n"
    content += "\n".join(exports) + "\n"
    
    info(f"Generated {len(exports)} exports")
    for exp in exports:
        info(f"  {exp}")
    
    # Write the file
    admin_index = admin_dir / "index.ts"
    admin_index.write_text(content, encoding="utf-8")
    ok(f"Written to {admin_index.relative_to(SRC)}")
    print("")

    # Step 3: Update App.tsx imports to match
    print("[Step 3] Updating App.tsx imports")
    print("-" * 70)
    
    app_file = SRC / "App.tsx"
    if app_file.exists():
        app_content = app_file.read_text(encoding="utf-8-sig")
        
        # Extract available export names using re.match (not str.match)
        available = set()
        for exp in exports:
            # Pattern: export { default as Name } or export { Name } or export * from
            match = re.match(r'export\s+\{\s*(?:default\s+as\s+)?(\w+)', exp)
            if match:
                available.add(match.group(1))
            elif 'export *' in exp:
                # For "export * from './subdir'", we can't know names statically
                # Just add the subdir name as a hint
                subdir_name = exp.split("'./")[1].split("'")[0]
                available.add(subdir_name)
        
        info(f"Available exports: {', '.join(sorted(available))}")
        
        # Find admin import in App.tsx
        admin_import_match = re.search(
            r"import\s+\{([^}]+)\}\s+from\s+['\"]\.\/pages\/admin['\"]",
            app_content
        )
        
        if admin_import_match:
            imports_str = admin_import_match.group(1)
            current_imports = [x.strip().split(' as ')[0].strip() for x in imports_str.split(',')]
            current_imports = [x for x in current_imports if x]
            
            # Find dead imports
            dead = [i for i in current_imports if i not in available]
            live = [i for i in current_imports if i in available]
            
            if dead:
                info(f"Dead imports found: {', '.join(dead)}")
                
                # Remove dead imports
                for d in dead:
                    pattern = r"\b" + re.escape(d) + r"(?:\s+as\s+\w+)?,?\s*"
                    app_content = re.sub(pattern, "", app_content, count=1)
                
                # Clean up
                app_content = re.sub(r"import\s+\{\s*,\s*", "import { ", app_content)
                app_content = re.sub(r",\s*\}\s+from", " } from", app_content)
                app_content = re.sub(r",\s*,+", ",", app_content)
                app_content = re.sub(r"\{\s+,", "{", app_content)
                
                app_file.write_text(app_content, encoding="utf-8")
                ok(f"Removed {len(dead)} dead import(s) from App.tsx")
            else:
                ok("All App.tsx imports are valid")
        else:
            info("No import from ./pages/admin found in App.tsx")
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
        output = result.stdout + result.stderr
        
        # Extract first error
        err_match = re.search(r"(\[.*?\][^\n]+(?:\n[^\n]{0,100})*)", output)
        if err_match:
            print(f"\n  First error:\n{err_match.group(1)}")
        
        print("\n  Last 20 lines:")
        for line in output.splitlines()[-20:]:
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
                "fix(admin): dynamic barrel file (v2 - corrected regex)\\n\\n"
                f"Generated admin/index.ts with {len(exports)} exports:\\n"
                "- Scanned src/pages/admin/ for actual .tsx files\\n"
                "- Only exports files that exist\\n"
                "- Handles subdirectories with 'export * from'\\n"
                "- Fixed regex: re.match(pattern, string) not str.match()\\n"
                "- Updated App.tsx to remove dead imports\\n\\n"
                "Build is now green. Workspace fully clean."
            )
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")
        
        print("")
        print("=" * 70)
        print("  ✅ COMPLETE - Build successful")
        print("=" * 70)
        print("")
        print("  Final state:")
        print(f"    • admin/index.ts: {len(exports)} verified exports")
        print("    • Build: green")
        print("    • Workspace: fully clean")
        print("")
        print("  Ready for standard simulator rebuild!")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())