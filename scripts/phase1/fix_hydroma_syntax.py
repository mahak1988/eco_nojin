#!/usr/bin/env python3
"""
Fix HyDroMaCenter.tsx - Syntax & Imports (v2)
=============================================
رفع خطای بحرانی قبل از شروع بازنویسی:
1. اصلاح div بسته‌نشده (demError/erosionEffect)
2. افزودن missing imports (TrendingUp, postprocessing)
3. رفع siteId undefined
4. پشتیبان‌گیری خودکار
"""

import re
import sys
import shutil
from pathlib import Path
from datetime import datetime


FILE = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "pages" / "HyDroMaCenter.tsx"


class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"


def info(msg): print(f"{Colors.BLUE}ℹ{Colors.RESET}  {msg}")
def success(msg): print(f"{Colors.GREEN}✓{Colors.RESET}  {msg}")
def warning(msg): print(f"{Colors.YELLOW}⚠{Colors.RESET}  {msg}")
def error(msg): print(f"{Colors.RED}✗{Colors.RESET}  {msg}")
def header(msg):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.RESET}\n")


def create_backup(path: Path) -> Path:
    """ایجاد پشتیبان با timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(f".tsx.backup_{timestamp}")
    shutil.copy2(path, backup)
    info(f"پشتیبان: {backup.name}")
    return backup


def fix_1_add_missing_imports(text: str) -> tuple:
    """افزودن imports گم‌شده"""
    header("گام ۱: افزودن imports گم‌شده")
    changes = []

    # 1. افزودن TrendingUp به lucide-react
    if "TrendingUp" not in text and "FlaskConical" in text:
        text = text.replace(
            "FlaskConical} from 'lucide-react';",
            "FlaskConical, TrendingUp} from 'lucide-react';",
            1
        )
        changes.append("Added TrendingUp")
        success("✓ TrendingUp به lucide-react اضافه شد")
    else:
        info("TrendingUp: نیاز به تغییر نیست")

    # 2. افزودن @react-three/postprocessing
    if "EffectComposer" not in text:
        post_import = (
            "import { EffectComposer, Bloom, Vignette } "
            "from '@react-three/postprocessing';\n"
        )
        # افزودن بعد از آخرین import از @react-three/drei
        text = text.replace(
            "import { OrbitControls, Sky, Grid, PerspectiveCamera, Html, Line, useTexture } from '@react-three/drei';",
            "import { OrbitControls, Sky, Grid, PerspectiveCamera, Html, Line, useTexture } from '@react-three/drei';\n" + post_import,
            1
        )
        changes.append("Added @react-three/postprocessing")
        success("✓ EffectComposer, Bloom, Vignette اضافه شد")
    else:
        info("postprocessing: نیاز به تغییر نیست")

    return text, changes


def fix_2_site_id(text: str) -> tuple:
    """رفع siteId undefined"""
    header("گام ۲: رفع siteId undefined")
    changes = []

    old_pattern = "سایت {siteId}"
    new_pattern = "سایت {siteMeta?.siteId || '---'}"

    if old_pattern in text:
        count = text.count(old_pattern)
        text = text.replace(old_pattern, new_pattern)
        changes.append(f"Fixed {count} siteId references")
        success(f"✓ {count} مرجع siteId اصلاح شد")
    else:
        info("siteId: نیاز به تغییر نیست")

    return text, changes


def fix_3_unclosed_div(text: str) -> tuple:
    """رفع div بسته‌نشده در demError"""
    header("گام ۳: رفع div بسته‌نشده (خطای syntax)")

    changes = []
    lines = text.splitlines(keepends=True)

    # جستجوی الگوی مشکل‌دار خط به خط
    for i, line in enumerate(lines):
        # دنبال خطی بگردیم که با {demError شروع و با </div> تمام می‌شود
        # ولی بعدش پرانتز بسته‌شدن ) نیست
        if '{demError' in line and '</div>' in line:
            # بررسی خط بعدی
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # اگر خط بعدی erosionEffect است ولی قبلی بسته نشده
                if 'erosionEffect' in next_line and not line.rstrip().endswith(')}'):
                    # این خط مشکل‌دار است
                    old_line = lines[i]
                    # اگر خط با </div> تمام می‌شود ولی بدون )} در انتها
                    if old_line.rstrip().endswith('</div>'):
                        # اضافه کردن )} به انتهای خط
                        # حذف newline، اضافه کردن )} و بازگرداندن newline
                        stripped = old_line.rstrip()
                        if old_line.endswith('\n'):
                            nl = '\n'
                        elif old_line.endswith('\r\n'):
                            nl = '\r\n'
                        else:
                            nl = ''
                        lines[i] = stripped + ')}' + nl
                        changes.append(f"Fixed unclosed demError div at line {i+1}")
                        success(f"✓ خط {i+1}: div بسته‌نشده اصلاح شد")
                        break

    if not changes:
        # تلاش دوم: جستجوی الگوی چندخطی
        info("الگوی خطی یافت نشد، جستجوی الگوی چندخطی...")

        # الگوی چندخطی
        pattern = re.compile(
            r'\{demError && \(\s*\n\s*<div[^>]*>\{demError\}</div>\s*\n\s*\{erosionEffect',
            re.MULTILINE
        )
        match = pattern.search(text)
        if match:
            old = match.group(0)
            new = (
                '{demError && (\n'
                '          <div style={{ fontSize: "11px", color: "#fca5a5" }}>'
                '{demError}</div>\n'
                '        )}\n'
                '        {erosionEffect'
            )
            text = text.replace(old, new, 1)
            changes.append("Fixed multi-line demError/erosionEffect pattern")
            success("✓ الگوی چندخطی اصلاح شد")
        else:
            warning("الگوی مشکل‌دار یافت نشد - احتمالاً قبلاً اصلاح شده")

    return "".join(lines) if changes and "multi-line" not in str(changes) else text, changes


def fix_4_map_prop(text: str) -> tuple:
    """رفع map={{esriTexture}} که غلط است و باید map={esriTexture} باشد"""
    header("گام ۴: اصلاح prop اشتباه map")
    changes = []

    old = "map={{esriTexture}}"
    new = "map={esriTexture}"
    if old in text:
        text = text.replace(old, new)
        changes.append("Fixed map prop (was object, should be value)")
        success("✓ map={{esriTexture}} → map={esriTexture}")
    else:
        info("map prop: نیاز به تغییر نیست")

    return text, changes


def analyze_result(text: str) -> dict:
    """تحلیل نهایی فایل اصلاح‌شده"""
    header("گام ۵: تحلیل نهایی")

    stats = {
        "lines": len(text.splitlines()),
        "chars": len(text),
    }

    # بررسی imports حیاتی
    critical_imports = [
        "TrendingUp",
        "EffectComposer",
        "Bloom",
        "Vignette",
    ]

    print(f"\n{Colors.BOLD}بررسی imports حیاتی:{Colors.RESET}")
    for imp in critical_imports:
        if imp in text:
            print(f"  {Colors.GREEN}✓{Colors.RESET} {imp}")
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} {imp} (گم شده!)")

    # بررسی الگوهای مشکل‌دار
    print(f"\n{Colors.BOLD}بررسی الگوهای مشکل‌دار:{Colors.RESET}")

    # demError بدون )}
    dem_error_pattern = re.compile(
        r'\{demError && \(\s*\n\s*<div[^>]*>\{demError\}</div>\s*\n\s*\{erosionEffect'
    )
    if dem_error_pattern.search(text):
        print(f"  {Colors.RED}✗{Colors.RESET} demError div هنوز بسته نشده!")
    else:
        print(f"  {Colors.GREEN}✓{Colors.RESET} demError div صحیح است")

    # siteId بدون ?
    if "سایت {siteId}" in text:
        print(f"  {Colors.RED}✗{Colors.RESET} siteId هنوز undefined است!")
    else:
        print(f"  {Colors.GREEN}✓{Colors.RESET} siteId safe است")

    # map={{
    if "map={{esriTexture}}" in text:
        print(f"  {Colors.RED}✗{Colors.RESET} map prop هنوز اشتباه است!")
    else:
        print(f"  {Colors.GREEN}✓{Colors.RESET} map prop صحیح است")

    return stats


def test_build():
    """تست build"""
    header("گام ۶: تست build")

    import subprocess
    import time

    frontend_dir = FILE.parent.parent.parent

    info("اجرای pnpm build برای ۶۰ ثانیه...")
    start = time.time()

    try:
        result = subprocess.run(
            "pnpm build",
            shell=True,
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120
        )

        elapsed = time.time() - start

        if result.returncode == 0:
            success(f"✓ build موفق در {elapsed:.1f} ثانیه")
            return True
        else:
            error(f"✗ build شکست خورد")
            if "Expected `,` or `)`" in result.stdout + result.stderr:
                error("خطای syntax هنوز وجود دارد!")
            print(f"\n{Colors.BOLD}۳۰ خط آخر خروجی:{Colors.RESET}")
            output = (result.stdout + result.stderr).splitlines()
            for line in output[-30:]:
                print(f"  {line}")
            return False

    except subprocess.TimeoutExpired:
        warning("build timeout شد (>120s)")
        return False
    except Exception as e:
        error(f"خطا در build: {e}")
        return False


def main() -> int:
    print(f"\n{Colors.BOLD}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}  🔧 Fix HyDroMaCenter - رفع خطاهای بحرانی (v2){Colors.RESET}")
    print(f"{Colors.BOLD}{'═' * 70}{Colors.RESET}")

    if not FILE.exists():
        error(f"فایل یافت نشد: {FILE}")
        return 1

    info(f"فایل: {FILE}")
    info(f"حجم: {FILE.stat().st_size:,} بایت")

    # پشتیبان‌گیری
    backup = create_backup(FILE)

    # خواندن فایل
    try:
        text = FILE.read_text(encoding="utf-8")
    except Exception as e:
        error(f"خطا در خواندن فایل: {e}")
        return 1

    original_size = len(text)
    info(f"حجم اولیه: {original_size:,} کاراکتر")

    # اعمال اصلاحات
    all_changes = []

    text, changes = fix_1_add_missing_imports(text)
    all_changes.extend(changes)

    text, changes = fix_2_site_id(text)
    all_changes.extend(changes)

    text, changes = fix_3_unclosed_div(text)
    all_changes.extend(changes)

    text, changes = fix_4_map_prop(text)
    all_changes.extend(changes)

    # ذخیره فایل
    header("ذخیره فایل")
    try:
        FILE.write_text(text, encoding="utf-8")
        new_size = len(text)
        success(f"✓ فایل ذخیره شد")
        info(f"حجم: {original_size:,} → {new_size:,} کاراکتر (تغییر: {new_size - original_size:+})")
    except Exception as e:
        error(f"خطا در ذخیره: {e}")
        info(f"💡 می‌توانید از پشتیبان بازیابی کنید: {backup.name}")
        return 1

    # تحلیل
    stats = analyze_result(text)

    # خلاصه
    header("خلاصه اصلاحات")
    if all_changes:
        for i, change in enumerate(all_changes, 1):
            print(f"  {i}. {change}")
    else:
        warning("هیچ تغییری لازم نبود")

    # تست build
    build_ok = test_build()

    # گزارش نهایی
    header("گزارش نهایی")
    if build_ok:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 همه اصلاحات موفق بود!{Colors.RESET}")
        print(f"\n{Colors.BOLD}گام بعدی:{Colors.RESET} شروع بازنویسی ساختاری")
        print(f"  - ایجاد features/hydroma/")
        print(f"  - استخراج types و constants")
        print(f"  - ایجاد Zustand store")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠️ اصلاحات اعمال شد اما build هنوز شکست می‌خورد{Colors.RESET}")
        print(f"\n{Colors.BOLD}اقدام بعدی:{Colors.RESET}")
        print(f"  1. خطاهای بالا را بررسی کنید")
        print(f"  2. اگر خطای دیگری وجود دارد، گزارش دهید")
        print(f"  3. پشتیبان: {backup.name}")
        return 1


if __name__ == "__main__":
    sys.exit(main())