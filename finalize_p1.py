# -*- coding: utf-8 -*-
"""finalize_p1.py — تکمیل کارهای نیمه‌تمام P1 (مستقل از PATH)"""

import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GIT_CANDIDATES = ["git", r"C:\Program Files\Git\cmd\git.exe",
                  r"C:\Program Files (x86)\Git\cmd\git.exe"]

def find_git():
    for g in GIT_CANDIDATES:
        try:
            if subprocess.run([g, "--version"], capture_output=True, timeout=10).returncode == 0:
                return g
        except Exception:
            continue

GIT = find_git()

def run(args, timeout=600):
    r = subprocess.run([GIT] + args, cwd=str(ROOT), capture_output=True,
                       text=True, errors="ignore", timeout=timeout)
    return r.returncode, r.stdout or "", r.stderr or ""

def section(t):
    print("\n" + "─" * 55 + f"\n{t}\n" + "─" * 55)

def main():
    if GIT is None:
        print("❌ git پیدا نشد"); sys.exit(1)
    print(f"✅ استفاده از: {GIT}")

    section("۱) git fsck — سلامت ریپو بعد از کرش filter-repo")
    rc, out, err = run(["fsck", "--full"])
    lines = [l for l in (out + err).splitlines() if l.strip()]
    bad = [l for l in lines if not l.startswith(("dangling", "unreachable", "Checking", "notice"))]
    print("✅ ریپو سالم است" if (rc == 0 and not bad)
          else "⚠️ موارد fsck:\n   " + "\n   ".join(lines[:12]))

    section("۲) reflog expire + gc — تکمیل پاکسازی ناتمام")
    run(["reflog", "expire", "--expire=now", "--all"])
    rc, out, err = run(["gc", "--prune=now"])
    print("✅ انجام شد" if rc == 0 else f"⚠️ {(out + err).strip()[:200]}")

    section("۳) تأیید حذف .env.backup از تاریخچه")
    _, env_out, _ = run(["log", "--all", "--oneline", "--", ".env.backup"])
    env_clean = not env_out.strip()
    print("✅ پاک شده" if env_clean else f"🚨 هنوز هست:\n{env_out}")

    section("۴) untrack دیتابیس SQLite")
    _, out, _ = run(["ls-files", "--", "data/"])
    dbs = [l.strip() for l in out.splitlines() if re.search(r"\.db(-shm|-wal)?$", l.strip())]
    for f in dbs:
        rc, _, e = run(["rm", "--cached", "--", f])
        print(f"   {'✅' if rc == 0 else '⚠️'} untracked: {f} {e.strip()[:60]}")
    if not dbs:
        print("✅ فایل db ای tracked نیست")

    gi = ROOT / ".gitignore"
    if gi.exists() and "*.db-shm" not in gi.read_text(encoding="utf-8", errors="ignore"):
        with open(gi, "a", encoding="utf-8") as f:
            f.write("\n*.db\n*.db-shm\n*.db-wal\n")
        print("✅ قواعد db به .gitignore اضافه شد")

    section("۵) مقایسه با ریموت")
    rc, _, err = run(["fetch", "origin", "--prune"])
    if rc != 0:
        print(f"⚠️ fetch: {err.strip()[:120]}")
    _, local, _ = run(["rev-parse", "main"])
    _, remote, _ = run(["rev-parse", "origin/main"])
    if local.strip() and remote.strip():
        if local.strip() == remote.strip():
            print("✅ main لوکال == origin/main")
        else:
            print(f"   main:        {local.strip()[:12]}\n   origin/main: {remote.strip()[:12]} → push لازم")

    section("۶) کامیت تغییرات باز + push")
    run(["add", "-A"])
    _, st, _ = run(["status", "--porcelain"])
    changes = [l for l in st.splitlines() if l.strip()]
    print(f"   {len(changes)} فایل:")
    for c in changes[:15]:
        print(f"   {c}")
    if changes:
        rc, _, err = run(["commit", "-m",
            "chore(p1): untrack sqlite db, ignore rules, quarantine residue"])
        print("✅ کامیت شد" if rc == 0 else f"⚠️ {err.strip()[:150]}")

    rc, out, err = run(["push", "origin", "main"])
    combined = (out + err).lower()
    if rc != 0 and "rejected" in combined:
        if env_clean:
            rc, out, err = run(["push", "--force", "origin", "main"])
        else:
            print("⛔ push رد شد و تاریخچه هنوز آلوده است — اول filter-repo را کامل کنید")
    print(f"{'✅ push انجام شد' if rc == 0 else '⚠️'} {(out + err).strip()[:250]}")

    section("جمع‌بندی")
    _, n, _ = run(["rev-list", "--count", "HEAD"])
    _, t, _ = run(["ls-files"])
    print(f"   کامیت‌ها: {n.strip()} | tracked: {len(t.splitlines()):,}")
    print("   .env.backup در تاریخچه: " + ("🚨 هنوز!" if not env_clean else "✅ پاک شده"))

if __name__ == "__main__":
    main()