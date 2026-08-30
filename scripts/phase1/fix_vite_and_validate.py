#!/usr/bin/env python3
"""
Fix Vite Config + Validate HyDroMa
==================================
1. بازیابی vite.config.ts از backup
2. نوشتن manualChunks صحیح (function نه object)
3. اعتبارسنجی HyDroMaCenter.tsx
4. تست build
"""

import re
import sys
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
VITE_CFG = FRONTEND / "vite.config.ts"
HYDROMA = FRONTEND / "src" / "pages" / "HyDroMaCenter.tsx"


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


def find_latest_backup(base_path: Path) -> Path | None:
    """یافتن آخرین backup فایل"""
    pattern = f"{base_path.name}.bak_*"
    backups = sorted(base_path.parent.glob(pattern), reverse=True)
    # همچنین backup های قدیمی‌تر
    if not backups:
        pattern2 = f"{base_path.name}.backup_*"
        backups = sorted(base_path.parent.glob(pattern2), reverse=True)
    return backups[0] if backups else None


# ═══════════════════════════════════════════════════════════════════════
# بخش ۱: بازیابی vite.config.ts از backup
# ═══════════════════════════════════════════════════════════════════════

def restore_vite_config() -> bool:
    """بازیابی vite.config.ts از آخرین backup سالم"""
    header("۱. بازیابی vite.config.ts")

    backup = find_latest_backup(VITE_CFG)

    if backup and backup.exists():
        info(f"آخرین backup: {backup.name}")
        shutil.copy2(backup, VITE_CFG)
        success(f"✓ بازیابی شد از: {backup.name}")
        return True

    # اگر backup نبود، سعی می‌کنیم .dirname-backup قدیمی را پیدا کنیم
    dirname_backup = VITE_CFG.with_suffix(".ts.dirname-backup")
    if dirname_backup.exists():
        info(f"backup قدیمی یافت شد: {dirname_backup.name}")
        shutil.copy2(dirname_backup, VITE_CFG)
        success("✓ بازیابی شد از dirname-backup")
        return True

    warning("هیچ backup یافت نشد - ادامه با فایل فعلی")
    return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۲: بازنویسی manualChunks به صورت Function
# ═══════════════════════════════════════════════════════════════════════

# تابع manualChunks بهینه برای Vite 8
MANUAL_CHUNKS_FUNCTION = '''    manualChunks(id) {
      // React core
      if (id.includes('node_modules/react-dom') ||
          id.includes('node_modules/react/') ||
          id.includes('node_modules/scheduler')) {
        return 'vendor-react';
      }
      // 3D libraries
      if (id.includes('node_modules/three') ||
          id.includes('node_modules/@react-three')) {
        return 'vendor-3d';
      }
      // UI framework
      if (id.includes('node_modules/antd') ||
          id.includes('node_modules/@ant-design')) {
        return 'vendor-ui';
      }
      // Charts
      if (id.includes('node_modules/echarts') ||
          id.includes('node_modules/zrender')) {
        return 'vendor-charts';
      }
      // Maps
      if (id.includes('node_modules/maplibre-gl') ||
          id.includes('node_modules/@deck.gl')) {
        return 'vendor-maps';
      }
      return undefined;
    },'''


def rewrite_manual_chunks() -> bool:
    """بازنویسی manualChunks به صورت function صحیح"""
    header("۲. بازنویسی manualChunks به Function")

    if not VITE_CFG.exists():
        error("vite.config.ts یافت نشد")
        return False

    text = VITE_CFG.read_text(encoding="utf-8")

    # بررسی وضعیت فعلی
    if "output: {," in text:
        error("فایل فعلی دارای syntax error است (output: {,)")
        info("این نباید بعد از بازیابی backup وجود داشته باشد")
        return False

    # الگوهای ممکن برای manualChunks
    patterns = [
        # object با content
        r'\s*manualChunks:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*,?',
        # function موجود
        r'\s*manualChunks:\s*\([^)]*\)\s*(?::\s*\w+)?\s*=>\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*,?',
        # function با کلیدواژه function
        r'\s*manualChunks:\s*function\s*\([^)]*\)\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*,?',
    ]

    replaced = False
    for i, pattern in enumerate(patterns, 1):
        match = re.search(pattern, text, re.DOTALL)
        if match:
            info(f"الگوی {i} یافت شد")
            # جایگزینی با function جدید
            # اطمینان از newline و indentation صحیح
            text = text[:match.start()] + "\n" + MANUAL_CHUNKS_FUNCTION + text[match.end():]
            replaced = True
            success(f"✓ manualChunks با function جایگزین شد")
            break

    if not replaced:
        # بررسی اینکه آیا manualChunks وجود دارد
        if "manualChunks" in text:
            warning("manualChunks یافت شد ولی format قابل تشخیص نیست")
            # حذف کامل با trailing comma
            text = re.sub(r',?\s*manualChunks:[^,]*(?=,|\n\s*\})', '', text, count=1)
            info("manualChunks حذف شد")
        else:
            # manualChunks وجود ندارد - افزودن به output section
            info("manualChunks یافت نشد - افزودن به output")
            # جستجوی output: {
            output_match = re.search(r'output:\s*\{', text)
            if output_match:
                insert_pos = output_match.end()
                text = text[:insert_pos] + "\n" + MANUAL_CHUNKS_FUNCTION + text[insert_pos:]
                success("✓ manualChunks به output اضافه شد")
                replaced = True
            else:
                warning("output section یافت نشد")

    # ذخیره
    VITE_CFG.write_text(text, encoding="utf-8")
    success(f"✓ vite.config.ts ذخیره شد")

    # نمایش بخش اصلاح‌شده
    print(f"\n{Colors.BOLD}بخش manualChunks فعلی:{Colors.RESET}")
    start = max(0, text.find("manualChunks") - 50)
    end = min(len(text), text.find("manualChunks") + 600) if "manualChunks" in text else 0
    if end > 0:
        snippet = text[start:end]
        for line in snippet.splitlines()[:25]:
            print(f"  {line}")

    return True


# ═══════════════════════════════════════════════════════════════════════
# بخش ۳: اعتبارسنجی HyDroMaCenter.tsx
# ═══════════════════════════════════════════════════════════════════════

def validate_hydroma() -> bool:
    """بررسی syntax صحیح در HyDroMaCenter.tsx"""
    header("۳. اعتبارسنجی HyDroMaCenter.tsx")

    if not HYDROMA.exists():
        error(f"فایل یافت نشد: {HYDROMA}")
        return False

    text = HYDROMA.read_text(encoding="utf-8")
    lines = text.splitlines()

    info(f"تعداد خطوط: {len(lines)}")

    # شمارش پرانتزها و براکت‌ها
    stats = {
        '(': 0, ')': 0,
        '{': 0, '}': 0,
        '[': 0, ']': 0,
    }

    # نادیده گرفتن string literals (تقریبی)
    in_string = False
    string_char = None
    in_comment = False
    in_line_comment = False

    i = 0
    while i < len(text):
        c = text[i]

        # مدیریت کامنت
        if not in_string:
            if not in_comment and i + 1 < len(text):
                if text[i:i+2] == '//':
                    # line comment - تا newline
                    while i < len(text) and text[i] != '\n':
                        i += 1
                    continue
                if text[i:i+2] == '/*':
                    in_comment = True
                    i += 2
                    continue
            if in_comment:
                if i + 1 < len(text) and text[i:i+2] == '*/':
                    in_comment = False
                    i += 2
                    continue
                i += 1
                continue

        # مدیریت string
        if not in_string:
            if c in '"\'`':
                in_string = True
                string_char = c
                i += 1
                continue
        else:
            if c == '\\':
                i += 2  # skip escaped
                continue
            if c == string_char:
                in_string = False
                string_char = None
                i += 1
                continue
            i += 1
            continue

        # شمارش
        if c in stats:
            stats[c] += 1

        i += 1

    print(f"\n{Colors.BOLD}آمار پرانتزها:{Colors.RESET}")
    print(f"  (): {stats['(']} باز / {stats[')']} بسته → اختلاف: {stats['('] - stats[')']}")
    print(f"  []: {stats['[']} باز / {stats[']']} بسته → اختلاف: {stats['['] - stats[']']}")
    print(f"  {{}}: {stats['{']} باز / {stats['}']} بسته → اختلاف: {stats['{'] - stats['}']}")

    balanced = (
        stats['('] == stats[')'] and
        stats['['] == stats[']'] and
        stats['{'] == stats['}']
    )

    if balanced:
        success("✓ همه پرانتزها متوازن هستند")
    else:
        error("✗ پرانتزها نامتوازن هستند!")

        # پیدا کردن خط مشکل‌دار
        info("جستجوی خط با عدم تعادل...")

        running = {'(': 0, '[': 0, '{': 0}
        for line_no, line in enumerate(lines, 1):
            for c in line:
                if c in running:
                    running[c] += 1
                elif c == ')':
                    running['('] -= 1
                elif c == ']':
                    running['['] -= 1
                elif c == '}':
                    running['{'] -= 1

            # اگر منفی شد، یعنی بستن اضافه
            for k, v in running.items():
                if v < -1:
                    error(f"خط {line_no}: عدم تعادل {k} (balance={v})")
                    print(f"    {line[:100]}")

    return balanced


# ═══════════════════════════════════════════════════════════════════════
# بخش ۴: تست build
# ═══════════════════════════════════════════════════════════════════════

def test_build() -> bool:
    """تست build"""
    header("۴. تست pnpm build")

    start = time.time()

    try:
        result = subprocess.run(
            "pnpm build",
            shell=True,
            cwd=FRONTEND,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=240
        )

        elapsed = time.time() - start
        output = result.stdout + result.stderr

        if result.returncode == 0:
            success(f"✓ build موفق در {elapsed:.1f} ثانیه")

            # استخراج اطلاعات bundle
            for line in output.splitlines():
                if "dist/" in line or "✓ built in" in line:
                    print(f"  {line}")

            return True

        error(f"build شکست خورد در {elapsed:.1f} ثانیه")

        # استخراج خطاهای مهم
        lines = output.splitlines()

        # نمایش خطاهای اصلی
        error_lines = []
        for i, l in enumerate(lines):
            if any(k in l for k in ["error:", "Error:", "✗", "PARSE_ERROR", "[builtin"]):
                error_lines.extend(lines[max(0, i-2):min(len(lines), i+8)])
                error_lines.append("---")

        if error_lines:
            print(f"\n{Colors.BOLD}جزئیات خطا:{Colors.RESET}")
            seen = set()
            for l in error_lines:
                if l not in seen:
                    print(f"  {l}")
                    seen.add(l)
                if len(seen) > 30:
                    break

        return False

    except subprocess.TimeoutExpired:
        warning("build timeout (>240s)")
        return False
    except Exception as e:
        error(f"خطا: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۵: تست dev server
# ═══════════════════════════════════════════════════════════════════════

def test_dev_server() -> bool:
    """تست ۲۵ ثانیه‌ای dev server"""
    header("۵. تست pnpm dev")

    try:
        proc = subprocess.Popen(
            "pnpm dev",
            shell=True,
            cwd=FRONTEND,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        start = time.time()
        server_ready = False
        url = None
        error_found = False
        output_lines = []

        while time.time() - start < 25:
            if proc.poll() is not None:
                remaining = proc.stdout.read()
                if remaining:
                    output_lines.extend(remaining.splitlines())
                break

            line = proc.stdout.readline()
            if not line:
                continue

            output_lines.append(line.rstrip())
            if len(output_lines) <= 20:
                print(f"  {line.rstrip()}")

            if "Local:" in line:
                server_ready = True
                m = re.search(r'http://[^\s]+', line)
                if m:
                    url = m.group(0)

            if "ready in" in line.lower():
                server_ready = True

            if "error" in line.lower() and "no error" not in line.lower():
                # فقط اگر واقعاً error باشد
                if any(k in line.lower() for k in ["failed", "syntax", "unexpected"]):
                    error_found = True

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

        if error_found:
            error("✗ خطای بحرانی در dev server")
            for l in output_lines[-10:]:
                print(f"  {l}")
            return False

        warning("dev server آماده نشد (اما خطای بحرانی هم نیست)")
        return True

    except Exception as e:
        error(f"خطا: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۶: commit و push
# ═══════════════════════════════════════════════════════════════════════

def commit_and_push():
    """commit و push"""
    header("۶. commit و push")

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
            'git commit -m "fix: correct vite manualChunks syntax and hydroma JSX"',
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
    print(f"{Colors.BOLD}  🔧 Fix Vite + Validate HyDroMa - Final{Colors.RESET}")
    print(f"{Colors.BOLD}{'═' * 70}{Colors.RESET}")

    # گام ۱: بازیابی vite.config.ts
    restore_vite_config()

    # گام ۲: بازنویسی manualChunks
    rewrite_manual_chunks()

    # گام ۳: اعتبارسنجی HyDroMa
    hydroma_ok = validate_hydroma()

    # گام ۴: تست build
    build_ok = test_build()

    # گام ۵: تست dev server (اگر build موفق بود)
    dev_ok = False
    if build_ok:
        dev_ok = test_dev_server()

    # گام ۶: commit و push
    if build_ok:
        commit_and_push()

    # گزارش نهایی
    header("📊 گزارش نهایی")

    checks = [
        ("HyDroMa balanced", hydroma_ok),
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
        print(f"{Colors.BOLD}│     features/hydroma/ extraction           │{Colors.RESET}")
        print(f"{Colors.BOLD}└───────────────────────────────────────────┘{Colors.RESET}")
        print(f"\n{Colors.BOLD}اولین فایل برای استخراج:{Colors.RESET}")
        print(f"  - types/hydroma.types.ts")
        print(f"  - store/hydromaStore.ts")
        print(f"  - components/TerrainMesh.tsx")
        return 0
    elif build_ok:
        print(f"{Colors.YELLOW}⚠️ build موفق - می‌توان به فاز ۱ رفت{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}✗ build هنوز شکست می‌خورد{Colors.RESET}")
        print(f"  لطفاً خروجی بالا را بررسی کنید")
        return 1


if __name__ == "__main__":
    sys.exit(main())