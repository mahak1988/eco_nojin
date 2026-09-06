#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v13.

STEP 1 ci-triage      — dump .github/workflows/ci.yml + local probes
                        (pytest collection, ruff stats) to find why CI is red
STEP 2 dead-modules   — remove dependencies.py & register_modules.py
                        (zero consumers; prove-then-commit, rollback)
STEP 3 motors-dedup   — drop the unused /api/v1 motors mount (evidence-gated)
STEP 4 ai-recon       — full dumps to design the AI surface consolidation

Usage:
    python eco_fix.py
    python eco_fix.py verify | ci-triage | dead-modules | motors-dedup | ai-recon
"""
import ast
import re
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

def read_text(p):
    with open(p, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    return raw, ("\r\n" in raw), raw.replace("\r\n", "\n")

def write_text(p, text, crlf):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", "\r\n") if crlf else text)

def import_smoke(mod, timeout=300):
    code = f"import importlib; importlib.import_module({mod!r}); print('OK')"
    try:
        r = sh([sys.executable, "-c", code], timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout"
    return "OK" if r.returncode == 0 else (r.stderr or r.stdout)[-300:]

def dump(p, lo=1, hi=None, title=None):
    p = Path(p)
    if not p.exists():
        warn(f"not found: {p}"); return
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    hi = hi or len(lines)
    out(f"--- {title or p} (lines {lo}-{min(hi, len(lines))} of {len(lines)}) ---")
    for i in range(lo - 1, min(hi, len(lines))):
        out(f"{i+1:4d}| {lines[i]}")
    out("--- end ---")

def frontend_paths():
    r = git("grep", "-h", "url: ", "--", "frontend/packages/api/src/")
    blob = r.stdout or ""
    return (re.findall(r"url:\s*'([^']+)'", blob)
            + re.findall(r"url:\s*`([^`]+)`", blob))

MAIN = ROOT / "services" / "api_gateway" / "main.py"
MAIN_MOD = "services.api_gateway.main"

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

# ------------------------------------------------------------- ci-triage ---
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"

def ci_triage():
    out(LINE, "STEP 1 — CI triage: why is ci.yml red?", LINE, sep="\n")
    if not CI_YML.exists():
        fail("ci.yml not found at .github/workflows/ci.yml")
        for f in (ROOT / ".github" / "workflows").glob("*"):
            out("    exists: " + f.name)
        return True
    dump(CI_YML, title=".github/workflows/ci.yml (FULL)")

    out("\nstructured step summary:")
    try:
        import yaml
        data = yaml.safe_load(CI_YML.read_text(encoding="utf-8",
                                               errors="replace"))
        for jname, job in (data.get("jobs") or {}).items():
            steps = job.get("steps") or []
            out(f"    job '{jname}' — runs-on: {job.get('runs-on')}, "
                f"{len(steps)} step(s)")
            for s in steps:
                run = s.get("run")
                if run:
                    one = " | ".join(l.strip() for l in str(run).splitlines())
                    out(f"      - {s.get('name', '(unnamed)')}: {one[:160]}")
    except Exception as e:
        warn(f"yaml parse failed ({e!r}) — raw dump above is authoritative")

    out("\nlocal probe A: pytest collection (import health of the suite)")
    try:
        r = sh([sys.executable, "-m", "pytest", "--collect-only", "-q",
                "--no-header"], timeout=600)
        errs = [l for l in r.stdout.splitlines()
                if l.startswith("ERROR") or "ModuleNotFoundError" in l
                or "ImportError" in l or l.startswith("error")]
        out(f"    exit={r.returncode} | collection errors: {len(errs)}")
        for l in errs[:15]:
            out("    " + l[:170])
        tail = [l for l in r.stdout.splitlines() if l.strip()]
        for l in tail[-3:]:
            out("    tail: " + l[:170])
        if "timeout" in r.stdout.lower():
            warn("    (timed out)")
    except subprocess.TimeoutExpired:
        warn("    collection TIMED OUT (>600s) — CI runners likely die here too")

    out("\nlocal probe B: ruff statistics")
    ruff_exe = ROOT / ".venv" / "Scripts" / "ruff.exe"
    cmd = [str(ruff_exe)] if ruff_exe.exists() else ["ruff"]
    try:
        r = sh(cmd + ["check", ".", "--statistics"], timeout=240)
        out(f"    exit={r.returncode}")
        for l in (r.stdout or "").splitlines()[:20]:
            out("    " + l[:170])
        if r.returncode != 0:
            warn("    ruff reports violations (CI may be red on lint)")
    except subprocess.TimeoutExpired:
        warn("    ruff timed out")
    return True

# ----------------------------------------------------------- dead-modules ---
DEAD_MODULES = ["services/api_gateway/dependencies.py",
                "services/api_gateway/register_modules.py"]

def dead_modules():
    out(LINE, "STEP 2 — remove dead infra modules", LINE, sep="\n")
    refs = 0
    for pat in ("api_gateway.dependencies", "api_gateway import dependencies",
                "api_gateway.register_modules", "register_new_modules"):
        r = git("grep", "-n", pat, "--", "services/", "tests/", "scripts/",
                "engine/")
        hits = [l for l in r.stdout.splitlines() if l.strip()
                and not l.startswith("eco_fix.py")]
        refs += len(hits)
        for l in hits[:4]:
            out("    " + l)
    if refs:
        fail(f"{refs} live reference(s) — NOT removing")
        return True
    ok("zero references — both modules confirmed dead")

    base = import_smoke(MAIN_MOD, timeout=300)
    if base != "OK":
        fail("baseline main import failing — aborting")
        out("    " + base[:300])
        return False

    for rel in DEAD_MODULES:
        git("rm", "--", rel)
        ok("git rm " + rel)

    post = import_smoke(MAIN_MOD, timeout=300)
    if post != "OK":
        fail("REGRESSION — restoring removed files")
        for rel in DEAD_MODULES:
            git("reset", "--", rel)
            git("checkout", "--", rel)
        ok("restored — nothing committed")
        return False
    ok("app still imports cleanly without them")

    r = git("commit", "-m",
            "chore(gateway): remove dead modules dependencies.py and "
            "register_modules.py (zero consumers, import-time side effects)")
    ok("committed") if r.returncode == 0 else \
        warn("commit failed: " + (r.stdout + r.stderr)[-300:])
    r = git("push", "origin", "main")
    ok("pushed") if r.returncode == 0 else warn("push failed")
    return True

# ----------------------------------------------------------- motors-dedup ---
def motors_dedup():
    out(LINE, "STEP 3 — motors dual-mount dedup (evidence-gated)", LINE, sep="\n")
    paths = frontend_paths()
    v1 = [p for p in paths if p.startswith("/api/v1/motors")]
    api = [p for p in paths if p.startswith("/api/motors")]
    out(f"    frontend /api/motors refs: {len(api)} | /api/v1/motors refs: {len(v1)}")
    if v1:
        ok("frontend uses the v1 mount too — keeping both, no change")
        return True
    if not api:
        warn("frontend uses neither — needs product decision, skipping")
        return True

    raw, crlf, text = read_text(MAIN)
    pat = re.compile(r'(?m)^app\.include_router\(motors\.router, prefix="/api/v1"[^\n]*\n')
    m = pat.search(text)
    if not m:
        ok("v1 mount not present (already removed?)")
        return True

    base = import_smoke(MAIN_MOD, timeout=300)
    if base != "OK":
        fail("baseline failing — aborting")
        return False

    text2 = text[:m.start()] + text[m.end():]
    ast.parse(text2)
    write_text(MAIN, text2, crlf)

    post = import_smoke(MAIN_MOD, timeout=300)
    if post != "OK":
        fail("REGRESSION — rolling back")
        write_text(MAIN, raw, False)
        ok("original restored")
        return False
    ok("app imports fine without the redundant mount")

    git("add", "--", "services/api_gateway/main.py")
    r = git("commit", "-m",
            "refactor(gateway): drop unused /api/v1 motors mount "
            "(frontend uses /api/motors only)")
    ok("committed") if r.returncode == 0 else \
        warn("commit failed: " + (r.stdout + r.stderr)[-300:])
    r = git("push", "origin", "main")
    ok("pushed") if r.returncode == 0 else warn("push failed")
    return True

# --------------------------------------------------------------- ai-recon ---
def ai_recon():
    out(LINE, "STEP 4 — AI surface recon (consolidation design)", LINE, sep="\n")
    dump(ROOT / "services" / "api_gateway" / "routers" / "ai.py",
         title="ai.py (RAG chat, 83 lines — FULL)")
    dump(ROOT / "services" / "api_gateway" / "routers" / "admin.py",
         lo=1295, hi=1365, title="admin.py AI routes region")
    dump(ROOT / "services" / "api_gateway" / "routers" / "ai_chat.py",
         lo=1, hi=70, title="ai_chat.py head (imports, get_db, models)")
    dump(ROOT / "services" / "api_gateway" / "routers" / "ai_chat.py",
         lo=200, hi=362, title="ai_chat.py endpoints region")

    out("\nunmounted/sleeping routers (parked — product decision later):")
    for f in sorted((ROOT / "services" / "api_gateway" / "routers").glob("*.py")):
        content = f.read_text(encoding="utf-8", errors="replace")
        if "APIRouter(" in content and f.stem in (
                "auth_supabase", "supabase_proxy", "lms", "audit",
                "ogc_router", "ai_advice_router", "insurance", "climate",
                "economy", "lab", "tourism_router", "security_router"):
            m = re.search(r'APIRouter\(\s*prefix="([^"]+)"', content)
            out(f"    {f.name:24s} prefix={m.group(1) if m else '(none)'}")
    return True

# ------------------------------------------------------------------ chore ---
def chore():
    git("add", "--", "eco_fix.py")
    r = git("commit", "-m", "chore: update automation script")
    if r.returncode == 0:
        ok("script committed")
        r2 = git("push", "origin", "main")
        ok("pushed") if r2.returncode == 0 else warn("push failed")
    else:
        ok("nothing to commit")

# ------------------------------------------------------------------- main ---
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"verify": verify, "ci-triage": ci_triage,
             "dead-modules": dead_modules, "motors-dedup": motors_dedup,
             "ai-recon": ai_recon}
    if cmd == "all":
        for name in ("verify", "ci-triage", "dead-modules",
                     "motors-dedup", "ai-recon"):
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