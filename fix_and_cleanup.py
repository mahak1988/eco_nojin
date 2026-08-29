# -*- coding: utf-8 -*-
"""
fix_and_cleanup.py — (۱) وصله SyntaxError خودکار p2_deps_v2.py
                    (۲) همگام‌سازی رفرش‌ها بعد از حذف شاخه‌ها از GitHub
                    (۳) بایگانی (bundle) و حذف شاخه‌های محلی قدیمی با تأیید
اجرا:  python fix_and_cleanup.py
"""
import os, py_compile, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
Q = ROOT / "_quarantine" / "branches"
P2 = ROOT / "p2_deps_v2.py"

for d in (r"C:\Program Files\Git\cmd",):
    if Path(d).is_dir() and d not in os.environ.get("PATH", ""):
        os.environ["PATH"] += os.pathsep + d

GIT = None

# ─────────── ۱) وصله p2_deps_v2.py ───────────
BROKEN = '                return g\n\ndef find_pnpm():'
FIXED = ('                return g\n'
         '        except Exception:\n'
         '            continue\n'
         '    return None\n\n'
         'def find_pnpm():')

def patch_p2() -> bool:
    print("\n── ۱) وصله p2_deps_v2.py (except جاافتاده من) ──")
    if not P2.exists():
        print("   ❌ فایل پیدا نشد"); return False
    src = P2.read_text(encoding="utf-8")
    if "continue\n    return None" in src:
        print("   ✅ قبلاً سالم است")
    elif BROKEN in src:
        P2.write_text(src.replace(BROKEN, FIXED), encoding="utf-8")
        print("   ✅ except جاافتاده به find_git اضافه شد")
    else:
        print("   ⚠️ الگو match نشد — این بخش از فایل شما:")
        for i, l in enumerate(src.splitlines()[24:44], start=25):
            print(f"   {i:3}| {l}")
        return False
    try:
        py_compile.compile(str(P2), doraise=True)
        print("   ✅ کامپایل موفق — اسکریپت آماده اجراست")
        return True
    except py_compile.PyCompileError as e:
        print(f"   ❌ هنوز خطا دارد:\n   {e}"); return False

# ─────────── ۲) همگام‌سازی رفرش‌ها ───────────
def find_git():
    for g in ("git", r"C:\Program Files\Git\cmd\git.exe"):
        try:
            if subprocess.run([g, "--version"], capture_output=True, timeout=10).returncode == 0:
                return g
        except Exception:
            continue
    return None

def run(args, timeout=300):
    r = subprocess.run([GIT] + args, cwd=str(ROOT), capture_output=True,
                       text=True, errors="ignore", timeout=timeout)
    return r.returncode, r.stdout or "", r.stderr or ""

def sync_refs():
    print("\n── ۲) همگام‌سازی بعد از حذف شاخه‌ها در GitHub ──")
    rc, _, err = run(["fetch", "origin", "--prune"])
    print("   ✅ fetch --prune — remote-tracking های یتیم پاک شدند" if rc == 0
          else f"   ⚠️ {err.strip()[:120]}")
    _, heads, _ = run(["ls-remote", "--heads", "origin"])
    remote = sorted(l.split()[1].replace("refs/heads/", "")
                    for l in heads.splitlines() if l.strip())
    print(f"   🌐 شاخه‌های GitHub: {', '.join(remote) or '—'}")

# ─────────── ۳) بایگانی + حذف شاخه‌های محلی ───────────
def archive_branches():
    print("\n── ۳) شاخه‌های محلی قدیمی (اول بایگانی، بعد حذف با تأیید) ──")
    _, cur, _ = run(["branch", "--show-current"])
    cur = cur.strip()
    _, out, _ = run(["branch", "--format=%(refname:short)"])
    others = [l.strip() for l in out.splitlines() if l.strip() and l.strip() != cur]
    if not others:
        print("   ✅ شاخه محلی دیگری وجود ندارد"); return
    Q.mkdir(parents=True, exist_ok=True)
    for b in others:
        _, st, _ = run(["diff", "--shortstat", f"main..{b}"])
        stat = (st or "").strip()
        print(f"\n   • {b}  →  {stat or 'محتوا با main یکسان'}")
        bundle = Q / f"branch_{b.replace('/', '_')}.bundle"
        if not bundle.exists():
            rc, _, e = run(["bundle", "create", str(bundle), b])
            print(f"      {'💾 بایگانی: ' + bundle.name if rc == 0 else '⚠️ بایگانی نشد: ' + e.strip()[:60]}")
        if stat:  # تفاوت محتوایی دارد
            print("      📌 تفاوت واقعی دارد — حذف نمی‌شود؛ خروجی را بفرستید")
            continue
        if input(f"      حذف شاخه محلی «{b}»؟ (بایگانی موجود) (y/N): ").lower() == "y":
            rc, _, e = run(["branch", "-D", b])
            print(f"      {'✅ حذف شد' if rc == 0 else '❌ ' + e.strip()[:80]}")
    _, tags, _ = run(["tag"])
    if "phase-a-complete" in tags.split():
        if input("\n   حذف تگ phase-a-complete؟ (y/N): ").lower() == "y":
            run(["tag", "-d", "phase-a-complete"])
            rc, _, _ = run(["push", "origin", "--delete", "phase-a-complete"])
            print("   ✅ تگ از لوکال و GitHub حذف شد" if rc == 0
                  else "   ✅ تگ لوکال حذف شد (روی GitHub نبود)")

def main():
    global GIT
    print("═" * 58)
    print("🔧 fix_and_cleanup.py — وصله + همگام‌سازی + بایگانی شاخه‌ها")
    print("═" * 58)
    GIT = find_git()
    if GIT is None:
        print("❌ git پیدا نشد"); sys.exit(1)
    print(f"✅ {run(['--version'])[1].strip()}")
    ok = patch_p2()
    sync_refs()
    archive_branches()
    print("\n📋 گام بعدی:")
    if ok:
        print("   python p2_deps_v2.py            # گزارش اصلاح‌شده وابستگی‌ها")
        print("   python p2_deps_v2.py --apply    # حذف + build/test + رول‌بک خودکار")
    print("   python git_audit.py             # تأیید اینکه ۹۵ حفظ شده")

if __name__ == "__main__":
    main()