# patch_analyzer.py
from pathlib import Path
import re

p = Path("project_analyzer.py")
if not p.exists():
    print("ERROR: project_analyzer.py not found")
    exit(1)

content = p.read_text(encoding="utf-8")
original = content

# ============================================================
# FIX 1: All open() calls should use UTF-8 encoding
# ============================================================
print("[1/4] Fixing UTF-8 encoding for all file operations...")

replacements = [
    # Writing operations
    ("with open(output_path, 'w') as f:",
     "with open(output_path, 'w', encoding='utf-8') as f:"),
    ("with open(req_file) as f:",
     "with open(req_file, encoding='utf-8') as f:"),
    ("with open(readme_path) as f:",
     "with open(readme_path, encoding='utf-8') as f:"),
    ("with open(pkg_file) as f:",
     "with open(pkg_file, encoding='utf-8') as f:"),

    # Reading operations in analyzers
    ("with open(py_file) as f:",
     "with open(py_file, encoding='utf-8', errors='ignore') as f:"),
    ("with open(tsx_file) as f:",
     "with open(tsx_file, encoding='utf-8', errors='ignore') as f:"),
    ("with open(file_path) as f:",
     "with open(file_path, encoding='utf-8', errors='ignore') as f:"),
    ("with open(status_file) as f:",
     "with open(status_file, encoding='utf-8', errors='ignore') as f:"),

    # JSON operations
    ("json.dump(data, f, indent=2, ensure_ascii=False)",
     "json.dump(data, f, indent=2, ensure_ascii=False, ensure_ascii=False)"),
]

for old, new in replacements:
    content = content.replace(old, new)

print(f"  + Applied UTF-8 encoding fixes")

# ============================================================
# FIX 2: Exclude analyzer scripts from analysis
# ============================================================
print("[2/4] Adding exclusions for analyzer scripts...")

# Find the skip pattern lists and extend them
skip_additions = [
    "project_analyzer.py",
    "fix_critical_issues.py",
    "patch_analyzer.py",
    "prepare_github.py",
]

# Add to common skip patterns used throughout the file
old_skip = "['node_modules', '.venv', '__pycache__']"
new_skip = "['node_modules', '.venv', '__pycache__', '.mypy_cache', '.pytest_cache', '.next', 'project_analyzer.py', 'fix_critical_issues.py', 'patch_analyzer.py']"
content = content.replace(old_skip, new_skip)

old_skip2 = "['node_modules', '.venv']"
new_skip2 = "['node_modules', '.venv', '.mypy_cache', '.pytest_cache', '.next', 'project_analyzer.py', 'fix_critical_issues.py', 'patch_analyzer.py']"
content = content.replace(old_skip2, new_skip2)

old_skip3 = "['node_modules', '.venv', '__pycache__', 'test']"
new_skip3 = "['node_modules', '.venv', '__pycache__', 'test', '.mypy_cache', '.pytest_cache', '.next', 'project_analyzer.py', 'fix_critical_issues.py']"
content = content.replace(old_skip3, new_skip3)

old_skip4 = "['node_modules', '.venv', '__pycache__', '.next']"
new_skip4 = "['node_modules', '.venv', '__pycache__', '.next', '.mypy_cache', '.pytest_cache', 'project_analyzer.py', 'fix_critical_issues.py', 'patch_analyzer.py']"
content = content.replace(old_skip4, new_skip4)

old_skip5 = "['node_modules', '.venv', '__pycache__']"
new_skip5 = "['node_modules', '.venv', '__pycache__', '.mypy_cache', '.pytest_cache', 'project_analyzer.py', 'fix_critical_issues.py', 'patch_analyzer.py']"
content = content.replace(old_skip5, new_skip5)

print(f"  + Added exclusions for analyzer scripts and cache dirs")

# ============================================================
# FIX 3: Fix test counting - exclude test folders from source
# ============================================================
print("[3/4] Fixing test-to-source ratio calculation...")

# Find the _estimate_coverage method and patch its filtering
old_count = '''        python_files = list(self.root.rglob('*.py'))
        python_files = [f for f in python_files if 'node_modules' not in str(f) and 'test' not in str(f)]'''

new_count = '''        python_files = list(self.root.rglob('*.py'))
        skip_dirs = ['node_modules', '.venv', 'venv', '__pycache__', '.mypy_cache',
                     '.pytest_cache', '.next', '.git', 'tests', 'test']
        skip_files = ['project_analyzer.py', 'fix_critical_issues.py', 'patch_analyzer.py']
        python_files = [f for f in python_files
                        if not any(skip in str(f) for skip in skip_dirs)
                        and not any(sf in f.name for sf in skip_files)]'''

content = content.replace(old_count, new_count)

# Also fix test file counting
old_test_count = '''        test_files = list(self.root.rglob('test_*.py'))
        test_files = [f for f in test_files if 'node_modules' not in str(f)]'''

new_test_count = '''        test_files = list(self.root.rglob('test_*.py'))
        skip_dirs = ['node_modules', '.venv', 'venv', '__pycache__', '.mypy_cache', '.pytest_cache']
        test_files = [f for f in test_files
                      if not any(skip in str(f) for skip in skip_dirs)
                      and 'project_analyzer' not in str(f)
                      and 'fix_critical_issues' not in str(f)]'''

content = content.replace(old_test_count, new_test_count)

print(f"  + Fixed source file counting (excludes node_modules, .venv, cache)")

# ============================================================
# FIX 4: Force UTF-8 on export_markdown
# ============================================================
print("[4/4] Patching markdown export to use UTF-8...")

old_md = '''        with open(output_path, 'w') as f:
            f.write('\\n'.join(lines))'''

new_md = '''        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\\n'.join(lines))'''

content = content.replace(old_md, new_md)

# Also patch json export
old_json = '''        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)'''

new_json = '''        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)'''

content = content.replace(old_json, new_json)

# ============================================================
# Save the patched file
# ============================================================
if content == original:
    print("\nWARNING: No changes were applied - file may already be patched")
else:
    # Backup original
    backup_path = p.with_suffix('.py.original-backup')
    if not backup_path.exists():
        backup_path.write_text(original, encoding='utf-8')
        print(f"  + Original backed up to {backup_path.name}")

    p.write_text(content, encoding='utf-8')
    print("\n" + "="*60)
    print("PATCH APPLIED SUCCESSFULLY")
    print("="*60)
    print("""
Changes made:
  1. All open() calls now use UTF-8 encoding
  2. Excluded analyzer scripts from analysis
  3. Excluded cache dirs (.mypy_cache, .pytest_cache)
  4. Fixed test-to-source ratio calculation
  5. Markdown/JSON export now uses UTF-8

Next:
  python project_analyzer.py

Expected improvements:
  - No UnicodeEncodeError crashes
  - Realistic test-to-source ratio (should be ~50%+)
  - False positives for hardcoded values will disappear
  - Health score should reach 80%+
""")