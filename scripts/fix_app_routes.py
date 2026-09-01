#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Routes JSX nesting error in App.tsx
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
APP_FILE = FRONTEND / "src" / "App.tsx"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def err(m): print(f"[ERROR] {m}")


def main():
    print("")
    print("=" * 70)
    print("  Fix Routes JSX Nesting Error")
    print("=" * 70)
    print("")

    # Step 1: Read file
    print("[Step 1] Reading App.tsx")
    print("-" * 70)
    
    content = APP_FILE.read_text(encoding="utf-8")
    lines = content.split('\n')
    
    info(f"Total lines: {len(lines)}")
    print("")

    # Step 2: Show the problematic area
    print("[Step 2] Lines 65-250 (around the error)")
    print("-" * 70)
    
    for i in range(64, min(250, len(lines))):
        marker = " >>>" if i in [70, 241, 242] else "    "
        print(f"{marker} {i+1:3d}: {lines[i]}")
    
    print("")

    # Step 3: Find the issue
    print("[Step 3] Analyzing structure")
    print("-" * 70)
    
    # Count tags
    routes_open = content.count('<Routes')
    routes_close = content.count('</Routes>')
    
    info(f"<Routes>: {routes_open} open, {routes_close} close")
    
    # Find all Route elements
    route_count = content.count('<Route ')
    info(f"<Route> elements: {route_count}")
    
    print("")

    # Step 4: Try to fix
    print("[Step 4] Attempting fix")
    print("-" * 70)
    
    fixed = False
    
    # Strategy 1: Check if </Routes> is missing
    if routes_open > routes_close:
        info(f"Missing {routes_open - routes_close} </Routes> tag(s)")
        
        # Find the last Route element
        last_route_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if '<Route ' in lines[i] or (lines[i].strip().startswith('<Route') and i > 70):
                last_route_idx = i
                break
        
        if last_route_idx >= 0:
            info(f"Last Route at line {last_route_idx + 1}")
            
            # Check if there's a closing tag for something else right after
            # Look for pattern: last Route, then some closing tags, but no </Routes>
            for i in range(last_route_idx + 1, min(last_route_idx + 10, len(lines))):
                line = lines[i]
                if '</ProtectedRoute>' in line or '</Suspense>' in line or '</AuthProvider>' in line:
                    # This is where </Routes> should be
                    indent = len(lines[last_route_idx]) - len(lines[last_route_idx].lstrip())
                    routes_close_line = ' ' * indent + '</Routes>'
                    lines.insert(i, routes_close_line)
                    ok(f"Added </Routes> at line {i + 1}")
                    fixed = True
                    break
    
    # Strategy 2: Check for misplaced </Routes>
    elif routes_close > routes_open:
        info(f"Extra {routes_close - routes_open} </Routes> tag(s)")
        
        # Find and remove the extra one
        for i in range(len(lines)):
            if '</Routes>' in lines[i] and i < 200:  # Too early
                lines[i] = lines[i].replace('</Routes>', '')
                ok(f"Removed early </Routes> from line {i + 1}")
                fixed = True
                break
    
    # Strategy 3: Check if Route elements are outside Routes
    if not fixed:
        info("Checking for Route elements outside <Routes>...")
        
        # Track if we're inside <Routes>
        in_routes = False
        for i, line in enumerate(lines):
            if '<Routes>' in line:
                in_routes = True
            elif '</Routes>' in line:
                in_routes = False
            elif '<Route ' in line and not in_routes and i > 50:
                warn(f"Route at line {i+1} is outside <Routes>")
    
    if not fixed:
        # Alternative: Look for the exact pattern in the error
        # The error says line 242 has </ProtectedRoute> but expects </Routes>
        # This means </Routes> should come before </ProtectedRoute>
        
        info("Trying pattern-based fix...")
        
        # Find line 242 area
        for i in range(240, min(245, len(lines))):
            if '</ProtectedRoute>' in lines[i]:
                # Check if </Routes> is missing before this
                has_routes_close_before = False
                for j in range(max(0, i - 10), i):
                    if '</Routes>' in lines[j]:
                        has_routes_close_before = True
                        break
                
                if not has_routes_close_before:
                    # Add </Routes> before </ProtectedRoute>
                    indent = len(lines[i]) - len(lines[i].lstrip())
                    routes_close_line = ' ' * indent + '</Routes>'
                    lines.insert(i, routes_close_line)
                    ok(f"Added </Routes> before </ProtectedRoute> at line {i + 1}")
                    fixed = True
                    break
    
    if fixed:
        # Save and rebuild
        new_content = '\n'.join(lines)
        APP_FILE.write_text(new_content, encoding="utf-8")
        ok("Saved App.tsx")
        print("")
        
        # Try build
        print("[Step 5] Testing build")
        print("-" * 70)
        
        result = subprocess.run(
            "pnpm build",
            shell=True, cwd=FRONTEND,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300,
        )
        
        if result.returncode == 0:
            ok("🎉 Build successful!")
            build_ok = True
        else:
            err("Build still failing")
            output = result.stdout + result.stderr
            for line in output.splitlines()[-20:]:
                if line.strip():
                    print(f"    {line}")
            build_ok = False
    else:
        err("Could not apply automated fix")
        build_ok = False
    
    print("")

    # Step 6: Show result
    if build_ok:
        print("=" * 70)
        print("  🎉 FIX SUCCESSFUL!")
        print("=" * 70)
        print("")
        print("  Run: pnpm dev")
        print("  Then visit: http://localhost:5173/hydroma")
        print("")
        
        # Commit
        print("[Commit] Saving fix")
        print("-" * 70)
        try:
            for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
                if Path(p).exists() and p not in os.environ["PATH"]:
                    os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
            
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = "fix(jsx): fix Routes nesting in App.tsx"
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")
    else:
        print("=" * 70)
        print("  ⚠️ Manual fix required")
        print("=" * 70)
        print("")
        print("  Open: frontend/src/App.tsx")
        print("  Go to line 242")
        print("")
        print("  The structure should be:")
        print("    <Routes>")
        print("      <Route ... />")
        print("      <Route ... />")
        print("    </Routes>  ← Add this before </ProtectedRoute>")
        print("    </ProtectedRoute>")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())