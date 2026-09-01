#!/usr/bin/env python3
"""
Fix All Issues - One-Shot Solution
==================================
حل یکپارچه همه مشکلات فاز صفر:
1. یافتن و افزودن PATH ابزارها
2. پاک‌سازی کامل frontend/frontend
3. ایجاد pnpm-workspace.yaml
4. اجرای git init/add/commit
"""

import structlog

logger = structlog.get_logger()
import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

# افزودن scripts به path
sys.path.insert(0, str(Path(__file__).parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"

# فعال‌سازی ANSI در Windows
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

def info(msg: str) -> None:
    logger.info(f"{Colors.BLUE}ℹ{Colors.RESET}  {msg}")

def success(msg: str) -> None:
    logger.info(f"{Colors.GREEN}✓{Colors.RESET}  {msg}")

def warning(msg: str) -> None:
    logger.info(f"{Colors.YELLOW}⚠{Colors.RESET}  {msg}")

def error(msg: str) -> None:
    logger.info(f"{Colors.RED}✗{Colors.RESET}  {msg}")

def header(msg: str) -> None:
    logger.info(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.RESET}")
    logger.info(f"{Colors.BOLD}{Colors.CYAN}  {msg}{Colors.RESET}")
    logger.info(f"{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.RESET}\n")

def step(number: int, msg: str) -> None:
    logger.info(f"\n{Colors.BOLD}{Colors.MAGENTA}[گام {number}]{Colors.RESET} {msg}")
    logger.info(f"{Colors.DIM if hasattr(Colors, 'DIM') else ''}{'─' * 70}{Colors.RESET}")


# ═══════════════════════════════════════════════════════════════════════
# بخش ۱: یافتن و تنظیم PATH
# ═══════════════════════════════════════════════════════════════════════

COMMON_PATHS = {
    "git": [
        r"C:\Program Files\Git\cmd",
        r"C:\Program Files\Git\bin",
        r"C:\Program Files (x86)\Git\cmd",
        r"C:\Users\{user}\AppData\Local\Programs\Git\cmd",
    ],
    "node": [
        r"C:\Program Files\nodejs",
        r"C:\Program Files (x86)\nodejs",
        r"C:\Users\{user}\AppData\Roaming\npm",
        r"C:\Users\{user}\AppData\Local\fnm_multishells",
    ],
    "pnpm": [
        r"C:\Users\{user}\AppData\Local\pnpm",
        r"C:\Users\{user}\AppData\Roaming\npm",
        r"C:\Program Files\nodejs",
    ],
}


def find_executable(name: str, extra_paths: Optional[list] = None) -> Optional[Path]:
    """یافتن مسیر کامل یک اجرایی"""
    # ابتدا با shutil.which
    which_result = shutil.which(name)
    if which_result:
        return Path(which_result)
    
    # سپس در مسیرهای رایج
    username = os.environ.get("USERNAME", os.environ.get("USER", ""))
    
    candidates = COMMON_PATHS.get(name, [])
    if extra_paths:
        candidates.extend(extra_paths)
    
    for candidate in candidates:
        path = Path(candidate.format(user=username))
        exe_name = f"{name}.exe" if sys.platform == "win32" else name
        full_path = path / exe_name
        if full_path.exists():
            return full_path
    
    return None


def setup_path() -> dict:
    """یافتن و افزودن ابزارها به PATH"""
    header("🔧 گام ۱: یافتن و تنظیم PATH ابزارها")
    
    tools = {}
    
    for tool_name in ["git", "node", "pnpm"]:
        exe_path = find_executable(tool_name)
        if exe_path:
            tools[tool_name] = exe_path
            success(f"{tool_name}: {exe_path}")
            
            # افزودن به PATH
            dir_path = str(exe_path.parent)
            if dir_path not in os.environ["PATH"]:
                os.environ["PATH"] = dir_path + os.pathsep + os.environ["PATH"]
                info(f"  افزوده شد به PATH: {dir_path}")
        else:
            error(f"{tool_name}: یافت نشد")
    
    # بررسی node و pnpm در AppData\Roaming\npm (محل نصب global)
    npm_global = Path(os.environ.get("APPDATA", "")) / "npm"
    if npm_global.exists() and str(npm_global) not in os.environ["PATH"]:
        os.environ["PATH"] = str(npm_global) + os.pathsep + os.environ["PATH"]
        info(f"npm global path افزوده شد: {npm_global}")
    
    # pnpm در Local
    pnpm_local = Path(os.environ.get("LOCALAPPDATA", "")) / "pnpm"
    if pnpm_local.exists() and str(pnpm_local) not in os.environ["PATH"]:
        os.environ["PATH"] = str(pnpm_local) + os.pathsep + os.environ["PATH"]
        info(f"pnpm local path افزوده شد: {pnpm_local}")
    
    # تست نهایی
    logger.info(f"\n{Colors.BOLD}نتیجه تشخیص:{Colors.RESET}")
    for tool in ["git", "node", "pnpm"]:
        code = subprocess.run(f"{tool} --version", shell=True, capture_output=True).returncode
        status = "🟢" if code == 0 else "🔴"
        logger.info(f"  {status} {tool}")
    
    return tools


# ═══════════════════════════════════════════════════════════════════════
# بخش ۲: پاک‌سازی کامل frontend/frontend
# ═══════════════════════════════════════════════════════════════════════

def clean_double_frontend() -> bool:
    """پاک‌سازی کامل ساختار اشتباه frontend/frontend"""
    header("🔨 گام ۲: پاک‌سازی frontend/frontend")
    
    double = FRONTEND_DIR / "frontend"
    
    if not double.exists():
        success("ساختار اشتباه یافت نشد - تمیز است")
        return True
    
    warning(f"ساختار اشتباه یافت شد: {double}")
    
    # شمارش محتوا
    items = list(double.rglob("*"))
    info(f"تعداد آیتم‌ها: {len(items)}")
    
    # بررسی تداخل
    conflicts = []
    for item in double.rglob("*"):
        if item.is_file():
            relative = item.relative_to(double)
            target = FRONTEND_DIR / relative
            if target.exists():
                conflicts.append((item, target))
    
    if conflicts:
        warning(f"{len(conflicts)} فایل تداخل دارند:")
        for src, dst in conflicts[:5]:
            logger.info(f"    - {src.name} → {dst}")
        if len(conflicts) > 5:
            logger.info(f"    - ... و {len(conflicts) - 5} فایل دیگر")
        
        info("فایل‌های تکراری حذف می‌شوند (مقصد حفظ می‌شود)")
    
    # انتقال فایل‌های بدون تداخل
    moved = 0
    for item in double.rglob("*"):
        if item.is_file():
            relative = item.relative_to(double)
            target = FRONTEND_DIR / relative
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(target))
                moved += 1
    
    if moved > 0:
        success(f"{moved} فایل منتقل شد")
    
    # حذف کامل پوشه frontend/frontend
    try:
        shutil.rmtree(double)
        success(f"✓ پوشه اشتباه کاملاً حذف شد: {double}")
        return True
    except Exception as e:
        error(f"حذف پوشه ناموفق: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۳: ایجاد pnpm-workspace.yaml و تنظیمات صحیح
# ═══════════════════════════════════════════════════════════════════════

def setup_pnpm_workspace() -> bool:
    """ایجاد pnpm-workspace.yaml با auto-install-peers"""
    header("📦 گام ۳: تنظیم pnpm workspace")
    
    workspace_file = PROJECT_ROOT / "pnpm-workspace.yaml"
    
    content = """# pnpm workspace configuration
packages:
  - 'frontend'
  - 'services/*'

# این تنظیمات باید در workspace level باشد نه global
autoInstallPeers: true
strictPeerDependencies: false

# تنظیمات performance
preferFrozenLockfile: true
"""
    
    try:
        workspace_file.write_text(content, encoding='utf-8')
        success(f"✓ pnpm-workspace.yaml ایجاد شد: {workspace_file}")
    except Exception as e:
        error(f"خطا: {e}")
        return False
    
    # اصلاح .npmrc (حذف auto-install-peers که در workspace باید باشد)
    npmrc = FRONTEND_DIR / ".npmrc"
    if npmrc.exists():
        content = """# pnpm configuration
registry=https://registry.npmjs.org/
strict-ssl=true

# استفاده از workspace برای auto-install-peers
# (در pnpm-workspace.yaml تنظیم شده)

# Hoist settings
shamefully-hoist=true
public-hoist-pattern[]=*eslint*
public-hoist-pattern[]=*typescript*
"""
        npmrc.write_text(content, encoding='utf-8')
        success("✓ .npmrc اصلاح شد")
    
    return True


# ═══════════════════════════════════════════════════════════════════════
# بخش ۴: Git init و commit اولیه
# ═══════════════════════════════════════════════════════════════════════

def setup_git_repo() -> bool:
    """راه‌اندازی ریپازیتوری Git و commit اولیه"""
    header("🔐 گام ۴: راه‌اندازی Git Repository")
    
    # بررسی .gitignore
    gitignore = PROJECT_ROOT / ".gitignore"
    if not gitignore.exists():
        error(".gitignore یافت نشد")
        return False
    success(f".gitignore: {gitignore}")
    
    # بررسی وجود git repo
    git_dir = PROJECT_ROOT / ".git"
    if git_dir.exists():
        info("ریپازیتوری Git قبلاً وجود دارد")
    else:
        info("ایجاد ریپازیتوری Git...")
        
        result = subprocess.run(
            "git init",
            shell=True,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error(f"git init ناموفق: {result.stderr}")
            return False
        success("✓ git init موفق")
    
    # تنظیم branch به main
    subprocess.run("git branch -M main", shell=True, cwd=PROJECT_ROOT)
    
    # افزودن فایل‌ها
    info("افزودن فایل‌ها به staging...")
    result = subprocess.run(
        "git add .",
        shell=True,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        error(f"git add ناموفق: {result.stderr}")
        return False
    
    # بررسی staging
    status_result = subprocess.run(
        "git status --porcelain",
        shell=True,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    staged_files = [line for line in status_result.stdout.split('\n') if line.strip()]
    info(f"تعداد فایل‌های staged: {len(staged_files)}")
    
    # بررسی فایل‌های حساس
    dangerous_patterns = [".env", ".pkl", ".bundle", "secrets/", "_quarantine/"]
    dangerous_files = []
    for line in staged_files:
        filename = line[3:]  # بعد از "M  " یا "A  "
        for pattern in dangerous_patterns:
            if pattern in filename:
                dangerous_files.append(filename)
                break
    
    if dangerous_files:
        warning(f"{len(dangerous_files)} فایل حساس در staging:")
        for f in dangerous_files[:10]:
            logger.info(f"    - {f}")
        if len(dangerous_files) > 10:
            logger.info(f"    - ... و {len(dangerous_files) - 10} فایل دیگر")
        
        info("این فایل‌ها unstage می‌شوند...")
        for f in dangerous_files:
            subprocess.run(
                f'git reset -- "{f}"',
                shell=True,
                cwd=PROJECT_ROOT,
                capture_output=True
            )
        success("✓ فایل‌های حساس unstage شدند")
    
    # commit
    info("ایجاد commit اولیه...")
    result = subprocess.run(
        'git commit -m "chore: initial project setup with .gitignore"',
        shell=True,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        if "nothing to commit" in result.stdout:
            warning("هیچ تغییری برای commit وجود ندارد")
        else:
            error(f"git commit ناموفق: {result.stderr}")
            return False
    else:
        success("✓ commit اولیه ایجاد شد")
    
    # نمایش وضعیت نهایی
    result = subprocess.run(
        "git log --oneline -5",
        shell=True,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.info(f"\n{Colors.BOLD}آخرین commits:{Colors.RESET}")
        for line in result.stdout.split('\n')[:5]:
            if line:
                logger.info(f"  {line}")
    
    return True


# ═══════════════════════════════════════════════════════════════════════
# بخش ۵: تست نهایی
# ═══════════════════════════════════════════════════════════════════════

def final_verification() -> bool:
    """تأیید نهایی همه موارد"""
    header("✅ گام ۵: تأیید نهایی")
    
    checks = []
    
    # 1. Git
    result = subprocess.run("git --version", shell=True, capture_output=True)
    checks.append(("Git", result.returncode == 0))
    
    # 2. Node
    result = subprocess.run("node --version", shell=True, capture_output=True)
    checks.append(("Node.js", result.returncode == 0))
    
    # 3. pnpm
    result = subprocess.run("pnpm --version", shell=True, capture_output=True)
    checks.append(("pnpm", result.returncode == 0))
    
    # 4. frontend/frontend حذف شده
    double = FRONTEND_DIR / "frontend"
    checks.append(("No double frontend", not double.exists()))
    
    # 5. pnpm-workspace.yaml
    workspace = PROJECT_ROOT / "pnpm-workspace.yaml"
    checks.append(("pnpm-workspace.yaml", workspace.exists()))
    
    # 6. .gitignore
    gitignore = PROJECT_ROOT / ".gitignore"
    checks.append((".gitignore", gitignore.exists()))
    
    # 7. .git
    git_dir = PROJECT_ROOT / ".git"
    checks.append(("Git repository", git_dir.exists()))
    
    # نمایش نتایج
    all_ok = True
    for name, ok in checks:
        status = "✓" if ok else "✗"
        color = Colors.GREEN if ok else Colors.RED
        logger.info(f"  {color}{status}{Colors.RESET} {name}")
        if not ok:
            all_ok = False
    
    return all_ok


# ═══════════════════════════════════════════════════════════════════════
# اجرای اصلی
# ═══════════════════════════════════════════════════════════════════════

def main() -> int:
    logger.info(f"\n{Colors.BOLD}{'═' * 70}{Colors.RESET}")
    logger.info(f"{Colors.BOLD}  🚀 Fix All - راه‌حل یکپارچه مشکلات فاز صفر{Colors.RESET}")
    logger.info(f"{Colors.BOLD}{'═' * 70}{Colors.RESET}\n")
    
    info(f"مسیر پروژه: {PROJECT_ROOT}")
    
    # بررسی مسیر
    if not PROJECT_ROOT.exists():
        error(f"مسیر پروژه یافت نشد: {PROJECT_ROOT}")
        return 1
    
    # گام ۱: تنظیم PATH
    tools = setup_path()
    
    if "git" not in tools:
        error("Git یافت نشد. لطفاً Git را نصب کنید:")
        info("  https://git-scm.com/download/win")
        return 1
    
    # گام ۲: پاک‌سازی frontend/frontend
    if not clean_double_frontend():
        error("پاک‌سازی frontend/frontend ناموفق")
        return 1
    
    # گام ۳: تنظیم pnpm workspace
    if not setup_pnpm_workspace():
        error("تنظیم pnpm workspace ناموفق")
        return 1
    
    # گام ۴: Git repository
    if not setup_git_repo():
        warning("راه‌اندازی Git ناموفق - ولی ادامه می‌دهیم")
    
    # گام ۵: تأیید نهایی
    all_ok = final_verification()
    
    # گزارش نهایی
    logger.info(f"\n{Colors.BOLD}{'═' * 70}{Colors.RESET}")
    if all_ok:
        logger.info(f"{Colors.GREEN}{Colors.BOLD}  🎉 همه موارد با موفقیت انجام شد!{Colors.RESET}")
        logger.info(f"{Colors.BOLD}{'═' * 70}{Colors.RESET}")
        logger.info(f"\n{Colors.BOLD}گام‌های بعدی:{Colors.RESET}")
        logger.info(f"  1. cd {FRONTEND_DIR}")
        logger.info(f"  2. pnpm install")
        logger.info(f"  3. pnpm dev")
        logger.info(f"\n{Colors.BOLD}برای push به origin:{Colors.RESET}")
        logger.info(f'  $env:Path += ";C:\\Program Files\\Git\\cmd"')
        logger.info(f'  git remote add origin <your-repo-url>')
        logger.info(f'  git push -u origin main')
        return 0
    else:
        logger.info(f"{Colors.RED}{Colors.BOLD}  ❌ برخی موارد ناموفق بود{Colors.RESET}")
        logger.info(f"{Colors.BOLD}{'═' * 70}{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())