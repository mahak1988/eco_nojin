#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v15.

STEP 1 route-map — AST-based mount map of main.py + live app.routes
                  enumeration; global route-collision report
STEP 2 ci-jobs  — fresh GitHub run verdict (after recent pushes)
STEP 3 ai-dedup — route-map-evidenced removal of the shadowed POST /chat
STEP 4 recon    — ai_chat head after dedup + ruff F821 hotspots

Usage:
    python eco_fix.py
    python eco_fix.py verify | route-map | ci-jobs | ai-dedup | recon
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

# -------------------------------------------------------------- route-map ---
MOUNT_PROBE = """
import json, ast
from pathlib import Path
src = Path('services/api_gateway/main.py').read_text(encoding='utf-8', errors='replace')
tree = ast.parse(src)
mounts = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == 'include_router':
        router_expr = node.args[0]
        if isinstance(router_expr, ast.Attribute):
            name = router_expr.attr
        elif isinstance(router_expr, ast.Name):
            name = router_expr.id
        else:
            name = '?'
        prefix = ''
        for kw in node.keywords:
            if kw.arg == 'prefix' and isinstance(kw.value, ast.Constant):
                prefix = kw.value.value
        mounts.append({'router': name, 'prefix': prefix})
print('MOUNTS:' + json.dumps(mounts))

from services.api_gateway.main import app
rows = []
for r in app.routes:
    path = getattr(r, 'path', None)
    if not path:
        continue
    methods = sorted(getattr(r, 'methods', None) or []) or ['WS']
    ep = getattr(getattr(r, 'endpoint', None), '__name__', '?')
    rows.append({'path': path, 'methods': ','.join(methods), 'ep': ep})
print('ROUTES:' + json.dumps(rows))
"""

def route_map():
    out(LINE, "STEP 1 — route map (AST mounts + live app.routes)", LINE, sep="\n")
    r = sh([sys.executable, "-c", MOUNT_PROBE], timeout=300)
    if r.returncode != 0:
        fail("probe failed: " + (r.stderr or r.stdout)[-500:])
        return None
    mounts = routes = None
    for line in r.stdout.splitlines():
        if line.startswith("MOUNTS:"):
            mounts = json.loads(line[7:])
        elif line.startswith("ROUTES:"):
            routes = json.loads(line[8:])
    if mounts is None or routes is None:
        fail("probe output unparsable")
        return None
    out("mounts (AST):")
    for m in mounts:
        out(f"    {m['router']:16s} prefix={m['prefix'] or '(none)'}")
    out(f"\nlive routes: {len(routes)}")
    ai = [row for row in routes if row["path"].startswith("/api/v1/ai")]
    out(f"AI routes ({len(ai)}):")
    for row in sorted(ai, key=lambda x: x["path"]):
        out(f"    {row['methods']:8s} {row['path']:34s} -> {row['ep']}")
    out("\nroute-collision audit (same path+method, different endpoints):")
    seen = {}
    for row in routes:
        k = (row["path"], row["methods"])
        seen.setdefault(k, []).append(row["ep"])
    collided = 0
    for (p, m), eps in sorted(seen.items()):
        if len(eps) > 1:
            collided += 1
            out(f"    {m:8s} {p}: {eps}  <== COLLISION")
    if not collided:
        ok("no collisions found across all mounted routes")
    return routes

# --------------------------------------------------------------- ci-jobs ---
STEP_HINTS = {
    "Install deps": "backend pip install (time/disk) — next: slim install",
    "Compile check": "syntax",
    "Import smoke": "app import on CI",
    "Pytest": "tests (has || true)",
    "Install": "frontend pnpm install — pnpm aligned to 11",
    "Build": "frontend build — probe locally",
}

def ci_jobs():
    out(LINE, "STEP 2 — CI diagnosis (fresh runs)", LINE, sep="\n")
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
    if not target:
        warn("no completed run yet — re-run ci-jobs after a few minutes")
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
                failed.append((job.get("name"), st.get("name")))
    if failed:
        out("\n    VERDICT:")
        for j, s in failed:
            out(f"      '{s}' (job {j}): " + STEP_HINTS.get(s, "inspect in browser"))
    else:
        ok("no failed steps in the latest completed run — possibly GREEN now!")
    return True

# --------------------------------------------------------------- ai-dedup ---
AI_CHAT = ROOT / "services" / "api_gateway" / "routers" / "ai_chat.py"

def ai_dedup():
    out(LINE, "STEP 3 — AI dedup (route-map evidence)", LINE, sep="\n")
    routes = route_map()
    if routes is None:
        return False
    chat_routes = [r for r in routes
                   if r["path"].endswith("/chat") and "POST" in r["methods"]]
    out(f"\n    POST .../chat routes: "
        + str([(r["path"], r["ep"]) for r in chat_routes]))
    dup = {}
    for r in chat_routes:
        dup.setdefault(r["path"], []).append(r["ep"])
    collision_path = next((p for p, eps in dup.items() if len(eps) > 1), None)
    if not collision_path:
        ok("no AI /chat collision — dedup complete (or already done)")
        return True
    eps = dup[collision_path]
    out(f"    collision at {collision_path}: {eps}")
    if "chat" not in eps or "chat_endpoint" not in eps:
        warn("unexpected endpoint names — aborting for manual review")
        return True

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
                        and dec.args
                        and isinstance(dec.args[0], ast.Constant)
                        and dec.args[0].value == "/chat"):
                    target = node
    if target is None:
        fail("chat endpoint not found in ai_chat.py — aborting")
        return False
    start = min(d.lineno for d in target.decorator_list)
    end = target.end_lineno
    lines = text.split("\n")
    new_text = re.sub(r"\n{4,}", "\n\n\n",
                      "\n".join(lines[: start - 1] + lines[end:]))
    ast.parse(new_text)
    write_text(AI_CHAT, new_text, crlf)
    ok(f"removed dead 'chat' endpoint (lines {start}-{end})")

    routes2 = route_map()
    if routes2 is None:
        fail("post-proof failed — ROLLING BACK")
        write_text(AI_CHAT, raw, False)
        ok("original restored")
        return False
    eps2 = [r["ep"] for r in routes2
            if r["path"] == collision_path and "POST" in r["methods"]]
    if eps2 != ["chat_endpoint"]:
        fail(f"post-proof mismatch ({eps2}) — ROLLING BACK")
        write_text(AI_CHAT, raw, False)
        ok("original restored")
        return False
    ok(f"{collision_path} now served only by 'chat_endpoint' (RAG)")
    git("add", "--", "services/api_gateway/routers/ai_chat.py")
    r = git("commit", "-m",
            "refactor(ai): remove shadowed duplicate POST /api/v1/ai/chat\n\n"
            "ai.py (RAG) was registered first and was the live handler; the "
            "auth-gated KB 'chat' in ai_chat.py was unreachable dead code.")
    if r.returncode == 0:
        ok("committed")
    else:
        warn("commit failed: " + (r.stdout + r.stderr)[-300:])
    git("push", "origin", "main")
    return True

# ------------------------------------------------------------------ recon ---
def recon():
    out(LINE, "STEP 4 — recon", LINE, sep="\n")
    dump(AI_CHAT, lo=1, hi=30, title="ai_chat.py head after dedup")
    out("\nruff F821 (undefined names) hotspots — next quality target:")
    ruff_exe = ROOT / ".venv" / "Scripts" / "ruff.exe"
    cmd = [str(ruff_exe)] if ruff_exe.exists() else ["ruff"]
    r = sh(cmd + ["check", ".", "--select", "F821", "--output-format", "concise"],
           timeout=240)
    hits = [l for l in (r.stdout or "").splitlines() if "F821" in l]
    out(f"    total F821: {len(hits)}")
    by_file = {}
    for l in hits:
        fp = l.split(":", 1)[0]
        by_file[fp] = by_file.get(fp, 0) + 1
    for fp, n in sorted(by_file.items(), key=lambda kv: -kv[1])[:15]:
        out(f"    {n:4d}  {fp}")
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
    steps = {"verify": verify, "route-map": route_map,
             "ci-jobs": ci_jobs, "ai-dedup": ai_dedup, "recon": recon}
    if cmd == "all":
        for name in ("verify", "route-map", "ci-jobs", "ai-dedup", "recon"):
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