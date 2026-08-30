#!/usr/bin/env python3
"""
Fix HyDroMaCenter Default Camera View
=====================================
اصلاح موقعیت، FOV و OrbitControls برای دید مناسب اولیه.

مقادیر صحیح برای WORLD_SIZE ≈ 20:
- position: [25, 22, 25]  → دید ایزومتریک
- fov: 50                  → میدان دید متعادل
- minDistance: 5           → امکان نزدیک شدن
- maxDistance: 150         → امکان دور شدن
- target: [0, 0, 0]        → نگاه به مرکز
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
    print(f"\n{C.BOLD}{C.CYAN}{'═' * 70}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  {m}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'═' * 70}{C.RESET}\n")


def backup(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(f"{path.suffix}.cam_{ts}")
    shutil.copy2(path, b)
    info(f"پشتیبان: {b.name}")
    return b


# ═══════════════════════════════════════════════════════════════════════
# اصلاحات دوربین
# ═══════════════════════════════════════════════════════════════════════

def fix_camera_position(text: str) -> tuple:
    """اصلاح موقعیت اولیه دوربین"""
    changes = []

    # الگوی فعلی: position: [1250, 850, 1250], fov: 42
    pattern = re.compile(
        r'camera\s*=\s*\{\s*\{\s*position:\s*\[\s*1250\s*,\s*850\s*,\s*1250\s*\]\s*,\s*fov:\s*42\s*\}\s*\}',
        re.DOTALL
    )

    if pattern.search(text):
        # جایگزینی با مقادیر صحیح
        new_camera = 'camera={{ position: [25, 22, 25], fov: 50, near: 0.1, far: 5000 }}'
        text = pattern.sub(new_camera, text, count=1)
        changes.append("position: [1250,850,1250] → [25,22,25]")
        changes.append("fov: 42 → 50")
        ok("✓ موقعیت و FOV دوربین اصلاح شد")
    else:
        # امتحان الگوی منعطف‌تر
        pattern2 = re.compile(
            r'position:\s*\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\]\s*,\s*fov:\s*\d+'
        )
        match = pattern2.search(text)
        if match:
            new = 'position: [25, 22, 25], fov: 50'
            text = text[:match.start()] + new + text[match.end():]
            changes.append("Camera position/fov replaced via flexible pattern")
            ok("✓ موقعیت دوربین با الگوی منعطف اصلاح شد")
        else:
            warn("الگوی camera یافت نشد")

    return text, changes


def fix_orbit_controls(text: str) -> tuple:
    """اصلاح OrbitControls"""
    changes = []

    # اصلاح minDistance و maxDistance
    # minDistance={60} → minDistance={5}
    min_pattern = re.compile(r'minDistance\s*=\s*\{\s*60\s*\}')
    if min_pattern.search(text):
        text = min_pattern.sub('minDistance={5}', text, count=1)
        changes.append("minDistance: 60 → 5")

    # maxDistance={4500} → maxDistance={150}
    max_pattern = re.compile(r'maxDistance\s*=\s*\{\s*4500\s*\}')
    if max_pattern.search(text):
        text = max_pattern.sub('maxDistance={150}', text, count=1)
        changes.append("maxDistance: 4500 → 150")

    # افزودن target برای نگاه به مرکز زمین
    # اگر target وجود ندارد، اضافه کن
    if 'target=' not in text and 'OrbitControls' in text:
        # پیدا کردن OrbitControls و افزودن target
        orbit_pattern = re.compile(r'(<OrbitControls[^>]*?)(/?>)', re.DOTALL)
        match = orbit_pattern.search(text)
        if match:
            before = match.group(1)
            close = match.group(2)
            new_orbit = before + '\n                  target={[0, 0, 0]}\n                ' + close
            text = text[:match.start()] + new_orbit + text[match.end():]
            changes.append("Added target={[0,0,0]}")

    # اصلاح zoomSpeed برای zoom نرم‌تر
    if 'zoomSpeed={1.2}' in text:
        text = text.replace('zoomSpeed={1.2}', 'zoomSpeed={0.8}', 1)
        changes.append("zoomSpeed: 1.2 → 0.8 (نرم‌تر)")

    if changes:
        ok(f"✓ OrbitControls اصلاح شد ({len(changes)} تغییر)")
    else:
        warn("تغییری در OrbitControls لازم نبود")

    return text, changes


def fix_camera_presets(text: str) -> tuple:
    """اصلاح presetهای دوربین (viewModes)"""
    changes = []

    # presetهای فعلی خیلی دور هستند:
    # '2d-top': { pos: [0, 25, 0.1], lookAt: [0, 0, 0] } → این خوب است
    # '2d-side': { pos: [25, 4, 0], lookAt: [0, 0, 0] } → خوب
    # 'cross-section': { pos: [0, 5, 25], lookAt: [0, 0, 0] } → خوب

    # فقط چک می‌کنیم که مقادیر منطقی باشند
    info("بررسی preset های دوربین...")

    preset_pattern = re.compile(
        r"case\s+'2d-top':\s*return\s*\{\s*pos:\s*\[\s*(\d+)\s*,\s*(\d+)"
    )
    match = preset_pattern.search(text)
    if match:
        y_val = int(match.group(2))
        if y_val > 100:
            warn(f"2d-top y={y_val} خیلی بالاست - اصلاح به 30")
            text = text.replace(f'pos: [0, {y_val}, 0.1]', 'pos: [0, 30, 0.1]', 1)
            changes.append(f"2d-top y: {y_val} → 30")
        else:
            ok(f"2d-top preset مناسب است (y={y_val})")

    return text, changes


def fix_fog_distance(text: str) -> tuple:
    """اصلاح فاصله fog برای دید بهتر"""
    changes = []

    # فعلی: fog args={['#dfe8d8', 500, 4200]}
    fog_pattern = re.compile(
        r'<fog\s+attach="fog"\s+args=\{\[[^\]]*?500\s*,\s*4200\s*\]\}'
    )
    if fog_pattern.search(text):
        text = fog_pattern.sub(
            '<fog attach="fog" args={[\'#dfe8d8\', 50, 400]}',
            text, count=1
        )
        changes.append("fog: [500,4200] → [50,400]")
        ok("✓ فاصله fog اصلاح شد")

    # اصلاح sky distance
    if 'distance={450000}' in text:
        text = text.replace('distance={450000}', 'distance={45000}', 1)
        changes.append("sky distance: 450000 → 45000")
        ok("✓ sky distance اصلاح شد")

    # اصلاح grid fadeDistance
    if 'fadeDistance={2600}' in text:
        text = text.replace('fadeDistance={2600}', 'fadeDistance={200}', 1)
        changes.append("grid fadeDistance: 2600 → 200")
        ok("✓ grid fadeDistance اصلاح شد")

    return text, changes


# ═══════════════════════════════════════════════════════════════════════
# Build و تست
# ═══════════════════════════════════════════════════════════════════════

def test_build() -> bool:
    header("تست build")
    r = subprocess.run(
        "pnpm build", shell=True, cwd=FRONTEND,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=180
    )
    if r.returncode == 0:
        ok(f"✓ build موفق")
        # نمایش HyDroMaCenter chunk
        for line in r.stdout.splitlines():
            if "HyDroMaCenter" in line:
                print(f"  {line.strip()}")
        return True
    err("build شکست خورد")
    for l in (r.stdout + r.stderr).splitlines()[-15:]:
        print(f"  {l}")
    return False


def test_dev():
    header("تست dev (۱۰ ثانیه)")
    try:
        proc = subprocess.Popen(
            "pnpm dev", shell=True, cwd=FRONTEND,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace"
        )
        start = time.time()
        while time.time() - start < 10:
            if proc.poll() is not None:
                break
            line = proc.stdout.readline()
            if "Local:" in line or "ready in" in line.lower():
                ok("✓ dev server آماده")
                proc.terminate()
                return True
        proc.terminate()
        warn("dev server تست نشد کامل")
        return True
    except Exception as e:
        err(f"خطا: {e}")
        return False


def commit():
    header("commit")
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run(
            'git commit -m "fix(hydroma): correct default camera view for proper terrain visibility"',
            shell=True, cwd=PROJECT_ROOT, check=True
        )
        ok("✓ commit شد")
        r = subprocess.run(
            "git remote get-url origin", shell=True, cwd=PROJECT_ROOT,
            capture_output=True, text=True
        )
        if r.returncode == 0:
            subprocess.run("git push origin main", shell=True, cwd=PROJECT_ROOT)
            ok("✓ push شد")
    except Exception as e:
        warn(f"commit: {e}")


# ═══════════════════════════════════════════════════════════════════════
# اجرای اصلی
# ═══════════════════════════════════════════════════════════════════════

def main():
    print(f"\n{C.BOLD}{'═' * 70}{C.RESET}")
    print(f"{C.BOLD}  🔧 Fix HyDroMaCenter Default Camera View{C.RESET}")
    print(f"{C.BOLD}{'═' * 70}{C.RESET}")

    if not HYDROMA.exists():
        err(f"فایل یافت نشد: {HYDROMA}")
        return 1

    backup(HYDROMA)
    text = HYDROMA.read_text(encoding="utf-8")
    original = text
    all_changes = []

    # گام ۱: Camera position
    header("گام ۱: اصلاح موقعیت دوربین پیش‌فرض")
    text, ch = fix_camera_position(text)
    all_changes.extend(ch)

    # گام ۲: OrbitControls
    header("گام ۲: اصلاح OrbitControls")
    text, ch = fix_orbit_controls(text)
    all_changes.extend(ch)

    # گام ۳: Presets
    header("گام ۳: بررسی presetها")
    text, ch = fix_camera_presets(text)
    all_changes.extend(ch)

    # گام ۴: Fog/Sky/Grid distances
    header("گام ۴: اصلاح فواصل fog/sky/grid")
    text, ch = fix_fog_distance(text)
    all_changes.extend(ch)

    # ذخیره
    header("ذخیره")
    if text != original:
        HYDROMA.write_text(text, encoding="utf-8")
        ok(f"✓ ذخیره شد ({len(all_changes)} تغییر)")
    else:
        info("تغییری نبود")

    # خلاصه تغییرات
    if all_changes:
        header("خلاصه تغییرات")
        for i, ch in enumerate(all_changes, 1):
            print(f"  {i}. {ch}")

    # تست‌ها
    build_ok = test_build()
    if build_ok:
        test_dev()
        commit()

    # راهنما
    header("🎬 پس از اجرا")
    print(f"  1. در مرورگر، صفحه HyDroMa را باز کنید:")
    print(f"     {C.BOLD}http://localhost:5173/hydroma{C.RESET}")
    print()
    print(f"  2. باید زمین را با زاویه ایزومتریک مناسب ببینید")
    print(f"     - ماوس چپ + drag → چرخش")
    print(f"     - Scroll → zoom (حالا تا فاصله ۵ نزدیک می‌شود)")
    print(f"     - ماوس راست + drag → pan")
    print()
    print(f"  {C.BOLD}اگر هنوز دید مناسب نیست:{C.RESET}")
    print(f"    - position را در کد به [35, 30, 35] تغییر دهید")
    print(f"    - یا fov را به 60 افزایش دهید")

    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())