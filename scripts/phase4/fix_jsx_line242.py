#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Precise JSX Fix for Line 242 Error
====================================
Problem: Expected </Routes> at line 242 but found </ProtectedRoute>
Solution: Analyze lines 220-250, find the nesting issue, fix it
"""

import os
import sys
import subprocess
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
APP_FILE = FRONTEND / "src" / "App.tsx"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def warn(m): print(f"[WARN] {m}")
def err(m): print(f"[ERROR] {m}")


def setup_git_path():
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


def main():
    print("")
    print("=" * 70)
    print("  Precise JSX Fix for Line 242")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Read and analyze the problematic area
    print("[Step 1] Analyzing lines 220-260 (around the error)")
    print("-" * 70)
    
    content = APP_FILE.read_text(encoding="utf-8-sig")
    lines = content.split('\n')
    
    # Show lines 220-260
    print("\n  Lines 220-260:")
    for i in range(219, min(260, len(lines))):
        marker = " >>>" if i == 241 else "    "  # Line 242 is index 241
        print(f"{marker} {i+1:3d}: {lines[i]}")
    
    print("")

    # Step 2: Check for common patterns
    print("[Step 2] Checking for common JSX nesting issues")
    print("-" * 70)
    
    # Count tag occurrences
    routes_open = 0
    routes_close = 0
    protected_open = 0
    protected_close = 0
    
    for i, line in enumerate(lines):
        routes_open += len(re.findall(r'<Routes[\s>]', line))
        routes_close += len(re.findall(r'</Routes>', line))
        protected_open += len(re.findall(r'<ProtectedRoute[\s>]', line))
        protected_close += len(re.findall(r'</ProtectedRoute>', line))
    
    info(f"<Routes>: {routes_open} open, {routes_close} close")
    info(f"<ProtectedRoute>: {protected_open} open, {protected_close} close")
    
    print("")

    # Step 3: Find the issue
    print("[Step 3] Identifying the nesting problem")
    print("-" * 70)
    
    # Strategy: Track tag depth as we go through lines
    tag_stack = []
    issues = []
    
    for i, line in enumerate(lines):
        # Find opening tags
        for match in re.finditer(r'<(\w+)[\s>]', line):
            tag = match.group(1)
            if tag in ['Routes', 'ProtectedRoute', 'Suspense', 'ErrorBoundary', 'AuthProvider', 'SimulationPipelineProvider']:
                tag_stack.append((tag, i + 1))
        
        # Find closing tags
        for match in re.finditer(r'</(\w+)>', line):
            tag = match.group(1)
            if tag_stack and tag_stack[-1][0] == tag:
                tag_stack.pop()
            elif tag_stack:
                # Mismatch - this is the error
                expected = tag_stack[-1][0]
                issues.append({
                    'line': i + 1,
                    'found': tag,
                    'expected': expected,
                    'opened_at': tag_stack[-1][1]
                })
                # Try to recover by finding the matching open tag
                for j in range(len(tag_stack) - 1, -1, -1):
                    if tag_stack[j][0] == tag:
                        # Pop everything up to and including this tag
                        tag_stack = tag_stack[:j]
                        break
    
    if issues:
        err(f"Found {len(issues)} nesting issue(s):")
        for issue in issues[:5]:  # Show first 5
            print(f"  Line {issue['line']}: Found </{issue['found']}>, expected </{issue['expected']}> (opened at line {issue['opened_at']})")
    else:
        info("No obvious nesting issues found via simple parsing")
    
    print("")

    # Step 4: Try to fix
    print("[Step 4] Attempting automated fix")
    print("-" * 70)
    
    fixed = False
    
    # Common issue: </Routes> appears before all Routes are done
    # Look for pattern where </Routes> comes right before </ProtectedRoute>
    for i in range(len(lines) - 1):
        if '</Routes>' in lines[i] and i + 1 < len(lines):
            # Check if next non-empty line is </ProtectedRoute> or similar
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip():
                    if '</ProtectedRoute>' in lines[j] or '</Suspense>' in lines[j]:
                        # This is likely wrong - </Routes> should come later
                        warn(f"Found suspicious pattern at line {i+1}: </Routes> before {lines[j].strip()[:30]}")
                        
                        # Check if there's another </Routes> later
                        has_later_routes = False
                        for k in range(j, len(lines)):
                            if '</Routes>' in lines[k]:
                                has_later_routes = True
                                break
                        
                        if not has_later_routes:
                            # This </Routes> at line i is probably misplaced
                            # Remove it
                            lines[i] = lines[i].replace('</Routes>', '')
                            ok(f"Removed misplaced </Routes> from line {i+1}")
                            fixed = True
                        break
                    break
    
    # Alternative fix: Look for Route elements without proper nesting
    # Check if there's a Route outside of Routes
    for i, line in enumerate(lines):
        if '<Route ' in line or '<Route>' in line:
            # Check if we're inside <Routes>
            before = '\n'.join(lines[:i])
            routes_before = before.count('<Routes')
            routes_close_before = before.count('</Routes>')
            
            if routes_before <= routes_close_before:
                warn(f"Route at line {i+1} might be outside <Routes>")
    
    if fixed:
        # Save and rebuild
        new_content = '\n'.join(lines)
        APP_FILE.write_text(new_content, encoding="utf-8")
        ok("Saved App.tsx")
        
        # Try build
        info("Retrying build...")
        result = subprocess.run(
            "pnpm build",
            shell=True, cwd=FRONTEND,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300,
        )
        
        if result.returncode == 0:
            ok("🎉 Build successful after fix!")
            build_ok = True
        else:
            err("Build still failing")
            output = result.stdout + result.stderr
            for line in output.splitlines()[-15:]:
                if line.strip():
                    print(f"    {line}")
            build_ok = False
    else:
        info("No automated fix applied - trying alternative approach")
        
        # Alternative: Add missing </Routes> in the right place
        # Find the last Route element and ensure </Routes> comes after it
        last_route_line = -1
        for i in range(len(lines) - 1, -1, -1):
            if '<Route ' in lines[i] or 'path=' in lines[i]:
                last_route_line = i
                break
        
        if last_route_line >= 0:
            info(f"Last Route element at line {last_route_line + 1}")
            
            # Check if </Routes> comes after it
            has_routes_after = False
            for i in range(last_route_line, min(last_route_line + 20, len(lines))):
                if '</Routes>' in lines[i]:
                    has_routes_after = True
                    break
            
            if not has_routes_after:
                # Add </Routes> after the last Route
                indent = len(lines[last_route_line]) - len(lines[last_route_line].lstrip())
                routes_close = ' ' * indent + '          </Routes>'
                lines.insert(last_route_line + 1, routes_close)
                ok(f"Added </Routes> after line {last_route_line + 1}")
                
                new_content = '\n'.join(lines)
                APP_FILE.write_text(new_content, encoding="utf-8")
                
                # Try build again
                info("Retrying build...")
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
                    build_ok = False
            else:
                info("</Routes> already present after last Route")
                build_ok = False
        else:
            err("Could not find last Route element")
            build_ok = False
    
    print("")

    # Step 5: If still failing, show detailed guidance
    if not build_ok:
        print("[Step 5] Manual fix guidance")
        print("-" * 70)
        print("")
        print("  The JSX nesting is complex. Please manually check:")
        print("")
        print("  1. Open: frontend/src/App.tsx")
        print("")
        print("  2. Look for this structure (should be like this):")
        print("     <AuthProvider>")
        print("       <SimulationPipelineProvider>")
        print("         <Suspense>")
        print("           <Routes>")
        print("             <Route path=\"/\" element={...} />")
        print("             <Route path=\"/cinematic\" element={...} />")
        print("             <Route path=\"/hydroma\" element={...} />")
        print("           </Routes>  ← Must close here")
        print("         </Suspense>")
        print("       </SimulationPipelineProvider>")
        print("     </AuthProvider>")
        print("")
        print("  3. Common mistakes:")
        print("     ❌ </Routes> before all Route elements")
        print("     ❌ Route elements outside <Routes>")
        print("     ❌ Missing </Routes> entirely")
        print("     ❌ Extra </Routes> in wrong place")
        print("")
        print("  4. Try this command to see the structure:")
        print("     cd D:\\eco_nojin\\frontend\\src")
        print("     Select-String -Path App.tsx -Pattern '<Routes|</Routes>' -Context 2,2")
        print("")
    
    # Step 6: Commit if successful
    if build_ok:
        print("[Step 6] Committing")
        print("-" * 70)
        try:
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = "fix(jsx): fix Routes nesting issue in App.tsx\n\n- Fixed JSX structure around line 242\n- Build now successful"
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            warn(f"Commit issue: {e}")
        
        print("")
        print("=" * 70)
        print("  🎉 FIX SUCCESSFUL!")
        print("=" * 70)
        print("")
        print("  Agricultural cinematic simulator ready at:")
        print("    http://localhost:5173/hydroma")
        print("    http://localhost:5173/cinematic")
        print("")
    else:
        print("=" * 70)
        print("  ⚠️ Manual intervention required")
        print("=" * 70)
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())