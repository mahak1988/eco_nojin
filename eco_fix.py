#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v5.

verify | canonical .gitignore (+ live tests) | fix admin_assistant syntax |
fix Flask-style reporting routes | recon phase-2 files |
history surgery (EXPLICIT confirmation only).

Usage:
    python eco_fix.py                     # all safe steps
    python eco_fix.py verify
    python eco_fix.py audit
    python eco_fix.py fix-assistant
    python eco_fix.py fix-reporting
    python eco_fix.py recon
    python eco_fix.py history-surgery CONFIRM
"""
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

GIT_EXE = None
for _c in (r"C:\Program Files\Git\cmd\git.exe",
           r"C:\Program Files (x86)\Git\cmd\git.exe",
           r"C:\Program Files\Git\bin\git.exe"):
    if Path(_c).exists():
        GIT_EXE = _c
        break

LINE = "=" * 62

def out(*a, **kw): print(*a, flush=True, **kw)
def ok(m): out(f"[ OK ] {m}")
def warn(m): out(f"[WARN] {m}")
def fail(m): out(f"[FAIL] {m}")

def sh(cmd, timeout=900, input=None):
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=timeout, input=input)

def git(*a, **kw):
    if GIT_EXE is None:
        raise RuntimeError("git.exe not found")
    return sh([GIT_EXE, *a], **kw)

# ------------------------------------------------------------- constants ---
CANONICAL_GITIGNORE = """\
# ==============================================================================
# eco_nojin .gitignore — canonical (managed by eco_fix.py)
# ==============================================================================

# --- 1. Environment & secrets ---
.env
.env.local
.env.*.local
!.env.example
!.env.template
secrets/
*.key
*.pem
*.p12
*.pfx
*.local

# --- 2. OS junk ---
.DS_Store
Thumbs.db
ehthumbs.db
Desktop.ini
._*
.Spotlight-V100
.Trashes

# --- 3. IDE ---
.vscode/
!.vscode/settings.json
!.vscode/extensions.json
.idea/
*.swp
*.swo
*~
.project
.classpath
.settings/
*.sublime-project
*.sublime-workspace

# --- 4. Python ---
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
/build/
/develop-eggs/
/dist/
/downloads/
/eggs/
/.eggs/
/parts/
/sdist/
/var/
/wheels/
*.egg-info/
.installed.cfg
*.egg
.venv/
venv/
/env/
/ENV/
.ipynb_checkpoints/
.pytest_cache/
.tox/
.nox/
.coverage
coverage/
htmlcov/
/html/
test-results/
playwright-report/
blob-report/
playwright/.cache/
.playwright-artifacts/
frontend/test-results/
frontend/playwright-report/

# --- 5. Node / pnpm / turbo ---
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
.pnpm-store/
/frontend/dist/
/frontend/build/
/frontend/.vite/
.turbo/
**/*.tsbuildinfo

# --- 6. C++ engine build outputs ---
engine/cpp_core/build*/
*.obj
*.o
*.a
*.lib
*.exe
*.dll
*.dylib
*.iobj
*.ipdb
*.pdb
*.tlog
*.lastbuildstate
*.vcxproj
*.vcxproj.filters
*.recipe

# --- 7. Databases & heavy geodata ---
*.db
*.db-wal
*.wal
*.sqlite
*.sqlite3
*.duckdb
*.tif
*.tiff
*.gpkg
*.nc
*.h5
*.hdf
*.shp
*.shx
*.dbf
*.prj
*.zst
*.zip
*.tar.gz
*.rar
*.7z
*.pkl

# --- 8. ML artifacts ---
*.pt
*.pth
*.onnx
*.bin
*.safetensors

# --- 9. Project data directories ---
data/maps/
data/motors/cache/
data/_archived_excel_data/
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep
data/copernicus_cache/*
!data/copernicus_cache/.gitkeep
ml/models/*
!ml/models/.gitkeep
/دیتا دستی اکسل/

# --- 10. Local-only project dirs ---
/_backups/
/backups/
/DELIVERY/
/_quarantine/
/analysis.json/
/benchmarks/
/.satellite_cache/
/.cache/
/.parcel-cache/
/.benchmarks/
/logs/

# --- 11. Logs & temp ---
*.log
*.log.*
*.tmp
reports/temp_*

# --- 12. Blockchain ---
contracts/artifacts/
contracts/cache/
contracts/typechain-types/
contracts/.env

# --- 13. Docs builds ---
docs/_build/
docs/.doctrees/

# --- 14. Legacy migration & tooling artifacts ---
*.bak
_one_shot_backup/
_secret_migration.local.txt
FIX_REVIEW.md
FIX_CONTEXT.txt
.kilo/
econojin.egg-info/
.agent_baseline.json
"""

AUDIT_SAMPLES = [
    "data/eco_nojin_master.duckdb",
    "data/eco_nojin.duckdb",
    "data/eco_nojin_analytics.duckdb",
    "data/maps/M-TOP_3d6aeb1b/contours.gpkg",
    "data/_archived_excel_data/Weather_Daily.csv",
    "database/hub/hub.py.phase4.bak",
    "engine/cpp_core/build2/hydroma_core.sln",
    ".coverage",
    "econojin.db-wal",
    "دیتا دستی اکسل/1787955036.png",
]
DANGER_EXT = (".duckdb", ".gpkg", ".tif", ".tiff", ".zst", ".xlsx", ".bak",
              ".iobj", ".ipdb", ".sqlite", "db-wal", "temp_bomb", ".wal")

FILTER_PATHS = [
    "data/maps", "data/_archived_excel_data", "data/motors",
    "data/copernicus_cache", "engine/cpp_core/build2",
    "_backups", "backups", "DELIVERY",
    "econojin.db", "econojin.db-wal", "دیتا دستی اکسل",
]
FILTER_GLOBS = [
    "reports/temp_*", "*.duckdb", "*.gpkg", "*.tif", "*.zst", "*.bak",
    "*.iobj", "*.ipdb", "*.tlog",
]

# ---------------------------------------------------------------- verify ---
def verify():
    out(LINE, "STEP 0 — verify remote state", LINE, sep="\n")
    git("fetch", "origin", timeout=300)
    r = git("log", "--oneline", "origin/main..main")
    unpushed = [l for l in r.stdout.splitlines() if l.strip()]
    if unpushed:
        warn(f"{len(unpushed)} unpushed commit(s) — pushing ...")
        r2 = git("push", "origin", "main")
        ok("pushed") if r2.returncode == 0 else \
            fail("push failed: " + (r2.stderr or "")[-400:])
    else:
        ok("everything pushed to origin/main")
    st = [l for l in git("status", "--porcelain").stdout.splitlines() if l.strip()]
    out(f"working-tree entries: {len(st)}")
    for l in st[:10]:
        out("    " + l)
    out("\n" + git("log", "--oneline", "-5").stdout)
    return True

# ---------------------------------------------------------------- audit ----
def audit():
    out(LINE, "STEP A — canonical .gitignore + live tests", LINE, sep="\n")
    gi = ROOT / ".gitignore"
    cur = gi.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n") \
        if gi.exists() else ""
    if cur.strip() == CANONICAL_GITIGNORE.strip():
        ok(".gitignore already canonical")
    else:
        gi.write_text(CANONICAL_GITIGNORE, encoding="utf-8", newline="\n")
        ok(".gitignore rewritten to canonical version")

    out("\nignore-check on sample heavy paths (untracked → reliable now):")
    problems = 0
    for f in AUDIT_SAMPLES:
        if not (ROOT / f).exists():
            continue
        r = git("check-ignore", "-v", "--", f)
        if r.returncode == 0 and r.stdout.strip():
            out(f"    IGNORED   {f}")
        else:
            problems += 1
            warn(f"    NOT IGNORED: {f}")
    if problems:
        fail(f"{problems} sample path(s) not ignored — report this output")
    else:
        ok("all sample heavy paths ignored")

    out("\ntracked-stray check (db / manual-data / sqlite / zst):")
    strays = []
    for f in (l.strip() for l in git("ls-files").stdout.splitlines() if l.strip()):
        p = f.replace("\\", "/")
        if (p.startswith("econojin.db") or p.startswith("دیتا دستی اکسل/")
                or p.lower().endswith((".sqlite", ".zst"))):
            strays.append(f)
    for f in strays:
        git("rm", "--cached", "--", f)
        out("    untracked stray: " + f)
    ok("no tracked strays") if not strays else \
        ok(f"{len(strays)} stray(s) untracked (stay on disk)")

    out("\nbehavioral test — 'git add --dry-run .':")
    r = git("add", "--dry-run", ".")
    would = [l.strip() for l in (r.stdout or "").splitlines() if l.strip()]
    dangers = [l for l in would if any(d in l.lower() for d in DANGER_EXT)]
    out(f"    files that would be added: {len(would)}")
    for l in would[:25]:
        out("    " + l)
    if len(would) > 25:
        out(f"    ... and {len(would) - 25} more")
    if dangers:
        fail("DANGER — heavy files would be re-added:")
        for l in dangers[:20]:
            out("    " + l)
        return False
    ok("no heavy file would be re-added by 'git add .'")

    git("add", "--", ".gitignore", "eco_fix.py")
    r = git("commit", "-m", "chore: canonical .gitignore; update automation script")
    if r.returncode == 0:
        ok("gitignore commit created")
        r2 = git("push", "origin", "main")
        ok("pushed") if r2.returncode == 0 else \
            warn("push failed — run: python eco_fix.py verify")
    elif "nothing to commit" in (r.stdout + r.stderr):
        ok("nothing to commit")
    else:
        warn("commit failed: " + (r.stdout + r.stderr)[-500:])
    return True

# --------------------------------------------------------- fix-assistant ---
ASSISTANT = ROOT / "services" / "ai" / "admin_assistant.py"
A_OLD = "    from database import models  # noqa: F401\nfrom database.hub import hub"
A_NEW = "    from database import models  # noqa: F401\n    from database.hub import hub"

def fix_assistant():
    out(LINE, "STEP B — admin_assistant.py syntax fix", LINE, sep="\n")
    if not ASSISTANT.exists():
        fail("file not found"); return False
    with open(ASSISTANT, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")

    if A_OLD in text:
        text = text.replace(A_OLD, A_NEW, 1)
        ok("indentation repaired (line ~362: 'from database.hub import hub')")
    elif A_NEW in text:
        ok("indentation already correct")
    else:
        fail("anchor not found — lines 355-375:")
        for i, ln in enumerate(text.splitlines()[354:375], 355):
            out(f"{i:4d}| {ln}")
        return False

    try:
        ast.parse(text)
        ok("file parses cleanly now")
    except SyntaxError as e:
        fail(f"STILL broken — line {e.lineno}: {e.msg}")
        lines = text.splitlines()
        ln = e.lineno or 1
        for i in range(max(0, ln - 12), min(len(lines), ln + 11)):
            out(f"{i+1:4d}| {lines[i]}")
        out(">>> NOT committed; report this output")
        return False

    with open(ASSISTANT, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", "\r\n") if crlf else text)
    git("add", "--", "services/ai/admin_assistant.py")
    r = git("commit", "-m",
            "fix(ai): repair lost indentation causing SyntaxError in admin_assistant")
    if r.returncode == 0:
        ok("committed")
        git("push", "origin", "main")
    else:
        warn("commit failed: " + (r.stdout + r.stderr)[-400:])
    return True

# --------------------------------------------------------- fix-reporting ---
REPORTING = ROOT / "services" / "reporting" / "api" / "__init__.py"
R_REPL = [
    ('"/<report_id>/generate"', '"/{report_id}/generate"'),
    ('"/<report_id>"', '"/{report_id}"'),
]

def fix_reporting():
    out(LINE, "STEP C — reporting routes: Flask <param> → FastAPI {param}", LINE, sep="\n")
    if not REPORTING.exists():
        fail("file not found"); return False
    with open(REPORTING, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")

    applied = []
    for old, new in R_REPL:
        if old in text:
            text = text.replace(old, new)
            applied.append(old)
    if applied:
        ok(f"replaced {len(applied)} route pattern(s)")
    elif "{report_id}" in text:
        ok("routes already FastAPI-style")
    else:
        warn("no <report_id> patterns found — file changed?")

    try:
        ast.parse(text)
    except SyntaxError as e:
        fail(f"parse failed after edit (line {e.lineno}: {e.msg}) — NOT written")
        return False

    if applied:
        with open(REPORTING, "w", encoding="utf-8", newline="") as f:
            f.write(text.replace("\n", "\r\n") if crlf else text)
        git("add", "--", "services/reporting/api/__init__.py")
        r = git("commit", "-m",
                "fix(reporting): convert Flask-style <report_id> routes to FastAPI {report_id}")
        if r.returncode == 0:
            ok("committed")
            git("push", "origin", "main")
        else:
            warn("commit failed: " + (r.stdout + r.stderr)[-400:])
    return True

# ----------------------------------------------------------------- recon ---
def recon():
    out(LINE, "STEP D — recon (read-only) for next phase", LINE, sep="\n")
    p = ROOT / "services" / "reporting" / "service.py"
    if p.exists():
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        out(f"--- services/reporting/service.py (first 70 of {len(lines)}) ---")
        for i, ln in enumerate(lines[:70], 1):
            out(f"{i:4d}| {ln}")
    else:
        warn("reporting/service.py not found")

    hp = ROOT / "database" / "hub" / "hub.py"
    if hp.exists():
        lines = hp.read_text(encoding="utf-8", errors="replace").splitlines()
        idx = [i for i, ln in enumerate(lines) if "def get_session" in ln]
        if idx:
            i = idx[0]
            out(f"\n--- database/hub/hub.py around get_session (line {i+1}) ---")
            for j in range(max(0, i - 10), min(len(lines), i + 25)):
                out(f"{j+1:4d}| {lines[j]}")
            if lines[i].lstrip().startswith("async def"):
                out(">>> get_session is ASYNC — reporting's sync 'with' is incompatible!")
            else:
                out(">>> get_session is SYNC — but reporting types it as AsyncSession.")
        else:
            warn("get_session not found in hub.py")
    else:
        warn("database/hub/hub.py not found")

    out("\ntracked-file census (surgery planning):")
    files = [l.strip() for l in git("ls-files").stdout.splitlines() if l.strip()]
    for pat in ("econojin.db", "db-wal", "دیتا دستی", "sandbox/", ".zst",
                ".sqlite", ".xlsx"):
        hits = [f for f in files if pat.lower() in f.lower()]
        out(f"    '{pat}': {len(hits)} tracked" + (f"  e.g. {hits[:3]}" if hits else ""))
    out("\ncount-objects:\n" + git("count-objects", "-vH").stdout)
    return True

# ------------------------------------------------------- history surgery ---
def history_surgery(confirm=None):
    out(LINE, "STEP E — history surgery (git filter-repo)", LINE, sep="\n")
    if confirm != "CONFIRM":
        out("""This REWRITES history to drop heavy blobs: 4 versions of
master.duckdb (~122 MiB), build2 (~45 MiB), maps, xlsx, .bak files,
~1856 temp ghosts, econojin.db-wal, Persian manual-data dir.
Current pack: 88.69 MiB → expected ~10-20 MiB.

Consequences: ALL commit SHAs change; remote is force-pushed.
A full backup bundle is created first (eco_nojin_pre_surgery.bundle).

If you accept, run EXACTLY:
    python eco_fix.py history-surgery CONFIRM""")
        return False

    st = [l for l in git("status", "--porcelain").stdout.splitlines() if l.strip()]
    dirty = [l for l in st if l[3:].strip().strip('"') != "eco_fix.py"]
    if dirty:
        fail("working tree not clean — commit/stash first: " + str(dirty[:5]))
        return False
    git("fetch", "origin", timeout=300)
    r = git("log", "--oneline", "origin/main..main")
    if [l for l in r.stdout.splitlines() if l.strip()]:
        fail("unpushed commits — push first"); return False
    ok("tree clean & everything pushed")

    url = git("remote", "get-url", "origin").stdout.strip()
    if not url:
        fail("no origin remote"); return False
    ok("remote: " + url)

    bundle = ROOT.parent / "eco_nojin_pre_surgery.bundle"
    r = git("bundle", "create", str(bundle), "--all")
    if r.returncode != 0:
        fail("bundle failed: " + r.stderr[-300:]); return False
    ok(f"backup bundle: {bundle} ({bundle.stat().st_size/1048576:.1f} MiB)")

    r = sh([sys.executable, "-m", "pip", "install", "-q", "git-filter-repo"],
           timeout=600)
    if r.returncode != 0:
        fail("pip install git-filter-repo failed: " + (r.stderr or "")[-300:])
        return False
    ok("git-filter-repo ready")

    fr = ROOT / ".venv" / "Scripts" / "git-filter-repo.exe"
    cmd = [str(fr)] if fr.exists() else [sys.executable, "-m", "git_filter_repo"]
    args = cmd + ["--force", "--invert-paths"]
    for pth in FILTER_PATHS:
        args += ["--path", pth]
    for g in FILTER_GLOBS:
        args += ["--path-glob", g]
    out("running filter-repo (minutes) ...")
    try:
        r = sh(args, timeout=3600)
    except subprocess.TimeoutExpired:
        fail("filter-repo timed out"); return False
    if r.returncode != 0:
        fail("filter-repo failed: " + (r.stdout + r.stderr)[-800:]); return False
    ok("history rewritten")

    git("remote", "add", "origin", url)
    if git("remote", "get-url", "origin").returncode != 0:
        fail("could not re-add origin — run: git remote add origin " + url)
        return False
    ok("origin re-added (filter-repo strips remotes)")

    for gk in ("data/copernicus_cache/.gitkeep",):
        p = ROOT / gk
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
            out("restored placeholder: " + gk)
    for gk in ("data/raw/.gitkeep", "data/processed/.gitkeep",
               "ml/models/.gitkeep", "data/copernicus_cache/.gitkeep"):
        if (ROOT / gk).exists():
            git("add", "--", gk)
    r = git("commit", "-m", "chore: restore placeholder files after history surgery")
    ok("placeholders committed") if r.returncode == 0 else \
        ok("no placeholder commit needed")

    r = git("push", "--force", "origin", "--all")
    ok("branches force-pushed") if r.returncode == 0 else \
        warn("branch push failed: " + r.stderr[-300:])
    r = git("push", "--force", "origin", "--tags")
    ok("tags force-pushed") if r.returncode == 0 else \
        warn("tag push failed: " + r.stderr[-300:])

    out("\ncount-objects after surgery:\n" + git("count-objects", "-vH").stdout)
    files = [l for l in git("ls-files").stdout.splitlines() if l.strip()]
    out(f"tracked files: {len(files)}")
    out("log:\n" + git("log", "--oneline", "-3").stdout)
    out("NOTE: GitHub keeps old objects server-side until its GC runs —")
    out("remote size may lag. Fine for a private single-dev repo.")
    return True

# ------------------------------------------------------------------ main ---
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    arg2 = sys.argv[2] if len(sys.argv) > 2 else None
    steps = {"verify": verify, "audit": audit, "recon": recon,
             "fix-assistant": fix_assistant, "fix-reporting": fix_reporting}
    if cmd == "all":
        verify()
        if audit():
            fix_assistant()
            fix_reporting()
        recon()
    elif cmd == "history-surgery":
        history_surgery(arg2)
    elif cmd in steps:
        steps[cmd]()
    else:
        out(__doc__)

if __name__ == "__main__":
    main()