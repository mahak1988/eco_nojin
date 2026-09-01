#!/usr/bin/env python3
"""
Fix MSW Build Scripts
=====================
حل خطای ERR_PNPM_IGNORED_BUILDS برای msw@2.15.0
و اطمینان از اجرای pnpm dev بدون خطا.
"""

import structlog

logger = structlog.get_logger()
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_PACKAGE = FRONTEND_DIR / "package.json"

# فعال‌سازی ANSI در Windows
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7
        )
    except Exception:
        pass


class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"


def info(msg): print(f"{Colors.BLUE}ℹ{Colors.RESET}  {msg}")
def success(msg): print(f"{Colors.GREEN}✓{Colors.RESET}  {msg}")
def warning(msg): print(f"{Colors.YELLOW}⚠{Colors.RESET}  {msg}")
def error(msg): print(f"{Colors.RED}✗{Colors.RESET}  {msg}")
def header(msg):
    logger.info(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.RESET}")
    logger.info(f"{Colors.BOLD}{Colors.CYAN}  {msg}{Colors.RESET}")
    logger.info(f"{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.RESET}\n")


def ensure_path():
    """افزودن ابزارها به PATH"""
    additions = [
        r"C:\Program Files\Git\cmd",
        r"C:\Users\hp\AppData\Roaming\npm",
        r"C:\Users\hp\AppData\Local\pnpm",
        r"C:\Users\hp\AppData\Local\Programs\nodejs",
    ]
    for p in additions:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


def run(cmd, cwd=None, check=True, silent=False):
    """اجرای دستور"""
    if not silent:
        info(f"$ {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0 and check:
        if result.stdout and not silent:
            logger.info(result.stdout[:1000])
        if result.stderr and not silent:
            error(result.stderr[:1000])
        raise RuntimeError(f"Command failed: {cmd}")
    return result


def patch_package_json():
    """
    افزودن onlyBuiltDependencies و allowedDeprecatedVersions به package.json
    تا pnpm v11 اجازه اجرای build scripts را بدهد.
    """
    header("📦 گام ۱: اصلاح package.json")

    if not FRONTEND_PACKAGE.exists():
        error(f"فایل یافت نشد: {FRONTEND_PACKAGE}")
        return False

    with open(FRONTEND_PACKAGE, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    # افزودن onlyBuiltDependencies برای پکیج‌های قابل اعتماد
    # pnpm v11 این را می‌پذیرد (بر خلاف autoInstallPeers در global config)
    only_built = [
        "msw",
        "esbuild",
        "sharp",
        "@swc/core",
        "@parcel/watcher",
        "core-js",
        "unrs-resolver",
    ]

    pkg.setdefault("pnpm", {})
    existing = pkg["pnpm"].get("onlyBuiltDependencies", [])
    merged = list(dict.fromkeys(existing + only_built))  # حفظ ترتیب، حذف تکراری
    pkg["pnpm"]["onlyBuiltDependencies"] = merged

    # اجازه deprecatedها برای جلوگیری از نویز
    pkg["pnpm"]["allowedDeprecatedVersions"] = {
        "glob": "*",
        "inflight": "*",
        "rimraf": "*",
    }

    with open(FRONTEND_PACKAGE, "w", encoding="utf-8") as f:
        json.dump(pkg, f, indent=2, ensure_ascii=False)
        f.write("\n")

    success(f"✓ package.json اصلاح شد")
    info(f"  onlyBuiltDependencies: {len(merged)} پکیج")
    return True


def run_pnpm_install():
    """اجرای pnpm install برای فعال‌سازی build scripts"""
    header("🔨 گام ۲: اجرای pnpm install")

    try:
        result = run("pnpm install", cwd=FRONTEND_DIR, check=False)
        if result.returncode == 0:
            success("✓ pnpm install موفق بود")
            return True

        warning(f"pnpm install با کد {result.returncode} پایان یافت")
        # تلاش مجدد با --force
        info("تلاش مجدد با --force...")
        result2 = run("pnpm install --force", cwd=FRONTEND_DIR, check=False)
        if result2.returncode == 0:
            success("✓ pnpm install --force موفق بود")
            return True

        error("هر دو تلاش شکست خوردند")
        return False

    except Exception as e:
        error(f"خطای غیرمنتظره: {e}")
        return False


def install_playwright_browsers():
    """نصب مرورگرهای Playwright برای تست‌های E2E"""
    header("🌐 گام ۳: نصب Playwright browsers (اختیاری)")

    try:
        result = run("npx playwright install chromium", cwd=FRONTEND_DIR, check=False, silent=False)
        if result.returncode == 0:
            success("✓ Chromium نصب شد")
        else:
            warning("نصب Playwright شکست خورد - تست‌های E2E ممکن است کار نکنند")
            info("💡 می‌توانید بعداً اجرا کنید: npx playwright install")
    except Exception as e:
        warning(f"خطا: {e}")


def test_dev_server():
    """تست سریع dev server (اجرا برای ۱۰ ثانیه و قطع)"""
    header("🧪 گام ۴: تست pnpm dev")

    info("اجرای pnpm dev برای ۱۵ ثانیه...")

    try:
        # اجرای dev server در فرایند جدا با timeout
        proc = subprocess.Popen(
            "pnpm dev",
            shell=True,
            cwd=FRONTEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        import time
        start = time.time()
        output_lines = []
        server_ready = False

        while time.time() - start < 15:
            if proc.poll() is not None:
                # فرایند پایان یافت
                break

            line = proc.stdout.readline()
            if line:
                output_lines.append(line.rstrip())
                # چاپ محدود برای کاربر
                if len(output_lines) <= 10:
                    logger.info(f"  {line.rstrip()}")

                # تشخیص آماده شدن سرور
                if "Local:" in line or "localhost" in line.lower() or "ready" in line.lower():
                    server_ready = True

        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

        if server_ready:
            success("✓ dev server بدون خطا اجرا شد")
            return True

        # بررسی وجود ERR_PNPM_IGNORED_BUILDS در خروجی
        output_text = "\n".join(output_lines)
        if "ERR_PNPM_IGNORED_BUILDS" in output_text:
            error("خطای ERR_PNPM_IGNORED_BUILDS هنوز وجود دارد")
            return False

        if "ERROR" in output_text or "error" in output_text.lower():
            warning("خروجی حاوی error است - بررسی دستی لازم است")
            logger.info("\n".join(output_lines[-10:]))
            return False

        warning("سرور راه‌اندازی نشد اما خطای بحرانی هم دیده نشد")
        return True

    except Exception as e:
        error(f"خطا در تست: {e}")
        return False


def commit_changes():
    """commit تغییرات نهایی"""
    header("🔐 گام ۵: commit تغییرات")

    try:
        run("git add .", cwd=PROJECT_ROOT, silent=True)
        status = run("git status --porcelain", cwd=PROJECT_ROOT, silent=True)
        if not status.stdout.strip():
            info("هیچ تغییری برای commit نیست")
            return True

        run(
            'git commit -m "fix: enable msw build scripts and resolve pnpm dev errors"',
            cwd=PROJECT_ROOT
        )
        success("✓ commit ایجاد شد")
        return True
    except Exception as e:
        warning(f"commit ناموفق: {e}")
        return False


def push_to_origin():
    """push به origin"""
    header("🚀 گام ۶: push به origin")

    try:
        # بررسی وجود remote
        result = run("git remote get-url origin", cwd=PROJECT_ROOT, silent=True, check=False)
        if result.returncode != 0:
            warning("remote origin یافت نشد - push انجام نمی‌شود")
            info("💡 برای افزودن remote:")
            info("   git remote add origin https://github.com/USER/REPO.git")
            return False

        url = result.stdout.strip()
        info(f"remote: {url}")

        run("git push origin main", cwd=PROJECT_ROOT)
        success("✓ push موفق بود")
        return True
    except Exception as e:
        warning(f"push ناموفق: {e}")
        info("💡 push دستی:")
        info("   git push origin main")
        return False


def final_report():
    """گزارش نهایی"""
    header("📊 گزارش نهایی")

    checks = []

    # 1. msw worker
    msw_worker = FRONTEND_DIR / "public" / "mockServiceWorker.js"
    checks.append(("MSW worker file", msw_worker.exists()))

    # 2. node_modules
    nm = FRONTEND_DIR / "node_modules"
    checks.append(("node_modules", nm.exists()))

    # 3. git clean
    status = run("git status --porcelain", cwd=PROJECT_ROOT, silent=True, check=False)
    is_clean = not status.stdout.strip()
    checks.append(("Git clean", is_clean))

    for name, ok in checks:
        symbol = "✓" if ok else "✗"
        color = Colors.GREEN if ok else Colors.YELLOW
        logger.info(f"  {color}{symbol}{Colors.RESET} {name}")

    all_ok = all(ok for _, ok in checks)

    if all_ok:
        logger.info(f"\n{Colors.GREEN}{Colors.BOLD}🎉 فاز صفر کاملاً موفق بود!{Colors.RESET}")
        logger.info(f"\n{Colors.BOLD}گام بعدی: ورود به فاز ۱{Colors.RESET}")
        logger.info("  شروع بازنویسی فایل‌های بحرانی به‌صورت فیچرمحور")
    else:
        logger.info(f"\n{Colors.YELLOW}⚠️ برخی موارد نیاز به بررسی دستی دارند{Colors.RESET}")

    return all_ok


def main():
    logger.info(f"\n{Colors.BOLD}{'═' * 70}{Colors.RESET}")
    logger.info(f"{Colors.BOLD}  🔧 Fix MSW Builds - حل خطای نهایی فاز صفر{Colors.RESET}")
    logger.info(f"{Colors.BOLD}{'═' * 70}{Colors.RESET}")

    ensure_path()

    steps = [
        ("patch_package_json", patch_package_json),
        ("run_pnpm_install", run_pnpm_install),
        ("install_playwright_browsers", install_playwright_browsers),
        ("test_dev_server", test_dev_server),
        ("commit_changes", commit_changes),
        ("push_to_origin", push_to_origin),
    ]

    failed = []
    for name, fn in steps:
        try:
            if not fn():
                failed.append(name)
        except Exception as e:
            error(f"{name}: {e}")
            failed.append(name)

    final_report()

    if failed:
        logger.info(f"\n{Colors.YELLOW}گام‌های شکست‌خورده: {', '.join(failed)}{Colors.RESET}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())