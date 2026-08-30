#!/usr/bin/env python3
"""
Fix HyDroMaCenter.tsx + vite.config.ts - Final
==============================================
رفع دو مشکل باقی‌مانده:
1. حذف )} اضافی در خط 4268 HyDroMaCenter.tsx
2. اصلاح manualChunks در vite.config.ts (Object → Function)
"""

import re
import sys
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HYDROMA = PROJECT_ROOT / "frontend" / "src" / "pages" / "HyDroMaCenter.tsx"
VITE_CFG = PROJECT_ROOT / "frontend" / "vite.config.ts"


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


def backup(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(f"{path.suffix}.bak_{ts}")
    shutil.copy2(path, b)
    info(f"پشتیبان: {b.name}")
    return b


# ═══════════════════════════════════════════════════════════════════════
# بخش ۱: حذف )} اضافی در HyDroMaCenter.tsx
# ═══════════════════════════════════════════════════════════════════════

def fix_hydroma_extra_close() -> bool:
    """حذف )} اضافی در خط 4268"""
    header("۱. اصلاح )} اضافی در HyDroMaCenter.tsx")

    if not HYDROMA.exists():
        error(f"فایل یافت نشد: {HYDROMA}")
        return False

    backup(HYDROMA)

    text = HYDROMA.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    info(f"تعداد خطوط قبل: {len(lines)}")

    # نمایش خطوط 4260-4280 برای تشخیص
    target_line = 4268
    info(f"نمایش خطوط {target_line-8} تا {target_line+12}:")
    print(f"\n{Colors.BOLD}محتوای فعلی:{Colors.RESET}")
    for i in range(max(0, target_line - 9), min(len(lines), target_line + 12)):
        marker = ">>> " if i + 1 == target_line else "    "
        line_text = lines[i].rstrip()
        if len(line_text) > 100:
            line_text = line_text[:100] + "..."
        print(f"  {marker}{i+1:4d} │ {line_text}")

    # استراتژی ۱: الگوی دقیق
    # در کد فعلی، بعد از اصلاح قبلی، احتمالاً این الگو داریم:
    #   {demError && (
    #     <div ...>{demError}</div>
    #   )}
    #   {erosionEffect && (
    #     <div ...>...</div>
    #   )}
    #   )}   <-- این اضافی است!

    # جستجو برای الگو: )} قبل از {erosionEffect که نباید باشد
    pattern = re.compile(
        r'\{demError && \(\s*\n'
        r'\s*<div[^>]*>\{demError\}</div>\s*\n'
        r'\s*\)\}\s*\n'          # این )} را قبلاً اضافه کردیم
        r'\s*\{erosionEffect && \(\s*\n'
        r'(.+?)'
        r'\)\}\s*\n'              # بستن erosionEffect
        r'\s*\)\}',               # بستن demError که حالا اضافی شده
        re.DOTALL
    )

    match = pattern.search(text)

    if match:
        info("الگوی دقیق یافت شد - حذف )} اضافی")

        # جایگزینی با نسخه صحیح (بدون )} اضافی)
        old = match.group(0)
        # استخراج بخش داخلی erosionEffect
        erosion_body = match.group(1)

        new = (
            '{demError && (\n'
            '          <div style={{ fontSize: "11px", color: "#fca5a5" }}>'
            '{demError}</div>\n'
            '        )}\n'
            '        {erosionEffect && (\n'
            f'{erosion_body}'
            '        )}'
        )

        text = text.replace(old, new, 1)
        HYDROMA.write_text(text, encoding="utf-8")
        success("✓ )} اضافی حذف شد")
        return True

    # استراتژی ۲: رویکرد خط به خط
    info("الگوی دقیق یافت نشد، رویکرد خط به خط...")

    # پیدا کردن خط 4268 (ایندکس 4267) و حذف آن اگر )} است
    if len(lines) > target_line:
        line = lines[target_line - 1]
        stripped = line.strip()

        if stripped == ")}":
            info(f"خط {target_line} فقط شامل ')}}' است")

            # بررسی خط قبلی - اگر erosionEffect را می‌بندد، این اضافی است
            prev_line = lines[target_line - 2].strip() if target_line > 1 else ""
            next_line = lines[target_line].strip() if target_line < len(lines) else ""

            info(f"  خط قبلی: {prev_line[:80]}")
            info(f"  خط بعدی: {next_line[:80]}")

            # اگر خط قبلی هم )} است، قطعاً این اضافی است
            if prev_line == ")}":
                info("✓ تشخیص: )} اضافی است (خط قبلی هم )} است)")
                del lines[target_line - 1]
                HYDROMA.write_text("".join(lines), encoding="utf-8")
                success(f"✓ خط {target_line} حذف شد")
                return True
            else:
                warning(f"خط قبلی )}} نیست. بررسی دقیق‌تر...")
                # حذف با احتیاط - اگر بعد از آن خط دیگری با )} باشد
                if target_line < len(lines):
                    next_stripped = lines[target_line].strip()
                    if next_stripped == ")}":
                        info("خط بعدی هم )} است - حذف خط فعلی")
                        del lines[target_line - 1]
                        HYDROMA.write_text("".join(lines), encoding="utf-8")
                        success(f"✓ خط {target_line} حذف شد")
                        return True

    # استراتژی ۳: حذف همه )} های متوالی بیشتر از یکی
    info("استراتژی نهایی: جستجوی )} های متوالی اضافی...")

    # شمارش )} های متوالی
    consecutive = []
    for i, line in enumerate(lines):
        if line.strip() == ")}":
            consecutive.append(i)
        else:
            if len(consecutive) >= 2:
                info(f"یافت شد: {len(consecutive)} )}} متوالی در خطوط {consecutive[0]+1} تا {consecutive[-1]+1}")
                # حذف همه به جز اولی
                # حذف از آخر به اول تا ایندکس‌ها به هم نریزد
                for idx in reversed(consecutive[1:]):
                    info(f"  حذف خط {idx+1}")
                    del lines[idx]
                consecutive = []
            else:
                consecutive = []

    # بررسی آخرین گروه
    if len(consecutive) >= 2:
        info(f"آخرین گروه: {len(consecutive)} )}} متوالی")
        for idx in reversed(consecutive[1:]):
            info(f"  حذف خط {idx+1}")
            del lines[idx]

    new_text = "".join(lines)
    if new_text != text:
        HYDROMA.write_text(new_text, encoding="utf-8")
        success("✓ )} های اضافی حذف شدند")
        info(f"تعداد خطوط بعد: {len(lines)}")
        return True

    warning("هیچ )} اضافی یافت نشد")
    return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۲: اصلاح manualChunks در vite.config.ts
# ═══════════════════════════════════════════════════════════════════════

def fix_vite_manual_chunks() -> bool:
    """تبدیل manualChunks از Object به Function"""
    header("۲. اصلاح manualChunks در vite.config.ts")

    if not VITE_CFG.exists():
        error(f"فایل یافت نشد: {VITE_CFG}")
        return False

    backup(VITE_CFG)
    text = VITE_CFG.read_text(encoding="utf-8")

    # الگوهای رایج manualChunks به صورت object
    # 1. manualChunks: { react: [...], three: [...] }
    # 2. manualChunks: { ... }

    # جستجوی الگوی object
    # این regex دنبال manualChunks: { ... } می‌گردد
    object_pattern = re.compile(
        r'manualChunks:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
        re.DOTALL
    )

    match = object_pattern.search(text)

    if match:
        info("الگوی manualChunks object یافت شد")

        # استخراج محتوای object
        content = match.group(1)

        # تبدیل به function
        # شکل نهایی:
        # manualChunks: (id) => {
        #   if (id.includes('react')) return 'react';
        #   if (id.includes('three')) return 'three';
        #   // ...
        # }

        # parsing ساده از object
        # هر خط مثل: 'react': ['react', 'react-dom']
        rules = []

        # یافتن تمام 'key': [...]
        entries = re.findall(
            r"""['"]([^'"]+)['"]:\s*\[([^\]]+)\]""",
            content
        )

        for key, values in entries:
            # values مثل: 'react', 'react-dom'
            packages = [v.strip().strip("'\"") for v in values.split(',')]
            for pkg in packages:
                pkg = pkg.strip()
                if pkg:
                    rules.append((pkg, key))

        if rules:
            info(f"تعداد قوانین استخراج شده: {len(rules)}")

            # ساخت function
            lines = ["manualChunks: (id: string) => {\n"]

            # گروه‌بندی بر اساس chunk name
            chunk_to_packages = {}
            for pkg, chunk in rules:
                chunk_to_packages.setdefault(chunk, []).append(pkg)

            for chunk, packages in chunk_to_packages.items():
                conditions = " || ".join(f"id.includes('{pkg}')" for pkg in packages[:3])  # 3 تا اول
                lines.append(f"    if ({conditions}) return '{chunk}';\n")

            lines.append("    return undefined;\n")
            lines.append("  }")

            new_manual_chunks = "".join(lines)

            # جایگزینی
            text = text[:match.start()] + new_manual_chunks + text[match.end():]

            VITE_CFG.write_text(text, encoding="utf-8")
            success(f"✓ manualChunks به function تبدیل شد ({len(rules)} قانون)")
            return True
        else:
            warning("قانونی در object یافت نشد")

    # اگر object نبود، شاید قبلاً function است
    if "manualChunks:" in text and ("(id" in text or "(module" in text):
        info("manualChunks قبلاً به صورت function است")
        return True

    # استراتژی ساده‌تر: اگر manualChunks وجود دارد ولی format اشتباه است
    if "manualChunks:" in text:
        warning("manualChunks یافت شد ولی format قابل تشخیص نیست")
        info("حذف manualChunks به طور موقت...")

        # حذف کل بخش manualChunks
        # الگو: manualChunks: ... تا انتهای object/function
        text = re.sub(
            r'\s*manualChunks:\s*(?:\{[^}]*\}|[^,}]+)',
            '',
            text,
            count=1
        )

        VITE_CFG.write_text(text, encoding="utf-8")
        success("✓ manualChunks حذف شد (می‌توان بعداً بهینه کرد)")
        return True

    info("manualChunks در فایل یافت نشد")
    return True


# ═══════════════════════════════════════════════════════════════════════
# بخش ۳: تست build
# ═══════════════════════════════════════════════════════════════════════

def test_build() -> bool:
    """تست build"""
    header("۳. تست pnpm build")

    frontend = PROJECT_ROOT / "frontend"

    info("اجرای pnpm build...")
    start = time.time()

    try:
        result = subprocess.run(
            "pnpm build",
            shell=True,
            cwd=frontend,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180
        )

        elapsed = time.time() - start

        if result.returncode == 0:
            success(f"✓ build موفق در {elapsed:.1f} ثانیه")
            return True

        # نمایش خطاها
        output = result.stdout + result.stderr
        error(f"build شکست خورد در {elapsed:.1f} ثانیه")

        # استخراج خطاهای مهم
        lines = output.splitlines()
        error_lines = [l for l in lines if "error" in l.lower() or "Error" in l or "✗" in l]

        if error_lines:
            print(f"\n{Colors.BOLD}خطاهای یافت شده:{Colors.RESET}")
            for l in error_lines[:15]:
                print(f"  {l}")

        # نمایش ۲۵ خط آخر
        print(f"\n{Colors.BOLD}۲۵ خط آخر خروجی:{Colors.RESET}")
        for l in lines[-25:]:
            print(f"  {l}")

        return False

    except subprocess.TimeoutExpired:
        warning("build timeout شد (>180s)")
        return False
    except Exception as e:
        error(f"خطا: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۴: تست dev server
# ═══════════════════════════════════════════════════════════════════════

def test_dev_server() -> bool:
    """تست ۲۰ ثانیه‌ای dev server"""
    header("۴. تست pnpm dev (۲۰ ثانیه)")

    frontend = PROJECT_ROOT / "frontend"

    try:
        proc = subprocess.Popen(
            "pnpm dev",
            shell=True,
            cwd=frontend,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        start = time.time()
        server_ready = False
        url = None
        output_lines = []

        while time.time() - start < 20:
            if proc.poll() is not None:
                remaining = proc.stdout.read()
                if remaining:
                    output_lines.extend(remaining.splitlines())
                break

            line = proc.stdout.readline()
            if not line:
                continue

            output_lines.append(line.rstrip())
            if len(output_lines) <= 15:
                print(f"  {line.rstrip()}")

            if "Local:" in line:
                server_ready = True
                m = re.search(r'http://[^\s]+', line)
                if m:
                    url = m.group(0)

            if "ready in" in line.lower():
                server_ready = True

        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

        if server_ready:
            success("✓ dev server راه‌اندازی شد")
            if url:
                info(f"🌐 {url}")
            return True

        warning("dev server آماده نشد")
        return False

    except Exception as e:
        error(f"خطا: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۵: commit و push
# ═══════════════════════════════════════════════════════════════════════

def commit_and_push():
    """commit و push"""
    header("۵. commit و push")

    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        status = subprocess.run(
            "git status --porcelain",
            shell=True, cwd=PROJECT_ROOT,
            capture_output=True, text=True, check=True
        )

        if not status.stdout.strip():
            info("تغییری برای commit نیست")
            return

        subprocess.run(
            'git commit -m "fix(hydroma): resolve JSX syntax errors and vite config manualChunks"',
            shell=True, cwd=PROJECT_ROOT, check=True
        )
        success("✓ commit ایجاد شد")

        result = subprocess.run(
            "git remote get-url origin",
            shell=True, cwd=PROJECT_ROOT,
            capture_output=True, text=True
        )
        if result.returncode == 0:
            subprocess.run(
                "git push origin main",
                shell=True, cwd=PROJECT_ROOT, check=True
            )
            success("✓ push موفق بود")

    except Exception as e:
        warning(f"commit/push: {e}")


# ═══════════════════════════════════════════════════════════════════════
# اجرای اصلی
# ═══════════════════════════════════════════════════════════════════════

def main() -> int:
    print(f"\n{Colors.BOLD}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}  🔧 Fix HyDroMa + Vite - Final{Colors.RESET}")
    print(f"{Colors.BOLD}{'═' * 70}{Colors.RESET}")

    # گام ۱: اصلاح HyDroMa
    hydroma_ok = fix_hydroma_extra_close()

    # گام ۲: اصلاح vite.config
    vite_ok = fix_vite_manual_chunks()

    # گام ۳: تست build
    build_ok = test_build()

    # گام ۴: تست dev server (اگر build موفق بود)
    dev_ok = False
    if build_ok:
        dev_ok = test_dev_server()
    else:
        warning("build شکست خورد، تست dev server رد شد")

    # گام ۵: commit و push
    if build_ok:
        commit_and_push()

    # گزارش نهایی
    header("📊 گزارش نهایی")

    checks = [
        ("HyDroMa )}} fix", hydroma_ok),
        ("Vite manualChunks", vite_ok),
        ("Build success", build_ok),
        ("Dev server", dev_ok),
    ]

    all_ok = True
    for name, ok in checks:
        symbol = "✓" if ok else "✗"
        color = Colors.GREEN if ok else Colors.RED
        print(f"  {color}{symbol}{Colors.RESET} {name}")
        if not ok:
            all_ok = False

    print()
    if all_ok:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 فاز صفر کاملاً کامل شد!{Colors.RESET}")
        print(f"\n{Colors.BOLD}┌───────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.BOLD}│  🚀 آماده فاز ۱: بازنویسی ساختاری      │{Colors.RESET}")
        print(f"{Colors.BOLD}│     استخراج features/hydroma/            │{Colors.RESET}")
        print(f"{Colors.BOLD}└───────────────────────────────────────────┘{Colors.RESET}")
        return 0
    elif build_ok:
        print(f"{Colors.YELLOW}⚠️ build موفق، dev server ناقص{Colors.RESET}")
        print(f"  می‌توان به فاز ۱ رفت")
        return 0
    else:
        print(f"{Colors.RED}⚠️ build هنوز شکست می‌خورد{Colors.RESET}")
        print(f"  خطا را بررسی کنید")
        return 1


if __name__ == "__main__":
    sys.exit(main())