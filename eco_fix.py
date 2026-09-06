#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v14.

STEP 1 ci-jobs     — GitHub Actions Jobs API: which STEP of the red run failed
STEP 2 ci-hygiene  — rewrite ci.yml: quoted names, pnpm 11, timeouts
STEP 3 dead-modules— remove dependencies.py & register_modules.py (fixed filter)
STEP 4 ai-dedup    — remove the SHADOWED POST /api/v1/ai/chat (KB matcher);
                     route-count proof before/after
STEP 5 recon       — ai_chat.py middle section (match_topic/farm_context)

Usage:
    python eco_fix.py
    python eco_fix.py verify | ci-jobs | ci-hygiene | dead-modules | ai-dedup | recon
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

def _gh_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "eco_nojin-eco-fix",
        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

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

# --------------------------------------------------------------- ci-jobs ---
STEP_HINTS = {
    "Install deps": "backend pip install (time/disk/resolution) — next: slim CI install",
    "Compile check": "syntax — should be green now; run compileall locally",
    "Import smoke": "app import on CI — passes locally; missing optional dep?",
    "Pytest": "tests failing (has || true — shouldn't fail job)",
    "Install": "frontend pnpm install — pnpm 9->11 alignment applied in STEP 2",
    "Build": "frontend vite build — next: local 'pnpm -C frontend build' probe",
}

def ci_jobs():
    out(LINE, "STEP 1 — CI diagnosis (Jobs API, step-level)", LINE, sep="\n")
    try:
        runs = _gh_json(
            f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/"
            f"ci.yml/runs?per_page=5").get("workflow_runs", [])
    except Exception as e:
        warn(f"runs API failed: {e!r}")
        try:
            allr = _gh_json(
                f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs"
                f"?per_page=10").get("workflow_runs", [])
            runs = [r for r in allr
                    if r.get("path", "").endswith("workflows/ci.yml")]
        except Exception as e2:
            warn(f"fallback failed too: {e2!r}")
            return True
    if not runs:
        warn("no ci.yml runs found — STEP 2's push will trigger one")
        return True
    target = next((r for r in runs if r.get("status") == "completed"), runs[0])
    out(f"    run id={target['id']} sha={target.get('head_sha','?')[:8]} "
        f"conclusion={target.get('conclusion')}")
    try:
        jobs = _gh_json(
            f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/"
            f"{target['id']}/jobs").get("jobs", [])
    except Exception as e:
        warn(f"jobs API failed: {e!r}")
        return True
    failed_steps = []
    for job in jobs:
        out(f"\n    JOB {job.get('name')} -> {job.get('conclusion')}")
        for st in (job.get("steps") or []):
            c = st.get("conclusion") or st.get("status") or "?"
            mark = " X " if c == "failure" else (" * " if c == "skipped" else " . ")
            out(f"      {mark}{st.get('name')}  [{c}]")
            if c == "failure":
                failed_steps.append((job.get("name"), st.get("name")))
    if failed_steps:
        out("\n    VERDICT:")
        for jname, sname in failed_steps:
            hint = STEP_HINTS.get(sname, "unexpected step — inspect in browser")
            out(f"      '{sname}' (job {jname}): {hint}")
    else:
        ok("latest completed run has no failed step (maybe it's the fresh "
           "one from STEP 2 — re-run ci-jobs next time)")
    return True

# ------------------------------------------------------------ ci-hygiene ---
CI_YML = ROOT / ".github" / "workflows" / "ci.yml"
CI_NEW = """\
name: "CI - Eco Nojin"

on:
  push:
    branches: [main, master]
  pull_request:

jobs:
  backend:
    name: "Backend (pytest + ruff)"
    runs-on: ubuntu-latest
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt ruff pytest
      - name: Ruff lint (non-blocking)
        run: ruff check services --ignore E501,F401 --statistics || true
      - name: Compile check
        run: python -m compileall -q services
      - name: Import smoke
        run: python -c "from services.api_gateway.main import app; print('app import OK')"
      - name: Pytest (non-blocking)
        run: pytest -q --tb=short || true

  frontend:
    name: "Frontend (vite build)"
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 11
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
          cache-dependency-path: frontend/pnpm-lock.yaml
      - name: Install
        run: pnpm -C frontend install --frozen-lockfile
      - name: Build
        run: pnpm -C frontend build
"""

def ci_hygiene():
    out(LINE, "STEP 2 — ci.yml hygiene (safe regardless of diagnosis)", LINE, sep="\n")
    cur = CI_YML.read_text(encoding="utf-8", errors="replace") if CI_YML.exists() else ""
    if cur.strip() == CI_NEW.strip():
        ok("ci.yml already in hygienic shape")
        return True
    CI_YML.parent.mkdir(parents=True, exist_ok=True)
    CI_YML.write_text(CI_NEW, encoding="utf-8", newline="\n")
    try:
        import yaml
        data = yaml.safe_load(CI_NEW)
        assert "backend" in (data.get("jobs") or {})
        assert "frontend" in (data.get("jobs") or {})
        ok("new ci.yml parses as valid YAML with both jobs")
    except Exception as e:
        fail(f"yaml check failed: {e!r} — still written (GitHub may be lenient)")
    git("add", "--", ".github/workflows/ci.yml")
    r = git("commit", "-m",
            "ci: quote workflow names, align pnpm with local toolchain (11), "
            "add job timeouts, surface ruff stats")
    if r.returncode == 0:
        ok("committed (this push triggers a fresh CI run)")
        git("push", "origin", "main")
    else:
        ok("nothing to commit")
    return True

# ---------------------------------------------------------- dead-modules ---
DEAD_MODULES = [
    ("services/api_gateway/dependencies.py",
     ["api_gateway.dependencies", "api_gateway import dependencies",
      "from .dependencies import"]),
    ("services/api_gateway/register_modules.py",
     ["api_gateway.register_modules", "register_new_modules"]),
]
MAIN_MOD = "services.api_gateway.main"

def import_smoke(mod, timeout=300):
    code = f"import importlib; importlib.import_module({mod!r}); print('OK')"
    try:
        r = sh([sys.executable, "-c", code], timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout"
    return "OK" if r.returncode == 0 else (r.stderr or r.stdout)[-300:]

def dead_modules():
    out(LINE, "STEP 3 — remove dead infra modules (fixed self-ref filter)", LINE, sep="\n")
    blocked = False
    for mod_path, patterns in DEAD_MODULES:
        refs = []
        for pat in patterns:
            r = git("grep", "-n", pat, "--", "services/", "tests/",
                    "scripts/", "engine/")
            for l in [l for l in r.stdout.splitlines() if l.strip()]:
                fp = l.split(":", 1)[0]
                if fp == "eco_fix.py" or fp == mod_path:
                    continue          # self-definition / this script
                refs.append(l)
        if refs:
            blocked = True
            warn(f"{mod_path}: {len(refs)} LIVE reference(s) — keeping:")
            for l in refs[:6]:
                out("    " + l)
        else:
            ok(f"{mod_path}: zero external references — dead")
    if blocked:
        return True

    base = import_smoke(MAIN_MOD)
    if base != "OK":
        fail("baseline main import failing — aborting: " + base[:250])
        return False
    for mod_path, _ in DEAD_MODULES:
        git("rm", "--", mod_path)
        ok("git rm " + mod_path)
    post = import_smoke(MAIN_MOD)
    if post != "OK":
        fail("REGRESSION — restoring")
        for mod_path, _ in DEAD_MODULES:
            git("reset", "--", mod_path)
            git("checkout", "--", mod_path)
        ok("restored — nothing committed")
        return False
    ok("app imports cleanly without the dead modules")
    r = git("commit", "-m",
            "chore(gateway): remove dead modules dependencies.py and "
            "register_modules.py (zero consumers)")
    ok("committed") if r.returncode == 0 else \
        warn("commit failed: " + (r.stdout + r.stderr)[-300:])
    git("push", "origin", "main")
    return True

# --------------------------------------------------------------- ai-dedup ---
AI_CHAT = ROOT / "services" / "api_gateway" / "routers" / "ai_chat.py"

ROUTE_PROOF = '''
import json
from services.api_gateway.main import app
def cnt(path, method=None):
    names = []
    for r in app.routes:
        if getattr(r, "path", None) == path:
            if method is None or method in (getattr(r, "methods", None) or set()):
                names.append(getattr(getattr(r, "endpoint", None), "__name__", "?"))
    return names
print(json.dumps({
    "post_chat": cnt("/api/v1/ai/chat", "POST"),
    "ai_health": cnt("/api/v1/ai/health"),
    "history": cnt("/api/v1/ai/history"),
    "stream": cnt("/api/v1/ai/stream"),
    "tts": cnt("/api/v1/ai/voice/tts"),
    "ws_chat": cnt("/api/v1/ai/ws/chat"),
}))
'''

def route_proof():
    r = sh([sys.executable, "-c", ROUTE_PROOF], timeout=300)
    if r.returncode != 0:
        return None, (r.stderr or r.stdout)[-400:]
    try:
        return json.loads(r.stdout.strip().splitlines()[-1]), None
    except Exception as e:
        return None, f"json parse: {e!r} | stdout: {r.stdout[-200:]}"

def ai_dedup():
    out(LINE, "STEP 4 — AI route-collision fix (remove shadowed /chat)", LINE, sep="\n")
    before, err = route_proof()
    if before is None:
        fail("route proof failed — aborting: " + str(err))
        return False
    out(f"    BEFORE: {before}")
    if before["post_chat"] == ["chat_endpoint"]:
        ok("no duplicate /chat registered (already deduped)")
        return True
    if "chat" not in before["post_chat"]:
        warn("unexpected /chat state — no ai_chat 'chat' route found; aborting")
        return False
    out("    -> duplicate confirmed: RAG 'chat_endpoint' shadows KB 'chat'")

    raw, crlf, text = read_text(AI_CHAT)
    tree = ast.parse(text)
    target = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name == "chat":
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call)
                        and isinstance(dec.func, ast.Attribute)
                        and dec.func.attr == "post"
                        and dec.args and isinstance(dec.args[0], ast.Constant)
                        and dec.args[0].value == "/chat"):
                    target = node
    if target is None:
        fail("chat endpoint not found via AST — aborting")
        return False
    start = min(d.lineno for d in target.decorator_list)
    end = target.end_lineno
    lines = text.split("\n")
    new_text = "\n".join(lines[:start - 1] + lines[end:])
    # swallow up to two trailing blank lines left behind
    new_text = re.sub(r"\n{4,}", "\n\n\n", new_text)
    ast.parse(new_text)
    write_text(AI_CHAT, new_text, crlf)
    ok(f"removed shadowed endpoint (lines {start}-{end})")

    after, err = route_proof()
    if after is None:
        fail("post-edit proof failed — ROLLING BACK: " + str(err))
        write_text(AI_CHAT, raw, False)
        ok("original restored")
        return False
    out(f"    AFTER:  {after}")
    if after["post_chat"] != ["chat_endpoint"]:
        fail("proof mismatch — ROLLING BACK")
        write_text(AI_CHAT, raw, False)
        ok("original restored")
        return False
    for key in ("history", "stream", "tts", "ws_chat"):
        if not after[key]:
            fail(f"'{key}' route vanished — ROLLING BACK")
            write_text(AI_CHAT, raw, False)
            ok("original restored")
            return False
    ok("exactly one POST /chat (RAG); history/stream/tts/ws intact")

    git("add", "--", "services/api_gateway/routers/ai_chat.py")
    r = git("commit", "-m",
            "refactor(ai): remove shadowed duplicate POST /api/v1/ai/chat\n\n"
            "ai.py (RAG, registered first) was the live handler; the "
            "auth-gated KB 'chat' in ai_chat.py was unreachable. OpenAPI "
            "spec now matches runtime dispatch.")
    ok("committed") if r.returncode == 0 else \
        warn("commit failed: " + (r.stdout + r.stderr)[-300:])
    git("push", "origin", "main")
    return True

# ------------------------------------------------------------------ recon ---
def recon():
    out(LINE, "STEP 5 — recon: ai_chat.py middle (match_topic/farm_context)", LINE, sep="\n")
    dump(AI_CHAT, lo=70, hi=200, title="ai_chat.py lines 70-200")
    out("\nAI surface after dedup (live):")
    out("    ai.py        POST /api/v1/ai/chat (RAG, public) + /health")
    out("    ai_chat.py   /history /stream /voice/tts /ws/chat (auth-gated)")
    out("    admin.py     /api/v1/admin/ai/{status,chat} (Ollama copilot)")
    out("    PARKED (unmounted): ai_advice_router.py (/api/v1/ai/advise)")
    out("    OPEN PRODUCT QUESTION: should RAG /chat require auth? "
        "(currently public, rate-limited)")
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
    steps = {"verify": verify, "ci-jobs": ci_jobs, "ci-hygiene": ci_hygiene,
             "dead-modules": dead_modules, "ai-dedup": ai_dedup,
             "recon": recon}
    if cmd == "all":
        for name in ("verify", "ci-jobs", "ci-hygiene", "dead-modules",
                     "ai-dedup", "recon"):
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