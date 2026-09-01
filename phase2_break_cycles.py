"""
Phase 2.2: Automated Circular Dependency Breaker
این اسکریپت ایمپورت‌های مشکل‌ساز را کامنت می‌کند تا پروژه لود شود.
"""
import os
import re

# ماژول‌هایی که باید ایمپورت‌هایشان شکسته شود (سمت فرزند، نه والد)
TARGETS_TO_FIX = [
    {
        "file": "services/data_manual/__init__.py", # یا مسیر دقیق فایل پایتون
        "block_import_from": "services.api_gateway.routers.manual_data"
    },
    {
        "file": "engine/hydroma/biofertilizer/calibration.py",
        "block_import_from": "database.config"
    }
]

def fix_file(filepath, block_module):
    if not os.path.exists(filepath):
        # گاهی ایمپورت در فایل اصلی نیست، در __init__.py پوشه است
        alt_path = os.path.join(os.path.dirname(filepath), '__init__.py')
        if os.path.exists(alt_path):
            filepath = alt_path
        else:
            print(f"  [SKIP] File not found: {filepath}")
            return False

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    new_lines = []
    
    # تبدیل نام ماژول به فرمت احتمالی در کد (نقطه‌ها می‌شوند اسلش)
    possible_matches = [
        block_module.replace('.', '/'),
        block_module.replace('.', os.sep)
    ]

    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # بررسی اینکه آیا این خط ایمپورت از ماژول ممنوعه است؟
        is_bad_import = (
            (stripped.startswith('import ') and block_module in stripped) or
            (stripped.startswith('from ') and any(m in stripped for m in possible_matches))
        )

        if is_bad_import and not stripped.startswith('#'):
            new_lines.append(f"# [PHASE 2 FIX] Commented out due to Circular Dependency with '{block_module}'\n")
            new_lines.append(f"# TODO: Refactor this. Move shared logic to a separate 'shared' module.\n")
            new_lines.append(f"# {line}")
            modified = True
            print(f"  [FIXED] Line {i+1}: {stripped[:60]}...")
        else:
            new_lines.append(line)

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
    return modified

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print("[ACTION] Breaking circular dependencies...\n")
    
    fixes_applied = 0
    for target in TARGETS_TO_FIX:
        filepath = os.path.join(base_dir, target["file"])
        print(f"Checking {target['file']} (blocking imports from {target['block_import_from']})...")
        
        if fix_file(filepath, target["block_import_from"]):
            fixes_applied += 1
            
    print(f"\n[RESULT] Applied {fixes_applied} automated fixes.")
    if fixes_applied > 0:
        print("[WARN] Please run your backend server to see if it complains about missing imports.")
        print("[INFO] If it does, you need to move that specific function/class to a shared module.")

if __name__ == "__main__":
    main()