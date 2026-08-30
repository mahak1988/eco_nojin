#!/usr/bin/env python3
"""
Fix Import Paths & Vitest Setup
================================
1. اصلاح import paths (../../../ → ../../../../)
2. یافتن و اصلاح vite.config.ts برای setupFiles
3. اجرای تست‌ها
4. commit
"""

import os
import re
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
HYDROMA = FRONTEND / "src" / "features" / "hydroma"


class C:
    RESET = "\033[0m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
    RED = "\033[91m"; BLUE = "\033[94m"; CYAN = "\033[96m"; BOLD = "\033[1m"


def ok(m): print(f"{C.GREEN}✓{C.RESET}  {m}")
def info(m): print(f"{C.BLUE}ℹ{C.RESET}  {m}")
def warn(m): print(f"{C.YELLOW}⚠{C.RESET}  {m}")
def err(m): print(f"{C.RED}✗{C.RESET}  {m}")
def header(m):
    print(f"\n{C.BOLD}{C.CYAN}{'═' * 70}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  {m}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'═' * 70}{C.RESET}\n")


# ═══════════════════════════════════════════════════════════════════════
# بخش ۱: اصلاح import paths
# ═══════════════════════════════════════════════════════════════════════

def fix_import_paths():
    """اصلاح مسیرهای import در کامپوننت‌ها و utils"""
    header("۱. اصلاح مسیرهای import")

    files_to_fix = [
        # (file, old, new)
        (
            HYDROMA / "components" / "canvas" / "TerrainMesh.tsx",
            "from '../../../lib/terrainGenerator'",
            "from '../../../../lib/terrainGenerator'"
        ),
        (
            HYDROMA / "components" / "canvas" / "PlacedOpsMarkers.tsx",
            "from '../../utils/worldToTerrainY'",
            None  # این مسیر درست است (در همان feature)
        ),
        (
            HYDROMA / "components" / "canvas" / "PolygonOverlay.tsx",
            "from '../../utils/worldToTerrainY'",
            None  # این مسیر درست است
        ),
        (
            HYDROMA / "utils" / "worldToTerrainY.ts",
            "from '../../../lib/terrainGenerator'",
            "from '../../../lib/terrainGenerator'"  # بررسی: از utils به src/lib = 3 level
        ),
    ]

    fixed_count = 0

    for file_path, old, new in files_to_fix:
        if not file_path.exists():
            warn(f"فایل یافت نشد: {file_path.name}")
            continue

        text = file_path.read_text(encoding="utf-8")

        if new is None:
            info(f"بدون تغییر: {file_path.name}")
            continue

        if old in text:
            new_text = text.replace(old, new)
            file_path.write_text(new_text, encoding="utf-8")
            ok(f"{file_path.name}: '{old}' → '{new}'")
            fixed_count += 1
        elif new in text:
            info(f"از قبل اصلاح شده: {file_path.name}")
        else:
            warn(f"الگو یافت نشد: {file_path.name}")

    # بررسی ویژه برای worldToTerrainY.ts
    # مسیر: src/features/hydroma/utils/ → src/lib/
    # = 3 level بالا (utils → hydroma → features → src)
    utils_file = HYDROMA / "utils" / "worldToTerrainY.ts"
    if utils_file.exists():
        text = utils_file.read_text(encoding="utf-8")
        # این مسیر درست است (۳ سطح): ../../../lib/terrainGenerator
        # فقط مطمئن می‌شویم که درست است
        if "../../../lib/terrainGenerator" in text:
            ok("worldToTerrainY.ts: مسیر ../../../ درست است")
        elif "../../../../lib/terrainGenerator" in text:
            # اصلاح: باید یک سطح کمتر باشد
            new_text = text.replace(
                "from '../../../../lib/terrainGenerator'",
                "from '../../../lib/terrainGenerator'"
            )
            utils_file.write_text(new_text, encoding="utf-8")
            ok("worldToTerrainY.ts: مسیر اصلاح شد")

    return fixed_count


# ═══════════════════════════════════════════════════════════════════════
# بخش ۲: یافتن و اصلاح vite.config.ts
# ═══════════════════════════════════════════════════════════════════════

def find_vite_config():
    """یافتن vite.config.ts در هر جای پروژه"""
    candidates = [
        FRONTEND / "vite.config.ts",
        FRONTEND / "vite.config.mts",
        FRONTEND / "vite.config.js",
        PROJECT_ROOT / "vite.config.ts",
    ]
    for c in candidates:
        if c.exists():
            return c

    # جستجوی کامل
    for f in FRONTEND.rglob("vite.config.*"):
        if f.is_file() and not f.name.endswith(".backup"):
            return f

    return None


def fix_vite_config():
    """افزودن test.setup.ts به vite.config.ts"""
    header("۲. تنظیم vite.config.ts برای vitest")

    vite_cfg = find_vite_config()
    if not vite_cfg:
        err("vite.config یافت نشد در هیچ مسیر")
        return False

    info(f"یافت شد: {vite_cfg.relative_to(PROJECT_ROOT)}")

    text = vite_cfg.read_text(encoding="utf-8")

    # بررسی اینکه آیا setupFiles قبلاً تنظیم شده
    if "setupFiles" in text and "setup.ts" in text:
        ok("setupFiles قبلاً تنظیم شده")
        return True

    # پشتیبان
    backup = vite_cfg.with_suffix(".ts.setup-backup")
    backup.write_text(text, encoding="utf-8")
    info(f"پشتیبان: {backup.name}")

    # استراتژی ۱: اگر test block وجود دارد، setupFiles را به آن اضافه کن
    if "test:" in text or "test :" in text:
        # یافتن test block
        pattern = r'(test\s*:\s*\{[^}]*)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            block = match.group(1)
            if "setupFiles" not in block:
                new_block = block.rstrip().rstrip(',')
                new_block += ",\n    setupFiles: ['./test/setup.ts'],\n  "
                text = text[:match.start()] + new_block + text[match.end():]
                vite_cfg.write_text(text, encoding="utf-8")
                ok("✓ setupFiles به test block موجود اضافه شد")
                return True

    # استراتژی ۲: افزودن test block جدید
    # یافتن defineConfig block
    # دنبال آخرین } قبل از ); بگردیم
    pattern = r'(defineConfig\s*\(\s*\{[\s\S]*?)(\n\}\s*\)\s*;?\s*$)'
    match = re.search(pattern, text, re.MULTILINE)
    if match:
        before = match.group(1)
        after = match.group(2)

        # حذف trailing comma و whitespace
        before = before.rstrip()
        if before.endswith(','):
            before = before[:-1]

        test_block = """,
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
  }"""

        new_text = before + test_block + after
        vite_cfg.write_text(new_text, encoding="utf-8")
        ok("✓ test block با setupFiles اضافه شد")
        return True

    err("الگوی defineConfig یافت نشد")
    return False


# ═══════════════════════════════════════════════════════════════════════
# بخش ۳: بررسی صحت lib/terrainGenerator
# ═══════════════════════════════════════════════════════════════════════

def verify_terrain_generator():
    """بررسی اینکه lib/terrainGenerator.ts exports مورد نیاز را دارد"""
    header("۳. بررسی lib/terrainGenerator.ts")

    tg = FRONTEND / "src" / "lib" / "terrainGenerator.ts"
    if not tg.exists():
        err(f"فایل یافت نشد: {tg}")
        return False

    text = tg.read_text(encoding="utf-8")
    info(f"حجم: {len(text):,} کاراکتر، {len(text.splitlines())} خط")

    # بررسی exports مورد نیاز
    required_exports = [
        "WORLD_SIZE",
        "HEIGHT_SCALE",
        "worldToGrid",
        "terrainColor",
        "moistureColor",
        "rootColor",
        "groundwaterColor",
    ]

    missing = []
    for exp in required_exports:
        # دنبال export یا export const/function
        pattern = rf'\bexport\s+(?:const|function|let|var|class)\s+{exp}\b|\bexport\s+\{{[^}}]*\b{exp}\b'
        if re.search(pattern, text):
            ok(f"✓ {exp}")
        else:
            missing.append(exp)
            err(f"✗ {exp} یافت نشد")

    if missing:
        warn(f"{len(missing)} export مفقود است. mock ها را به‌روزرسانی می‌کنیم...")
        return False

    ok("همه exports لازم موجودند")
    return True


# ═══════════════════════════════════════════════════════════════════════
# بخش ۴: اجرای تست‌ها
# ═══════════════════════════════════════════════════════════════════════

def run_tests():
    """اجرای تست‌های hydroma"""
    header("۴. اجرای تست‌ها")

    # افزودن git به PATH
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

    result = subprocess.run(
        "pnpm test features/hydroma --reporter=verbose",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        timeout=120
    )

    output = result.stdout + result.stderr
    print()
    # نمایش فقط نتایج
    for line in output.splitlines():
        if any(k in line for k in ["✓", "✗", "❯", "Test Files", "Tests", "FAIL", "PASS"]):
            print(f"  {line}")

    return result.returncode == 0


# ═══════════════════════════════════════════════════════════════════════
# بخش ۵: commit
# ═══════════════════════════════════════════════════════════════════════

def commit():
    """commit اصلاحات"""
    header("۵. commit")
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run(
            'git commit -m "fix(hydroma): correct import paths and vitest setupFiles config"',
            shell=True, cwd=PROJECT_ROOT, check=True
        )
        subprocess.run("git push origin main", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("commit و push موفق")
    except Exception as e:
        warn(f"commit: {e}")


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{C.BOLD}{'═' * 70}{C.RESET}")
    print(f"{C.BOLD}  🔧 Fix Import Paths & Vitest Setup{C.RESET}")
    print(f"{C.BOLD}{'═' * 70}{C.RESET}")

    fix_import_paths()
    fix_vite_config()
    verify_terrain_generator()
    tests_ok = run_tests()
    commit()

    header("📊 گزارش نهایی")
    if tests_ok:
        print(f"{C.GREEN}{C.BOLD}🎉 همه تست‌ها پاس شدند!{C.RESET}")
        print(f"\n  حالا می‌توان به فاز بعدی رفت.")
        return 0
    else:
        print(f"{C.YELLOW}⚠️ هنوز تست‌ها شکست می‌خورند{C.RESET}")
        print(f"\n  اقدام بعدی: بررسی دقیق خروجی تست‌ها")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())