# -*- coding: utf-8 -*-
"""
ref_detective.py — پیدا کردن دقیق ref هایی که هنوز تاریخچه «پاک‌شده» را نگه می‌دارند
اجرا:
    python ref_detective.py          # فقط کارآگاهی (گزارش، بدون تغییر)
    python ref_detective.py --fix    # + حذف ref های مزاحم (با تأیید) + gc + تأیید نهایی
"""
import os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for d in (r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\mingw64\bin"):
    if Path(d).is_dir() and d not in os.environ.get("PATH", ""):
        os.environ["PATH"] += os.pathsep + d

def find_git():
    for g in ("git", r"C:\Program Files\Git\cmd\git.exe"):
        try:
            if subprocess.run([g, "--version"], capture_output=True, timeout=10).returncode == 0:
                return g
        except Exception:
            continue

GIT = find_git()

def run(args, timeout=300):
    r = subprocess.run([GIT] + args, cwd=str(ROOT), capture_output=True,
                       text=True, errors="ignore", timeout=timeout)
    return r.returncode, r.stdout or "", r.stderr or ""

PURGED = [".env.backup", "engine/hydroma/config/settings.py.env-backup",
          ".venv_ghost", "_trash", "_project_history", "Analyze-Venv.ps1",
          "venv-analysis.json", "venv-local-audit.json",
          "database/models.py.bak_final_env", "tests/conftest.py.bak_final_env",
          "tests/test_db.py.bak_final_env", "services/auth/models.py.bak_final_env"]

def classify(ref):
    if ref in ("refs/heads/main", "refs/remotes/origin/main"): return "حیاتی"
    if ref.startswith("refs/heads/"):      return "شاخه-محلی"
    if ref.startswith("refs/remotes/"):    return "remote-tracking"
    if ref.startswith("refs/tags/"):       return "تگ"
    if ref == "refs/stash":                return "stash"
    if ref.startswith(("refs/original/", "refs/replace/")): return "سیستمی"
    return "سایر"

def all_refs():
    _, out, _ = run(["for-each-ref", "--format=%(refname) %(objectname:short)"])
    return [l.split() for l in out.splitlines() if l.strip()]

def culprit_commits(path):
    _, out, _ = run(["log", "--all", "--full-history", "--diff-filter=A",
                     "--format=%H", "--", path])   # ← --full-history: بدون simplify
    return [l.strip() for l in out.splitlines() if l.strip()]

def refs_containing(commit):
    _, out, _ = run(["for-each-ref", "--format=%(refname)", "--contains", commit])
    return [l.strip() for l in out.splitlines() if l.strip()]

def main():
    print("═" * 58 + "\n🕵️  ref_detective.py — کارآگاه رفرش‌ها\n" + "═" * 58)
    fix = "--fix" in sys.argv
    if GIT is None: print("❌ git پیدا نشد"); sys.exit(1)

    print("\n── تمام ref ها ──")
    refs = all_refs()
    for r in refs:
        print(f"   {r[1][:9]}  {r[0]}  [{classify(r[0])}]")

    print("\n── جستجوی کامیت‌های حامل فایل‌های پاک‌شده (با --full-history) ──")
    culprit_refs = {}
    any_found = False
    for p in PURGED:
        cs = culprit_commits(p)
        if not cs: continue
        any_found = True
        print(f"   🚨 {p}: {len(cs)} کامیت")
        for c in cs:
            for ref in refs_containing(c):
                culprit_refs.setdefault(ref, set()).add(p)
    if not any_found:
        print("   ✅ هیچ — تاریخچه واقعاً تمیز است (audit باید صفر بدهد)")
        return

    print("\n── حکم: کدام ref ها مقصرند؟ ──")
    remote_heads = set()
    if any(r[0].startswith("refs/remotes/origin/") for r in culprit_refs):
        rc, out, _ = run(["ls-remote", "--heads", "origin"])
        if rc == 0:
            remote_heads = {l.split()[1].replace("refs/heads/", "")
                            for l in out.splitlines() if l.strip()}
    for ref, files in sorted(culprit_refs.items()):
        cls = classify(ref)
        extra = ""
        if ref.startswith("refs/remotes/origin/"):
            br = ref.replace("refs/remotes/origin/", "")
            extra = " — 🌐 روی GitHub هم هست!" if br in remote_heads \
                    else " — فقط لوکال (GitHub ندارد)"
        print(f"   [{cls:14}] {ref} ← {', '.join(sorted(files))}{extra}")
        if cls == "حیاتی":
            print("      🚨🚨 این یعنی مشکل در main اصلی — فوراً گزارش دهید!")

    if not fix:
        print("\n💡 برای پاکسازی خودکار:  python ref_detective.py --fix")
        return

    print("\n── 🧹 پاکسازی (با تأیید هر مورد) ──")
    for ref in sorted(culprit_refs):
        cls = classify(ref)
        if cls == "حیاتی":
            print(f"   ⏭️  {ref} — دست نمی‌خورد (حیاتی)")
            continue
        if input(f"   حذف {ref} [{cls}]؟ (y/N): ").lower() != "y":
            print(f"      ↷ رد شد"); continue
        if cls == "شاخه-محلی":
            rc, _, e = run(["branch", "-D", ref.replace("refs/heads/", "")])
        elif cls == "تگ":
            rc, _, e = run(["tag", "-d", ref.replace("refs/tags/", "")])
        elif cls == "remote-tracking":
            br = ref.replace("refs/remotes/origin/", "")
            if br in remote_heads:
                rc, _, e = run(["push", "origin", "--delete", br])
                print(f"      {'✅ از GitHub حذف شد' if rc == 0 else '⚠️ ' + e.strip()[:80]}")
            rc, _, e = run(["update-ref", "-d", ref])
        elif cls == "stash":
            rc, _, e = run(["stash", "clear"])
        else:  # سیستمی / سایر
            rc, _, e = run(["update-ref", "-d", ref])
        print(f"      {'✅ حذف شد' if rc == 0 else '❌ ' + e.strip()[:80]}")

    print("\n── زباله‌روبی نهایی ──")
    run(["reflog", "expire", "--expire=now", "--all"])
    rc, _, _ = run(["gc", "--prune=now"])
    print("   ✅ reflog expire + gc انجام شد")

    print("\n── تأیید نهایی (این‌بار با --full-history) ──")
    clean = True
    for p in PURGED:
        if culprit_commits(p):
            print(f"   🚨 هنوز: {p}"); clean = False
    print("   ✅ همه مسیرهای پاک‌شده از کل تاریخچه حذف شدند" if clean
          else "   ⚠️ موارد بالا باقی مانده‌اند — خروجی را بفرستید")

    _, out, _ = run(["count-objects", "-vH"])
    for l in out.splitlines():
        if l.startswith(("size-pack", "count")):
            print(f"   {l.strip()}")

    print("\n📋 گام آخر:  python git_audit.py   ← انتظار: ~95 و صفر هشدار")

if __name__ == "__main__":
    main()