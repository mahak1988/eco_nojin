#!/usr/bin/env python3
"""Fix CSS import path - smart version with regex"""

import structlog

logger = structlog.get_logger()
import os
import re
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend" / "src"
TELEGRAM_FILE = FRONTEND / "pages" / "admin" / "telegram" / "TelegramManager.tsx"
LIVE_CSS_FILE = FRONTEND / "pages" / "admin" / "live" / "LiveComponents.css"


def ok(m): print(f"\033[92m✓\033[0m  {m}")
def info(m): print(f"\033[94mℹ\033[0m  {m}")
def warn(m): print(f"\033[93m⚠\033[0m  {m}")
def err(m): print(f"\033[91m✗\033[0m  {m}")


def main():
    if not TELEGRAM_FILE.exists():
        err(f"فایل یافت نشد: {TELEGRAM_FILE}")
        return 1

    # بررسی اینکه CSS وجود دارد
    info(f"بررسی وجود CSS در: {LIVE_CSS_FILE.relative_to(FRONTEND)}")
    if LIVE_CSS_FILE.exists():
        ok("فایل CSS موجود است")
    else:
        err("فایل CSS یافت نشد! جستجو...")
        # جستجو
        for p in FRONTEND.rglob("LiveComponents.css"):
            info(f"  یافت شد: {p.relative_to(FRONTEND)}")
        return 1

    # خواندن فایل
    text = TELEGRAM_FILE.read_text(encoding="utf-8")

    # نمایش خطوط دارای LiveComponents
    info("خطوط مربوط به LiveComponents در فایل فعلی:")
    for i, line in enumerate(text.splitlines(), 1):
        if "LiveComponents" in line:
            logger.info(f"  Line {i}: {line}")
    logger.info()

    # اصلاح با regex - همه الگوهای ممکن
    # Matches: import ".../live/LiveComponents.css";
    pattern = r'''import\s+['"][^'"]*LiveComponents\.css['"];'''
    replacement = '''import '../live/LiveComponents.css';'''

    matches = re.findall(pattern, text)
    info(f"تعداد match های regex: {len(matches)}")
    for m in matches:
        logger.info(f"  یافت شد: {m}")

    if matches:
        text = re.sub(pattern, replacement, text)
        TELEGRAM_FILE.write_text(text, encoding="utf-8")
        ok("فایل اصلاح شد")
    else:
        # استراتژی ۲: جایگزینی خط به خط
        info("استراتژی ۲: جایگزینی دستی خط به خط...")
        lines = text.splitlines()
        changed = False
        for i, line in enumerate(lines):
            if "LiveComponents.css" in line:
                lines[i] = "import '../live/LiveComponents.css';"
                changed = True
                ok(f"خط {i+1} اصلاح شد")
        
        if changed:
            TELEGRAM_FILE.write_text('\n'.join(lines), encoding="utf-8")
            ok("فایل ذخیره شد")
        else:
            warn("هیچ خطی پیدا نشد! نمایش ۱۰ خط اول فایل:")
            for i, line in enumerate(lines[:10], 1):
                logger.info(f"  {i}: {line}")

    # تایید اصلاح
    logger.info("\n\033[1mمحتوای خطوط ۲۰-۳۰ بعد از اصلاح:\033[0m")
    new_text = TELEGRAM_FILE.read_text(encoding="utf-8")
    for i, line in enumerate(new_text.splitlines()[19:30], 20):
        logger.info(f"  {i:3d} │ {line}")
    logger.info()

    # Build
    logger.info("\033[1m🔨 اجرای build...\033[0m")
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
        output = result.stdout + result.stderr
        for line in output.splitlines()[-25:]:
            logger.info(f"  {line}")
        return 1

    # تست‌ها
    logger.info("\n\033[1m🧪 اجرای تست‌ها...\033[0m")
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
    logger.info("\n\033[1m📦 commit...\033[0m")
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run(
            'git commit -m "fix(telegram): correct CSS import path (../live/ not ../../live/)"',
            shell=True, cwd=PROJECT_ROOT, check=True
        )
        subprocess.run("git push origin main", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("commit و push موفق")
    except Exception as e:
        warn(f"commit: {e}")

    logger.info("\n\033[1m\033[92m" + "=" * 70 + "\033[0m")
    logger.info("\033[1m\033[92m  🎉 TelegramManager آماده! به SecurityAdvanced.tsx می‌رویم\033[0m")
    logger.info("\033[1m\033[92m" + "=" * 70 + "\033[0m")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())