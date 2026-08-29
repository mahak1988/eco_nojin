# -*- coding: utf-8 -*-
"""p1_cleanup.py — پاکسازی ایمن رسوب‌های ساختاری (فاز P1)
✂️ هیچ فایلی حذف نمی‌شود | 📦 قرنطینه با MANIFEST | 🔓 untrack بکاپ‌های کد"""

import re, os, json, shutil, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
Q = ROOT / "_quarantine" / "p1"
LOG, MANIFEST, UNTRACKED = [], [], []
_cache: dict = {}

def say(m=""):
    print(m); LOG.append(m)

def find_git():
    for g in ("git", r"C:\Program Files\Git\cmd\git.exe"):
        try:
            if subprocess.run([g, "--version"], capture_output=True, timeout=10).returncode == 0:
                return g
        except Exception:
            pass

GIT = find_git()

def run(args, timeout=120):
    if not GIT: return 1, "", "git not found"
    r = subprocess.run([GIT] + args, cwd=str(ROOT), capture_output=True,
                       text=True, errors="ignore", timeout=timeout)
    return r.returncode, r.stdout or "", r.stderr or ""

SRC_DIRS = ("frontend/src", "services", "engine", "database", "tests",
            "scripts", "alembic", "contracts", "blockchain", "interfaces", "adapters")

def read_code(f: Path) -> str:
    key = str(f)
    if key not in _cache:
        try:
            _cache[key] = f.read_text(encoding="utf-8", errors="ignore") \
                if f.stat().st_size < 500_000 else ""
        except OSError:
            _cache[key] = ""
    return _cache[key]

def code_files():
    exts = {".py", ".ts", ".tsx", ".js"}
    for d in SRC_DIRS:
        base = ROOT / d
        if base.is_dir():
            for f in base.rglob("*"):
                if f.is_file() and f.suffix.lower() in exts:
                    yield f

def count_refs(token: str) -> list:
    pat = re.compile(re.escape(token))
    return [f.relative_to(ROOT).as_posix() for f in code_files() if pat.search(read_code(f))]

def quarantine(src: Path, sub: str):
    rel = src.relative_to(ROOT)
    dest = Q / sub / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    MANIFEST.append({"from": rel.as_posix(), "to": dest.relative_to(ROOT).as_posix()})

def untrack(rel: str):
    rc, _, err = run(["rm", "--cached", "-q", "--", rel])
    if rc == 0:
        UNTRACKED.append(rel)
    else:
        say(f"   ⚠️ untrack ناموفق {rel}: {err.strip()[:80]}")

SECRET_SCAN = [
    re.compile(r"(?i)(password|secret|api[_-]?key|private[_-]?key)\s*[=:]\s*['\"][^'\"]{8,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"),          # JWT
    re.compile(r"\b0x[0-9a-fA-F]{64}\b"),                                 # کلید اتریوم
    re.compile(r"postgres(ql)?://[^@\s/]+:[^@\s]+@"),                     # URL دیتابیس
]

def looks_secret(p: Path) -> bool:
    try:
        if p.stat().st_size > 500_000: return False
        t = p.read_text(encoding="utf-8", errors="ignore")
        return any(rx.search(t) for rx in SECRET_SCAN)
    except OSError:
        return False

# ─── ۱) بکاپ‌های کد: untrack + قرنطینه (+ هشدار secret) ───
def step_baks():
    say("\n── ۱) بکاپ‌های کد (*.bak_final_env / *.env-backup) ──")
    targets = list(ROOT.rglob("*.bak_final_env")) + list(ROOT.rglob("*.env-backup"))
    if not targets:
        say("   ✅ موردی نبود."); return
    for p in targets:
        rel = p.relative_to(ROOT).as_posix()
        rc, out, _ = run(["ls-files", "--", rel])
        danger = looks_secret(p)
        say(f"   • {rel} — {'🚨 مشکوک به SECRET!' if danger else 'فقط کد قدیمی'} — tracked: {bool(out.strip())}")
        if out.strip():
            untrack(rel)
        quarantine(p, "code_baks")
        if danger:
            say("      ↳ ⚠️ اگر secret واقعی است: چرخش کلید + افزودن مسیر به git filter-repo")

# ─── ۲) src/ تک‌فایلی ریشه ───
def step_src():
    say("\n── ۲) پوشه src/ ریشه (بقایای CRA) ──")
    src = ROOT / "src"
    if not src.is_dir():
        say("   ✅ وجود ندارد."); return
    files = [f for f in src.rglob("*") if f.is_file()]
    for f in files: say(f"   • {f.relative_to(ROOT)}")
    refs = [r for t in ('"src/', "'src/", "from src ") for r in count_refs(t) if not r.startswith("src/")]
    if refs:
        say(f"   ⚠️ {len(refs)} ارجاع در کد — منتقل نمی‌شود: {refs[:5]}")
    else:
        for f in files: quarantine(f, "old_root_src")
        say(f"   📦 {len(files)} فایل بدون هیچ ارجاعی → قرنطینه.")

# ─── ۳) صفحات legacy فرانت ───
def step_legacy():
    say("\n── ۳) frontend/src/pages/_legacy_models ──")
    lm = ROOT / "frontend/src/pages/_legacy_models"
    if not lm.is_dir():
        say("   ✅ وجود ندارد."); return
    refs = [r for r in count_refs("_legacy_models") if "_legacy_models" not in r]
    if refs:
        say(f"   ⚠️ هنوز {len(refs)} ارجاع دارد — دست نمی‌زنیم: {refs[:5]}")
    else:
        n = 0
        for f in lm.rglob("*"):
            if f.is_file(): quarantine(f, "legacy_models"); n += 1
        say(f"   📦 {n} فایل legacy بدون ارجاع → قرنطینه.")

# ─── ۴) پوشه عجیب analysis.json/ ───
def step_analysis():
    say("\n── ۴) پوشه analysis.json/ ──")
    aj = ROOT / "analysis.json"
    if not aj.is_dir():
        say("   ✅ پوشه نیست (درست است)."); return
    for f in list(aj.rglob("*"))[:8]:
        say(f"   • {f.relative_to(ROOT)}" + (f" ({f.stat().st_size:,} B)" if f.is_file() else "/"))
    refs = [r for r in count_refs("analysis.json") if not r.startswith("analysis.json/")]
    if refs:
        say(f"   ⚠️ کد به آن ارجاع دارد ({len(refs)} جا) — تصمیم با شما:")
        for r in refs[:5]: say(f"      ↳ {r}")
    else:
        n = 0
        for f in aj.rglob("*"):
            if f.is_file(): quarantine(f, "analysis_json_dir"); n += 1
        say(f"   📦 {n} فایل بدون هیچ ارجاعی → قرنطینه. (احتمالاً باگ mkdir در کد قدیمی)")

# ─── ۵) تشخیص: context/contexts و locales ───
def step_dupes():
    say("\n── ۵) تشخیص دوباره‌کاری‌ها (فقط گزارش) ──")
    fe = ROOT / "frontend/src"
    for name in ("context", "contexts"):
        d = fe / name
        if d.is_dir():
            n = len(list(d.rglob("*.*")))
            refs = [r for t in (f"/{name}/", f"/{name}'", f'/{name}"')
                    for r in count_refs(t) if not r.startswith(f"frontend/src/{name}")]
            say(f"   • src/{name}: {n} فایل | {len(refs)} ارجاع خارجی" +
                ("  ← ← بی‌استفاده!" if n and not refs else ""))
    for loc in ("i18n/locales", "locales"):
        d = fe / loc
        if d.is_dir():
            n = len(list(d.rglob("*.*")))
            refs = [r for r in count_refs(loc) if not r.startswith(f"frontend/src/{loc}")]
            say(f"   • src/{loc}: {n} فایل | {len(refs)} ارجاع" +
                ("  ← ← بی‌استفاده!" if n and not refs else ""))
    say("   📌 موارد «بی‌استفاده» را تأیید کنید تا در اجرای بعدی قرنطینه شوند.")

# ─── ۶) گزارش تصمیم: migration و بلاکچین ───
def step_report():
    say("\n── ۶) تصمیم‌گیری ساختاری (فقط گزارش) ──")
    for d in ("alembic", "migrations", "supabase/migrations", "services/supabase/migrations",
              "contracts", "blockchain", "services/business_modules/blockchain"):
        p = ROOT / d
        if p.is_dir():
            say(f"   • {d}/ : {len(list(p.rglob('*.*')))} فایل")
    ini = ROOT / "alembic.ini"
    if ini.is_file():
        m = re.search(r"script_location\s*=\s*(\S+)", ini.read_text(encoding="utf-8", errors="ignore"))
        if m: say(f"   ↳ alembic.ini رسمی → script_location = {m.group(1)}")
    say("   📌 یک سیستم migration و یک لایه بلاکچین را «رسمی» اعلام کنید؛ بقیه را جلسه بعد آرشیو می‌کنیم.")

def main():
    say("═" * 58)
    say("🧹 p1_cleanup.py — پاکسازی رسوب‌ها (بدون حذف هیچ فایل)")
    say("═" * 58)
    if not GIT: say("❌ git پیدا نشد — فقط بخش untrack رد می‌شود.")
    step_baks(); step_src(); step_legacy(); step_analysis(); step_dupes(); step_report()
    if MANIFEST:
        Q.mkdir(parents=True, exist_ok=True)
        (Q / "MANIFEST.json").write_text(json.dumps(
            {"date": datetime.now().isoformat(), "items": MANIFEST},
            ensure_ascii=False, indent=2), encoding="utf-8")
    if UNTRACKED:
        say(f"\n🔓 {len(UNTRACKED)} فایل از گیت خارج شد (فایل‌ها امن در قرنطینه‌اند):")
        for u in UNTRACKED: say(f"   • {u}")
    (ROOT / "P1_LOG.txt").write_text("\n".join(LOG), encoding="utf-8")
    say("\n📋 بعد از بازبینی خروجی، کامیت کنید:")
    say('   git add -A ; git commit -m "chore(p1): quarantine residue files, untrack code backups"')
    say("♻️ بازگردانی: _quarantine/p1/MANIFEST.json")

if __name__ == "__main__":
    main()