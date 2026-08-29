# -*- coding: utf-8 -*-
"""
patch_audit.py — وصله خودکار git_audit.py + تحلیل locales + عیب‌یابی ignore
اجرا:
    python patch_audit.py            # وصله + تحلیل (بدون تغییر تاریخچه)
    python patch_audit.py --rewrite  # + بازنویسی تاریخچه (با تأیید و بکاپ)
"""
import re, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIT, GI = ROOT / "git_audit.py", ROOT / ".gitignore"
FE_SRC = ROOT / "frontend" / "src"
GIT_CANDIDATES = ["git", r"C:\Program Files\Git\cmd\git.exe"]

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

# ───────────── ۱) وصله‌های git_audit.py ─────────────
OLD_DANGER = r'''    danger = sorted(
        f for f in ever
        if re.fullmatch(r"\.env(\..*)?", f, re.I)
        or f.lower().endswith((".pem", ".key", ".p12", ".pfx"))
        or (re.search(r"(?i)env|secret|credential", Path(f).name)
            and not re.search(r"(?i)example|template|sample", f))
    )'''

NEW_DANGER = r'''    # فایل‌های استاندارد — هرگز هشدار نیستند
    ALLOW = re.compile(r"(?i)(^|/)(\.env\.example|\.env\.template|"
                       r"[^/]*env\.d\.ts|alembic/env\.py|migrations/env\.py)$")
    danger = sorted(
        f for f in ever
        if not ALLOW.search(f)
        and (re.fullmatch(r"\.env(\..*)?", f, re.I)
             or f.lower().endswith((".pem", ".key", ".p12", ".pfx"))
             or (re.search(r"(?i)env|secret|credential", Path(f).name)
                 and not re.search(r"(?i)example|template|sample", f)))
    )'''

OLD_IGNORE = r'''    for c in [".env", "contracts/.env", "_quarantine", "htmlcov",
              "frontend/node_modules", ".satellite_cache"]:'''

NEW_IGNORE = r'''    for c in [".env", "contracts/.env", "_quarantine",
              "frontend/node_modules", ".satellite_cache/"]:'''

OLD_SCORE = r'''    score += 10  # تست بک‌اند (66+ فایل دارید)
    # تست فرانت‌اند: 0 → 10 امتیاز از دست می‌رود'''

NEW_SCORE = r'''    score += 10  # تست بک‌اند
    _, fe_ls, _ = run(["ls-files", "--", "frontend/src"])
    fe_tests = sum(1 for l in fe_ls.splitlines()
                   if re.search(r"\.(test|spec)\.[cm]?[jt]sx?$", l.strip()))
    if fe_tests:
        score += 10'''

def apply_patches():
    if not AUDIT.exists():
        print("   ❌ git_audit.py پیدا نشد"); return
    src = AUDIT.read_text(encoding="utf-8")
    shutil.copy2(AUDIT, AUDIT.with_suffix(".py.bak"))
    for old, new, title in [(OLD_DANGER, NEW_DANGER, "whitelist فایل‌های استاندارد"),
                            (OLD_IGNORE, NEW_IGNORE, "چک‌لیست ignore"),
                            (OLD_SCORE, NEW_SCORE, "امتیازدهی تست فرانت‌اند")]:
        if new.strip() in src:
            print(f"   ↷ {title}: قبلاً اعمال شده")
        elif old in src:
            src = src.replace(old, new)
            print(f"   ✅ {title}")
        else:
            print(f"   ⚠️ {title}: متن مرجع یافت نشد — دست‌نخورده ماند")
    AUDIT.write_text(src, encoding="utf-8")

# ───────────── ۲) تحلیل locales (بدون دام quoting) ─────────────
SPEC = re.compile(r"""(?:from|import)\s*\(?\s*['"]([^'"]*locales[^'"]*)['"]""")

def locale_analysis():
    print("\n── ۲) تحلیل واقعی imports لوکال‌ها ──")
    if not FE_SRC.is_dir():
        print("   ⚠️ frontend/src نیست"); return
    i18n_users, src_users, other = [], [], []
    for f in sorted(list(FE_SRC.rglob("*.ts")) + list(FE_SRC.rglob("*.tsx"))):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = f.relative_to(FE_SRC).as_posix()
        for m in SPEC.finditer(text):
            spec = m.group(1)
            if spec.startswith("."):
                try:
                    r = (f.parent / spec).resolve().relative_to(FE_SRC).as_posix()
                except ValueError:
                    r = "؟"
                if r.startswith("i18n/locales"):
                    i18n_users.append(f"{rel} → '{spec}'")
                elif r == "locales" or r.startswith("locales/"):
                    src_users.append(f"{rel} → '{spec}'")
                else:
                    other.append(f"{rel} → '{spec}'")
            else:
                other.append(f"{rel} → '{spec}' (پکیج/alias)")
    print(f"   i18n/locales : {len(i18n_users)} مصرف‌کننده")
    for x in i18n_users[:5]: print(f"      • {x}")
    print(f"   src/locales  : {len(src_users)} مصرف‌کننده")
    for x in src_users[:8]: print(f"      • {x}")
    for x in other[:5]: print(f"      ~ {x}")
    print("   🎯 حکم: " + (
        "هر دو پوشه زنده‌اند — هیچ‌کدام قرنطینه نشود" if i18n_users and src_users
        else "i18n/locales زنده ✅ | src/locales مرده → در اجرای بعدی p1 قرنطینه می‌شود" if i18n_users
        else "src/locales زنده ✅ | i18n/locales فقط داخلی است" if src_users
        else "هیچ import مستقیمی نیست — بررسی عمیق‌تر لازم"))

# ───────────── ۳) عیب‌یابی ignore ─────────────
def ignore_diagnostics():
    print("\n── ۳) git check-ignore -v ──")
    targets = [".env", "_quarantine/", "frontend/node_modules/", ".satellite_cache/"]
    need_fix = []
    for t in targets:
        rc, out, _ = run(["check-ignore", "-v", "--", t])
        if rc == 0 and out.strip():
            print(f"   ✅ {t:26} ← {out.strip()}")
        else:
            print(f"   ❌ {t:26} — قاعده‌ای match نشد")
            need_fix.append(t)
    if need_fix:
        with open(GI, "a", encoding="utf-8") as f:
            f.write(f"\n# افزوده توسط patch_audit.py — {datetime.now():%Y-%m-%d}\n")
            for t in need_fix:
                f.write(t + "\n")
        print(f"   🔧 قواعد تازه اضافه شد: {need_fix}")
        for t in need_fix:
            rc, out, _ = run(["check-ignore", "-v", "--", t])
            print(f"   {'✅' if rc == 0 else '🚨'} دوباره: {t} {out.strip()[:60]}")

# ───────────── ۴) تاریخچه (+ بازنویسی اختیاری) ─────────────
def history_dirty():
    _, out, _ = run(["log", "--all", "--oneline", "--", ".env.backup"])
    return out.strip()

def rewrite_history():
    print("\n── ۴) بازنویسی تاریخچه ──")
    print("   ℹ️ پروسه‌های سرور python (uvicorn و...) را ببندید تا فایل‌های db قفل نشوند.")
    if input("   ⚠️ هش همه کامیت‌ها عوض می‌شود + force push. ادامه؟ (y/N): ").lower() != "y":
        print("   ↷ رد شد"); return
    bundle = f"..\\eco_nojin_pre_rewrite_{datetime.now():%Y%m%d_%H%M%S}.bundle"
    rc, _, err = run(["bundle", "create", bundle, "--all"])
    print(f"   {'✅ بکاپ' if rc == 0 else '⚠️ بکاپ ناموفق: ' + err.strip()[:80]} → {bundle}")
    av = ROOT / "Analyze-Venv.ps1"
    if av.exists():
        q = ROOT / "_quarantine" / "p1"; q.mkdir(parents=True, exist_ok=True)
        shutil.move(str(av), str(q / av.name))
        print("   📦 Analyze-Venv.ps1 → قرنطینه (نگه داشته شد)")
    purge = [".env.backup", ".venv_ghost", "_trash", "Analyze-Venv.ps1",
             "engine/hydroma/config/settings.py.env-backup",
             "database/models.py.bak_final_env", "tests/conftest.py.bak_final_env",
             "tests/test_db.py.bak_final_env", "services/auth/models.py.bak_final_env"]
    args = [sys.executable, "-m", "git_filter_repo", "--force", "--invert-paths"]
    for p in purge: args += ["--path", p]
    print("   ⏳ filter-repo...")
    if subprocess.run(args, cwd=str(ROOT)).returncode != 0:
        print("   ❌ ناموفق — بکاپ bundle موجود است"); return
    if run(["remote", "get-url", "origin"])[0] != 0:
        run(["remote", "add", "origin", "https://github.com/mahak1988/eco_nojin.git"])
    rc, out, err = run(["push", "--force", "-u", "origin", "main"])
    print("   ✅ force push انجام شد" if rc == 0 else f"   ⚠️ push: {(out+err).strip()[:150]}")
    print("   " + ("✅ تأیید نهایی: .env.backup از تاریخچه پاک شد" if not history_dirty()
                   else "🚨 هنوز در تاریخچه است!"))

def main():
    print("═" * 58 + "\n🩹 patch_audit.py — وصله خودکار + تحلیل\n" + "═" * 58)
    if GIT is None:
        print("❌ git پیدا نشد"); sys.exit(1)
    print(f"✅ {run(['--version'])[1].strip()}")
    print("\n── ۱) وصله git_audit.py ──")
    apply_patches()
    locale_analysis()
    ignore_diagnostics()
    print("\n── ۴) وضعیت تاریخچه ──")
    if history_dirty():
        print("   .env.backup: 🚨 هنوز در تاریخچه")
        if "--rewrite" in sys.argv:
            rewrite_history()
        else:
            print("   💡 بازنویسی خودکار:  python patch_audit.py --rewrite")
    else:
        print("   ✅ .env.backup پاک شده — نیازی به بازنویسی نیست")
    print("\n📋 گام بعدی:  python git_audit.py")

if __name__ == "__main__":
    main()