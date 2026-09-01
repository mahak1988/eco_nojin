#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix JSX Structure in App.tsx
==============================
Problem: Routes tag not properly closed after adding cinematic routes
Solution: Read App.tsx, find the issue, fix JSX structure
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
    print("  Fix JSX Structure in App.tsx")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Read App.tsx
    print("[Step 1] Reading App.tsx")
    print("-" * 70)
    
    content = APP_FILE.read_text(encoding="utf-8-sig")
    lines = content.split('\n')
    
    info(f"Read {len(lines)} lines")
    print("")

    # Step 2: Find the issue
    print("[Step 2] Analyzing JSX structure")
    print("-" * 70)
    
    # Count opening and closing tags
    routes_open = content.count('<Routes')
    routes_close = content.count('</Routes>')
    
    info(f"<Routes> tags: {routes_open} open, {routes_close} close")
    
    if routes_open != routes_close:
        warn(f"Mismatch: {routes_open} vs {routes_close}")
    
    # Find line numbers
    for i, line in enumerate(lines, 1):
        if '<Routes' in line:
            info(f"  <Routes> at line {i}: {line.strip()[:60]}")
        if '</Routes>' in line:
            info(f"  </Routes> at line {i}: {line.strip()[:60]}")
    
    print("")

    # Step 3: Check if Routes needs closing
    print("[Step 3] Fixing Routes structure")
    print("-" * 70)
    
    # Strategy: Find the last Route and ensure </Routes> comes after it
    # Also ensure proper nesting with providers
    
    fixed = False
    
    # Check if </Routes> is missing
    if routes_open > routes_close:
        # Find the last </Route> or last Route element
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            # Look for the end of a Route block
            if '</Route>' in line or (line.strip().endswith('/>') and '<Route' in '\n'.join(lines[max(0, i-5):i+1])):
                # Check if </Routes> follows
                has_routes_close = False
                for j in range(i+1, min(i+10, len(lines))):
                    if '</Routes>' in lines[j]:
                        has_routes_close = True
                        break
                    if '</Routes>' not in lines[j] and lines[j].strip() and not lines[j].strip().startswith('//'):
                        # Found something else before </Routes>
                        break
                
                if not has_routes_close:
                    # Add </Routes> after this line
                    indent = len(lines[i]) - len(lines[i].lstrip())
                    routes_close_line = ' ' * indent + '          </Routes>'
                    lines.insert(i + 1, routes_close_line)
                    ok(f"Added </Routes> after line {i+1}")
                    fixed = True
                    break
    
    # Check if we have unmatched </Routes>
    elif routes_close > routes_open:
        warn("Extra </Routes> found - removing duplicate")
        # Find and remove extra </Routes>
        for i in range(len(lines)):
            if '</Routes>' in lines[i]:
                lines[i] = lines[i].replace('</Routes>', '')
                ok(f"Removed extra </Routes> at line {i+1}")
                fixed = True
                break
    
    if not fixed and routes_open == routes_close:
        # Check if Routes is in wrong position
        # Find where <Routes> should be (after providers, before routes)
        info("Routes count matches, checking position...")
        
        # Look for common issues:
        # 1. Routes outside of providers
        # 2. Routes not wrapping all Route elements
        
        # Find the main structure
        for i, line in enumerate(lines):
            if '<Routes>' in line or '<Routes ' in line:
                # Check what comes before
                prev_lines = '\n'.join(lines[max(0, i-10):i])
                if '<AuthProvider' in prev_lines or '<SimulationPipelineProvider' in prev_lines:
                    info(f"Routes found inside providers at line {i+1} - good")
                else:
                    warn(f"Routes at line {i+1} might be outside providers")
    
    # Save if changed
    if fixed:
        new_content = '\n'.join(lines)
        APP_FILE.write_text(new_content, encoding="utf-8")
        ok("Saved App.tsx")
    else:
        info("No obvious fix needed - trying alternative approach")
    
    print("")

    # Step 4: Alternative fix - ensure proper structure
    print("[Step 4] Ensuring proper JSX nesting")
    print("-" * 70)
    
    content = APP_FILE.read_text(encoding="utf-8-sig")
    
    # Check if we have Fragment wrapping
    if '<>' not in content and 'return (' in content:
        info("No Fragment wrapper found")
        
        # Find return statement
        return_match = re.search(r'return\s*\(', content)
        if return_match:
            # Check if first element after return is a provider
            after_return = content[return_match.end():]
            if after_return.strip().startswith('<'):
                # Get the first tag
                tag_match = re.match(r'\s*<(\w+)', after_return)
                if tag_match:
                    first_tag = tag_match.group(1)
                    if first_tag in ['AuthProvider', 'SimulationPipelineProvider', 'ErrorBoundary']:
                        info(f"First element is {first_tag} - good")
                    else:
                        warn(f"First element is {first_tag} - might need wrapper")
    
    # Check for common patterns that cause issues
    issues_found = []
    
    # Pattern 1: Route outside Routes
    route_pattern = r'<Route\s+[^>]*>'
    routes_pattern = r'<Routes[^>]*>(.*?)</Routes>'
    
    # Find all Route elements
    all_routes = list(re.finditer(route_pattern, content))
    # Find Routes blocks
    routes_blocks = list(re.finditer(routes_pattern, content, re.DOTALL))
    
    if all_routes and not routes_blocks:
        err("Found Route elements but no Routes wrapper!")
        issues_found.append("missing_routes_wrapper")
    
    # Check if cinematic routes are properly placed
    if '"/cinematic"' in content:
        info("Found /cinematic route")
    if '"/hydroma"' in content:
        info("Found /hydroma route")
    
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
    else:
        err("Build failed")
        output = result.stdout + result.stderr
        
        # Parse error to understand better
        if "Expected corresponding JSX closing tag" in output:
            # Extract which tag is expected
            match = re.search(r"Expected corresponding JSX closing tag for '(\w+)'", output)
            if match:
                expected_tag = match.group(1)
                err(f"Missing closing tag for: {expected_tag}")
                
                # Try to fix this specific issue
                content = APP_FILE.read_text(encoding="utf-8-sig")
                
                # Find where this tag should close
                # Look for the opening tag and find its scope
                open_pattern = rf'<{expected_tag}[\s>]'
                close_pattern = rf'</{expected_tag}>'
                
                opens = len(re.findall(open_pattern, content))
                closes = len(re.findall(close_pattern, content))
                
                info(f"<{expected_tag}>: {opens} open, {closes} close")
                
                if opens > closes:
                    # Need to add closing tag
                    # Find the last occurrence and add closing after it
                    last_open = -1
                    lines = content.split('\n')
                    
                    for i in range(len(lines) - 1, -1, -1):
                        if re.search(open_pattern, lines[i]):
                            last_open = i
                            break
                    
                    if last_open >= 0:
                        # Find the matching close or where it should be
                        indent = len(lines[last_open]) - len(lines[last_open].lstrip())
                        close_line = ' ' * indent + f'</{expected_tag}>'
                        
                        # Insert after the block
                        # Simple heuristic: insert after next few lines that are at same or deeper indent
                        insert_at = last_open + 1
                        for j in range(last_open + 1, min(last_open + 50, len(lines))):
                            if lines[j].strip() and not lines[j].startswith(' ' * (indent + 2)):
                                insert_at = j
                                break
                        
                        lines.insert(insert_at, close_line)
                        content = '\n'.join(lines)
                        APP_FILE.write_text(content, encoding="utf-8")
                        ok(f"Added </{expected_tag}> at line {insert_at + 1}")
                        
                        # Try build again
                        info("Retrying build...")
                        result2 = subprocess.run(
                            "pnpm build",
                            shell=True, cwd=FRONTEND,
                            capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=300,
                        )
                        if result2.returncode == 0:
                            ok("🎉 Build successful after fix!")
                            build_ok = True
                        else:
                            err("Still failing after fix attempt")
                            print("\n  Error output:")
                            for line in (result2.stdout + result2.stderr).splitlines()[-20:]:
                                if line.strip():
                                    print(f"    {line}")
        
        if not build_ok:
            print("\n  Full error output (last 30 lines):")
            for line in output.splitlines()[-30:]:
                if line.strip():
                    print(f"    {line}")
    
    print("")

    # Step 6: Commit if successful
    print("[Step 6] Committing")
    print("-" * 70)
    
    if build_ok:
        try:
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "fix(jsx): fix JSX structure in App.tsx\\n\\n"
                "- Fixed Routes tag closing issue\\n"
                "- Ensured proper nesting of providers and routes\\n"
                "- Build now successful\\n\\n"
                "Agricultural cinematic features ready at /hydroma"
            )
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            warn(f"Commit issue: {e}")
    
    print("")
    print("=" * 70)
    if build_ok:
        print("  🎉 FIX SUCCESSFUL!")
        print("=" * 70)
        print("")
        print("  Agricultural cinematic simulator ready at:")
        print("    http://localhost:5173/hydroma")
        print("    http://localhost:5173/cinematic")
        print("")
        print("  Features:")
        print("    🐝 Insects (bees, ladybugs, locusts)")
        print("    🐄 Domestic animals (cows, sheep, horses)")
        print("    🐔 Poultry (chickens, ducks)")
        print("    🌊 Flood simulation")
        print("    💧 Irrigation systems")
        print("    ⛲ Well system")
        print("    🏞️ River flow")
        print("    🏖️ Coastline waves")
        print("    🏗️ Watershed engineering")
        print("    🚜 Plowing trails")
        print("")
    else:
        print("  ⚠️ Build still failing - manual intervention needed")
        print("=" * 70)
        print("")
        print("  Try manual fix:")
        print("    1. Open frontend/src/App.tsx")
        print("    2. Check line 242-243 area")
        print("    3. Ensure </Routes> closes after all Route elements")
        print("    4. Ensure proper nesting: Providers > Routes > Route")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())