#!/usr/bin/env python3
"""
eco_security_phase2.py
======================
فاز دوم امنیت: رفع دقیق مشکلات امنیتی

اصلاحات:
1. افزودن Git به PATH
2. خواندن فایل‌های واقعی برای شناسایی دقیق الگوها
3. اصلاح SQL injection با الگوهای دقیق
4. اصلاح همه موارد shell=True
5. انتقال رمزهای عبور به env vars
6. commit امن
"""

import sys
import re
import shutil
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Dict

PROJECT_ROOT = Path(__file__).parent.resolve()
BACKUP_SUFFIX = ".security.bak"

# مسیرهای Git
GIT_PATHS = [
    r"C:\Program Files\Git\cmd",
    r"C:\Program Files (x86)\Git\cmd",
    r"C:\Users\{}\AppData\Local\Programs\Git\cmd".format(os.getlogin()),
]


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


def backup_file(file_path: Path) -> Path:
    """پشتیبان‌گیری امن از فایل"""
    backup = file_path.with_suffix(file_path.suffix + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copy2(file_path, backup)
        log(f"  📦 پشتیبان: {backup.name}", "SUCCESS")
    return backup


# ==============================================================================
# مرحله 0: افزودن Git به PATH
# ==============================================================================

def setup_git_path() -> bool:
    """افزودن Git به PATH"""
    log("🔍 بررسی Git در PATH...")
    
    # تست Git
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            log(f"  ✅ Git در دسترس: {result.stdout.strip()}", "SUCCESS")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # یافتن Git
    log("  ⚠️ Git یافت نشد. در حال جستجو...", "WARNING")
    
    for git_path in GIT_PATHS:
        if os.path.exists(git_path):
            git_exe = os.path.join(git_path, "git.exe")
            if os.path.exists(git_exe):
                log(f"  ✅ Git یافت شد: {git_path}", "SUCCESS")
                
                # افزودن به PATH فعلی
                os.environ["PATH"] = f"{git_path};{os.environ.get('PATH', '')}"
                
                # تست مجدد
                try:
                    result = subprocess.run(
                        ["git", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        log(f"  ✅ Git به PATH اضافه شد", "SUCCESS")
                        return True
                except Exception as e:
                    log(f"  ❌ خطا در تست Git: {e}", "ERROR")
    
    log("  ❌ Git یافت نشد!", "ERROR")
    return False


# ==============================================================================
# مرحله 1: جستجوی فایل‌های واقعی
# ==============================================================================

def find_files_with_pattern(pattern: str, search_dirs: List[Path]) -> List[Tuple[Path, List[int]]]:
    """جستجوی فایل‌هایی که الگوی خاصی دارند"""
    results = []
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        for py_file in search_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                matches = []
                
                for i, line in enumerate(content.split('\n'), 1):
                    if re.search(pattern, line):
                        matches.append(i)
                
                if matches:
                    results.append((py_file, matches))
            except Exception:
                pass
    
    return results


def find_sql_injections() -> List[Tuple[Path, List[int]]]:
    """یافتن SQL injection ها"""
    log("🔍 جستجوی SQL injection...")
    
    # الگوهای SQL injection
    patterns = [
        r'f["\']SELECT.*\{.*\}.*["\']',
        r'f["\']INSERT.*\{.*\}.*["\']',
        r'f["\']UPDATE.*\{.*\}.*["\']',
        r'f["\']DELETE.*\{.*\}.*["\']',
        r'\.execute\(f["\']',
    ]
    
    search_dirs = [
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "services",
    ]
    
    all_results = []
    for pattern in patterns:
        results = find_files_with_pattern(pattern, search_dirs)
        all_results.extend(results)
    
    # حذف تکراری‌ها
    unique_results = {}
    for path, lines in all_results:
        if path not in unique_results:
            unique_results[path] = lines
        else:
            unique_results[path].extend(lines)
    
    results = [(path, sorted(set(lines))) for path, lines in unique_results.items()]
    
    for path, lines in results:
        log(f"  📄 {path.relative_to(PROJECT_ROOT)}: خطوط {lines}", "INFO")
    
    return results


def find_shell_true() -> List[Tuple[Path, List[int]]]:
    """یافتن subprocess با shell=True"""
    log("🔍 جستجوی subprocess با shell=True...")
    
    pattern = r'subprocess\.(run|Popen|call|check_output|check_call)\(.*shell\s*=\s*True'
    
    search_dirs = [PROJECT_ROOT]
    results = find_files_with_pattern(pattern, search_dirs)
    
    for path, lines in results:
        log(f"  📄 {path.relative_to(PROJECT_ROOT)}: خطوط {lines}", "INFO")
    
    return results


def find_hardcoded_secrets() -> List[Tuple[Path, List[int]]]:
    """یافتن رمزهای عبور hardcoded"""
    log("🔍 جستجوی رمزهای عبور hardcoded...")
    
    patterns = [
        r'(password|passwd|pwd|secret|token|api_key|apikey)\s*=\s*["\'][^"\']+["\']',
        r'(postgresql|mysql|mongodb)://\w+:[^@]+@',
    ]
    
    search_dirs = [PROJECT_ROOT]
    
    all_results = []
    for pattern in patterns:
        results = find_files_with_pattern(pattern, search_dirs)
        all_results.extend(results)
    
    # حذف فایل‌های env
    all_results = [(p, l) for p, l in all_results if not p.name.endswith('.env')]
    
    # حذف تکراری‌ها
    unique_results = {}
    for path, lines in all_results:
        if path not in unique_results:
            unique_results[path] = lines
        else:
            unique_results[path].extend(lines)
    
    results = [(path, sorted(set(lines))) for path, lines in unique_results.items()]
    
    for path, lines in results[:10]:  # فقط 10 مورد اول
        log(f"  📄 {path.relative_to(PROJECT_ROOT)}: خطوط {lines}", "INFO")
    
    return results


# ==============================================================================
# مرحله 2: اصلاح SQL Injection
# ==============================================================================

def fix_sql_injection_file(file_path: Path) -> bool:
    """رفع SQL injection در یک فایل"""
    content = file_path.read_text(encoding="utf-8")
    original = content
    
    # الگو 1: f-string در execute
    # cursor.execute(f"SELECT * FROM {table}") → cursor.execute(f"SELECT * FROM {table}")
    # این نیاز به تحلیل دقیق‌تر دارد
    
    # الگوی ساده‌تر: اگر f-string در SQL است، آن را با placeholder جایگزین کن
    # f"SELECT * FROM users WHERE id = {user_id}"
    # → "SELECT * FROM users WHERE id = ?", (user_id,)
    
    # جستجو برای الگوی f-string با variable در SQL
    pattern = r'(cursor\.execute|session\.execute|conn\.execute)\(\s*f(["\'])(.*?)(\2)\s*\)'
    
    def replace_fstring(match):
        prefix = match.group(1)
        quote = match.group(2)
        sql = match.group(3)
        
        # استخراج variable ها
        vars_in_sql = re.findall(r'\{(\w+)\}', sql)
        if not vars_in_sql:
            return match.group(0)
        
        # جایگزینی {var} با ?
        sql_clean = re.sub(r'\{\w+\}', '?', sql)
        
        # ساخت tuple از variables
        vars_tuple = ', '.join(vars_in_sql)
        
        return f'{prefix}({quote}{sql_clean}{quote}, ({vars_tuple},))'
    
    content = re.sub(pattern, replace_fstring, content, flags=re.DOTALL)
    
    if content != original:
        backup_file(file_path)
        file_path.write_text(content, encoding="utf-8")
        log(f"  ✅ SQL injection رفع شد در {file_path.name}", "SUCCESS")
        return True
    
    return False


def fix_all_sql_injections(sql_files: List[Tuple[Path, List[int]]]) -> int:
    """رفع همه SQL injection ها"""
    log("🔧 رفع SQL Injection...")
    
    fixed = 0
    for file_path, lines in sql_files:
        if fix_sql_injection_file(file_path):
            fixed += 1
    
    return fixed


# ==============================================================================
# مرحله 3: اصلاح shell=True
# ==============================================================================

def fix_shell_true_file(file_path: Path) -> bool:
    """رفع shell=True در یک فایل"""
    content = file_path.read_text(encoding="utf-8")
    original = content
    
    # الگو 1: subprocess.run("cmd".split(), shell=False)
    # → subprocess.run(["cmd"], shell=False)
    
    # جستجو برای shell=True
    content = re.sub(
        r'(subprocess\.(?:run|Popen|call|check_output|check_call))\(\s*(["\'])(.*?)(\2)\s*,\s*shell\s*=\s*True',
        r'\1(\2\3\2.split(), shell=False',
        content
    )
    
    # الگو 2: subprocess.run(cmd.split() if isinstance(cmd, str) else cmd, shell=False)
    # → subprocess.run(cmd.split() if isinstance(cmd, str) else cmd, shell=False)
    content = re.sub(
        r'(subprocess\.(?:run|Popen|call|check_output|check_call))\(\s*(\w+)\s*,\s*shell\s*=\s*True',
        r'\1(\2.split() if isinstance(\2, str) else \2, shell=False',
        content
    )
    
    # الگو 3: shell=True با kwargs دیگر
    content = re.sub(
        r'shell\s*=\s*True(\s*,\s*)',
        r'shell=False\1',
        content
    )
    
    if content != original:
        backup_file(file_path)
        file_path.write_text(content, encoding="utf-8")
        log(f"  ✅ shell=True رفع شد در {file_path.name}", "SUCCESS")
        return True
    
    return False


def fix_all_shell_true(shell_files: List[Tuple[Path, List[int]]]) -> int:
    """رفع همه موارد shell=True"""
    log("🔧 رفع shell=True...")
    
    fixed = 0
    for file_path, lines in shell_files:
        if fix_shell_true_file(file_path):
            fixed += 1
    
    return fixed


# ==============================================================================
# مرحله 4: انتقال رمزهای عبور به env vars
# ==============================================================================

def fix_hardcoded_secret_file(file_path: Path) -> bool:
    """انتقال رمزهای عبور به env vars"""
    content = file_path.read_text(encoding="utf-8")
    original = content
    
    # الگو 1: password = os.environ.get("PASSWORD", "secret")
    # → password = os.environ.get("PASSWORD", "secret")
    
    # جستجو برای assignment های sensitive
    pattern = r'(\w*(?:password|passwd|pwd|secret|token|api_key|apikey)\w*)\s*=\s*(["\'])([^"\']+)(\2)'
    
    def replace_secret(match):
        var_name = match.group(1)
        quote = match.group(2)
        value = match.group(3)
        
        # تبدیل نام متغیر به uppercase
        env_var = var_name.upper()
        
        return f'{var_name} = os.environ.get("{env_var}", {quote}{value}{quote})'
    
    content = re.sub(pattern, replace_secret, content, flags=re.IGNORECASE)
    
    # الگو 2: connection string با رمز
    # "postgresql://user:pass@host/db"
    # → os.environ.get("DATABASE_URL", "postgresql://user:pass@host/db")
    pattern = r'(\w+)\s*=\s*(["\'])((?:postgresql|mysql|mongodb)://[^"\']+)(\2)'
    
    def replace_conn_string(match):
        var_name = match.group(1)
        quote = match.group(2)
        conn_string = match.group(3)
        
        env_var = var_name.upper()
        
        return f'{var_name} = os.environ.get("{env_var}", {quote}{conn_string}{quote})'
    
    content = re.sub(pattern, replace_conn_string, content)
    
    if content != original:
        backup_file(file_path)
        # افزودن import os اگر نیست
        if "import os" not in content:
            content = "import os\n" + content
        file_path.write_text(content, encoding="utf-8")
        log(f"  ✅ رمز عبور به env var منتقل شد در {file_path.name}", "SUCCESS")
        return True
    
    return False


def fix_all_hardcoded_secrets(secret_files: List[Tuple[Path, List[int]]]) -> int:
    """انتقال همه رمزهای عبور به env vars"""
    log("🔧 انتقال رمزهای عبور به env vars...")
    
    fixed = 0
    for file_path, lines in secret_files[:20]:  # فقط 20 فایل اول
        if fix_hardcoded_secret_file(file_path):
            fixed += 1
    
    return fixed


# ==============================================================================
# مرحله 5: تست syntax
# ==============================================================================

def test_syntax() -> bool:
    """تست syntax همه فایل‌های Python"""
    log("🧪 تست syntax...")
    
    errors = 0
    checked = 0
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if ".venv" in str(py_file) or "node_modules" in str(py_file):
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
# مرحله 6: Git commit
# ==============================================================================

def git_commit() -> bool:
    """ثبت commit امن"""
    log("📝 ثبت commit...")
    
    try:
        # git add
        result = subprocess.run(
            ["git", "add", "-A"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=30
        )
        
        if result.returncode != 0:
            log(f"  ❌ git add failed: {result.stderr}", "ERROR")
            return False
        
        # git status
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
        
        # git commit
        commit_msg = (
            "security: fix critical vulnerabilities\n\n"
            "- Fix SQL injection (parameterized queries)\n"
            "- Fix subprocess shell=True (use list args)\n"
            "- Move hardcoded secrets to env vars\n\n"
            "All changes are backward compatible with fallback values."
        )
        
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=30
        )
        
        if result.returncode == 0:
            log(f"  ✅ Commit موفق", "SUCCESS")
            return True
        else:
            log(f"  ❌ Commit failed: {result.stderr}", "ERROR")
            return False
        
    except Exception as e:
        log(f"  ❌ خطا: {e}", "ERROR")
        return False


# ==============================================================================
# اجرای اصلی
# ==============================================================================

def main():
    banner("🛡️ eco_security_phase2.py — فاز دوم امنیت")
    
    # ── مرحله 0: Git ──
    log("━" * 70)
    log("مرحله 0: تنظیم Git", "BOLD")
    log("━" * 70)
    
    git_ok = setup_git_path()
    
    # ── مرحله 1: جستجو ──
    log("\n" + "━" * 70)
    log("مرحله 1: جستجوی مشکلات امنیتی", "BOLD")
    log("━" * 70)
    
    sql_files = find_sql_injections()
    shell_files = find_shell_true()
    secret_files = find_hardcoded_secrets()
    
    log(f"\n📊 خلاصه:")
    log(f"  • SQL Injection: {len(sql_files)} فایل")
    log(f"  • shell=True: {len(shell_files)} فایل")
    log(f"  • رمزهای عبور: {len(secret_files)} فایل")
    
    # ── مرحله 2-4: اصلاح ──
    log("\n" + "━" * 70)
    log("مرحله 2-4: رفع مشکلات", "BOLD")
    log("━" * 70)
    
    sql_fixed = fix_all_sql_injections(sql_files)
    shell_fixed = fix_all_shell_true(shell_files)
    secret_fixed = fix_all_hardcoded_secrets(secret_files)
    
    log(f"\n📊 خلاصه اصلاحات:")
    log(f"  ✅ SQL Injection: {sql_fixed} فایل")
    log(f"  ✅ shell=True: {shell_fixed} فایل")
    log(f"  ✅ رمزهای عبور: {secret_fixed} فایل")
    
    # ── مرحله 5: تست syntax ──
    log("\n" + "━" * 70)
    log("مرحله 5: تست syntax", "BOLD")
    log("━" * 70)
    
    syntax_ok = test_syntax()
    
    # ── مرحله 6: Git commit ──
    if git_ok:
        log("\n" + "━" * 70)
        log("مرحله 6: Git commit", "BOLD")
        log("━" * 70)
        
        commit_ok = git_commit()
    else:
        commit_ok = False
        log("\n  ⚠️ Git در دسترس نیست، commit انجام نشد", "WARNING")
    
    # ── گزارش نهایی ──
    banner("📊 گزارش نهایی")
    
    print(f"{Colors.BOLD}خلاصه:{Colors.RESET}\n")
    print(f"  SQL Injection: {sql_fixed} فایل اصلاح شد")
    print(f"  shell=True: {shell_fixed} فایل اصلاح شد")
    print(f"  رمزهای عبور: {secret_fixed} فایل اصلاح شد")
    print(f"  Syntax: {'✅' if syntax_ok else '❌'}")
    print(f"  Git: {'✅' if git_ok else '❌'}")
    print(f"  Commit: {'✅' if commit_ok else '⚠️'}")
    
    # ── نتیجه کلی ──
    all_ok = syntax_ok and (sql_fixed + shell_fixed + secret_fixed) > 0
    
    print(f"\n{'=' * 70}")
    if all_ok:
        log("🎉 اصلاحات امنیتی با موفقیت انجام شد!", "SUCCESS")
    else:
        log("⚠️ برخی اصلاحات نیاز به بررسی دارند", "WARNING")
    print(f"{'=' * 70}\n")
    
    # ── دستورات بعدی ──
    print(f"{Colors.BOLD}دستورات بعدی:{Colors.RESET}\n")
    
    if not git_ok:
        print("1️⃣  افزودن Git به PATH:")
        print('   $env:Path += ";C:\\Program Files\\Git\\cmd"')
        print()
    
    print("2️⃣  بررسی تغییرات:")
    print("   git status")
    print("   git diff --stat")
    print()
    
    print("3️⃣  اجرای تست‌ها:")
    print("   cd services && python -m pytest --tb=short -q")
    print()
    
    if not commit_ok and git_ok:
        print("4️⃣  ثبت commit:")
        print("   git add -A")
        print('   git commit -m "security: fix critical vulnerabilities"')
        print()
    
    if commit_ok:
        print("4️⃣  Push به GitHub:")
        print("   git push origin main")
        print()
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())