"""
Phase 1.3: Print Statement Annihilator
تبدیل 4776 مورد print() به structlog
استفاده: python phase1_remove_prints.py --dry-run   (برای شبیه‌سازی)
استفاده: python phase1_remove_prints.py             (برای اعمال واقعی)
"""
import os
import re
import argparse

IGNORE_DIRS = {'.git', 'node_modules', '.venv', 'venv', 'env', '__pycache__', 
               'engine/cpp_core/build2', 'frontend/test-results', '_quarantine', '_backups'}

# الگوی پیدا کردن print
# مثال: print("hello") یا print( f"val: {x}" )
PRINT_PATTERN = re.compile(r'^(\s*)print\((.*)\)\s*$')

def should_scan(path):
    for ignore_dir in IGNORE_DIRS:
        if f"\\{ignore_dir}\\" in path or f"/{ignore_dir}/" in path:
            return False
    return True

def process_file(filepath, dry_run):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    new_lines = []
    changes = 0
    has_structlog_import = False

    for i, line in enumerate(lines):
        # بررسی وجود ایمپورت structlog
        if 'import structlog' in line or 'from structlog' in line:
            has_structlog_import = True

        match = PRINT_PATTERN.match(line)
        if match:
            indent = match.group(1)
            content = match.group(2).strip()
            
            # تصمیم‌گیری درباره سطح لاگ
            content_lower = content.lower()
            if 'error' in content_lower or 'exception' in content_lower or 'traceback' in content_lower:
                log_level = 'error'
            elif 'warn' in content_lower:
                log_level = 'warning'
            elif 'debug' in content_lower:
                log_level = 'debug'
            else:
                log_level = 'info'

            new_line = f"{indent}logger.{log_level}({content})\n"
            new_lines.append(new_line)
            changes += 1
            
            if dry_run:
                logger.info(f"[DRY-RUN] {filepath}:{i+1}\n  - {line.strip()}\n  + {new_line.strip()}\n")
        else:
            new_lines.append(line)

    # اگر تغییراتی ایجاد شد و structlog ایمپورت نشده بود، آن را اضافه کن
    if changes > 0 and not has_structlog_import:
        # پیدا کردن اولین ایمپورت برای قرار دادن structlog در کنار آن
        for i, line in enumerate(new_lines):
            if line.startswith('import ') or line.startswith('from '):
                new_lines.insert(i, "import structlog\n\nlogger = structlog.get_logger()\n")
                break

    if changes > 0 and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
    return changes

def main():
    parser = argparse.ArgumentParser(description="Replace print() with structlog")
    parser.add_argument('--dry-run', action='store_true', help='Simulate without changing files')
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    total_changes = 0

    mode_msg = "[DRY-RUN MODE] No files will be modified." if args.dry_run else "[LIVE MODE] Modifying files!"
    logger.info(f"=== Print Annihilator Started ({mode_msg}) ===\n")

    for root, _, files in os.walk(base_dir):
        if not should_scan(root):
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                changes = process_file(filepath, args.dry_run)
                if changes > 0:
                    logger.info(f"[{'SIMULATED' if args.dry_run else 'APPLIED'}] Fixed {changes} prints in {filepath}")
                    total_changes += changes

    logger.info(f"\n=== Summary ===")
    logger.info(f"Total 'print()' statements processed: {total_changes}")
    if not args.dry_run:
        logger.info("Please run 'pnpm quality' or your linter to ensure nothing broke.")

if __name__ == "__main__":
    main()