#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v18.

STEP 1 mystery     — traced import: which include_router calls ran, on which
                     app instance, with how many routes at mount time;
                     manual re-mount experiment; FastAPI version; pyc check
STEP 2 compile     — local repro of CI 'Compile check' + auto-fix of the
                     proven mangled-indent pattern (parse-gated, rollback)
STEP 3 ci-frontend — pin pnpm/action-setup to exact packageManager version
STEP 4 dead-models — services/models package: broad grep, delete if dead
STEP 5 health-twin — actually remove the dead /health twin (v12 was a no-op)

Usage:
    python eco_fix.py
    python eco_fix.py verify | mystery | compile | ci-frontend | dead-models | health-twin
"""
import ast
import json
import re
import subprocess
import sys
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

def read_text(p):
    with open(p, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    return raw, ("\r\n" in raw), raw.replace("\r\n", "\n")

def write_text(p, text, crlf):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", "\r\n") if crlf else text)

def write_raw(p, raw):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(raw)

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

def import_smoke(mod, timeout=300):
    code = f"import importlib; importlib.import_module({mod!r}); print('OK')"
    try:
        r = sh([sys.executable, "-c", code], timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout"
    return "OK" if r.returncode == 0 else (r.stderr or r.stdout)[-300:]

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

# ---------------------------------------------------------------- mystery ---
MYSTERY = """
import json, os, sys
import fastapi
from fastapi import FastAPI

creations = []
_orig_init = FastAPI.__init__
def _traced_init(self, *a, **kw):
    creations.append(id(self))
    return _orig_init(self, *a, **kw)
FastAPI.__init__ = _traced_init

mount_calls = []
_orig_ir = FastAPI.include_router
def _traced_ir(self, router, *a, **kw):
    mount_calls.append({
        "app": id(self),
        "rprefix": getattr(router, "prefix", ""),
        "n": len(getattr(router, "routes", []) or []),
        "mprefix": kw.get("prefix", ""),
    })
    return _orig_ir(self, router, *a, **kw)
FastAPI.include_router = _traced_ir

import services.api_gateway.main as m
FastAPI.include_router = _orig_ir
FastAPI.__init__ = _orig_init

print("VERSION:" + str(fastapi.__version__))
print("FILE:" + str(m.__file__))
print("APP_ID:" + str(id(m.app)))
print("CREATIONS:" + json.dumps(creations))
print("NMOUNTS:" + str(len(mount_calls)))
for e in mount_calls:
    print("MOUNT:" + json.dumps(e))
print("MOUNTS_EMPTY:" + str(sum(1 for e in mount_calls if e["n"] == 0)))
print("TOTAL_ROUTES:" + str(len(m.app.routes)))

import services.api_gateway.routers.land as land_mod
print("LAND_NOW:" + str(len(land_mod.router.routes)))
before = len(m.app.routes)
m.app.include_router(land_mod.router)
print("REMOUNT:" + str(before) + "->" + str(len(m.app.routes)))

import importlib.util
pyc = importlib.util.cache_from_source(m.__file__)
print("PYC:" + str(os.path.exists(pyc)))
"""

def mystery():
    out(LINE, "STEP 1 — mystery probe (traced import — decisive)", LINE, sep="\n")
    r = sh([sys.executable, "-c", MYSTERY], timeout=300)
    if r.returncode != 0:
        fail("probe failed: " + (r.stderr or r.stdout)[-700:])
        return False
    app_id = ""
    nmounts = 0
    nempty = 0
    remount = ""
    for line in r.stdout.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        if key == "MOUNT":
            e = json.loads(val)
            out(f"      mount app={e['app']} router={e['rprefix']:18s} "
                f"routes_at_mount={e['n']:3d} mount_prefix={e['mprefix']}")
        elif key == "APP_ID":
            app_id = val
            out("    APP_ID: " + val)
        elif key == "NMOUNTS":
            nmounts = int(val)
        elif key == "MOUNTS_EMPTY":
            nempty = int(val)
        elif key == "REMOUNT":
            remount = val
        else:
            out("    " + key + ": " + val)

    out("\n    INTERPRETATION:")
    if nmounts == 0:
        out("      >>> ZERO include_router calls executed — mount block never "
            "ran. Check FILE above (pyc/source mismatch?).")
    elif nempty == nmounts:
        out("      >>> ALL mounts ran with EMPTY routers — circular import "
            "confirmed: routers populated AFTER mounting. v19 = break the cycle.")
    elif remount and "->" in remount:
        b, a = remount.split("->")
        if int(a) > int(b):
            out("      >>> include_router works manually; mounts had "
                f"{nmounts - nempty}/{nmounts} populated calls — inspect "
                "trace rows above (which routers were empty).")
        else:
            out("      >>> include_router does NOT add routes even manually — "
                "FastAPI-level anomaly; report VERSION above.")
    else:
        out("      >>> mixed state — inspect trace rows above.")

    out("\n    circular-import candidates (who references api_gateway.main):")
    r = git("grep", "-n", "-E",
            "api_gateway[.]main|api_gateway import main|from [.]main import",
            "--", "services/", "engine/", "scripts/", "tests/")
    hits = [l for l in r.stdout.splitlines() if l.strip()]
    out(f"    hits: {len(hits)}")
    for l in hits[:20]:
        out("    " + l)
    dump(ROOT / "services" / "api_gateway" / "auth.py", hi=45,
         title="services/api_gateway/auth.py head (imports)")
    return True

# ---------------------------------------------------------------- compile ---
TWO_LINE_BUG = ("    from database import models  # noqa: F401\n"
                "from database.hub import hub")
TWO_LINE_FIX = ("    from database import models  # noqa: F401\n"
                "    from database.hub import hub")

def _next_nonblank(lines, j):
    for k in range(j + 1, len(lines)):
        if lines[k].strip():
            return lines[k]
    return ""

def _try_auto_fix(text, lineno):
    lines = text.split("\n")
    for j in range((lineno or 2) - 2, max(-1, (lineno or 2) - 40), -1):
        s = lines[j]
        if not s.strip() or s.startswith((" ", "\t")):
            continue
        stripped = s.lstrip()
        if stripped.startswith(("def ", "class ", "@", "#")):
            return None
        if not stripped.startswith(("import ", "from ")):
            continue
        nxt = _next_nonblank(lines, j)
        if nxt.startswith((" ", "\t")):
            indent = len(nxt) - len(nxt.lstrip())
            lines[j] = " " * indent + s
            return "\n".join(lines), j + 1
    return None

def compile_step():
    out(LINE, "STEP 2 — compileall local repro (CI's failing step)", LINE, sep="\n")
    r = sh([sys.executable, "-m", "compileall", "-q", "services"], timeout=900)
    out("    exit code: " + str(r.returncode))
    combined = (r.stdout or "") + (r.stderr or "")
    files = []
    for m in re.finditer(r'File "([^"]+)", line', combined):
        f = m.group(1)
        if f not in files:
            files.append(f)
    if r.returncode == 0 and not files:
        ok("services/ compiles cleanly LOCALLY — CI failure is environment-"
           "specific; open the run in browser and paste the Compile step log")
        return True

    out(f"    failing file(s): {len(files)}")
    originals = {}
    fixed = []
    for f in files:
        p = Path(f)
        if not p.exists() or not str(p).startswith(str(ROOT)):
            out("    (outside root, skipped): " + f)
            continue
        raw, crlf, text = read_text(p)
        originals[p] = raw
        changed = False
        if TWO_LINE_BUG in text:
            text = text.replace(TWO_LINE_BUG, TWO_LINE_FIX)
            changed = True
        for _ in range(8):
            try:
                ast.parse(text)
                break
            except SyntaxError as e:
                if (e.msg or "").startswith("unexpected indent"):
                    res = _try_auto_fix(text, e.lineno)
                    if res:
                        text = res[0]
                        changed = True
                        continue
                out(f"    {p.name}: unfixable — line {e.lineno}: {e.msg}")
                break
        try:
            ast.parse(text)
        except SyntaxError:
            out("    " + str(p.relative_to(ROOT)) + " left unfixed (context next round)")
            continue
        if changed:
            write_text(p, text, crlf)
            fixed.append(p)
            ok("fixed: " + str(p.relative_to(ROOT)))

    if not fixed:
        fail("nothing auto-fixed — report the file list above")
        return False

    r2 = sh([sys.executable, "-m", "compileall", "-q", "services"], timeout=900)
    if r2.returncode != 0:
        fail("compileall still red — rolling back all fixes")
        for p, raw in originals.items():
            if p in fixed:
                write_raw(p, raw)
        ok("originals restored — nothing committed")
        return False
    ok("compileall now GREEN locally")

    for p in fixed:
        git("add", "--", str(p.relative_to(ROOT)).replace("\\", "/"))
    r = git("commit", "-m",
            "fix(services): repair formatter-mangled indents found by CI "
            "compile check")
    if r.returncode == 0:
        ok("committed (push triggers fresh CI run)")
        git("push", "origin", "main")
    else:
        ok("nothing to commit")
    return True

# ------------------------------------------------------------ ci-frontend ---
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"

def ci_frontend():
    out(LINE, "STEP 3 — ci.yml: pin pnpm to exact packageManager version", LINE, sep="\n")
    version = "11.4.0"
    pj = ROOT / "package.json"
    if pj.exists():
        m = re.search(r'"packageManager"\s*:\s*"pnpm@([^"]+)"',
                      pj.read_text(encoding="utf-8", errors="replace"))
        if m:
            version = m.group(1)
    out("    target version: " + version)
    if not CI_YML.exists():
        fail("ci.yml not found")
        return False
    text = CI_YML.read_text(encoding="utf-8", errors="replace")
    pat = re.compile(r"(pnpm/action-setup@v4[^\n]*\n\s*with:\s*\n\s*version:\s*)([^\n]+)")
    new, n = pat.subn(lambda mm: mm.group(1) + version, text)
    if n == 0 or new == text:
        ok("already pinned (or block not found — check ci.yml manually)")
        return True
    CI_YML.write_text(new, encoding="utf-8", newline="\n")
    try:
        import yaml
        yaml.safe_load(new)
        ok("ci.yml still valid YAML")
    except Exception as e:
        warn(f"yaml check failed: {e!r}")
    git("add", "--", ".github/workflows/ci.yml")
    r = git("commit", "-m",
            "ci(frontend): pin pnpm version to exact packageManager value ("
            + version + ") — fixes version-mismatch failure")
    if r.returncode == 0:
        ok("committed (push triggers fresh CI run)")
        git("push", "origin", "main")
    else:
        ok("nothing to commit")
    return True

# ------------------------------------------------------------ dead-models ---
def dead_models():
    out(LINE, "STEP 4 — services/models: dead-package verdict", LINE, sep="\n")
    dump(ROOT / "services" / "models" / "__init__.py",
         title="services/models/__init__.py (FULL)")
    dump(ROOT / "services" / "models" / "base.py", hi=30,
         title="services/models/base.py head")

    r = git("grep", "-n", "-E",
            "services[.]models|from services import models", "--", ".")
    hits = [l for l in r.stdout.splitlines() if l.strip()]
    code_refs = []
    for l in hits:
        fp = l.split(":", 1)[0]
        if fp == "eco_fix.py":
            continue
        if fp.replace("\\", "/").startswith("services/models/"):
            continue
        if fp.endswith(".py"):
            code_refs.append(l)
    out(f"    total hits: {len(hits)} | live CODE refs outside package: {len(code_refs)}")
    for l in code_refs[:12]:
        out("    " + l)
    if code_refs:
        warn("live code references exist — NOT deleting")
        return True
    ok("no live code references — package is dead")

    base = import_smoke("services.api_gateway.main")
    if base != "OK":
        fail("baseline main import failing — aborting")
        return False
    git("rm", "-r", "--", "services/models")
    ok("git rm -r services/models (recoverable from history)")

    post = import_smoke("services.api_gateway.main")
    coll = sh([sys.executable, "-m", "pytest", "--collect-only", "-q",
               "--no-header"], timeout=600)
    if post != "OK" or coll.returncode != 0:
        fail("regression — restoring package")
        git("reset", "--", "services/models")
        git("checkout", "--", "services/models")
        ok("restored — nothing committed")
        return False
    ok("main import OK, pytest collection OK without the package")

    ruff_exe = ROOT / ".venv" / "Scripts" / "ruff.exe"
    cmd = [str(ruff_exe)] if ruff_exe.exists() else ["ruff"]
    r = sh(cmd + ["check", ".", "--select", "F821"], timeout=240)
    m = re.search(r"(\d+)\s+F821", r.stdout or "")
    out("    remaining F821 repo-wide: " + (m.group(1) if m else "?"))

    r = git("commit", "-m",
            "chore: remove dead services/models package (superseded by "
            "database.models; imports were commented out, base broken)")
    if r.returncode == 0:
        ok("committed")
        git("push", "origin", "main")
    else:
        ok("nothing to commit")
    return True

# ------------------------------------------------------------ health-twin ---
MAIN = ROOT / "services" / "api_gateway" / "main.py"
HEALTH_PROBE = (
    "from services.api_gateway.main import app; "
    "hs=[(sorted(getattr(r,'methods',[]) or []), "
    "getattr(getattr(r,'endpoint',None),'__name__','?')) "
    "for r in app.routes if getattr(r,'path',None)=='/health']; "
    "print(hs)"
)

def health_state():
    r = sh([sys.executable, "-c", HEALTH_PROBE], timeout=300)
    return r.stdout.strip()

def health_twin():
    out(LINE, "STEP 5 — remove the dead /health twin (for real this time)", LINE, sep="\n")
    before = health_state()
    out("    BEFORE: " + before)
    if "health_check" not in before:
        ok("twin already gone")
        return True

    raw, crlf, text = read_text(MAIN)
    tree = ast.parse(text)
    target = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name == "health_check":
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call)
                        and isinstance(dec.func, ast.Attribute)
                        and dec.func.attr == "get"
                        and dec.args
                        and isinstance(dec.args[0], ast.Constant)
                        and dec.args[0].value == "/health"):
                    target = node
    if target is None:
        warn("twin endpoint not found via AST — skipping")
        return True
    start = min(d.lineno for d in target.decorator_list)
    end = target.end_lineno
    lines = text.split("\n")
    new_text = re.sub(r"\n{4,}", "\n\n\n",
                      "\n".join(lines[: start - 1] + lines[end:]))
    ast.parse(new_text)
    write_text(MAIN, new_text, crlf)
    ok(f"removed twin 'health_check' (lines {start}-{end})")

    after = health_state()
    out("    AFTER:  " + after)
    if "health_check" in after or "'health'" not in after:
        fail("proof mismatch — ROLLING BACK")
        write_raw(MAIN, raw)
        ok("original restored")
        return False
    ok("exactly one GET /health remains ('health' — the rich one)")

    git("add", "--", "services/api_gateway/main.py")
    r = git("commit", "-m",
            "fix(gateway): actually remove dead /health twin endpoint "
            "(previous attempt in 9b30b6b was a silent no-op)")
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
    steps = {"verify": verify, "mystery": mystery, "compile": compile_step,
             "ci-frontend": ci_frontend, "dead-models": dead_models,
             "health-twin": health_twin}
    if cmd == "all":
        for name in ("verify", "mystery", "compile", "ci-frontend",
                     "dead-models", "health-twin"):
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