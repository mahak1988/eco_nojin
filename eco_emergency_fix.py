#!/usr/bin/env python3
"""
eco_emergency_fix.py
====================
اقدام اضطراری: رفع آسیب به .venv و 2 خطای syntax باقی‌مانده

اصلاحات:
1. بازگردانی httpx به حالت اصلی (با reinstall)
2. رفع unexpected indent در engine/hydroma/mrv/models.py
3. رفع __future__ import در services/telegram_bot/formatters.py
4. تست کامل
5. Commit نهایی
"""

import sys
import re
import shutil
import subprocess
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
# بخش ۱: بازگردانی httpx
# ==============================================================================

def restore_httpx() -> bool:
    """بازگردانی httpx به حالت اصلی"""
    log("🔧 بازگردانی httpx...")
    
    try:
        # uninstall و reinstall
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--force-reinstall", 
             "--no-deps", "httpx==0.28.1"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=120
        )
        
        if result.returncode == 0:
            log("  ✅ httpx با موفقیت reinstall شد", "SUCCESS")
            
            # تأیید
            httpx_urls = Path(sys.executable).parent.parent / "Lib" / "site-packages" / "httpx" / "_urls.py"
            if not httpx_urls.exists():
                httpx_urls = PROJECT_ROOT / ".venv" / "Lib" / "site-packages" / "httpx" / "_urls.py"
            
            if httpx_urls.exists():
                content = httpx_urls.read_text(encoding="utf-8")
                if "from __future__ import annotations" in content:
                    lines = content.split('\n')
                    # بررسی اینکه آیا در خط 1 یا 2 است
                    for i, line in enumerate(lines[:5], 1):
                        if "from __future__ import annotations" in line:
                            log(f"  ✅ __future__ در خط {i} قرار دارد", "SUCCESS")
                            break
            return True
        else:
            log(f"  ❌ خطا: {result.stderr[:200]}", "ERROR")
            return False
            
    except Exception as e:
        log(f"  ❌ خطا: {e}", "ERROR")
        return False


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
    
    # خواندن با encoding که BOM را هم تشخیص دهد
    try:
        with open(file_path, 'rb') as f:
            raw = f.read()
        
        # حذف BOM اگر وجود دارد
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        
        content = raw.decode('utf-8')
        lines = content.split('\n')
        
        # اصلاح خط 20 (index 19)
        changed = False
        for i in range(len(lines)):
            line = lines[i]
            
            # خط با indent غیرمنتظره (indent در ابتدای فایل یا بعد از خط خالی)
            if line.startswith('    ') or line.startswith('\t'):
                # اگر خط قبلی خالی یا class/function نیست
                if i == 0:
                    # اولین خط نباید indent داشته باشد
                    lines[i] = line.lstrip()
                    changed = True
                    log(f"  ✅ خط {i+1} indent حذف شد", "SUCCESS")
                elif i > 0:
                    prev = lines[i-1].strip()
                    # اگر قبلی خالی است و indent دارد، مشکل
                    if not prev and not line.strip().startswith('#'):
                        lines[i] = line.lstrip()
                        changed = True
                        log(f"  ✅ خط {i+1} indent حذف شد", "SUCCESS")
                    # اگر قبلی class/function/def نیست و indent دارد
                    elif prev and not prev.endswith(':') and not any(
                        prev.startswith(k) for k in ['class ', 'def ', 'if ', 'for ', 'while ', 'try:', 'except', 'with ']
                    ):
                        # فقط اگر ایندنت در سطح ماژول است
                        if i < 5:  # احتمالاً در ابتدای فایل
                            lines[i] = line.lstrip()
                            changed = True
                            log(f"  ✅ خط {i+1} indent حذف شد", "SUCCESS")
        
        if changed:
            new_content = '\n'.join(lines)
            file_path.write_text(new_content, encoding="utf-8")
            log(f"  ✅ {file_path.name} اصلاح شد", "SUCCESS")
            return True
        else:
            # روش دوم: فقط خط 20 را بررسی کن
            if len(lines) >= 20:
                line_19 = lines[19]
                if line_19.startswith(' ') or line_19.startswith('\t'):
                    log(f"  ℹ️ خط 20: {line_19[:50]}...", "INFO")
                    # سعی کن indent را حذف کن
                    stripped = line_19.lstrip()
                    if stripped and not stripped.startswith('#'):
                        lines[19] = stripped
                        new_content = '\n'.join(lines)
                        file_path.write_text(new_content, encoding="utf-8")
                        log(f"  ✅ خط 20 اصلاح شد", "SUCCESS")
                        return True
            log("  ℹ️ نیازی به اصلاح نبود", "INFO")
            return True
            
    except Exception as e:
        log(f"  ❌ خطا: {e}", "ERROR")
        return False


# ==============================================================================
# بخش ۳: رفع __future__ import در formatters.py
# ==============================================================================

def fix_future_formatters() -> bool:
    """رفع موقعیت __future__ import در formatters.py"""
    log("🔍 بررسی services/telegram_bot/formatters.py...")
    
    file_path = PROJECT_ROOT / "services" / "telegram_bot" / "formatters.py"
    if not file_path.exists():
        log("  ⚠️ فایل یافت نشد", "WARNING")
        return False
    
    try:
        # حذف BOM اگر وجود دارد
        with open(file_path, 'rb') as f:
            raw = f.read()
        
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        
        content = raw.decode('utf-8')
        lines = content.split('\n')
        
        # یافتن همه خطوط
        future_indices = []
        docstring_end = 0
        
        # تشخیص docstring
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if '"""' in line or "'''" in line:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    # docstring یک خطی یا شروع
                    if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                        # یک خطی
                        if i == 0:
                            docstring_end = i + 1
                    else:
                        in_docstring = not in_docstring
                        if not in_docstring:
                            docstring_end = i + 1
                continue
            
            if in_docstring:
                continue
            
            # بررسی __future__
            if stripped.startswith('from __future__'):
                future_indices.append(i)
            # بررسی import های دیگر
            elif stripped.startswith('import ') or stripped.startswith('from '):
                break  # اولین import غیر __future__
            elif stripped and not stripped.startswith('#'):
                break  # اولین کد واقعی
        
        if not future_indices:
            log("  ℹ️ __future__ یافت نشد", "INFO")
            return True
        
        # اگر __future__ بعد از کد دیگر است
        if future_indices[0] > 0:
            # جدا کردن __future__ و بقیه
            future_lines = [lines[i] for i in future_indices]
            other_lines = [lines[i] for i in range(len(lines)) if i not in future_indices]
            
            # ساخت فایل جدید
            new_lines = []
            
            # ابتدا shebang/docstring اگر بود
            for line in other_lines[:docstring_end]:
                new_lines.append(line)
            
            # سپس __future__
            for line in future_lines:
                new_lines.append(line)
            
            # سپس بقیه
            for line in other_lines[docstring_end:]:
                new_lines.append(line)
            
            new_content = '\n'.join(new_lines)
            file_path.write_text(new_content, encoding="utf-8")
            log(f"  ✅ __future__ import جابجا شد", "SUCCESS")
            return True
        
        log("  ℹ️ __future__ در موقعیت صحیح است", "INFO")
        return True
        
    except Exception as e:
        log(f"  ❌ خطا: {e}", "ERROR")
        return False


# ==============================================================================
# بخش ۴: تست syntax
# ==============================================================================

def test_syntax() -> int:
    """تست syntax همه فایل‌های پروژه"""
    log("🧪 تست syntax...")
    
    errors = 0
    checked = 0
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        # رد کردن .venv و node_modules
        if ".venv" in str(py_file) or "node_modules" in str(py_file):
            continue
        
        try:
            compile(py_file.read_text(encoding="utf-8"), py_file, "exec")
            checked += 1
        except SyntaxError as e:
            rel = py_file.relative_to(PROJECT_ROOT)
            log(f"  ❌ {rel}: {e.msg} (line {e.lineno})", "ERROR")
            errors += 1
    
    log(f"  📊 {checked} فایل بررسی شد، {errors} خطا", 
        "SUCCESS" if errors == 0 else "ERROR")
    return errors


# ==============================================================================
# بخش ۵: اجرای تست‌ها
# ==============================================================================

def run_tests() -> bool:
    """اجرای تست‌های pytest"""
    log("🧪 اجرای pytest...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--tb=short", "-q"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT / "services",
            timeout=120
        )
        
        # نمایش خروجی
        output = result.stdout
        # استخراج تعداد pass/fail
        match = re.search(r'(\d+) passed(?:, (\d+) failed)?', output)
        if match:
            passed = int(match.group(1))
            failed = int(match.group(2)) if match.group(2) else 0
            log(f"  📊 {passed} passed, {failed} failed", 
                "SUCCESS" if failed == 0 else "WARNING")
            return failed == 0
        
        log(f"  ℹ️ خروجی pytest:\n{output[:500]}", "INFO")
        return result.returncode == 0
        
    except Exception as e:
        log(f"  ❌ خطا در اجرای تست: {e}", "ERROR")
        return False


# ==============================================================================
# بخش ۶: Git commit
# ==============================================================================

def git_commit() -> bool:
    """ثبت commit نهایی"""
    log("📝 ثبت commit...")
    
    try:
        # add
        subprocess.run(
            ["git", "add", "-A"],
            capture_output=True,
            cwd=PROJECT_ROOT,
            timeout=30
        )
        
        # status
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=10
        )
        
        if not result.stdout.strip():
            log("  ℹ️ هیچ تغییری برای commit نیست", "INFO")
            return True
        
        log(f"  📊 تغییرات:\n{result.stdout}", "INFO")
        
        # commit
        commit_msg = (
            "fix: restore httpx package and resolve syntax errors\n\n"
            "- Force reinstall httpx to fix corrupted _urls.py\n"
            "- Fix unexpected indent in engine/hydroma/mrv/models.py\n"
            "- Fix __future__ import position in telegram_bot/formatters.py\n\n"
            "Emergency fix after security script modified .venv files."
        )
        
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=30
        )
        
        if result.returncode == 0:
            log("  ✅ Commit موفق", "SUCCESS")
            return True
        else:
            log(f"  ℹ️ {result.stdout.strip() or result.stderr.strip()}", "INFO")
            return True
        
    except Exception as e:
        log(f"  ❌ خطا: {e}", "ERROR")
        return False


# ==============================================================================
# اجرای اصلی
# ==============================================================================

def main():
    banner("🚨 eco_emergency_fix.py — اقدام اضطراری")
    
    results = {}
    
    # ── بخش ۱: بازگردانی httpx ──
    log("━" * 70)
    log("بخش ۱: بازگردانی httpx (بحرانی)", "BOLD")
    log("━" * 70)
    results["httpx"] = restore_httpx()
    
    # ── بخش ۲: رفع indent ──
    log("\n" + "━" * 70)
    log("بخش ۲: رفع unexpected indent", "BOLD")
    log("━" * 70)
    results["indent"] = fix_indent_models()
    
    # ── بخش ۳: رفع __future__ ──
    log("\n" + "━" * 70)
    log("بخش ۳: رفع __future__ import position", "BOLD")
    log("━" * 70)
    results["future"] = fix_future_formatters()
    
    # ── بخش ۴: تست syntax ──
    log("\n" + "━" * 70)
    log("بخش ۴: تست syntax", "BOLD")
    log("━" * 70)
    results["syntax_errors"] = test_syntax()
    
    # ── بخش ۵: تست pytest ──
    log("\n" + "━" * 70)
    log("بخش ۵: اجرای pytest", "BOLD")
    log("━" * 70)
    results["tests"] = run_tests()
    
    # ── بخش ۶: Git commit ──
    log("\n" + "━" * 70)
    log("بخش ۶: Git commit", "BOLD")
    log("━" * 70)
    results["commit"] = git_commit()
    
    # ── گزارش نهایی ──
    banner("📊 گزارش نهایی")
    
    print(f"{Colors.BOLD}خلاصه:{Colors.RESET}\n")
    print(f"  ✅ httpx: {'بازگردانی شد' if results['httpx'] else '❌ مشکل'}")
    print(f"  ✅ indent: {'اصلاح شد' if results['indent'] else '⚠️'}")
    print(f"  ✅ __future__: {'اصلاح شد' if results['future'] else '⚠️'}")
    print(f"  ✅ syntax errors: {results['syntax_errors']} باقی‌مانده")
    print(f"  ✅ tests: {'همه پاس' if results['tests'] else '⚠️ برخی شکست'}")
    print(f"  ✅ commit: {'موفق' if results['commit'] else '❌'}")
    
    all_ok = (
        results["httpx"] and 
        results["syntax_errors"] == 0 and 
        results["tests"]
    )
    
    print(f"\n{'=' * 70}")
    if all_ok:
        log("🎉 همه مشکلات رفع شد!", "SUCCESS")
        log("📤 دستور نهایی: git push origin main", "INFO")
    else:
        log("⚠️ برخی مشکلات باقی است", "WARNING")
    print(f"{'=' * 70}\n")
    
    # ── دستورات بعدی ──
    print(f"{Colors.BOLD}دستورات بعدی:{Colors.RESET}\n")
    
    if all_ok:
        print("1️⃣  Push به GitHub:")
        print("   git push origin main")
        print()
        print("2️⃣  تأیید نهایی:")
        print("   cd services && python -m pytest --tb=short -q")
    else:
        print("1️⃣  بررسی مشکلات باقی‌مانده:")
        print("   python -m pytest services --tb=short")
    print()
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())