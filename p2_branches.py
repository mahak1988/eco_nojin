# -*- coding: utf-8 -*-
"""p2_branches.py — ادامه p2_gate_fix از بخش ۳ و ۴
(باگ پیشین: پیشوند GIT در فراخوانی‌ها جا افتاده بود — این‌بار داخل خود run تزریق می‌شود)
اجرا:  python p2_branches.py
"""
import os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for d in (r"C:\Program Files\Git\cmd",):
    if Path(d).is_dir() and d not in os.environ.get("PATH", ""):
        os.environ["PATH"] += os.pathsep + d

def find_git():
    for g in ("git", r"C:\Program Files\Git\cmd\git.exe"):
        try:
            if subprocess.run([g, "--version"], capture_output=True, timeout=10).returncode == 0:
                return g
        except Exception:
            continue
    return None

GIT = find_git()

def run(args, timeout=300):
    # ✅ اصلاح باگ: GIT همیشه به‌عنوان اجرایی اول، داخل همین تابع اضافه می‌شود
    r = subprocess.run([GIT] + args, cwd=str(ROOT), capture_output=True,
                       text=True, errors="ignore", timeout=timeout)
    return r.returncode, r.stdout or "", r.stderr or ""

def main():
    if GIT is None:
        print("❌ git پیدا نشد"); sys.exit(1)
    print(f"✅ {run(['--version'])[1].strip()}")

    print("\n" + "─" * 55 + "\n🌿 شاخه‌های محلی — تست «اجدادِ main بودن»\n" + "─" * 55)
    _, cur, _ = run(["branch", "--show-current"])
    cur = cur.strip()
    _, out, _ = run(["branch", "--format=%(refname:short)"])
    branches = [l.strip() for l in out.splitlines() if l.strip() and l.strip() != cur]
    if not branches:
        print("   ✅ شاخه دیگری نیست")
    deletable = []
    for b in branches:
        rc, _, _ = run(["merge-base", "--is-ancestor", b, "main"])
        if rc == 0:
            print(f"   ✅ {b}: اجدادِ main است → همه محتوایش در main هست → حذف بی‌خطر")
            deletable.append(b)
        else:
            _, n, _ = run(["rev-list", "--count", f"main..{b}"])
            _, log, _ = run(["log", "--oneline", f"main..{b}"])
            print(f"   📌 {b}: {n.strip()} کامیت یکتا خارج از main دارد:")
            for l in log.splitlines()[:8]:
                print(f"        {l}")
            print("        → تصمیم با شما (باندل بایگانی موجود است)")
    for b in deletable:
        if input(f"   حذف «{b}»؟ (بایگانی bundle موجود) (y/N): ").lower() == "y":
            rc, _, e = run(["branch", "-D", b])
            print(f"      {'🗑️ حذف شد' if rc == 0 else '❌ ' + e.strip()[:60]}")

    print("\n" + "─" * 55 + "\n💾 کامیت ابزارها و تغییرات باز\n" + "─" * 55)
    run(["add", "-A"])
    _, st, _ = run(["status", "--porcelain"])
    files = [l for l in st.splitlines() if l.strip()]
    print(f"   {len(files)} فایل:")
    for f in files[:14]:
        print(f"   {f}")
    if files and input("   کامیت + push؟ (y/N): ").lower() == "y":
        run(["commit", "-m",
             "chore(p2): vite build gate, typecheck debt documented, audit tooling"])
        rc, _, e = run(["push", "origin", "main"])
        print("   ✅ کامیت + push انجام شد" if rc == 0 else f"   ⚠️ push: {e.strip()[:120]}")

    print("\n📋 گام بعدی (توجه: با python و .\\ ):")
    print("   python .\\p2_deps_v2.py --apply   ← دروازه حالا سبز است؛ ۲۸ پکیج حذف می‌شوند")

if __name__ == "__main__":
    main()