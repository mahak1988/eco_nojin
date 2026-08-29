# -*- coding: utf-8 -*-
"""
p1_finish.py — پایان‌بندی کامل فاز P1 (بدون هیچ کار دستی)
  ۱) تزریق PATH گیت به این پروسه (برای فرزندان مثل filter-repo)
  ۲) untrack کردن .satellite_cache (تا قواعد ignore بالاخره اثر کنند)
  ۳) کامیت تغییرات باز
  ۴) بازنویسی تاریخچه: حذف فایل‌های حساس/زباله از همه کامیت‌ها
     ← هر مسیر موجود روی دیسک، اول به _quarantine/history_purge می‌رود (هیچ‌چیز از بین نمی‌رود)
  ۵) وصل مجدد ریموت + force push
  ۶) تأیید نهایی
اجرا:
    python p1_finish.py           # عادی
    python p1_finish.py --slim    # + حذف کش‌های سنگین ماهواره از تاریخچه (~۳۴۰MB سبک‌تر شدن ریپو)
"""
import os, re, json, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
Q = ROOT / "_quarantine" / "history_purge"
GIT_DIRS = [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\mingw64\bin"]

# ── ۱) PATH برای این پروسه و همه فرزندان ──
for d in GIT_DIRS:
    if Path(d).is_dir() and d not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + d

def find_git():
    for g in ["git", r"C:\Program Files\Git\cmd\git.exe"]:
        try:
            if subprocess.run([g, "--version"], capture_output=True, timeout=10).returncode == 0:
                return g
        except Exception:
            continue

GIT = find_git()

def run(args, timeout=900):
    r = subprocess.run([GIT] + args, cwd=str(ROOT), capture_output=True,
                       text=True, errors="ignore", timeout=timeout)
    return r.returncode, r.stdout or "", r.stderr or ""

# مسیرهایی که باید از کل تاریخچه پاک شوند (اگر روی دیسک باشند → قرنطینه)
PURGE = [
    ".env.backup", ".venv_ghost", "_trash", "_project_history",
    "Analyze-Venv.ps1", "venv-analysis.json", "venv-local-audit.json",
    "engine/hydroma/config/settings.py.env-backup",
    "database/models.py.bak_final_env", "tests/conftest.py.bak_final_env",
    "tests/test_db.py.bak_final_env", "services/auth/models.py.bak_final_env",
    "htmlcov",
]

def main():
    print("═" * 58)
    print("🏁 p1_finish.py — پایان‌بندی فاز P1")
    print("═" * 58)
    if GIT is None:
        print("❌ git پیدا نشد"); sys.exit(1)
    print(f"✅ {run(['--version'])[1].strip()}")

    # ── ۲) untrack کش ماهواره ──
    print("\n── ۲) untrack .satellite_cache ──")
    _, ls, _ = run(["ls-files", "--", ".satellite_cache"])
    tracked_n = len([l for l in ls.splitlines() if l.strip()])
    if tracked_n:
        rc, _, err = run(["rm", "-r", "--cached", "-q", "--", ".satellite_cache"])
        print(f"   {'✅' if rc == 0 else '❌'} {tracked_n} فایل از ایندکس خارج شد "
              f"(روی دیسک می‌مانند) {err.strip()[:80]}")
    else:
        print("   ✅ از قبل track نیست")

    # ── ۳) کامیت تغییرات باز ──
    print("\n── ۳) کامیت تغییرات باز ──")
    run(["add", "-A"])
    _, st, _ = run(["status", "--porcelain"])
    changes = [l for l in st.splitlines() if l.strip()]
    for c in changes[:12]:
        print(f"   {c}")
    if changes:
        rc, _, err = run(["commit", "-m",
            "chore(p1): untrack satellite cache, patched audit tooling"])
        print("   ✅ کامیت شد" if rc == 0 else f"   ⚠️ {err.strip()[:120]}")
    else:
        print("   ✅ چیزی باز نبود")

    # ── ۴) بازنویسی تاریخچه ──
    print("\n── ۴) بازنویسی تاریخچه ──")
    slim = "--slim" in sys.argv
    if slim:
        PURGE.append(".satellite_cache")
        print("   🧹 حالت slim: کش‌های ماهواره هم از تاریخچه حذف می‌شوند")
    print("   ℹ️ هش همه کامیت‌ها عوض می‌شود + force push به GitHub")
    if input("   ادامه؟ (y/N): ").lower() != "y":
        print("   ↷ رد شد — فقط کامیت‌های بالا باقی مانده‌اند"); return

    bundle = f"..\\eco_nojin_pre_finish_{datetime.now():%Y%m%d_%H%M%S}.bundle"
    rc, _, err = run(["bundle", "create", bundle, "--all"])
    print(f"   {'✅ بکاپ' if rc == 0 else '⚠️ بکاپ ناموفق: ' + err.strip()[:80]} → {bundle}")

    # قرنطینه هر مسیر موجود روی دیسک (تا reset --hard آنها را پاک نکند)
    Q.mkdir(parents=True, exist_ok=True)
    moved = []
    for p in PURGE:
        src = ROOT / p
        if src.exists():
            dest = Q / p
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            moved.append(p)
    if moved:
        (Q / "MANIFEST.json").write_text(json.dumps(
            {"date": datetime.now().isoformat(), "moved": moved},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   📦 {len(moved)} مسیر به قرنطینه رفت: {', '.join(moved)}")

    args = [sys.executable, "-m", "git_filter_repo", "--force", "--invert-paths"]
    for p in PURGE:
        args += ["--path", p]
    print("   ⏳ git_filter_repo در حال اجرا (PATH تزریق‌شده ✅)...")
    if subprocess.run(args, cwd=str(ROOT)).returncode != 0:
        print("   ❌ ناموفق — بکاپ bundle موجود است؛ خروجی بالا را بفرستید"); return
    print("   ✅ تاریخچه بازنویسی شد")

    # ── ۵) ریموت + force push ──
    print("\n── ۵) ریموت + force push ──")
    if run(["remote", "get-url", "origin"])[0] != 0:
        run(["remote", "add", "origin", "https://github.com/mahak1988/eco_nojin.git"])
        print("   ✅ origin دوباره وصل شد")
    rc, out, err = run(["push", "--force", "-u", "origin", "main"])
    print("   ✅ force push انجام شد" if rc == 0 else f"   ⚠️ {(out+err).strip()[:200]}")

    # ── ۶) تأیید نهایی ──
    print("\n── ۶) تأیید نهایی ──")
    _, l1, _ = run(["log", "--all", "--oneline", "--", ".env.backup"])
    _, l2, _ = run(["log", "--all", "--oneline", "--", "_project_history"])
    print(f"   .env.backup در تاریخچه:   {'🚨' if l1.strip() else '✅ پاک شده'}")
    print(f"   _project_history:          {'🚨' if l2.strip() else '✅ پاک شده'}")
    rc, out, _ = run(["check-ignore", "-v", "--", ".satellite_cache/"])
    print(f"   check-ignore .satellite_cache/: {'✅ ' + out.strip()[:60] if rc == 0 else '🚨 هنوز!'}")
    _, n, _ = run(["rev-list", "--count", "HEAD"])
    _, t, _ = run(["ls-files"])
    print(f"   کامیت‌ها: {n.strip()} | tracked: {len(t.splitlines()):,}")
    print("\n📋 گام آخر:  python git_audit.py   ← انتظار: ~95/100 و صفر هشدار حساس")

if __name__ == "__main__":
    main()