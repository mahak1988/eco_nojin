#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: ThemeContext.tsx barrel export (named vs default)
=======================================================
Root cause: ThemeContext.tsx uses named exports, not default export.
Solution: Parse the file to detect export type and generate correct barrel.
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


def detect_exports(file_path):
    """Detect if a file has default export, named exports, or both."""
    content = file_path.read_text(encoding="utf-8-sig")
    
    has_default = bool(re.search(r'export\s+default\s+', content))
    
    # Find named exports
    named_exports = set()
    for match in re.finditer(r'export\s+(?:const|let|var|function|class|enum|interface|type)\s+(\w+)', content):
        named_exports.add(match.group(1))
    for match in re.finditer(r'export\s+\{([^}]+)\}', content):
        exports_str = match.group(1)
        for exp in exports_str.split(','):
            exp = exp.strip()
            if ' as ' in exp:
                named_exports.add(exp.split(' as ')[-1].strip())
            elif exp:
                named_exports.add(exp)
    
    return {
        'has_default': has_default,
        'named_exports': named_exports
    }


def main():
    print("")
    print("=" * 70)
    print("  Fix: ThemeContext.tsx Barrel Export")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Analyze ThemeContext.tsx
    print("[Step 1] Analyzing ThemeContext.tsx")
    print("-" * 70)
    
    theme_file = SRC / "pages" / "admin" / "ThemeContext.tsx"
    
    if not theme_file.exists():
        err("ThemeContext.tsx not found!")
        return 1
    
    exports = detect_exports(theme_file)
    
    info(f"Default export: {exports['has_default']}")
    info(f"Named exports: {', '.join(sorted(exports['named_exports'])) or 'none'}")
    print("")

    # Step 2: Generate correct barrel for ThemeContext
    print("[Step 2] Generating correct barrel entry")
    print("-" * 70)
    
    if exports['has_default'] and not exports['named_exports']:
        # Only default export
        barrel_line = "export { default as ThemeContext } from './ThemeContext';"
        info("Using: default export pattern")
    elif exports['named_exports'] and not exports['has_default']:
        # Only named exports
        barrel_line = "export * from './ThemeContext';"
        info("Using: export * pattern (named exports)")
    elif exports['has_default'] and exports['named_exports']:
        # Both - use export * which handles both
        barrel_line = "export * from './ThemeContext';"
        info("Using: export * pattern (mixed exports)")
    else:
        err("No exports detected in ThemeContext.tsx!")
        return 1
    
    info(f"Barrel line: {barrel_line}")
    print("")

    # Step 3: Update admin/index.ts
    print("[Step 3] Updating admin/index.ts")
    print("-" * 70)
    
    admin_index = SRC / "pages" / "admin" / "index.ts"
    content = admin_index.read_text(encoding="utf-8-sig")
    
    # Find and replace the ThemeContext line
    pattern = r"export\s+\{[^}]*ThemeContext[^}]*\}\s+from\s+['\"]\.\/ThemeContext['\"];?\s*\n"
    if re.search(pattern, content):
        content = re.sub(pattern, barrel_line + "\n", content)
        ok("Replaced ThemeContext export line")
    else:
        # Line might not exist yet - add it
        if "ThemeContext" not in content:
            content = content.rstrip() + "\n" + barrel_line + "\n"
            ok("Added ThemeContext export line")
        else:
            warn("ThemeContext already in barrel - checking format")
            if "export { default as ThemeContext }" in content and not exports['has_default']:
                content = content.replace(
                    "export { default as ThemeContext } from './ThemeContext';",
                    barrel_line
                )
                ok("Fixed ThemeContext export format")
    
    admin_index.write_text(content, encoding="utf-8")
    ok("Saved admin/index.ts")
    print("")

    # Step 4: Check if App.tsx needs ThemeProvider
    print("[Step 4] Checking App.tsx for ThemeProvider usage")
    print("-" * 70)
    
    app_file = SRC / "App.tsx"
    app_content = app_file.read_text(encoding="utf-8-sig")
    
    # Check if ThemeProvider is used in JSX
    uses_theme_provider = "<ThemeProvider" in app_content or "ThemeProvider>" in app_content
    
    if uses_theme_provider:
        info("ThemeProvider is used in App.tsx JSX")
        
        # Check if it's imported
        if "ThemeProvider" not in app_content.split("import")[1] if "import" in app_content else "":
            # Need to add import
            # Find where to insert (after other admin imports)
            admin_import_match = re.search(
                r"(import\s+\{[^}]+\}\s+from\s+['\"]\.\/pages\/admin['\"];?\s*\n)",
                app_content
            )
            
            if admin_import_match:
                # Add ThemeProvider to the import list
                import_line = admin_import_match.group(1)
                if "ThemeProvider" not in import_line:
                    # Insert ThemeProvider before the closing }
                    new_import = import_line.replace("} from", ", ThemeProvider } from")
                    app_content = app_content.replace(import_line, new_import)
                    app_file.write_text(app_content, encoding="utf-8")
                    ok("Added ThemeProvider to App.tsx imports")
            else:
                # No admin import found - add one
                new_import = "import { ThemeProvider } from './pages/admin';\n"
                # Insert after last import
                lines = app_content.split("\n")
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith("import "):
                        insert_idx = i + 1
                lines.insert(insert_idx, new_import.rstrip())
                app_content = "\n".join(lines)
                app_file.write_text(app_content, encoding="utf-8")
                ok("Added ThemeProvider import to App.tsx")
    else:
        info("ThemeProvider not used in App.tsx - no import needed")
    print("")

    # Step 5: Build verification
    print("[Step 5] Build verification")
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

    # Step 6: Commit
    if build_ok:
        print("[Step 6] Committing")
        print("-" * 70)
        try:
            subprocess.run("git add -A .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "fix(barrel): ThemeContext.tsx named export detection\\n\\n"
                "Root cause: ThemeContext.tsx uses named exports (e.g., ThemeProvider)\\n"
                "but barrel generator assumed default export.\\n\\n"
                "Solution:\\n"
                "- Parse ThemeContext.tsx to detect export type\\n"
                "- Use 'export *' for named exports (not 'export { default }')\\n"
                "- Ensure App.tsx imports ThemeProvider if used in JSX\\n\\n"
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
        print("    • ThemeContext.tsx: correctly exported via barrel")
        print("    • App.tsx: ThemeProvider imported if needed")
        print("    • Build: green")
        print("    • Workspace: fully clean")
        print("")
        print("  Ready for standard simulator rebuild!")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())