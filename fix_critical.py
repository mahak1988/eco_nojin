# -*- coding: utf-8 -*-
"""
fix_critical.py — رفع ایمن یافته‌های بحرانی پروژه eco_nojin + تحلیل قبل/بعد

اصول اسکریپت:
  ✂️ هیچ فایلی حذف نمی‌شود
  📦 فایل‌های خطرناک فقط به _quarantine منتقل می‌شوند (بازگشت‌پذیر با MANIFEST)
  🔒 قبل از کامیت، فایل‌های staging برای اسرار اسکن می‌شوند؛ اگر secret پیدا شود unstaged می‌شود
  📊 در پایان، امتیاز سلامت «قبل» و «بعد» محاسبه و گزارش می‌شود

اجرا:  python fix_critical.py
"""

import os
import re
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
QUARANTINE = ROOT / "_quarantine"
LOG: list = []


def log(msg: str = ""):
    print(msg)
    LOG.append(msg)


def run(args, cwd=ROOT, timeout=60):
    try:
        r = subprocess.run(args, cwd=str(cwd), capture_output=True,
                           text=True, errors="ignore", timeout=timeout)
        return r.returncode, (r.stdout or ""), (r.stderr or "")
    except Exception as e:
        return 1, "", str(e)


# ============================================================
# بخش ۱) .gitignore پروژه‌محور
# ============================================================
GITIGNORE_EXTRA = """\
# ═══ افزوده‌شده توسط fix_critical.py ({date}) ═══

# --- کش‌ها و داده‌های سنگین (~۳۴۰MB) ---
.satellite_cache/
data/maps/
data/copernicus_cache/
data/motors/cache/
data/**/cache/
*.pkl
htmlcov/
.coverage
.coverage.*

# --- بیلد C++ و artifacts ویژوال استودیو ---
engine/cpp_core/build*/
*.iobj
*.obj
*.pdb
*.ilk
*.exp
*.tlog
*.lastbuildstate
*.recipe
*.vcxproj
*.vcxproj.filters

# --- پایتون ---
__pycache__/
*.py[cod]
.venv/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# --- Node / فرانت‌اند ---
node_modules/
frontend/dist/

# --- اسرار ---
.env
.env.*
!**/.env.example
!**/.env.template

# --- بکاپ‌ها و رسوب‌ها ---
_project_history/
*.bak*
*.bak_old_test
*.bak_session_import
_quarantine/

# --- پوشه مشکوک (پوشه‌ای با پسوند json!) ---
analysis.json/
"""


def fix_gitignore():
    gi = ROOT / ".gitignore"
    existing = gi.read_text(encoding="utf-8", errors="ignore") if gi.exists() else ""
    have = {l.strip() for l in existing.splitlines()
            if l.strip() and not l.strip().startswith("#")}
    missing = [l for l in GITIGNORE_EXTRA.splitlines()
               if l.strip() and not l.strip().startswith("#")
               and l.strip() not in have and not l.startswith("!")]
    # قواعد نفی (!) جدا چون مقایسه رشته‌ای ساده کافی نیست
    neg = [l for l in GITIGNORE_EXTRA.splitlines() if l.startswith("!")]
    neg = [l for l in neg if l not in existing]
    if not missing and not neg:
        log("✅ .gitignore قبلاً کامل است — تغییری لازم نبود.")
        return
    with open(gi, "a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write(GITIGNORE_EXTRA.format(date=datetime.now().strftime("%Y-%m-%d")))
    log(f"✅ .gitignore به‌روزرسانی شد (+{len(missing)} قاعده جدید).")


# ============================================================
# بخش ۲) قرنطینه فایل‌های خطرناک (انتقال، نه حذف!)
# ============================================================
SECRET_PATTERNS = [
    ("کلید خصوصی PEM",
     re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("کلید خصوصی اتریوم (0x64hex)",
     re.compile(r"\b0x[0-9a-fA-F]{64}\b")),
    ("Access Key AWS",
     re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("JWT / Service Role",
     re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}")),
    ("کلید/رمز عمومی",
     re.compile(r"(?i)(api[_-]?key|secret|password|private[_-]?key|token)"
                r"\s*[=:]\s*['\"][^'\"]{12,}['\"]")),
]

QUAR_MOVE_PATTERNS = ["*.bak_old_test", "*.bak_session_import"]


def scan_secrets_in_file(p: Path):
    """برمی‌گرداند: لیست (نوع الگو، شماره خط، مقدار ماسک‌شده)"""
    hits = []
    try:
        if p.stat().st_size > 1_000_000:
            return hits
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return hits
    for name, pat in SECRET_PATTERNS:
        for m in pat.finditer(text):
            val = m.group(0)
            masked = val[:8] + "…(ماسک‌شده)"
            ln = text.count("\n", 0, m.start()) + 1
            hits.append((name, ln, masked))
    return hits


def fix_quarantine():
    QUARANTINE.mkdir(exist_ok=True)
    manifest, moved = [], 0

    # ۲-الف) بکاپ‌های env حاوی احتمالی اسرار
    env_baks = [ROOT / ".env.bak-20260829"] if (ROOT / ".env.bak-20260829").exists() else []
    env_baks += list(ROOT.glob(".env.bak*"))
    for p in env_baks:
        if not p.is_file():
            continue
        hits = scan_secrets_in_file(p)
        if hits:
            log(f"🚨 secret در `{p.name}` پیدا شد ({len(hits)} مورد) — قرنطینه می‌شود.")
        dest = QUARANTINE / "secrets" / p.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dest))
        manifest.append({"from": str(p.relative_to(ROOT)), "to": str(dest.relative_to(ROOT))})
        moved += 1

    # ۲-ب) فایل‌های .bak پراکنده در پروژه
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in
                       {".git", "node_modules", ".venv", "htmlcov", "_quarantine"}]
        for fn in filenames:
            if any(fn.endswith(pat.replace("*", "")) or fn == pat.lstrip("*")
                   for pat in QUAR_MOVE_PATTERNS):
                src = Path(dirpath) / fn
                rel = src.relative_to(ROOT)
                dest = QUARANTINE / "legacy_bak" / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.move(str(src), str(dest))
                    manifest.append({"from": str(rel), "to": str(dest.relative_to(ROOT))})
                    moved += 1
                except Exception as e:
                    log(f"⚠️ انتقال ناموفق {rel}: {e}")

    # ۲-ج) htmlcov (خروجی coverage — تولیدشده، کاملاً ایمن برای انتقال)
    htmlcov = ROOT / "htmlcov"
    if htmlcov.is_dir():
        dest = QUARANTINE / "htmlcov"
        if not dest.exists():
            shutil.move(str(htmlcov), str(dest))
            manifest.append({"from": "htmlcov", "to": str(dest.relative_to(ROOT))})
            moved += 1
            log("📦 پوشه htmlcov به قرنطینه منتقل شد (قابل بازگشت).")

    if manifest:
        (QUARANTINE / "MANIFEST.json").write_text(
            json.dumps({"date": datetime.now().isoformat(),
                        "note": "برای بازگرداندن هر فایل، از 'to' به 'from' جابه‌جا کنید.",
                        "items": manifest}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        log(f"✅ {moved} مورد به _quarantine منتقل شد (MANIFEST.json ثبت شد — هیچ‌چیز حذف نشده).")
    else:
        log("✅ موردی برای قرنطینه نبود.")
    return manifest


# ============================================================
# بخش ۳) Git: init + کامیت امن
# ============================================================
def fix_git():
    if (ROOT / ".git").is_dir():
        log("✅ Git از قبل موجود است.")
        return True
    if shutil.which("git") is None:
        log("❌ git نصب نیست! ابتدا از git-scm.com نصب کنید و دوباره اجرا کنید.")
        return False
    run(["git", "init"])
    # اگر هویت git تنظیم نیست، محلی (local) تنظیم می‌شود
    rc, out, _ = run(["git", "config", "user.email"])
    if rc != 0 or not out.strip():
        run(["git", "config", "--local", "user.name", "eco-nojin-dev"])
        run(["git", "config", "--local", "user.email", "dev@eco-nojin.local"])
        log("ℹ️ هویت git محلی تنظیم شد (dev@eco-nojin.local) — بعداً با "
            "`git config --global user.email` شخصی‌سازی کنید.")

    run(["git", "add", "-A"])

    # ── سپر امنیتی: اسکن فایل‌های staging شده ──
    rc, out, _ = run(["git", "diff", "--cached", "--name-only"])
    staged = [l for l in out.splitlines() if l.strip()]
    dangerous, heavy = [], []
    for rel in staged:
        p = ROOT / rel
        if not p.is_file():
            continue
        try:
            if p.stat().st_size > 50_000_000:
                heavy.append(rel)
                continue
        except OSError:
            continue
        if scan_secrets_in_file(p):
            dangerous.append(rel)

    for rel in dangerous:
        run(["git", "reset", "-q", "--", rel])
    if dangerous:
        log(f"🛑 {len(dangerous)} فایل حاوی secret از staging خارج شد:")
        for d in dangerous[:10]:
            log(f"   • {d}")
        log("   ⚠️ این فایل‌ها هنوز روی دیسک هستند! اسرار داخلشان را چرخش (rotate) کنید.")

    for rel in heavy:
        run(["git", "reset", "-q", "--", rel])
    if heavy:
        log(f"⚠️ {len(heavy)} فایل بالای ۵۰MB از staging خارج شد (مناسب گیت نیستند).")

    rc2, out2, _ = run(["git", "diff", "--cached", "--name-only"])
    n = len([l for l in out2.splitlines() if l.strip()])
    if n == 0:
        log("⚠️ هیچ فایلی برای کامیت نماند.")
        return True
    run(["git", "commit", "-m",
         "chore: initial commit — safe import by fix_critical.py"])
    log(f"✅ کامیت اولیه انجام شد ({n:,} فایل).")
    return True


# ============================================================
# بخش ۴) پیشنهاد تقسیم requirements (بدون دست‌زدن به فایل اصلی)
# ============================================================
REQ_CATEGORIES = {
    "base.txt": (
        "هسته وب/API",
        {"fastapi", "uvicorn", "starlette", "pydantic", "pydantic-settings",
         "pydantic_core", "sqlalchemy", "alembic", "geoalchemy2", "python-jose",
         "pyjwt", "passlib", "bcrypt", "python-multipart", "python-dotenv",
         "httpx", "httpcore", "requests", "jinja2", "websockets", "psycopg",
         "psycopg-binary", "structlog", "aiofiles", "email-validator",
         "cryptography", "supabase", "supabase-auth", "supabase-functions",
         "postgrest", "storage3", "realtime", "dnspython", "pytz", "tzdata",
         "typing_extensions", "anyio", "urllib3", "certifi", "packaging"}),
    "scientific.txt": (
        "GIS / هیدرولوژی / کشاورزی / بهینه‌سازی",
        {"geopandas", "rasterio", "shapely", "fiona", "pyproj", "rioxarray",
         "xarray", "netCDF4", "affine", "pysheds", "landlab", "pyswatplus",
         "aquacrop", "hbv", "pyrothc", "pyfao56", "openet-core", "osmnx",
         "pyvista", "pyvistaqt", "vtk", "pywr", "salib", "pymoo", "cvxpy",
         "highspy", "scs", "osqp", "clarabel", "qdldl", "scipy", "numpy",
         "pandas", "matplotlib", "seaborn", "earthengine-api", "sentinelhub",
         "planetary-computer", "cdsapi", "ecmwf-datastores-client", "pystac",
         "pystac-client", "pystac-core", "py-richdep", "networkx", "numba",
         "llvmlite", "statsmodels", "polars", "polars-runtime-32", "duckdb",
         "duckdb_engine", "tables", "tifffile", "sympy", "patsy", "cftime",
         "pyogrio", "pyshp", "geojson", "utm", "rfactor", "blosc2", "numexpr"}),
    "ml.txt": (
        "یادگیری ماشین / NLP",
        {"torch", "transformers", "sentence-transformers", "tokenizers",
         "safetensors", "huggingface_hub", "hf-xet", "scikit-learn",
         "scikit-image", "scikit-surprise", "keybert", "yake", "autograd",
         "segtok", "langdetect"}),
    "web3.txt": (
        "بلاکچین",
        {"web3", "eth-account", "eth-hash", "eth-keyfile", "eth-keys",
         "eth-rlp", "eth-tester", "eth-typing", "eth-utils", "eth_abi",
         "hexbytes", "rlp", "py-ecc", "ecdsa", "pycryptodome"}),
    "dev.txt": (
        "ابزارهای توسعه (فقط لوکال/CI — در پروداکشن نصب نشود)",
        {"pytest", "pytest-asyncio", "pytest-cov", "coverage", "hypothesis",
         "black", "isort", "pylint", "mypy", "mypy_extensions", "ruff",
         "bandit", "pip_audit", "pre_commit", "vulture", "autoflake", "pycln",
         "pydocstyle", "pyflakes", "pyupgrade", "eradicate", "faker",
         "types-requests", "virtualenv", "nodeenv"}),
}


def fix_requirements_split():
    src = ROOT / "requirements.txt"
    if not src.exists():
        log("⚠️ requirements.txt پیدا نشد — تقسیم رد شد.")
        return
    out_dir = ROOT / "requirements_proposal"
    out_dir.mkdir(exist_ok=True)
    buckets = {k: [] for k in REQ_CATEGORIES}
    unknown = []
    for raw in src.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "-")):
            continue
        name = re.split(r"[=<>!\[\s;]", line, 1)[0].lower().lstrip("\ufeff")
        placed = False
        for fname, (_, pkgs) in REQ_CATEGORIES.items():
            if name in pkgs:
                buckets[fname].append(line)
                placed = True
                break
        if not placed:
            unknown.append(line)
    total = 0
    for fname, (title, _) in REQ_CATEGORIES.items():
        items = buckets[fname]
        if not items:
            continue
        header = (f"# {title}\n# استخراج‌شده از requirements.txt — بازبینی کنید\n\n")
        (out_dir / fname).write_text(header + "\n".join(items) + "\n", encoding="utf-8")
        total += len(items)
    (out_dir / "00_UNREVIEWED.txt").write_text(
        "# این موارد دسته‌بندی نشدند — خودتان تکلیفشان را روشن کنید\n"
        "# (بسیاری از این‌ها dependency واسط هستند و اصلاً نباید pin شوند)\n\n"
        + "\n".join(unknown) + "\n", encoding="utf-8")
    log(f"✅ پیشنهاد تقسیم در requirements_proposal/ ساخته شد "
        f"({total} پکیج دسته‌بندی، {len(unknown)} نامشخص).")
    log("   📌 requirements.txt اصلی دست‌نخورده ماند.")


# ============================================================
# بخش ۵) تحلیل قبل/بعد + امتیاز سلامت
# ============================================================
ENDPOINT_RE = re.compile(
    r"@\w+\.(?:get|post|put|delete|patch|head|options)\(\s*[\"']([^\"']*)[\"']")


def analyze() -> dict:
    m = {"has_git": (ROOT / ".git").is_dir()}
    gi = ROOT / ".gitignore"
    content = gi.read_text(encoding="utf-8", errors="ignore").lower() if gi.exists() else ""
    critical_patterns = ["node_modules", ".venv", "__pycache__", ".env",
                         "*.pkl", "htmlcov", ".satellite_cache", "dist"]
    m["gitignore_coverage"] = sum(1 for p in critical_patterns if p in content) / len(critical_patterns)

    # فایل‌های سنگین که ignore نشده‌اند
    heavy_unignored = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in
                       {".git", "node_modules", ".venv", "_quarantine"}]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                if p.stat().st_size > 10_000_000:
                    rc, _, _ = run(["git", "check-ignore", "-q", str(p.relative_to(ROOT))])
                    if rc != 0:  # ignore نشده
                        heavy_unignored.append(p.relative_to(ROOT).as_posix())
            except OSError:
                pass
    m["heavy_unignored"] = heavy_unignored

    # اسرار در فایل‌های env فعال (نه example/template)
    secret_files = []
    for p in ROOT.glob(".env*"):
        n = p.name.lower()
        if "example" in n or "template" in n:
            continue
        if p.is_file() and scan_secrets_in_file(p):
            secret_files.append(p.name)
    for sub in ("contracts", "frontend"):
        for p in (ROOT / sub).glob(".env*"):
            n = p.name.lower()
            if "example" in n or "template" in n:
                continue
            if p.is_file() and scan_secrets_in_file(p):
                secret_files.append(f"{sub}/{p.name}")
    m["secret_env_files"] = secret_files

    # env نادیده گرفته شده؟
    m["env_ignored"] = False
    probe = ROOT / ".env"
    if probe.exists():
        rc, _, _ = run(["git", "check-ignore", "-q", ".env"])
        m["env_ignored"] = (rc == 0)

    # آمار کد
    py = tsx = ts = 0
    loc = 0
    endpoints = 0
    be_tests = fe_tests = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_root = Path(dirpath).relative_to(ROOT).as_posix()
        dirnames[:] = [d for d in dirnames if d not in
                       {".git", "node_modules", ".venv", "_quarantine", "htmlcov"}]
        if rel_root.startswith(("engine/cpp_core/build", "docs/")):
            dirnames[:] = []
            continue
        for fn in filenames:
            ext = os.path.splitext(fn)[1]
            if ext == ".py":
                py += 1
                if fn.startswith("test_"):
                    be_tests += 1
            elif ext == ".tsx":
                tsx += 1
                if fn.endswith((".test.tsx", ".spec.tsx")):
                    fe_tests += 1
            elif ext == ".ts":
                ts += 1
                if fn.endswith((".test.ts", ".spec.ts")):
                    fe_tests += 1
            else:
                continue
            p = Path(dirpath) / fn
            try:
                if p.stat().st_size > 1_000_000:
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")
                loc += text.count("\n") + 1
                if ext == ".py":
                    endpoints += len(ENDPOINT_RE.findall(text))
            except OSError:
                pass
    m.update({"py": py, "tsx": tsx, "ts": ts, "loc": loc,
              "endpoints": endpoints, "tests_backend": be_tests,
              "tests_frontend": fe_tests})

    # تعداد فایل‌های track شده
    m["tracked_files"] = 0
    if m["has_git"]:
        rc, out, _ = run(["git", "ls-files"])
        m["tracked_files"] = len([l for l in out.splitlines() if l.strip()])
    return m


def health_score(m: dict) -> tuple:
    score, notes = 0, []
    if m["has_git"]:
        score += 25
    else:
        notes.append("گیت مقداردهی نشده (۲۵ امتیاز)")
    score += int(15 * m["gitignore_coverage"])
    if m["gitignore_coverage"] < 1:
        notes.append(f".gitignore ناقص ({m['gitignore_coverage']*100:.0f}٪) — ۱۵ امتیاز")
    if not m["secret_env_files"]:
        score += 20
    else:
        notes.append(f"فایل env مشکوک به secret: {', '.join(m['secret_env_files'])} — ۲۰ امتیاز")
    if not m["heavy_unignored"]:
        score += 15
    else:
        notes.append(f"{len(m['heavy_unignored'])} فایل سنگین ignore نشده — ۱۵ امتیاز")
    if m["env_ignored"]:
        score += 10
    else:
        notes.append(".env از گیت پنهان نیست — ۱۰ امتیاز")
    if m["tests_backend"] > 0:
        score += 5
    if m["tests_frontend"] > 0:
        score += 10
    else:
        notes.append("تست فرانت‌اند صفر است — ۱۰ امتیاز")
    return min(score, 100), notes


# ============================================================
# بخش ۶) نقشه اقدامات دستی
# ============================================================
ACTION_PLAN = """\
# 🗺️ نقشه اقدامات باقی‌مانده (نیازمند تصمیم انسانی)

## 🔴 اولویت بالا
- [ ] **چرخش اسرار:** اگر `.env.bak` یا `contracts/.env` قبلاً جایی به اشتراک گذاشته شده،
      کلیدهای Supabase / private key بلاکچین را عوض کنید.
- [ ] `contracts/.env` بررسی شود (private key هاردهت) — مطمئن شوید فقط در گیت ignored است نه حذف.

## 🟠 پاکسازی رسوب‌ها (بعد از بازبینی — دستورات پیشنهادی)
- [ ] `analysis.json/` پوشه است نه فایل! محتوایش را ببینید:
      `Get-ChildItem "analysis.json" -Recurse`
- [ ] پوشه `src/` تک‌فایلی ریشه (بقایای CRA):
      `Move-Item src\\* _quarantine\\old_src\\ -Force` (بعد از ساخت پوشه)
- [ ] یکی‌کردن `frontend/src/context/` و `contexts/`:
      `Select-String -Path frontend\\src\\**\\*.ts*,frontend\\src\\**\\*.tsx -Pattern "from ['\\"].*context" -List`
- [ ] کدام locales استفاده می‌شود؟ `i18n/locales` یا `locales`؟ بالا را ببینید.
- [ ] ۴ سیستم مهاجرت موازی (`alembic/`, `migrations/`, `supabase/migrations/`,
      `services/supabase/migrations/`) → یکی رسمی تعیین و بقیه آرشیو شوند.
- [ ] ۳ لایه بلاکچین (`contracts/`, `blockchain/`, `services/business_modules/blockchain/`) → تجمیع.
- [ ] `frontend/src/pages/_legacy_models/` → برنامه حذف/ادغام.

## 🟡 کیفیت کد (تدریجی)
- [ ] مهاجرت ۴۲۱ مورد `print()` به `structlog` (نصب دارید).
      شروع: `git grep -n "print(" -- "*.py" | Measure-Object -Line`
- [ ] `engine/hydroma/config/settings.py` — آدرس‌های localhost از env خوانده شوند:
      ```python
      # قبل:  BACKEND_URL = "http://localhost:8000"
      # بعد:
      from pydantic_settings import BaseSettings
      class Settings(BaseSettings):
          backend_url: str = "http://localhost:8000"
          class Config: env_file = ".env"
      ```
- [ ] `passlib==1.7.4` قدیمی است — در ارتقای بعدی با `bcrypt` مستقیم جایگزین شود.
- [ ] `python-jose` و `PyJWT` هر دو نصب‌اند — یکی کافی است (PyJWT توصیه می‌شود).

## 🔵 فرانت‌اند
- [ ] نصب تست: `pnpm add -D vitest @testing-library/react @testing-library/jest-dom jsdom`
      و اولین تست برای `components/payment` (درگاه پرداخت = بالاترین ریسک).
- [ ] `pnpm dlx depcheck` → حذف `georaster-layer-for-leaflet`، `terraformer`،
      `@types/mapbox-gl` (اگر تأیید شد).
- [ ] `pnpm dlx vite-bundle-visualizer` → بررسی باندل.

## 📦 داده‌ها
- [ ] `data/` و کش‌ها الان از گیت خارج‌اند (درست است)، ولی برای استقرار سرور باید
      استراتژی sync داده داشته باشید (S3/MinIO یا اسکریپت restore).
- [ ] `pnpm-lock.yaml` کامیت شده؟ بررسی: `git ls-files frontend | findstr lock`
"""


# ============================================================
# main
# ============================================================
def main():
    t0 = datetime.now()
    log("═" * 60)
    log("🛠️  fix_critical.py — رفع ایمن یافته‌های بحرانی")
    log("═" * 60)

    log("\n── ۱) تحلیل «قبل» ──")
    before = analyze()
    score_before, _ = health_score(before)
    log(f"   امتیاز سلامت قبل: {score_before}/100")

    log("\n── ۲) اصلاح .gitignore ──")
    fix_gitignore()

    log("\n── ۳) قرنطینه فایل‌های خطرناک (بدون حذف) ──")
    fix_quarantine()

    log("\n── ۴) راه‌اندازی Git + کامیت امن ──")
    fix_git()

    log("\n── ۵) تولید requirements_proposal/ ──")
    fix_requirements_split()

    log("\n── ۶) تحلیل «بعد» ──")
    after = analyze()
    score_after, notes = health_score(after)

    # ── ذخیره گزارش‌ها ──
    (ROOT / "ACTION_PLAN.md").write_text(ACTION_PLAN, encoding="utf-8")
    (ROOT / "FIX_LOG.txt").write_text("\n".join(LOG), encoding="utf-8")

    def fmt(m):
        return (f"git={'✅' if m['has_git'] else '❌'} | "
                f"tracked={m['tracked_files']:,} | py={m['py']} | "
                f"tsx={m['tsx']} | LOC={m['loc']:,} | "
                f"endpoints={m['endpoints']} | tests={m['tests_backend']}/{m['tests_frontend']}")

    report = f"""\
# 🛠️ گزارش رفع یافته‌های بحرانی — {datetime.now():%Y-%m-%d %H:%M}

## امتیاز سلامت
| وضعیت | امتیاز |
|---|---|
| قبل | {score_before}/100 |
| **بعد** | **{score_after}/100** |
| تغییر | {'📈 +' if score_after >= score_before else '📉 '}{score_after - score_before} |

## جزئیات قبل/بعد
| سنجه | قبل | بعد |
|---|---|---|
| Git | {'موجود' if before['has_git'] else 'نداشت ❌'} | {'موجود ✅' if after['has_git'] else 'نداشت'} |
| فایل‌های track شده | {before['tracked_files']:,} | {after['tracked_files']:,} |
| پوشش .gitignore | {before['gitignore_coverage']*100:.0f}٪ | {after['gitignore_coverage']*100:.0f}٪ |
| فایل env مشکوک به secret | {len(before['secret_env_files'])} | {len(after['secret_env_files'])} |
| فایل سنگین ignore‌نشده | {len(before['heavy_unignored'])} | {len(after['heavy_unignored'])} |

## باقی‌مانده (اقدام دستی)
{chr(10).join('- [ ] ' + n for n in notes) or '- هیچ ✅'}

→ جزئیات کامل: **ACTION_PLAN.md**
→ بازگرداندن فایل‌های قرنطینه: **_quarantine/MANIFEST.json**
"""
    (ROOT / "FIX_REPORT.md").write_text(report, encoding="utf-8")

    log("\n" + "═" * 60)
    log(f"📊 قبل:  {fmt(before)}")
    log(f"📊 بعد:  {fmt(after)}")
    log(f"🎯 امتیاز سلامت: {score_before}/100 → {score_after}/100")
    if notes:
        log("\nباقی‌مانده (نیازمند تصمیم شما):")
        for n in notes:
            log(f"   • {n}")
    log("\n📄 گزارش‌ها: FIX_REPORT.md | ACTION_PLAN.md | FIX_LOG.txt")
    log("♻️  بازگردانی: _quarantine/MANIFEST.json را ببینید")
    log("═" * 60)


if __name__ == "__main__":
    main()