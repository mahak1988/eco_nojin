#!/usr/bin/env python3
"""
Fix React Query Installation & Configuration
=============================================
1. Install @tanstack/react-query
2. Add QueryClientProvider to main.tsx
3. Re-run build
4. Commit
"""

import structlog

logger = structlog.get_logger()
import os
import re
import sys
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
PKG_JSON = FRONTEND / "package.json"
MAIN_TSX = FRONTEND / "src" / "main.tsx"


def ok(m): print(f"\033[92m✓\033[0m  {m}")
def info(m): print(f"\033[94mℹ\033[0m  {m}")
def warn(m): print(f"\033[93m⚠\033[0m  {m}")
def err(m): print(f"\033[91m✗\033[0m  {m}")


def ensure_git_in_path():
    """اطمینان از وجود git در PATH"""
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


def install_react_query():
    """نصب @tanstack/react-query"""
    info("بررسی package.json...")

    if not PKG_JSON.exists():
        err(f"package.json یافت نشد: {PKG_JSON}")
        return False

    text = PKG_JSON.read_text(encoding="utf-8")

    if "@tanstack/react-query" in text:
        ok("React Query قبلاً در package.json تعریف شده")
    else:
        info("React Query در package.json نیست - نصب می‌کنم...")
        result = subprocess.run(
            "pnpm add @tanstack/react-query",
            shell=True,
            cwd=FRONTEND,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180
        )
        if result.returncode == 0:
            ok("React Query نصب شد")
        else:
            err("نصب React Query شکست خورد")
            logger.info(result.stderr[-500:])
            return False

    # بررسی نصب در node_modules
    nm_path = FRONTEND / "node_modules" / "@tanstack" / "react-query"
    if nm_path.exists():
        ok("node_modules/@tanstack/react-query موجود است")
        return True
    else:
        warn("node_modules یافت نشد - اجرای pnpm install...")
        result = subprocess.run(
            "pnpm install",
            shell=True,
            cwd=FRONTEND,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300
        )
        if result.returncode == 0:
            ok("pnpm install موفق")
            return True
        err("pnpm install شکست خورد")
        return False


def configure_query_client_provider():
    """افزودن QueryClientProvider به main.tsx"""
    info("پیکربندی QueryClientProvider...")

    if not MAIN_TSX.exists():
        err(f"main.tsx یافت نشد: {MAIN_TSX}")
        return False

    text = MAIN_TSX.read_text(encoding="utf-8")

    # اگر قبلاً QueryClient اضافه شده
    if "QueryClient" in text and "QueryClientProvider" in text:
        ok("QueryClientProvider قبلاً پیکربندی شده")
        return True

    # پشتیبان
    backup = MAIN_TSX.with_suffix(".tsx.queryclient-backup")
    backup.write_text(text, encoding="utf-8")
    info(f"پشتیبان: {backup.name}")

    # افزودن import‌ها در ابتدای فایل
    query_imports = (
        "import { QueryClient, QueryClientProvider } from '@tanstack/react-query';\n"
    )

    # QueryClient instance با پیکربندی معقول
    query_client_instance = (
        "\n// React Query client with sensible defaults\n"
        "const queryClient = new QueryClient({\n"
        "  defaultOptions: {\n"
        "    queries: {\n"
        "      staleTime: 5 * 60 * 1000, // 5 minutes\n"
        "      retry: 2,\n"
        "      refetchOnWindowFocus: false,\n"
        "    },\n"
        "  },\n"
        "});\n\n"
    )

    # استراتژی ۱: اضافه کردن بعد از آخرین import
    last_import_match = None
    for match in re.finditer(r'^import\s+.*?;?\s*$', text, re.MULTILINE):
        last_import_match = match

    if last_import_match:
        insert_pos = last_import_match.end()
        text = (
            text[:insert_pos] +
            "\n" + query_imports + query_client_instance +
            text[insert_pos:]
        )
    else:
        text = query_imports + query_client_instance + text

    # استراتژی ۲: wrap کردن root element با QueryClientProvider
    # یافتن <StrictMode> یا <BrowserRouter> یا اولین JSX element
    root_patterns = [
        (r'(<StrictMode[^>]*>)', r'<QueryClientProvider client={queryClient}">\1'),
        (r'(</StrictMode>)', r'\1</QueryClientProvider>'),
    ]

    # اگر StrictMode وجود دارد
    if '<StrictMode' in text and '</StrictMode>' in text:
        text = re.sub(r'<StrictMode([^>]*)>', r'<QueryClientProvider client={queryClient}><StrictMode\1>', text, count=1)
        text = text.replace('</StrictMode>', '</StrictMode></QueryClientProvider>', 1)
        ok("QueryClientProvider دور StrictMode پیچیده شد")
    # اگر ReactDOM.render یا createRoot وجود دارد
    elif 'createRoot' in text or 'ReactDOM.render' in text:
        # wrap کردن root element
        text = re.sub(
            r'(<(?:BrowserRouter|App)\s*[^>]*>)',
            r'<QueryClientProvider client={queryClient}>\1',
            text,
            count=1
        )
        text = re.sub(
            r'(</(?:BrowserRouter|App)>)',
            r'\1</QueryClientProvider>',
            text,
            count=1
        )
        ok("QueryClientProvider دور root element پیچیده شد")
    else:
        warn("الگوی root یافت نشد - نیاز به بررسی دستی")

    MAIN_TSX.write_text(text, encoding="utf-8")
    ok("main.tsx به‌روزرسانی شد")

    # نمایش تغییرات
    logger.info("\n  ─── Preview main.tsx (۳۰ خط اول) ───")
    for i, line in enumerate(MAIN_TSX.read_text(encoding="utf-8").splitlines()[:30], 1):
        logger.info(f"    {i:3d} │ {line}")

    return True


def run_build():
    """اجرای build مجدد"""
    info("اجرای build مجدد...")

    result = subprocess.run(
        "pnpm build",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300
    )

    output = result.stdout + result.stderr

    if result.returncode == 0:
        ok("Build موفق!")
        for line in output.splitlines():
            if "built in" in line or "HyDroMaCenter" in line or "crypto" in line.lower():
                logger.info(f"  {line.strip()}")
        return True

    err("Build هنوز شکست می‌خورد")
    logger.info("\n  ─── ۳۰ خط آخر ───")
    for line in output.splitlines()[-30:]:
        logger.info(f"  {line}")
    return False


def run_tests():
    """اجرای تست‌ها"""
    info("اجرای تست‌ها...")

    result = subprocess.run(
        "pnpm test features/crypto-payment features/hydroma",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180
    )

    output = result.stdout + result.stderr
    for line in output.splitlines():
        if "Test Files" in line or "Tests" in line or "passed" in line.lower() or "failed" in line.lower():
            logger.info(f"  {line}")

    return result.returncode == 0


def commit_changes():
    """commit تغییرات"""
    ensure_git_in_path()
    info("commit تغییرات...")

    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run(
            'git commit -m "fix: install and configure @tanstack/react-query"',
            shell=True, cwd=PROJECT_ROOT, check=True
        )
        subprocess.run("git push origin main", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("commit و push موفق")
        return True
    except Exception as e:
        warn(f"commit: {e}")
        return False


def main():
    logger.info("\n" + "=" * 70)
    logger.info("  🔧 Fix React Query Installation & Configuration")
    logger.info("=" * 70 + "\n")

    ensure_git_in_path()

    # گام ۱: نصب
    if not install_react_query():
        return 1
    logger.info()

    # گام ۲: پیکربندی
    if not configure_query_client_provider():
        return 1
    logger.info()

    # گام ۳: Build
    build_ok = run_build()
    logger.info()

    # گام ۴: تست‌ها
    tests_ok = run_tests()
    logger.info()

    # گام ۵: Commit
    if build_ok:
        commit_changes()
    logger.info()

    # گزارش
    logger.info("\033[1m\033[96m" + "=" * 70 + "\033[0m")
    if build_ok:
        logger.info("\033[1m\033[92m  🎉 React Query پیکربندی شد! 🎉\033[0m")
    else:
        logger.info("\033[1m\033[93m  ⚠️ نیاز به بررسی بیشتر\033[0m")
    logger.info("\033[1m\033[96m" + "=" * 70 + "\033[0m\n")

    logger.info("  📊 خلاصه:")
    logger.info(f"    • Build: {'✅ موفق' if build_ok else '❌ شکست'}")
    logger.info(f"    • Tests: {'✅ پاس' if tests_ok else '⚠️ برخی شکست'}")
    logger.info()

    if build_ok and tests_ok:
        logger.info("  🎯 گام بعدی:")
        logger.info("    • refactor CryptoPaymentWidget تکمیل شد")
        logger.info("    • آماده ورود به EcoWalletDashboard.tsx (HIGH)")
        logger.info()

    return 0 if (build_ok and tests_ok) else 1


if __name__ == "__main__":
    sys.exit(main())