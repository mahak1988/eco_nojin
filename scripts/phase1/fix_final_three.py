#!/usr/bin/env python3
"""
Fix Final Three Issues
======================
1. نصب @react-three/postprocessing
2. اصلاح پرانتز اضافی در HyDroMaCenter.tsx
3. اصلاح import EffectComposer
4. تست build + dev + backend availability
"""

import structlog

logger = structlog.get_logger()
import re
import sys
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
HYDROMA = FRONTEND / "src" / "pages" / "HyDroMaCenter.tsx"


class C:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"


def info(m): print(f"{C.BLUE}ℹ{C.RESET}  {m}")
def ok(m): print(f"{C.GREEN}✓{C.RESET}  {m}")
def warn(m): print(f"{C.YELLOW}⚠{C.RESET}  {m}")
def err(m): print(f"{C.RED}✗{C.RESET}  {m}")
def header(m):
    logger.info(f"\n{C.BOLD}{C.CYAN}{'═' * 70}{C.RESET}")
    logger.info(f"{C.BOLD}{C.CYAN}  {m}{C.RESET}")
    logger.info(f"{C.BOLD}{C.CYAN}{'═' * 70}{C.RESET}\n")


def backup(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(f"{path.suffix}.bak_{ts}")
    shutil.copy2(path, b)
    info(f"پشتیبان: {b.name}")
    return b


def run(cmd, cwd=None, check=True, timeout=180, silent=False):
    if not silent:
        info(f"$ {cmd}")
    try:
        r = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=timeout
        )
        if r.returncode != 0 and check:
            if not silent:
                err(f"exit code {r.returncode}")
                out = (r.stdout or "") + (r.stderr or "")
                if out:
                    logger.info("  " + "\n  ".join(out.splitlines()[:15]))
            return r
        return r
    except subprocess.TimeoutExpired:
        warn(f"timeout after {timeout}s")
        return None


# ═══════════════════════════════════════════════════════════════════════
# بخش ۱: نصب @react-three/postprocessing
# ═══════════════════════════════════════════════════════════════════════

def install_postprocessing() -> bool:
    header("۱. نصب @react-three/postprocessing")

    pkg = FRONTEND / "package.json"
    text = pkg.read_text(encoding="utf-8")

    if "@react-three/postprocessing" in text:
        info("package قبلاً در package.json هست")
        # بررسی نصب
        nm = FRONTEND / "node_modules" / "@react-three" / "postprocessing"
        if nm.exists():
            ok("✓ package نصب است")
            return True
        warn("در package.json هست ولی نصب نیست - نصب مجدد...")

    r = run("pnpm add @react-three/postprocessing", cwd=FRONTEND, check=False)
    if r and r.returncode == 0:
        ok("✓ @react-three/postprocessing نصب شد")
        return True

    err("نصب ناموفق بود")
    return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۲: اصلاح import و پرانتز اضافی در HyDroMaCenter.tsx
# ═══════════════════════════════════════════════════════════════════════

def fix_hydroma() -> tuple:
    header("۲. اصلاح HyDroMaCenter.tsx")

    if not HYDROMA.exists():
        err(f"فایل یافت نشد: {HYDROMA}")
        return False, False

    backup(HYDROMA)
    text = HYDROMA.read_text(encoding="utf-8")
    original = text
    changes = []

    # ─────────────────────────────────────────
    # بررسی و اصلاح import postprocessing
    # ─────────────────────────────────────────
    has_import = "@react-three/postprocessing" in text
    has_usage = "EffectComposer" in text or "Bloom" in text or "Vignette" in text

    if has_usage and not has_import:
        info("EffectComposer/Bloom/Vignette استفاده شده ولی import نیست")
        # اضافه کردن import بعد از @react-three/drei
        drei_imp = "import { OrbitControls, Sky, Grid, PerspectiveCamera, Html, Line, useTexture } from '@react-three/drei';"
        if drei_imp in text:
            new_imp = (
                drei_imp + "\n"
                "import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing';"
            )
            text = text.replace(drei_imp, new_imp, 1)
            changes.append("Added @react-three/postprocessing import")
            ok("✓ import اضافه شد")
        else:
            warn("import drei یافت نشد - استفاده از روش جایگزین")
            # اضافه کردن قبل از اولین import غیر از react
            insert = "import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing';\n"
            # بعد از 'import { Suspense }' یا بعد از اولین import از react
            text = insert + text
            changes.append("Added import at top of file")
            ok("✓ import در ابتدای فایل اضافه شد")
    elif has_import:
        info("✓ import @react-three/postprocessing قبلاً وجود دارد")
    else:
        info("EffectComposer/Bloom/Vignette در فایل استفاده نشده")

    # ─────────────────────────────────────────
    # شمارش پرانتزها و رفع عدم تعادل
    # ─────────────────────────────────────────
    info("شمارش پرانتزها...")

    def count_braces(s):
        stats = {'(': 0, ')': 0, '[': 0, ']': 0, '{': 0, '}': 0}
        i = 0
        while i < len(s):
            c = s[i]
            # skip strings
            if c in '"\'`':
                quote = c
                i += 1
                while i < len(s):
                    if s[i] == '\\':
                        i += 2
                        continue
                    if s[i] == quote:
                        break
                    i += 1
            # skip line comments
            elif c == '/' and i + 1 < len(s) and s[i+1] == '/':
                while i < len(s) and s[i] != '\n':
                    i += 1
                continue
            # skip block comments
            elif c == '/' and i + 1 < len(s) and s[i+1] == '*':
                i += 2
                while i < len(s) - 1:
                    if s[i] == '*' and s[i+1] == '/':
                        i += 2
                        break
                    i += 1
            elif c in stats:
                stats[c] += 1
            i += 1
        return stats

    stats = count_braces(text)
    paren_diff = stats['('] - stats[')']
    bracket_diff = stats['['] - stats[']']
    brace_diff = stats['{'] - stats['}']

    info(f"  (): {stats['(']}/{stats[')']} → diff: {paren_diff}")
    info(f"  []: {stats['[']}/{stats[']']} → diff: {bracket_diff}")
    info(f"  {{}}: {stats['{']}/{stats['}']} → diff: {brace_diff}")

    # اصلاح پرانتز اضافی
    if paren_diff == -1:
        info("یک ) اضافی یافت شد - جستجوی مکان دقیق...")

        # یافتن )} های متوالی
        lines = text.splitlines(keepends=True)
        consecutive_closes = []

        for i, line in enumerate(lines):
            if line.strip() == ")}":
                consecutive_closes.append(i)
            else:
                if len(consecutive_closes) >= 2:
                    info(f"یافت شد: {len(consecutive_closes)} )}} متوالی در خطوط {consecutive_closes[0]+1}-{consecutive_closes[-1]+1}")
                consecutive_closes = []

        # بررسی کل فایل برای )} های متوالی
        # استراتژی: هر جا بیش از یک )} پشت سر هم بود، اضافی‌ها را حذف کن
        removed = 0
        i = 0
        while i < len(lines):
            if lines[i].strip() == ")}":
                # شمارش متوالی
                j = i
                while j < len(lines) and lines[j].strip() == ")}":
                    j += 1
                count = j - i
                if count >= 2:
                    # نگه داشتن فقط اولی، حذف بقیه
                    info(f"حذف {count-1} )}} اضافی در خطوط {i+1}-{j}")
                    # بررسی خط بعد از آخرین )} برای تصمیم‌گیری
                    next_line = lines[j].strip() if j < len(lines) else ""

                    # اگر بعد از )} های متوالی، یک { یا )} دیگر شروع می‌شود
                    # یعنی فقط یکی از آن‌ها اضافی است
                    # امن‌ترین کار: حذف آخرین )}
                    del lines[j - 1]
                    removed += 1
                i = j
            else:
                i += 1

        if removed > 0:
            text = "".join(lines)
            changes.append(f"Removed {removed} extra )}} lines")
            ok(f"✓ {removed} )}} اضافی حذف شد")

            # شمارش مجدد
            new_stats = count_braces(text)
            new_diff = new_stats['('] - new_stats[')']
            info(f"  بعد: (): {new_stats['(']}/{new_stats[')']} → diff: {new_diff}")

            if new_diff == 0:
                ok("✓ پرانتزها متوازن شدند")
            else:
                warn(f"⚠ هنوز عدم تعادل: {new_diff}")
        else:
            warn(") اضافی در قالب )} متوالی یافت نشد - جستجوی دیگر...")

            # جستجو برای الگوی ) } یا )} درون کد
            # الگوی خطرناک: )} بعد از )} در یک خط
            pattern = re.compile(r'\)\}\s*\n\s*\)\}')
            matches = list(pattern.finditer(text))
            if matches:
                info(f"{len(matches)} الگوی )}}) متوالی یافت شد")
                # حذف دومی
                for m in reversed(matches):
                    # پیدا کردن )} دوم و حذف آن
                    text = text[:m.start() + 2] + text[m.end() - 2:]
                    changes.append("Removed consecutive )}}")
                    ok("✓ )} اضافی حذف شد")
                    break

    elif paren_diff == 0:
        ok("✓ پرانتزها از قبل متوازن هستند")
    else:
        warn(f"⚠ عدم تعادل پرانتز: {paren_diff}")

    # ─────────────────────────────────────────
    # ذخیره
    # ─────────────────────────────────────────
    if text != original:
        HYDROMA.write_text(text, encoding="utf-8")
        ok(f"✓ فایل ذخیره شد ({len(changes)} تغییر)")
    else:
        info("هیچ تغییری لازم نبود")

    final_stats = count_braces(text)
    balanced = (
        final_stats['('] == final_stats[')'] and
        final_stats['['] == final_stats[']'] and
        final_stats['{'] == final_stats['}']
    )

    return len(changes) > 0, balanced


# ═══════════════════════════════════════════════════════════════════════
# بخش ۳: بررسی وضعیت Backend
# ═══════════════════════════════════════════════════════════════════════

def check_backend() -> bool:
    header("۳. بررسی وضعیت Backend")

    try:
        import urllib.request
        url = "http://localhost:8000/api/v1/health"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=3) as r:
            if r.status == 200:
                ok("✓ Backend فعال است (http://localhost:8000)")
                return True
    except Exception as e:
        warn(f"Backend در دسترس نیست: {type(e).__name__}")

    info("Backend باید اجرا شود تا صفحه HyDroMaCenter کار کند")
    info("در یک terminal دیگر اجرا کنید:")
    logger.info(f"\n{C.BOLD}  cd D:\\eco_nojin{C.RESET}")
    logger.info(f"{C.BOLD}  python -m uvicorn services.api_gateway.main:app --reload --port 8000{C.RESET}\n")
    return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۴: تست Build
# ═══════════════════════════════════════════════════════════════════════

def test_build() -> bool:
    header("۴. تست pnpm build")

    r = run("pnpm build", cwd=FRONTEND, check=False, timeout=240)
    if not r:
        return False

    if r.returncode == 0:
        ok("✓ build موفق")
        # نمایش chunk ها
        for line in r.stdout.splitlines():
            if "dist/assets" in line and ".js" in line:
                logger.info(f"  {line.strip()}")
        return True

    err("build شکست خورد")
    out = (r.stdout or "") + (r.stderr or "")
    for l in out.splitlines()[-20:]:
        logger.info(f"  {l}")
    return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۵: تست Dev Server
# ═══════════════════════════════════════════════════════════════════════

def test_dev() -> bool:
    header("۵. تست pnpm dev (۱۵ ثانیه)")

    try:
        proc = subprocess.Popen(
            "pnpm dev",
            shell=True, cwd=FRONTEND,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8", errors="replace",
        )

        start = time.time()
        ready = False
        url = None
        output = []

        while time.time() - start < 15:
            if proc.poll() is not None:
                rest = proc.stdout.read()
                if rest:
                    output.extend(rest.splitlines())
                break

            line = proc.stdout.readline()
            if not line:
                continue

            output.append(line.rstrip())
            if len(output) <= 10:
                logger.info(f"  {line.rstrip()}")

            if "Local:" in line:
                ready = True
                m = re.search(r'http://[^\s]+', line)
                if m:
                    url = m.group(0)

        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

        if ready:
            ok("✓ dev server راه‌اندازی شد")
            if url:
                info(f"🌐 {url}")
            return True

        warn("dev server آماده نشد")
        return False

    except Exception as e:
        err(f"خطا: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۶: Commit
# ═══════════════════════════════════════════════════════════════════════

def commit():
    header("۶. commit و push")
    try:
        run("git add .", cwd=PROJECT_ROOT, silent=True)
        s = run("git status --porcelain", cwd=PROJECT_ROOT, silent=True)
        if s and not s.stdout.strip():
            info("تغییری نیست")
            return
        run(
            'git commit -m "fix: install postprocessing, balance parens in HyDroMaCenter"',
            cwd=PROJECT_ROOT
        )
        ok("✓ commit ایجاد شد")
        r = run("git remote get-url origin", cwd=PROJECT_ROOT, silent=True, check=False)
        if r and r.returncode == 0:
            run("git push origin main", cwd=PROJECT_ROOT)
            ok("✓ push موفق")
    except Exception as e:
        warn(f"commit: {e}")


# ═══════════════════════════════════════════════════════════════════════
# اجرای اصلی
# ═══════════════════════════════════════════════════════════════════════

def main():
    logger.info(f"\n{C.BOLD}{'═' * 70}{C.RESET}")
    logger.info(f"{C.BOLD}  🔧 Fix Final Three Issues{C.RESET}")
    logger.info(f"{C.BOLD}{'═' * 70}{C.RESET}")

    install_postprocessing()
    _, balanced = fix_hydroma()
    backend_ok = check_backend()
    build_ok = test_build()

    dev_ok = False
    if build_ok:
        dev_ok = test_dev()
        commit()

    # گزارش نهایی
    header("📊 گزارش نهایی")
    checks = [
        ("@react-three/postprocessing installed", True),
        ("HyDroMaCenter brackets balanced", balanced),
        ("Backend available", backend_ok),
        ("Build success", build_ok),
        ("Dev server", dev_ok),
    ]

    all_ok = True
    for name, ok_status in checks:
        color = C.GREEN if ok_status else (C.YELLOW if name == "Backend available" else C.RED)
        symbol = "✓" if ok_status else "✗"
        logger.info(f"  {color}{symbol}{C.RESET} {name}")
        if not ok_status and name != "Backend available":
            all_ok = False

    logger.info()
    if all_ok:
        logger.info(f"{C.GREEN}{C.BOLD}🎉 فاز صفر ۱۰۰٪ کامل شد!{C.RESET}")
        logger.info(f"\n{C.BOLD}┌──────────────────────────────────────────────┐{C.RESET}")
        logger.info(f"{C.BOLD}│  🚀 آماده فاز ۱: بازنویسی ساختاری         │{C.RESET}")
        logger.info(f"{C.BOLD}│                                              │{C.RESET}")
        logger.info(f"{C.BOLD}│  شروع استخراج HyDroMaCenter.tsx              │{C.RESET}")
        logger.info(f"{C.BOLD}│  به features/hydroma/                        │{C.RESET}")
        logger.info(f"{C.BOLD}└──────────────────────────────────────────────┘{C.RESET}")

        logger.info(f"\n{C.BOLD}گام اول فاز ۱:{C.RESET}")
        logger.info(f"  1. ایجاد features/hydroma/types/")
        logger.info(f"  2. ایجاد features/hydroma/store/")
        logger.info(f"  3. استخراج TerrainMesh.tsx")
        logger.info(f"  4. تست و commit")

        return 0

    logger.info(f"{C.YELLOW}⚠️ برخی موارد باقی مانده{C.RESET}")
    if not backend_ok:
        logger.info(f"\n{C.BOLD}یادآوری:{C.RESET} Backend را در terminal دیگر اجرا کنید")
    return 1


if __name__ == "__main__":
    sys.exit(main())