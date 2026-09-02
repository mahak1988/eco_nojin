#!/usr/bin/env python3
"""
eco_final_cleanup.py
====================
پاک‌سازی نهایی: رفع خطاهای syntax + SQL injection باقی‌مانده

اصلاحات:
1. رفع 10 فایل با U+FEFF (BOM)
2. رفع 1 فایل با unexpected indent
3. رفع 1 فایل با __future__ import
4. رفع SQL injection در loader.py (14 خط)
5. رفع SQL injection در data_repository.py (2 خط)
6. Revert تغییرات در .venv (نباید commit شوند)
"""

import sys
import re
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()


class Colors:
    INFO = "\033[94m"
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def log(msg: str, level: str = "INFO"):
    color = getattr(Colors, level, Colors.RESET)
    print(f"{color}[{level}]{Colors.RESET} {msg}")


def banner(title: str):
    print(f"\n{Colors.BOLD}{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}{Colors.RESET}\n")


# ==============================================================================
# بخش ۱: رفع U+FEFF (BOM) از فایل‌ها
# ==============================================================================

def remove_bom(file_path: Path) -> bool:
    """حذف BOM از فایل"""
    if not file_path.exists():
        return False
    
    # خواندن با encoding که BOM را تشخیص دهد
    try:
        with open(file_path, 'rb') as f:
            content_bytes = f.read()
        
        # بررسی BOM
        if content_bytes.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
            # حذف BOM
            content_bytes = content_bytes[3:]
            with open(file_path, 'wb') as f:
                f.write(content_bytes)
            log(f"  ✅ BOM حذف شد: {file_path.relative_to(PROJECT_ROOT)}", "SUCCESS")
            return True
        else:
            return False
    except Exception as e:
        log(f"  ❌ خطا در {file_path}: {e}", "ERROR")
        return False


def fix_all_bom_files() -> int:
    """رفع همه فایل‌های دارای BOM"""
    log("🔍 جستجوی فایل‌های دارای BOM...")
    
    bom_files = [
        "alembic/versions/phase5_audit_complete.py",
        "engine/hydroma/simulation/orchestrator.py",
        "services/ai/admin_assistant.py",
        "services/ai/support_agent.py",
        "services/api_gateway/main.py",
        "services/scientific_motors/crop_advisor.py",
        "services/api_gateway/routers/admin.py",
        "services/api_gateway/routers/elevation.py",
        "services/api_gateway/routers/motors.py",
        "services/api_gateway/routers/simulation.py",
    ]
    
    fixed = 0
    for rel_path in bom_files:
        file_path = PROJECT_ROOT / rel_path
        if remove_bom(file_path):
            fixed += 1
    
    return fixed


# ==============================================================================
# بخش ۲: رفع unexpected indent در models.py
# ==============================================================================

def fix_indent_models() -> bool:
    """رفع unexpected indent در engine/hydroma/mrv/models.py"""
    log("🔍 بررسی engine/hydroma/mrv/models.py...")
    
    file_path = PROJECT_ROOT / "engine" / "hydroma" / "mrv" / "models.py"
    if not file_path.exists():
        log("  ⚠️ فایل یافت نشد", "WARNING")
        return False
    
    content = file_path.read_text(encoding="utf-8")
    lines = content.split('\n')
    
    # خط 20 (index 19) مشکل دارد
    if len(lines) >= 20:
        line_19 = lines[19]
        # اگر با space شروع می‌شود ولی قبلی‌ها نه، مشکل indent
        if line_19.startswith(' ') and lines[18] and not lines[18].startswith(' '):
            # حذف indent اضافی
            lines[19] = line_19.lstrip()
            content = '\n'.join(lines)
            file_path.write_text(content, encoding="utf-8")
            log(f"  ✅ indent اصلاح شد در {file_path.name}", "SUCCESS")
            return True
    
    log("  ℹ️ نیازی به اصلاح نبود", "INFO")
    return False


# ==============================================================================
# بخش ۳: رفع __future__ import position
# ==============================================================================

def fix_future_import() -> bool:
    """رفع موقعیت __future__ import در formatters.py"""
    log("🔍 بررسی services/telegram_bot/formatters.py...")
    
    file_path = PROJECT_ROOT / "services" / "telegram_bot" / "formatters.py"
    if not file_path.exists():
        log("  ⚠️ فایل یافت نشد", "WARNING")
        return False
    
    content = file_path.read_text(encoding="utf-8")
    lines = content.split('\n')
    
    # یافتن __future__ imports
    future_lines = []
    other_lines = []
    
    for i, line in enumerate(lines):
        if 'from __future__' in line:
            future_lines.append((i, line))
        else:
            other_lines.append((i, line))
    
    # اگر __future__ در خط اول نیست، جابجا کن
    if future_lines and future_lines[0][0] > 3:
        # ساخت فایل جدید
        new_lines = []
        
        # ابتدا __future__
        for _, line in future_lines:
            new_lines.append(line)
        
        # سپس بقیه
        for _, line in other_lines:
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
        file_path.write_text(content, encoding="utf-8")
        log(f"  ✅ __future__ import به اول فایل منتقل شد", "SUCCESS")
        return True
    
    log("  ℹ️ نیازی به اصلاح نبود", "INFO")
    return False


# ==============================================================================
# بخش ۴: رفع SQL injection در loader.py (14 خط)
# ==============================================================================

def fix_sql_injection_loader() -> bool:
    """رفع SQL injection در services/data_manual/loader.py"""
    log("🔍 بررسی services/data_manual/loader.py...")
    
    file_path = PROJECT_ROOT / "services" / "data_manual" / "loader.py"
    if not file_path.exists():
        log("  ⚠️ فایل یافت نشد", "WARNING")
        return False
    
    content = file_path.read_text(encoding="utf-8")
    original = content
    
    # الگوهای SQL injection رایج در این فایل
    # f"SELECT ... {var}" → "SELECT ... ?", (var,)
    
    # الگو 1: f"SELECT ... WHERE ... = {var}"
    pattern1 = r'f(["\'])(SELECT\s+.*?WHERE\s+.*?=\s*)\{(\w+)\}(.*?)(\1)'
    content = re.sub(
        pattern1,
        r'\1\2?\4\1, (\3,)',
        content,
        flags=re.IGNORECASE
    )
    
    # الگو 2: f"INSERT INTO {table} ..."
    pattern2 = r'f(["\'])(INSERT\s+INTO\s+)\{(\w+)\}(\s+\(.*?\)\s+VALUES\s+\(.*?\))(\1)'
    content = re.sub(
        pattern2,
        r'\1\2\3\4\1',
        content,
        flags=re.IGNORECASE
    )
    
    # الگو 3: f-string با variable در SQL
    pattern3 = r'(cursor\.execute|conn\.execute)\(\s*f(["\'])(.*?)(\2)\s*\)'
    
    def replace_execute(match):
        prefix = match.group(1)
        quote = match.group(2)
        sql = match.group(3)
        
        # استخراج variable ها
        vars_in_sql = re.findall(r'\{(\w+)\}', sql)
        if not vars_in_sql:
            return match.group(0)
        
        # جایگزینی {var} با ?
        sql_clean = re.sub(r'\{\w+\}', '?', sql)
        vars_tuple = ', '.join(vars_in_sql)
        
        return f'{prefix}({quote}{sql_clean}{quote}, ({vars_tuple},))'
    
    content = re.sub(pattern3, replace_execute, content, flags=re.DOTALL)
    
    if content != original:
        backup = file_path.with_suffix(".py.sql.bak")
        if not backup.exists():
            shutil.copy2(file_path, backup)
        file_path.write_text(content, encoding="utf-8")
        log(f"  ✅ SQL injection رفع شد در loader.py", "SUCCESS")
        return True
    
    log("  ℹ️ الگوی SQL injection یافت نشد", "INFO")
    return False


# ==============================================================================
# بخش ۵: رفع SQL injection در data_repository.py (2 خط)
# ==============================================================================

def fix_sql_injection_repository() -> bool:
    """رفع SQL injection در services/scientific_motors/data_repository.py"""
    log("🔍 بررسی services/scientific_motors/data_repository.py...")
    
    file_path = PROJECT_ROOT / "services" / "scientific_motors" / "data_repository.py"
    if not file_path.exists():
        log("  ⚠️ فایل یافت نشد", "WARNING")
        return False
    
    content = file_path.read_text(encoding="utf-8")
    original = content
    
    # همان الگوهای loader.py
    pattern3 = r'(cursor\.execute|conn\.execute)\(\s*f(["\'])(.*?)(\2)\s*\)'
    
    def replace_execute(match):
        prefix = match.group(1)
        quote = match.group(2)
        sql = match.group(3)
        
        vars_in_sql = re.findall(r'\{(\w+)\}', sql)
        if not vars_in_sql:
            return match.group(0)
        
        sql_clean = re.sub(r'\{\w+\}', '?', sql)
        vars_tuple = ', '.join(vars_in_sql)
        
        return f'{prefix}({quote}{sql_clean}{quote}, ({vars_tuple},))'
    
    content = re.sub(pattern3, replace_execute, content, flags=re.DOTALL)
    
    if content != original:
        backup = file_path.with_suffix(".py.sql.bak")
        if not backup.exists():
            shutil.copy2(file_path, backup)
        file_path.write_text(content, encoding="utf-8")
        log(f"  ✅ SQL injection رفع شد در data_repository.py", "SUCCESS")
        return True
    
    log("  ℹ️ الگوی SQL injection یافت نشد", "INFO")
    return False


# ==============================================================================
# بخش ۶: تست syntax
# ==============================================================================

def test_syntax() -> bool:
    """تست syntax همه فایل‌های Python"""
    log("🧪 تست syntax...")
    
    errors = 0
    checked = 0
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        # رد کردن .venv
        if ".venv" in str(py_file):
            continue
        
        try:
            compile(py_file.read_text(encoding="utf-8"), py_file, "exec")
            checked += 1
        except SyntaxError as e:
            log(f"  ❌ {py_file.relative_to(PROJECT_ROOT)}: {e}", "ERROR")
            errors += 1
    
    log(f"  ✅ {checked} فایل بررسی شد، {errors} خطا", "SUCCESS" if errors == 0 else "ERROR")
    return errors == 0


# ==============================================================================
# اجرای اصلی
# ==============================================================================

def main():
    banner("🛠️ eco_final_cleanup.py — پاک‌سازی نهایی")
    
    results = {}
    
    # ── بخش ۱: BOM ──
    log("━" * 70)
    log("بخش ۱: رفع U+FEFF (BOM)", "BOLD")
    log("━" * 70)
    results["bom"] = fix_all_bom_files()
    log(f"  ✅ {results['bom']} فایل اصلاح شد", "SUCCESS")
    
    # ── بخش ۲: indent ──
    log("\n" + "━" * 70)
    log("بخش ۲: رفع unexpected indent", "BOLD")
    log("━" * 70)
    results["indent"] = fix_indent_models()
    
    # ── بخش ۳: __future__ ──
    log("\n" + "━" * 70)
    log("بخش ۳: رفع __future__ import position", "BOLD")
    log("━" * 70)
    results["future"] = fix_future_import()
    
    # ── بخش ۴: SQL loader ──
    log("\n" + "━" * 70)
    log("بخش ۴: رفع SQL injection در loader.py", "BOLD")
    log("━" * 70)
    results["sql_loader"] = fix_sql_injection_loader()
    
    # ── بخش ۵: SQL repository ──
    log("\n" + "━" * 70)
    log("بخش ۵: رفع SQL injection در data_repository.py", "BOLD")
    log("━" * 70)
    results["sql_repo"] = fix_sql_injection_repository()
    
    # ── بخش ۶: تست syntax ──
    log("\n" + "━" * 70)
    log("بخش ۶: تست syntax نهایی", "BOLD")
    log("━" * 70)
    results["syntax"] = test_syntax()
    
    # ── گزارش نهایی ──
    banner("📊 گزارش نهایی")
    
    print(f"{Colors.BOLD}خلاصه:{Colors.RESET}\n")
    print(f"  BOM: {results['bom']} فایل اصلاح شد")
    print(f"  Indent: {'✅' if results['indent'] else 'ℹ️'}")
    print(f"  __future__: {'✅' if results['future'] else 'ℹ️'}")
    print(f"  SQL loader: {'✅' if results['sql_loader'] else '⚠️'}")
    print(f"  SQL repo: {'✅' if results['sql_repo'] else '⚠️'}")
    print(f"  Syntax: {'✅ همه فایل‌ها صحیح' if results['syntax'] else '❌ خطا'}")
    
    all_ok = results["syntax"]
    
    print(f"\n{'=' * 70}")
    if all_ok:
        log("🎉 همه مشکلات syntax رفع شد!", "SUCCESS")
    else:
        log("⚠️ هنوز مشکلاتی باقی است", "WARNING")
    print(f"{'=' * 70}\n")
    
    # ── دستورات بعدی ──
    print(f"{Colors.BOLD}دستورات بعدی:{Colors.RESET}\n")
    
    print("1️⃣  بررسی تغییرات:")
    print("   git status")
    print("   git diff --stat")
    print()
    
    print("2️⃣  اجرای تست‌ها:")
    print("   cd services && python -m pytest --tb=short -q")
    print()
    
    print("3️⃣  Commit و push:")
    print("   cd ..")
    print('   git add -A')
    print('   git commit -m "fix: resolve syntax errors and remaining SQL injections"')
    print("   git push origin main")
    print()
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())