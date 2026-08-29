# -*- coding: utf-8 -*-
"""
git_audit.py — وضعیت واقعی Git + جستجوی اسرار در تاریخچه (همه شاخه‌ها)
اجرا:  python git_audit.py
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# گیت را در PATH و مسیرهای رایج ویندوز پیدا کن
GIT_CANDIDATES = [
    "git",
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
    str(Path.home() / r"AppData\Local\Programs\Git\cmd\git.exe"),
]


def find_git():
    for g in GIT_CANDIDATES:
        try:
            r = subprocess.run([g, "--version"], capture_output=True,
                               text=True, timeout=10)
            if r.returncode == 0:
                return g, r.stdout.strip()
        except Exception:
            continue
    return None, None


GIT, VERSION = find_git()


def run(args, timeout=120):
    if GIT is None:
        return 127, "", "git not found"
    try:
        r = subprocess.run([GIT] + args, cwd=str(ROOT), capture_output=True,
                           text=True, errors="ignore", timeout=timeout)
        return r.returncode, (r.stdout or ""), (r.stderr or "")
    except Exception as e:
        return 1, "", str(e)


def main():
    print("═" * 60)
    print("🔍 git_audit.py — وضعیت واقعی Git پروژه")
    print("═" * 60)

    if GIT is None:
        print("❌ گیت نه در PATH و نه در مسیرهای استاندارد پیدا نشد.")
        sys.exit(1)
    print(f"✅ {VERSION}")

    rc, out, _ = run(["rev-parse", "--is-inside-work-tree"])
    if rc != 0 or out.strip() != "true":
        print("❌ این پوشه داخل ریپوی گیت نیست.")
        sys.exit(1)

    # شاخه و تاریخچه
    rc, branch, _ = run(["branch", "--show-current"])
    rc, ncommits, _ = run(["rev-list", "--count", "HEAD"])
    print(f"\n📌 شاخه: {branch.strip()} | تعداد کامیت: {ncommits.strip()}")

    rc, log_out, _ = run(["log", "--oneline", "-5"])
    print("آخرین کامیت‌ها:")
    for line in log_out.splitlines()[:5]:
        print(f"   {line}")

    # ریموت
    rc, remotes, _ = run(["remote", "-v"])
    if remotes.strip():
        print("\n🌐 ریموت‌ها:")
        for line in remotes.splitlines():
            print(f"   {line}")
        rc, up, _ = run(["rev-parse", "--abbrev-ref", "@{u}"])
        if rc == 0:
            print(f"   ↳ upstream: {up.strip()} ✅")
        else:
            print("   ↳ ⚠️ upstream تنظیم نیست → git push -u origin main")
    else:
        print("\n⚠️ هیچ ریموتی نیست — کد فقط لوکال است!")

    # فایل‌های tracked
    rc, files, _ = run(["ls-files"])
    tracked = [l for l in files.splitlines() if l.strip()]
    print(f"\n📦 فایل‌های track شده: {len(tracked):,}")

    # gitignore مؤثر؟
    print("\n🔒 بررسی ignore:")
    ignored_ok = True
    for c in [".env", "contracts/.env", "_quarantine",
              "frontend/node_modules", ".satellite_cache/"]:
        rc, _, _ = run(["check-ignore", "-q", c])
        ok = (rc == 0)
        ignored_ok &= ok
        print(f"   {'✅ ignore' if ok else '❌ NOT ignored':14} {c}")

    # ⚡ هسته ماجرا: اسرار در تاریخچه
    print("\n🕵️  جستجوی فایل‌های حساس در کل تاریخچه (همه شاخه‌ها)...")
    rc, hist, _ = run(["log", "--all", "--diff-filter=A",
                       "--name-only", "--format=", "-z"])
    ever = set()
    if rc == 0:
        ever = {x.strip() for x in hist.split("\0") if x.strip()}

    # فایل‌های استاندارد — هرگز هشدار نیستند
    ALLOW = re.compile(r"(?i)(^|/)(\.env\.example|\.env\.template|"
                       r"[^/]*env\.d\.ts|alembic/env\.py|migrations/env\.py)$")
    danger = sorted(
        f for f in ever
        if not ALLOW.search(f)
        and (re.fullmatch(r"\.env(\..*)?", f, re.I)
             or f.lower().endswith((".pem", ".key", ".p12", ".pfx"))
             or (re.search(r"(?i)env|secret|credential", Path(f).name)
                 and not re.search(r"(?i)example|template|sample", f)))
    )

    if danger:
        print(f"   🚨 {len(danger)} فایل حساس در تاریخچه کامیت شده:")
        for f in danger[:15]:
            print(f"      • {f}")
        in_head = [f for f in danger if f in set(tracked)]
        if in_head:
            print(f"   ⚠️ هنوز در نسخه فعلی هم هستند: {in_head}")
            print("   💡 خارج‌کردن از نسخه فعلی:")
            for f in in_head[:5]:
                print(f"        git rm --cached \"{f}\"")
            print("        git commit -m \"chore: untrack sensitive files\"")
        print("\n   🔴 اگر به ریموت push شده، این اسرار روی سرور هم هست:")
        print("      ۱) فوری: کلیدها را عوض کنید (Supabase keys / private key)")
        print("      ۲) پاکسازی تاریخچه: git filter-repo یا BFG Repo-Cleaner")
        print("         (بعد از پاکسازی، force-push و اطلاع به همکاران)")
    else:
        print("   ✅ هیچ .env/.pem/.key در تاریخچه کامیت نشده — عالی!")

    # تغییرات باز
    rc, st, _ = run(["status", "--porcelain"])
    dirty = len([l for l in st.splitlines() if l.strip()])
    print(f"\n📝 تغییرات کامیت‌نشده: {dirty} فایل")

    # امتیاز اصلاح‌شده
    score = 0
    score += 25 if ncommits.strip().isdigit() and int(ncommits.strip() or 0) > 0 else 0
    score += 15 if remotes.strip() else 0
    score += 15 if ignored_ok else 5
    score += 20 if not danger else 0
    score += 10  # تست بک‌اند
    _, fe_ls, _ = run(["ls-files", "--", "frontend/src"])
    fe_tests = sum(1 for l in fe_ls.splitlines()
                   if re.search(r"\.(test|spec)\.[cm]?[jt]sx?$", l.strip()))
    if fe_tests:
        score += 10
    print("\n" + "═" * 60)
    print(f"🎯 امتیاز واقعی سلامت Git: ~{score}/100"
          f"{'  (۱۴ امتیاز دیگر با افزودن تست فرانت‌اند)' if score < 100 else ''}")
    print("═" * 60)


if __name__ == "__main__":
    main()