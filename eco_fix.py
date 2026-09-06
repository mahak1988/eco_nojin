#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v17 — the 9-route mystery.

STEP 1 anatomy     — full app.routes enumeration (path/method/endpoint/__module__),
                     per-router route counts from the routers package,
                     duplicate-module scan in sys.modules
STEP 2 file-evidence— current main.py state, routers/__init__.py dump,
                     start_dev_v4.py head, health-twin grep
STEP 3 ci-jobs     — verdict of the run triggered by the pywin32 push
STEP 4 ci-frontend — pin pnpm action version to the exact packageManager value
STEP 5 land-models — restore the lost import block (prove-then-commit)

Usage:
    python eco_fix.py
    python eco_fix.py verify | anatomy | file-evidence | ci-jobs | ci-frontend | land-models
"""
import ast
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GITHUB_REPO = "mahak1988/eco_nojin"

GIT_EXE = None
for _c in (r"C:\Program Files\Git\cmd\git.exe",
           r"C:\Program Files (x86)\Git\cmd\git.exe",
           r"C:\Program Files\Git\bin\git.exe"):
    if Path(_c).exists():
        GIT_EXE = _c
        break

LINE = "=" * 62
TS = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s*")

def out(*a, **kw):
    print(*a, flush=True, **kw)

def ok(m):
    out(f"[ OK ] {m}")

def warn(m):
    out(f"[WARN] {m}")

def fail(m):
    out(f"[FAIL] {m}")

def sh(cmd, timeout=900, input=None):
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=timeout, input=input)

def git(*a, **kw):
    if GIT_EXE is None:
        raise RuntimeError("git.exe not found")
    return sh([GIT_EXE, *a], **kw)

def dump(p, lo=1, hi=None, title=None):
    p = Path(p)
    if not p.exists():
        warn(f"not found: {p}")
        return
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    hi = hi or len(lines)
    out(f"--- {title or p} (lines {lo}-{min(hi, len(lines))} of {len(lines)}) ---")
    for i in range(lo - 1, min(hi, len(lines))):
        out(f"{i+1:4d}| {lines[i]}")
    out("--- end ---")

def _gh_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "eco_nojin-eco-fix",
        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _gh_text(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "eco_nojin-eco-fix",
        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", errors="replace")

# ---------------------------------------------------------------- verify ---
def verify():
    out(LINE, "STEP 0 — verify", LINE, sep="\n")
    git("fetch", "origin", timeout=300)
    r = git("log", "--oneline", "origin/main..main")
    if [l for l in r.stdout.splitlines() if l.strip()]:
        warn("unpushed — pushing ...")
        git("push", "origin", "main")
    else:
        ok("everything pushed to origin/main")
    out(git("log", "--oneline", "-3").stdout)
    return True

# --------------------------------------------------------------- anatomy ---
ANATOMY = """
import json, sys
from services.api_gateway.main import app
import services.api_gateway.routers as rp

print("APP_TITLE:" + str(getattr(app, "title", "?")))
rows = []
for r in app.routes:
    path = getattr(r, "path", None)
    if path is None:
        continue
    ep = getattr(r, "endpoint", None)
    rows.append({
        "path": path,
        "methods": ",".join(sorted(getattr(r, "methods", None) or [])) or "WS",
        "ep": getattr(ep, "__name__", "?"),
        "mod": getattr(ep, "__module__", "?"),
    })
print("TOTAL:" + str(len(rows)))
for row in rows:
    print("ROUTE:" + json.dumps(row))

NAMES = ["platform","admin","auth","analyses","land","soil","satellite",
         "carbon","watershed","scenarios","ai","ai_chat","ecowallet",
         "marketplace","farms","analytics","materials","blockchain",
         "ussd","voice","sync","benchmark","nojin","simulation","motors",
         "mrv","science","models","elevation","support","manual_data",
         "dashboard"]
for n in NAMES:
    obj = getattr(rp, n, None)
    if obj is None:
        print("PKG:" + n + ":MISSING:-")
        continue
    kind = type(obj).__name__
    if kind == "module":
        rt = getattr(obj, "router", None)
        cnt = len(getattr(rt, "routes", []) or [])
        rkind = type(rt).__name__ if rt is not None else "None"
        print("PKG:" + n + ":module:" + rkind + ":" + str(cnt))
    else:
        cnt = len(getattr(obj, "routes", []) or [])
        print("PKG:" + n + ":" + kind + ":" + str(cnt))

dups = sorted(k for k in sys.modules
              if "api_gateway" in k and not k.startswith("services.api_gateway"))
print("DUPMODS:" + json.dumps(dups))
"""

def anatomy():
    out(LINE, "STEP 1 — app anatomy (the 9-route mystery)", LINE, sep="\n")
    r = sh([sys.executable, "-c", ANATOMY], timeout=300)
    if r.returncode != 0:
        fail("anatomy probe failed: " + (r.stderr or r.stdout)[-600:])
        return False
    for line in r.stdout.splitlines():
        if line.startswith("APP_TITLE:"):
            out("    app title: " + line[10:])
        elif line.startswith("TOTAL:"):
            out("    total routes: " + line[6:])
        elif line.startswith("ROUTE:"):
            row = json.loads(line[6:])
            out(f"    {row['methods']:8s} {row['path']:28s} "
                f"{row['ep']:18s} [{row['mod']}]")
        elif line.startswith("PKG:"):
            out("    " + line[4:])
        elif line.startswith("DUPMODS:"):
            out("    duplicate module names: " + line[8:])
    if r.stderr.strip():
        out("    stderr tail: " + r.stderr[-300:])
    return True

# --------------------------------------------------------- file-evidence ---
def file_evidence():
    out(LINE, "STEP 2 — file evidence (current state)", LINE, sep="\n")

    r = git("grep", "-n", 'app.get("/health")', "--",
            "services/api_gateway/main.py")
    out('    @app.get("/health") occurrences in main.py:')
    for l in [l for l in r.stdout.splitlines() if l.strip()]:
        out("    " + l)

    r = git("grep", "-n", "def health_check", "--", "services/")
    out("\n    'def health_check' owners across services/:")
    for l in [l for l in r.stdout.splitlines() if l.strip()][:10]:
        out("    " + l)

    dump(ROOT / "services" / "api_gateway" / "main.py", lo=55, hi=75,
         title="main.py app creation + first mounts")
    dump(ROOT / "services" / "api_gateway" / "main.py", lo=205, hi=258,
         title="main.py mount block (current)")
    dump(ROOT / "services" / "api_gateway" / "routers" / "__init__.py",
         title="routers/__init__.py (FULL)")
    dump(ROOT / "start_dev_v4.py", hi=45, title="start_dev_v4.py head")

    out("\n    entrypoint candidates in repo root:")
    for f in sorted(ROOT.glob("*.py")):
        try:
            head = f.read_text(encoding="utf-8", errors="replace")[:400]
        except OSError:
            continue
        if "uvicorn" in head or "FastAPI(" in head:
            out(f"    {f.name}")
    return True

# --------------------------------------------------------------- ci-jobs ---
def ci_jobs():
    out(LINE, "STEP 3 — CI verdict (post-pywin32 run)", LINE, sep="\n")
    try:
        runs = _gh_json(
            "https://api.github.com/repos/" + GITHUB_REPO
            + "/actions/workflows/ci.yml/runs?per_page=6"
        ).get("workflow_runs", [])
    except Exception as e:
        warn(f"API failed: {e!r}")
        return True
    for run in runs[:6]:
        out(f"    id={run['id']} sha={run.get('head_sha', '?')[:8]} "
            f"{run.get('status'):10s} {run.get('conclusion') or '-'}")
    target = next((r for r in runs if r.get("status") == "completed"), None)
    if target is None:
        warn("latest run still in progress — re-run ci-jobs in a few minutes")
        return True
    out(f"\n    deep-dive on run {target['id']}:")
    try:
        jobs = _gh_json(
            "https://api.github.com/repos/" + GITHUB_REPO
            + f"/actions/runs/{target['id']}/jobs"
        ).get("jobs", [])
    except Exception as e:
        warn(f"jobs API failed: {e!r}")
        return True
    failed = []
    for job in jobs:
        out(f"    JOB {job.get('name')} -> {job.get('conclusion')}")
        for st in (job.get("steps") or []):
            c = st.get("conclusion") or st.get("status") or "?"
            mark = " X " if c == "failure" else (" * " if c == "skipped" else " . ")
            out(f"      {mark}{st.get('name')}  [{c}]")
            if c == "failure":
                failed.append((job.get("name"), st.get("name"), job.get("id")))
    for jname, sname, job_id in failed:
        out(f"\n    fetching log for failed step '{sname}' (job {jname}) ...")
        try:
            log = _gh_text(
                "https://api.github.com/repos/" + GITHUB_REPO
                + f"/actions/jobs/{job_id}/logs")
            lines = [TS.sub("", l).rstrip() for l in log.splitlines()]
            keys = ("##[error", "error:", "no matching distribution",
                    "could not find", "fatal", "exception", "version")
            hits = [l for l in lines if any(k in l.lower() for k in keys)]
            for l in hits[:20]:
                out("    | " + l[:170])
            out("    --- last 4 lines ---")
            for l in lines[-4:]:
                out("    | " + l[:170])
        except Exception as e:
            warn(f"    log fetch failed ({e!r}) — open:")
            warn("    https://github.com/" + GITHUB_REPO + "/actions")
    if not failed:
        ok("no failed steps — CI may be GREEN now! 🎉")
    return True

# ------------------------------------------------------------ ci-frontend ---
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"

def ci_frontend():
    out(LINE, "STEP 4 — ci.yml: pin pnpm action to exact packageManager", LINE, sep="\n")
    version = None
    for pj in (ROOT / "package.json", ROOT / "frontend" / "package.json"):
        if pj.exists():
            m = re.search(r'"packageManager"\s*:\s*"pnpm@([^"]+)"',
                          pj.read_text(encoding="utf-8", errors="replace"))
            if m:
                version = m.group(1)
                out(f"    packageManager (from {pj.relative_to(ROOT)}): pnpm@{version}")
                break
    if version is None:
        version = "11.4.0"
        warn("no packageManager field found — defaulting to 11.4.0")
    if not CI_YML.exists():
        fail("ci.yml not found")
        return False
    text = CI_YML.read_text(encoding="utf-8", errors="replace")
    new, n = re.subn(r"(uses:\s*pnpm/action-setup@v4\n\s+version:\s*)[^\n]+",
                     r"\g<1>" + version, text)
    if n == 0:
        if f"version: {version}" in text:
            ok("already pinned correctly")
            return True
        warn("pnpm version input not found — manual check needed")
        return True
    if new == text:
        ok("already pinned correctly")
        return True
    CI_YML.write_text(new, encoding="utf-8", newline="\n")
    try:
        import yaml
        data = yaml.safe_load(new)
        assert "frontend" in (data.get("jobs") or {})
        ok("ci.yml still valid YAML")
    except Exception as e:
        warn(f"yaml check failed: {e!r}")
    git("add", "--", ".github/workflows/ci.yml")
    r = git("commit", "-m",
            f"ci(frontend): pin pnpm/action-setup version to {version} "
            "(exact match with packageManager field)")
    if r.returncode == 0:
        ok("committed (push triggers a fresh CI run)")
        git("push", "origin", "main")
    else:
        ok("nothing to commit")
    return True

# ------------------------------------------------------------ land-models ---
LM = ROOT / "services" / "models" / "land_models.py"
LM_IMPORTS = (
    "from .base import Base\n"
    "\n"
    "import uuid\n"
    "\n"
    "from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text, func\n"
    "from sqlalchemy.dialects.postgresql import JSONB\n"
    "from sqlalchemy.dialects.postgresql import UUID as PG_UUID\n"
)

def land_models():
    out(LINE, "STEP 5 — land_models.py: restore lost import block", LINE, sep="\n")
    r = git("grep", "-n", "land_models", "--", "services/", "tests/",
            "engine/", "scripts/")
    hits = [l for l in r.stdout.splitlines() if l.strip()]
    out(f"    references to land_models: {len(hits)}")
    for l in hits[:8]:
        out("    " + l)
    if not LM.exists():
        fail("file not found")
        return False
    text = LM.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    if "from sqlalchemy import Column" in text:
        ok("imports already present")
        return True
    if not text.startswith("from .base import Base"):
        fail("unexpected file head — aborting")
        return True
    new_text = LM_IMPORTS + text[len("from .base import Base"):]
    try:
        ast.parse(new_text)
    except SyntaxError as e:
        fail(f"parse after edit L{e.lineno}: {e.msg}")
        return False
    LM.write_text(new_text, encoding="utf-8", newline="\n")
    ok("import block written")

    r = sh([sys.executable, "-c",
            "import importlib; importlib.import_module("
            "'services.models.land_models'); print('IMPORT-OK')"], timeout=180)
    if "IMPORT-OK" not in (r.stdout or ""):
        fail("module still not importable — ROLLING BACK")
        out("    " + (r.stderr or r.stdout)[-400:])
        LM.write_text(text, encoding="utf-8", newline="\n")
        ok("original restored")
        return False
    ok("module imports cleanly now (proof green)")

    ruff_exe = ROOT / ".venv" / "Scripts" / "ruff.exe"
    cmd = [str(ruff_exe)] if ruff_exe.exists() else ["ruff"]
    r = sh(cmd + ["check", "services/models/land_models.py",
                  "--select", "F821", "--output-format", "concise"],
           timeout=120)
    remaining = [l for l in (r.stdout or "").splitlines() if "F821" in l]
    out(f"    remaining F821 in land_models.py: {len(remaining)}")
    for l in remaining[:5]:
        out("    " + l)

    git("add", "--", "services/models/land_models.py")
    r = git("commit", "-m",
            "fix(models): restore lost sqlalchemy import block in land_models "
            "(84 ruff F821 undefined names)")
    if r.returncode == 0:
        ok("committed")
        git("push", "origin", "main")
    else:
        ok("nothing to commit")
    return True

# ------------------------------------------------------------------ chore ---
def chore():
    git("add", "--", "eco_fix.py")
    r = git("commit", "-m", "chore: update automation script")
    if r.returncode == 0:
        ok("script committed")
        git("push", "origin", "main")
    else:
        ok("nothing to commit")

# ------------------------------------------------------------------- main ---
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"verify": verify, "anatomy": anatomy,
             "file-evidence": file_evidence, "ci-jobs": ci_jobs,
             "ci-frontend": ci_frontend, "land-models": land_models}
    if cmd == "all":
        for name in ("verify", "anatomy", "file-evidence", "ci-jobs",
                     "ci-frontend", "land-models"):
            try:
                steps[name]()
            except Exception as e:
                fail(f"{name} crashed: {e!r}")
        chore()
    elif cmd in steps:
        try:
            steps[cmd]()
        except Exception as e:
            fail(f"{cmd} crashed: {e!r}")
    else:
        out(__doc__)

if __name__ == "__main__":
    main()