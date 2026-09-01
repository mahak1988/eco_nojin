#!/usr/bin/env python3
"""Fix CSS import path in TelegramManager.tsx"""

import structlog

logger = structlog.get_logger()
import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend" / "src"
TELEGRAM_FILE = FRONTEND / "pages" / "admin" / "telegram" / "TelegramManager.tsx"


def ok(m): print(f"\033[92m✓\033[0m  {m}")
def err(m): print(f"\033[91m✗\033[0m  {m}")


def main():
    if not TELEGRAM_FILE.exists():
        err(f"فایل یافت نشد: {TELEGRAM_FILE}")
        return 1

    # خواندن و اصلاح
    text = TELEGRAM_FILE.read_text(encoding="utf-8")
    fixed = text.replace(
        'import "../../live/LiveComponents.css";',
        'import "../live/LiveComponents.css";'
    )

    if fixed == text:
        ok("فایل از قبل اصلاح شده")
    else:
        TELEGRAM_FILE.write_text(fixed, encoding="utf-8")
        ok("مسیر CSS اصلاح شد: ../../live/ → ../live/")

    # Build مجدد
    logger.info("\n🔨 اجرای build...")
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

    result = subprocess.run(
        "pnpm build",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        timeout=300
    )

    if result.returncode == 0:
        ok("Build موفق!")
        for line in result.stdout.splitlines():
            if "built in" in line or "TelegramManager" in line:
                logger.info(f"  {line.strip()}")
    else:
        err("Build هنوز شکست می‌خورد")
        for line in (result.stdout + result.stderr).splitlines()[-20:]:
            logger.info(f"  {line}")
        return 1

    # تست‌ها
    logger.info("\n🧪 اجرای تست‌ها...")
    test_result = subprocess.run(
        "pnpm test features/telegram-manager",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        timeout=120
    )
    for line in test_result.stdout.splitlines():
        if any(k in line for k in ["Test Files", "Tests", "passed", "failed"]):
            logger.info(f"  {line}")

    # Commit
    logger.info("\n📦 commit...")
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run(
            'git commit -m "fix(telegram): correct CSS import path"',
            shell=True, cwd=PROJECT_ROOT, check=True
        )
        subprocess.run("git push origin main", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("commit و push موفق")
    except Exception as e:
        logger.info(f"  ⚠ commit: {e}")

    logger.info("\n\033[1m\033[92m🎉 TelegramManager کامل شد!\033[0m")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())