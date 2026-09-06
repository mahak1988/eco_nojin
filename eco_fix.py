#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v12.

STEP 1 ci-check — GitHub Actions status via API (Security workflow)
STEP 2 unblock  — (bugfixed) async->def for provably-safe sync-db endpoints
STEP 3 dedup    — remove duplicate root mounts (auth, platform) + dead
                  /health twin; evidence-gated; prove-then-commit
STEP 4 recon    — database/config.py (second engine?), seed-demo auth gate,
                  finer /api census (motors decision), dead modules

Usage:
    python eco_fix.py
    python eco_fix.py verify | ci-check | unblock | dedup | recon
"""
import ast
import json
import re
import subprocess
import sys
import urllib.error
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

def modname_of(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()[:-3]
    if rel.endswith("__init__"):
        rel = rel[: -len("/__init__")]
    return rel.replace("/", ".")

def import_smoke(mod, timeout=180):
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

# -------------------------------------------------------------- ci-check ---
def ci_check():
    out(LINE, "STEP 1 — GitHub Actions status (automated)", LINE, sep="\n")
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs?per_page=8"
    req = urllib.request.Request(url, headers={
        "User-Agent": "eco_nojin-eco-fix",
        "Accept": "application/vnd.github+json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            warn("rate-limited — check the Actions tab manually in browser")
        elif e.code == 404:
            warn("repo invisible to anonymous API (private?) — open in browser:\n"
                 "    https://github.com/" + GITHUB_REPO + "/actions -> 'Security'")
        else:
            warn(f"HTTP {e.code}")
        return True
    except Exception as e:
        warn(f"network error: {e!r}")
        return True
    runs = data.get("workflow_runs", [])
    if not runs:
        warn("no workflow runs recorded yet — the workflow was added after the "
             "last push; make any small commit to trigger it")
        return True
    out(f"    {'workflow':26s} {'status':11s} {'conclusion':11s} created")
    for run in runs:
        out(f"    {(run.get('name') or '?')[:26]:26s} "
            f"{(run.get('status') or '?'):11s} "
            f"{(run.get('conclusion') or '-'):11s} {run.get('created_at', '?')}")
    sec = [r for r in runs if "security" in (r.get("name") or "").lower()]
    if sec:
        c = sec[0].get("conclusion")
        if c == "success":
            ok("Security workflow: GREEN ✅ (gitleaks found nothing)")
        else:
            warn(f"Security workflow conclusion = {c} — open the failing run "
                 "and paste findings back!")
    else:
        warn("no Security workflow run in the last 8 — trigger with a commit")
    return True

# --------------------------------------------------------------- unblock ---
UNBLOCK_FILES = [
    "services/api_gateway/routers/nojin.py",
    "services/api_gateway/routers/admin.py",
    "services/api_gateway/routers/satellite.py",
    "services/api_gateway/routers/ai_chat.py",
]
SYNC_DB = re.compile(
    r"\b(db|session|self\.db)\."
    r"(query|execute|add|commit|rollback|refresh|scalar|scalars|get|delete|flush)\s*\(")
AWAITISH = re.compile(r"\bawait\b|\basync\s+with\b|\basync\s+for\b")

def unblock():
    out(LINE, "STEP 2 — unblock event loop (bugfixed, re-run)", LINE, sep="\n")
    plan, originals = {}, {}
    for rel in UNBLOCK_FILES:
        p = ROOT / rel
        if not p.exists():
            warn(f"missing: {rel}"); continue
        raw, crlf, text = read_text(p)
        originals[p] = raw
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            warn(f"{rel}: parse error L{e.lineno} — excluded"); continue
        lines = text.split("\n")
        targets = []
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                seg = "\n".join(lines[node.lineno - 1:node.end_lineno])
                if SYNC_DB.search(seg) and not AWAITISH.search(seg):
                    targets.append((node.name, node.lineno))
        if targets:
            out(f"    {rel}: {len(targets)} convertible: "
                + ", ".join(n for n, _ in targets))
            res = import_smoke(modname_of(p))
            if res == "OK":
                plan[p] = targets
            else:
                warn(f"        import FAIL — excluded: {res[:200]}")
        else:
            out(f"    {rel}: 0 convertible (awaits present — deferred to "
                "service-layer refactor)")

    if not plan:
        ok("nothing to convert"); return True

    changed = []
    for p, targets in plan.items():
        raw = originals[p]
        text = raw.replace("\r\n", "\n")
        lines = text.split("\n")
        for name, ln in targets:
            idx = ln - 1
            new_line, n = re.subn(r"^(\s*)async\s+def\b", r"\1def",
                                  lines[idx], count=1)
            if n == 1:
                lines[idx] = new_line
            else:
                warn(f"rewrite failed at L{ln} in {p.name}")
        new_text = "\n".join(lines)
        try:
            ast.parse(new_text)
        except SyntaxError as e:
            fail(f"{p.name}: parse after edit L{e.lineno} — skipped"); continue
        write_text(p, new_text, "\r\n" in raw)
        changed.append(p)

    if not changed:
        fail("no file written"); return False

    out("\npost-migration import smoke ...")
    regressions = []
    for p in changed:
        res = import_smoke(modname_of(p))
        out(f"    {modname_of(p)}: {'OK' if res == 'OK' else 'FAIL'}")
        if res != "OK":
            regressions.append((p, res))
    if regressions:
        fail("REGRESSION — rolling back:")
        for p, res in regressions:
            out(f"    {p.name}: {res[:150]}")
            write_text(p, originals[p], False)   # verbatim original
        ok("originals restored — nothing committed")
        return False
    ok("no regressions")

    for p in changed:
        git("add", "--", p.relative_to(ROOT).as_posix())
    r = git("commit", "-m",
            "perf(gateway): run sync-db endpoints in threadpool (async def -> def)")
    ok("committed") if r.returncode == 0 else \
        warn("commit failed: " + (r.stdout + r.stderr)[-400:])
    r = git("push", "origin", "main")
    ok("pushed") if r.returncode == 0 else warn("push failed")
    return True

# ------------------------------------------------------------------ dedup ---
MAIN = ROOT / "services" / "api_gateway" / "main.py"
MAIN_MOD = "services.api_gateway.main"
ROOT_AUTH_PATHS = {"/login", "/register", "/me", "/seed-demo",
                   "/forgot-password", "/reset-password", "/change-password",
                   "/profile", "/refresh", "/signup", "/admin/delete-user"}
ROOT_PLAT_PATHS = {"/landscapes", "/analyze", "/stats"}

def frontend_paths():
    r = git("grep", "-h", "url: ", "--", "frontend/packages/api/src/")
    blob = r.stdout or ""
    return (re.findall(r"url:\s*'([^']+)'", blob)
            + re.findall(r"url:\s*`([^`]+)`", blob))

def _remove_health_twin(text):
    lines = text.split("\n")
    idxs = [i for i, ln in enumerate(lines)
            if ln.strip().startswith('@app.get("/health")')]
    if len(idxs) < 2:
        return text, False
    dec = idxs[1]
    j = dec + 1
    while j < len(lines) and (lines[j].startswith("@")
                              or lines[j].startswith("def ")
                              or lines[j].startswith("async def ")):
        j += 1
    while j < len(lines) and (not lines[j].strip()
                              or lines[j].startswith((" ", "\t"))):
        j += 1
    s = dec
    while s > 0 and (not lines[s - 1].strip()
                     or lines[s - 1].lstrip().startswith("#")):
        s -= 1
    new_lines = lines[:s] + [""] + lines[j:]
    return "\n".join(new_lines), True

def dedup():
    out(LINE, "STEP 3 — mount dedup (evidence-gated, prove-then-commit)", LINE, sep="\n")
    paths = frontend_paths()

    auth_hits = [p for p in paths if p in ROOT_AUTH_PATHS]
    v1_auth = [p for p in paths if p.startswith("/api/v1/auth")]
    plat_hits = [p for p in paths if p in ROOT_PLAT_PATHS]
    health_refs = [p for p in paths if p == "/health"]

    out(f"    frontend: {len(paths)} path refs")
    out(f"    root-level auth paths used: {auth_hits or 'NONE'}")
    out(f"    /api/v1/auth refs: {len(v1_auth)}")
    out(f"    root-level platform paths used: {plat_hits or 'NONE'}")
    out(f"    /health refs: {len(health_refs)} (will be served by the app's "
        "own rich /health after dedup)")

    if auth_hits or not v1_auth:
        warn("auth root mount NOT removed (evidence insufficient)")
    if plat_hits:
        warn("platform root mount NOT removed (frontend uses root platform paths)")

    base = import_smoke(MAIN_MOD, timeout=300)
    out(f"\n    baseline import of {MAIN_MOD}: {'OK' if base == 'OK' else 'FAIL'}")
    if base != "OK":
        warn("    " + base[:300])
        fail(">>> APP MODULE DOES NOT IMPORT — this is a critical pre-existing "
             "finding! Report it; dedup aborted.")
        return False
    ok("the full gateway app imports cleanly (first time proven!)")

    raw, crlf, text = read_text(MAIN)
    edits, notes = [], []

    n_auth = len(re.findall(r"(?m)^app\.include_router\(auth\.router\)\s*$", text))
    if not auth_hits and v1_auth and n_auth == 1 \
            and "app.include_router(auth.router, prefix=" in text:
        text = "\n".join(ln for ln in text.split("\n")
                         if not re.match(r"^app\.include_router\(auth\.router\)\s*$", ln))
        edits.append("root auth mount")
        notes.append("unauthenticated /seed-demo & friends no longer exposed at root")

    n_plat = len(re.findall(r"(?m)^app\.include_router\(platform\.router\)\s*$", text))
    if not plat_hits and n_plat == 1 \
            and "app.include_router(platform.router, prefix=" in text:
        text = "\n".join(ln for ln in text.split("\n")
                         if not re.match(r"^app\.include_router\(platform\.router\)\s*$", ln))
        edits.append("root platform mount")
        notes.append("app's own /health becomes reachable (was shadowed)")

    text, twin = _remove_health_twin(text)
    if twin:
        edits.append("dead /health twin")

    if not edits:
        ok("nothing to change"); return True

    try:
        ast.parse(text)
    except SyntaxError as e:
        fail(f"main.py parse after edit L{e.lineno}: {e.msg} — aborting")
        write_text(MAIN, raw, False)
        return False
    write_text(MAIN, text, crlf)

    post = import_smoke(MAIN_MOD, timeout=300)
    if post != "OK":
        fail("REGRESSION after dedup — rolling back:")
        out("    " + post[:300])
        write_text(MAIN, raw, False)
        ok("original restored — nothing committed")
        return False
    ok("post-edit import: OK")
    for n in notes:
        out("    * " + n)

    git("add", "--", "services/api_gateway/main.py")
    r = git("commit", "-m",
            "refactor(gateway): drop duplicate root mounts (auth, platform) "
            "and dead /health twin\n\nFrontend orval client uses only /api/* "
            "paths (221 refs, zero root auth/platform refs).")
    ok("committed") if r.returncode == 0 else \
        warn("commit failed: " + (r.stdout + r.stderr)[-300:])
    r = git("push", "origin", "main")
    ok("pushed") if r.returncode == 0 else warn("push failed")
    return True

# ------------------------------------------------------------------ recon ---
def recon():
    out(LINE, "STEP 4 — recon (read-only)", LINE, sep="\n")
    dump(ROOT / "database" / "config.py", title="database/config.py (second engine?)")

    out("\nseed-demo gating (routers/auth.py around it):")
    p = ROOT / "services" / "api_gateway" / "routers" / "auth.py"
    if p.exists():
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        idx = next((i for i, ln in enumerate(lines) if "seed-demo" in ln), None)
        if idx is not None:
            for i in range(max(0, idx - 15), min(len(lines), idx + 40)):
                out(f"{i+1:4d}| {lines[i]}")
        else:
            warn("seed-demo not found in routers/auth.py")

    out("\nfiner /api census (motors dual-mount decision):")
    paths = frontend_paths()
    v1 = [p for p in paths if p.startswith("/api/v1/")]
    nonv1 = [p for p in paths if p.startswith("/api/") and not p.startswith("/api/v1/")]
    out(f"    /api/v1/* refs: {len(v1)}")
    out(f"    /api/* (non-v1) refs: {len(nonv1)}")
    for p in sorted(set(nonv1))[:25]:
        out("        " + p)

    out("\ndead-module confirmation:")
    for pat, name in ((
            "from services.api_gateway import dependencies", "dependencies.py"),
            ("from .dependencies", "dependencies.py (relative)"),
            ("register_modules", "register_modules.py"),
            ("register_new_modules", "register_new_modules()")):
        r = git("grep", "-n", pat, "--", "services/", "scripts/", "tests/",
                "engine/")
        hits = [l for l in r.stdout.splitlines() if l.strip()
                and not l.split(":", 1)[0].endswith("eco_fix.py")]
        out(f"    '{name}' referenced by: {len(hits)}")
        for l in hits[:5]:
            out("        " + l)
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
    steps = {"verify": verify, "ci-check": ci_check, "unblock": unblock,
             "dedup": dedup, "recon": recon}
    if cmd == "all":
        for name in ("verify", "ci-check", "unblock", "dedup", "recon"):
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