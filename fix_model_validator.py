#!/usr/bin/env python3
"""
Eco Nojin - Fix model_validator Import
=======================================
Final fix: Add model_validator import to settings.py
"""
import re
import ast
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent


def print_section(title: str) -> None:
    print(f"\n{'='*70}\n  {title}\n{'='*70}")


def fix_settings_import() -> bool:
    """Fix model_validator import in settings.py."""
    print_section("FIXING SETTINGS IMPORT")
    
    settings_file = PROJECT_ROOT / "engine" / "hydroma" / "config" / "settings.py"
    content = settings_file.read_text(encoding='utf-8')
    
    print(f"  File size: {len(content)} chars")
    
    # Check current pydantic imports
    print("\n  Current pydantic imports:")
    for line in content.splitlines():
        if 'pydantic' in line.lower() and ('import' in line or 'from' in line):
            print(f"    {line.strip()}")
    
    # Check if model_validator is used
    uses_model_validator = '@model_validator' in content or 'model_validator(' in content
    print(f"\n  Uses model_validator: {uses_model_validator}")
    
    # Check if model_validator is already imported
    has_import = bool(re.search(r'from pydantic import[^\n]*model_validator', content))
    print(f"  Already imported: {has_import}")
    
    if not uses_model_validator:
        print("  ℹ️  model_validator not used, nothing to do")
        return True
    
    if has_import:
        print("  ℹ️  model_validator already imported")
        return True
    
    # Strategy: Find existing pydantic import and add model_validator
    modified = False
    
    # Pattern 1: "from pydantic import field_validator" (without model_validator)
    pattern1 = r'from pydantic import ([^\n]+?)(?:\n|$)'
    
    def add_to_import(match):
        nonlocal modified
        current_imports = match.group(1).strip()
        if 'model_validator' not in current_imports:
            modified = True
            new_imports = current_imports + ', model_validator'
            return f'from pydantic import {new_imports}\n'
        return match.group(0)
    
    content = re.sub(pattern1, add_to_import, content)
    
    # Pattern 2: If no pydantic import at all, add one after pydantic_settings
    if not modified and 'from pydantic import' not in content:
        if 'from pydantic_settings import' in content:
            content = content.replace(
                'from pydantic_settings import',
                'from pydantic import model_validator\nfrom pydantic_settings import'
            )
            modified = True
            print("  ✅ Added: from pydantic import model_validator (before pydantic_settings)")
        else:
            # Add at top after docstring
            lines = content.splitlines()
            # Find first non-comment, non-docstring line
            insert_idx = 0
            in_docstring = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    in_docstring = not in_docstring
                    continue
                if in_docstring or stripped.startswith('#') or not stripped:
                    insert_idx = i + 1
                    continue
                break
            
            lines.insert(insert_idx, 'from pydantic import model_validator')
            content = '\n'.join(lines)
            modified = True
            print(f"  ✅ Added: from pydantic import model_validator (line {insert_idx+1})")
    
    if not modified:
        print("  ⚠️  Could not add import automatically")
        return False
    
    # Verify syntax
    try:
        ast.parse(content)
        print("  ✅ Syntax validation: PASSED")
    except SyntaxError as e:
        print(f"  ❌ Syntax validation FAILED: {e}")
        return False
    
    # Show updated imports
    print("\n  Updated pydantic imports:")
    for line in content.splitlines():
        if 'pydantic' in line.lower() and ('import' in line or 'from' in line):
            print(f"    {line.strip()}")
    
    # Save
    settings_file.write_text(content, encoding='utf-8')
    print(f"\n  ✅ settings.py saved ({len(content)} chars)")
    return True


def run_settings_tests() -> bool:
    """Run settings tests to verify."""
    print_section("RUNNING SETTINGS TESTS")
    
    import subprocess
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 
         'tests/unit/test_settings.py', '-v', '--tb=short'],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=60
    )
    
    # Print key lines
    for line in result.stdout.splitlines():
        if any(k in line for k in ['PASSED', 'FAILED', 'ERROR', 'passed', 'failed', 'error']):
            print(f"  {line}")
    
    if result.returncode == 0:
        print("\n  ✅ ALL SETTINGS TESTS PASSED!")
        return True
    
    print(f"\n  ❌ Settings tests failed (exit code: {result.returncode})")
    return False


def run_security_tests() -> bool:
    """Run security tests (use is_production)."""
    print_section("RUNNING SECURITY TESTS")
    
    import subprocess
    result = subprocess.run(
        [sys.executable, '-m', 'pytest',
         'tests/unit/test_security.py', '-v', '--tb=short'],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=60
    )
    
    for line in result.stdout.splitlines():
        if any(k in line for k in ['PASSED', 'FAILED', 'ERROR', 'passed', 'failed', 'error']):
            print(f"  {line}")
    
    return result.returncode == 0


def run_full_suite() -> bool:
    """Run full test suite."""
    print_section("RUNNING FULL TEST SUITE")
    
    import subprocess
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '--tb=line', '-q'],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=300
    )
    
    # Print summary (last 20 lines)
    lines = result.stdout.splitlines()
    for line in lines[-25:]:
        print(f"  {line}")
    
    return result.returncode == 0


def main():
    """Execute fixes."""
    print("\n" + "="*70)
    print("  ECO NOJIN - FINAL FIX: model_validator IMPORT")
    print("="*70)
    print(f"\n  Project: {PROJECT_ROOT}")
    
    # Step 1: Fix import
    import_ok = fix_settings_import()
    
    if not import_ok:
        print("\n  ❌ Import fix failed, aborting")
        return 1
    
    # Step 2: Verify with tests
    settings_ok = run_settings_tests()
    security_ok = run_security_tests()
    
    # Step 3: Full suite
    full_ok = run_full_suite()
    
    # Summary
    print_section("FINAL SUMMARY")
    print(f"\n  1. Settings import fix: {'✅' if import_ok else '❌'}")
    print(f"  2. Settings tests: {'✅' if settings_ok else '❌'}")
    print(f"  3. Security tests: {'✅' if security_ok else '❌'}")
    print(f"  4. Full test suite: {'✅' if full_ok else '❌'}")
    
    if all([import_ok, settings_ok, security_ok, full_ok]):
        print("\n  🎉 ALL FIXES SUCCESSFUL! PROJECT IS STABLE!")
        return 0
    else:
        print("\n  ⚠️  Some issues remain, review output above")
        return 1


if __name__ == '__main__':
    sys.exit(main())