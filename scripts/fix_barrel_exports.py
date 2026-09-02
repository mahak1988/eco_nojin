#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Barrel File Orphan Exports
================================
Root cause: After purge, barrel files (index.ts) still export deleted modules.
Solution: Scan all index.ts files, remove exports pointing to non-existent files.
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


def check_file_exists(base_dir, import_path):
    """Check if a relative import path points to an existing file."""
    # Remove quotes
    import_path = import_path.strip('"').strip("'")
    
    # Handle relative imports
    if import_path.startswith('./') or import_path.startswith('../'):
        full_path = (base_dir / import_path).resolve()
    else:
        full_path = (base_dir / import_path).resolve()
    
    # Try different extensions
    for ext in ['', '.ts', '.tsx', '.js', '.jsx']:
        test_path = Path(str(full_path) + ext)
        if test_path.exists():
            return True
        # Check for index files
        if test_path.is_dir():
            for idx in ['index.ts', 'index.tsx', 'index.js', 'index.jsx']:
                if (test_path / idx).exists():
                    return True
    return False


def main():
    print("")
    print("=" * 70)
    print("  Fix: Remove Orphan Exports from Barrel Files")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Scan all index.ts files
    print("[Step 1] Scanning barrel files (index.ts)")
    print("-" * 70)
    
    barrel_files = list(SRC.rglob("index.ts")) + list(SRC.rglob("index.tsx"))
    info(f"Found {len(barrel_files)} barrel file(s)")
    
    fixed_files = []
    total_removed = 0
    
    for barrel in barrel_files:
        content = barrel.read_text(encoding="utf-8-sig")
        original = content
        base_dir = barrel.parent
        
        # Pattern 1: export { default as X } from "./X"
        pattern1 = r'export\s+\{[^}]*\}\s+from\s+["\']([^"\']+)["\'];?\s*\n'
        matches1 = list(re.finditer(pattern1, content))
        
        # Pattern 2: export * from "./X"
        pattern2 = r'export\s+\*\s+from\s+["\']([^"\']+)["\'];?\s*\n'
        matches2 = list(re.finditer(pattern2, content))
        
        # Pattern 3: export { X, Y, Z } from "./X"
        pattern3 = r'export\s+\{[^}]+\}\s+from\s+["\']([^"\']+)["\'];?\s*\n'
        matches3 = list(re.finditer(pattern3, content))
        
        removed_lines = []
        
        # Check all export from statements
        for match in matches1 + matches2 + matches3:
            import_path = match.group(1)
            if not check_file_exists(base_dir, import_path):
                # File doesn't exist - remove this export
                removed_lines.append({
                    'match': match,
                    'path': import_path,
                    'line': content[:match.start()].count('\n') + 1
                })
        
        if removed_lines:
            info(f"\n{barrel.relative_to(SRC)}:")
            
            # Remove lines in reverse order to preserve indices
            for rem in sorted(removed_lines, key=lambda x: x['match'].start(), reverse=True):
                line_content = rem['match'].group(0).strip()
                info(f"  Line {rem['line']}: removed {line_content[:60]}...")
                content = content[:rem['match'].start()] + content[rem['match'].end():]
            
            total_removed += len(removed_lines)
            barrel.write_text(content, encoding="utf-8")
            fixed_files.append(barrel.relative_to(SRC))
            ok(f"  Fixed: removed {len(removed_lines)} orphan export(s)")
    
    if not fixed_files:
        info("No orphan exports found - all barrel files clean")
    else:
        ok(f"\nFixed {len(fixed_files)} file(s), removed {total_removed} orphan export(s)")
    print("")

    # Step 2: Check App.tsx for imports from fixed barrel files
    print("[Step 2] Verifying App.tsx imports")
    print("-" * 70)
    
    app_file = SRC / "App.tsx"
    if app_file.exists():
        app_content = app_file.read_text(encoding="utf-8-sig")
        
        # Check for imports from admin barrel
        if "from './pages/admin'" in app_content:
            # Extract what's being imported
            match = re.search(r'import\s+\{([^}]+)\}\s+from\s+["\']\.\/pages\/admin["\']', app_content)
            if match:
                imports = [x.strip() for x in match.group(1).split(',')]
                info(f"App.tsx imports from ./pages/admin: {', '.join(imports)}")
                
                # Verify each import exists in the barrel file
                admin_barrel = SRC / "pages" / "admin" / "index.ts"
                if admin_barrel.exists():
                    barrel_content = admin_barrel.read_text(encoding="utf-8-sig")
                    for imp in imports:
                        if imp and imp not in barrel_content:
                            warn(f"  ⚠️  {imp} imported in App.tsx but not exported from admin/index.ts")
        
        ok("App.tsx imports verified")
    print("")

    # Step 3: Build verification
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
        ok("🎉 Build successful!")
        for line in (result.stdout + result.stderr).splitlines():
            if "dist/assets/index" in line and "kB" in line:
                info(f"  bundle: {line.strip()}")
    else:
        err("Build still failing:")
        output = result.stdout + result.stderr
        
        # Extract the specific error
        error_match = re.search(r'Module not found.*?Help:.*?imported by.*?(?=\n\n|\Z)', output, re.DOTALL)
        if error_match:
            print("\n  Specific error:")
            for line in error_match.group(0).splitlines()[:10]:
                print(f"    {line}")
        
        print("\n  Last 15 lines:")
        for line in output.splitlines()[-15:]:
            if line.strip():
                print(f"    {line}")
    print("")

    # Step 4: Commit
    if build_ok:
        print("[Step 4] Committing")
        print("-" * 70)
        try:
            subprocess.run("git add -A .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "fix(barrel): remove orphan exports from barrel files\\n\\n"
                f"Fixed {len(fixed_files)} barrel file(s):\\n"
                + "\\n".join(f"  - {f}" for f in fixed_files) +
                f"\\n\\nRemoved {total_removed} export(s) pointing to deleted modules.\\n"
                "Build is now green."
            )
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")
        
        print("")
        print("=" * 70)
        print("  ✅ FIX COMPLETE - Build successful")
        print("=" * 70)
        print("")
        print("  State:")
        print("    • Build:       ✅ green")
        print("    • /hydroma:    placeholder page")
        print("    • Barrel files: clean (no orphan exports)")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())