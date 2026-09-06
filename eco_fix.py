#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v11 — event-loop unblocking + gateway hygiene.

STEP 1 unblock: async endpoints using a SYNC session with NO awaits in
       body -> plain `def` (FastAPI runs them in threadpool — correct
       pattern for blocking IO). ast-based, prove-then-commit, rollback.
STEP 2 main.py: fix broken f-string (HOST not interpolated).
STEP 3 untrack *.offgit backups + gitignore pattern.
STEP 4 recon: main.py tail, register_modules, nojin get_db,
       database/__init__, frontend mutator + generated path inventory.

Usage:
    python eco_fix.py
    python eco_fix.py verify | unblock | mainfix | offgit | recon
"""
import ast
import re
import subprocess
import sys
from collections import Counter
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

def modname_of(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()[:-3]
    if rel.endswith("__init__"):
        rel = rel[: -len("/__init__")]
    return rel.replace("/", ".")

def import_smoke(mod, timeout=150):
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
    out(LINE, "STEP 1 — unblock event loop (async->def where provably safe)", LINE, sep="\n")
    plan, originals = {}, {}
    for rel in UNBLOCK_FILES:
        p = ROOT / rel
        if not p.exists():
            warn(f"missing: {rel}"); continue
        raw, crlf, text = read_text(p)
        originals[p] = (raw, crlf)
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            warn(f"{rel}: parse error line {e.lineno} — excluded"); continue
        lines = text.split("\n")
        targets = []
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                seg = "\n".join(lines[node.lineno - 1:node.end_lineno])
                if SYNC_DB.search(seg) and not AWAITISH.search(seg):
                    targets.append((node.name, node.lineno))
        out(f"    {rel}: {len(targets)} convertible endpoint(s)"
            + (f" -> {', '.join(n for n, _ in targets)}" if targets else ""))
        if not targets:
            continue
        res = import_smoke(modname_of(p))
        out(f"        baseline import: {'OK' if res == 'OK' else 'FAIL — excluded'}")
        if res != "OK":
            warn(f"        {res[:200]}")
            continue
        plan[p] = targets

    if not plan:
        ok("nothing convertible & provable — done")
        return True

    changed = []
    for p, targets in plan.items():
        raw, crlf, text = originals[p]
        lines = text.split("\n")
        for name, ln in targets:
            idx = ln - 1
            new_line, n = re.subn(r"^(\s*)async\s+def\b", r"\1def",
                                  lines[idx], count=1)
            if n == 1:
                lines[idx] = new_line
            else:
                warn(f"could not rewrite line {ln} in {p.name}")
        new_text = "\n".join(lines)
        try:
            ast.parse(new_text)
        except SyntaxError as e:
            fail(f"{p.name}: parse failed after edit (line {e.lineno}) — skipped")
            continue
        write_text(p, new_text, crlf)
        _, _, check = read_text(p)
        ast.parse(check)          # paranoia: re-read from disk
        changed.append((p, targets))
    if not changed:
        fail("no file written"); return False

    out("\npost-migration import smoke ...")
    regressions = []
    for p, _ in changed:
        res = import_smoke(modname_of(p))
        out(f"    {modname_of(p)}: {'OK' if res == 'OK' else 'FAIL'}")
        if res != "OK":
            regressions.append((p, res))
    if regressions:
        fail("REGRESSION — rolling back:")
        for p, res in regressions:
            out(f"    {p.name}: {res[:150]}")
            raw, crlf = originals[p]
            write_text(p, raw if not crlf else raw.replace("\n", "\r\n"), crlf)
        ok("originals restored — nothing committed")
        return False
    ok("no regressions")

    for p, targets in changed:
        git("add", "--", p.relative_to(ROOT).as_posix())
        out(f"    staged {p.relative_to(ROOT).as_posix()} "
            f"({len(targets)} endpoints)")
    r = git("commit", "-m",
            "perf(gateway): run sync-db endpoints in threadpool (async def -> def)")
    ok("committed") if r.returncode == 0 else \
        warn("commit failed: " + (r.stdout + r.stderr)[-400:])
    r = git("push", "origin", "main")
    ok("pushed") if r.returncode == 0 else warn("push failed")
    return True

# ---------------------------------------------------------------- mainfix ---
MAIN = ROOT / "services" / "api_gateway" / "main.py"
FSTR_OLD = "http://os.environ.get('HOST', '127.0.0.1'):8000/docs"
FSTR_NEW = "http://{os.environ.get('HOST', '127.0.0.1')}:8000/docs"

def mainfix():
    out(LINE, "STEP 2 — main.py f-string fix", LINE, sep="\n")
    if not MAIN.exists():
        fail("main.py not found"); return False
    raw, crlf, text = read_text(MAIN)
    if FSTR_NEW in text:
        ok("already fixed"); return True
    if FSTR_OLD not in text:
        warn("pattern not found — line changed? skipped"); return True
    text = text.replace(FSTR_OLD, FSTR_NEW, 1)
    ast.parse(text)
    write_text(MAIN, text, crlf)
    ok("f-string fixed — HOST now interpolates in startup log")
    git("add", "--", "services/api_gateway/main.py")
    r = git("commit", "-m", "fix(gateway): interpolate HOST in startup log f-string")
    if r.returncode == 0:
        ok("committed")
        git("push", "origin", "main")
    else:
        ok("nothing to commit")
    return True

# ----------------------------------------------------------------- offgit ---
def offgit():
    out(LINE, "STEP 3 — untrack *.offgit backups", LINE, sep="\n")
    files = [l.strip() for l in git("ls-files").stdout.splitlines() if l.strip()]
    offg = [f for f in files if f.endswith(".offgit")]
    for f in offg:
        git("rm", "--cached", "--", f)
        out("    untracked: " + f)
    ok("no .offgit tracked") if not offg else \
        ok(f"{len(offg)} .offgit file(s) untracked (stay on disk)")
    gi = ROOT / ".gitignore"
    text = gi.read_text(encoding="utf-8", errors="replace")
    if "*.offgit" not in text:
        with open(gi, "a", encoding="utf-8") as fh:
            fh.write("\n# off-site backup snapshots\n*.offgit\n")
        ok("gitignore: *.offgit added")
    git("add", "--", ".gitignore")
    r = git("commit", "-m", "chore: untrack .offgit backup snapshots")
    if r.returncode == 0:
        ok("committed")
        git("push", "origin", "main")
    else:
        ok("nothing to commit")
    return True

# ------------------------------------------------------------------ recon ---
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

def recon():
    out(LINE, "STEP 4 — recon (read-only) for next decisions", LINE, sep="\n")
    dump(ROOT / "services/api_gateway/main.py", lo=318, hi=400, title="main.py tail")
    dump(ROOT / "services/api_gateway/register_modules.py", title="register_modules.py")
    out("\nwho calls register_modules:")
    r = git("grep", "-n", "register_modules", "--", "services/", "scripts/", "tests/")
    for l in [l for l in r.stdout.splitlines() if l.strip()][:15]:
        out("    " + l)
    dump(ROOT / "services/api_gateway/routers/nojin.py", lo=250, hi=300,
         title="nojin.py get_db region")
    dump(ROOT / "database/__init__.py", title="database/__init__.py")

    out("\nfrontend api mutator (base URL + token wiring):")
    dump(ROOT / "frontend/packages/api/src/mutator.ts", hi=90)

    out("\nfrontend generated path inventory (orval client):")
    r = git("grep", "-h", "url: ", "--", "frontend/packages/api/src/")
    blob = r.stdout or ""
    paths = [m.group(1) for m in re.finditer(r"url:\s*'([^']+)'", blob)]
    paths += [m.group(1) for m in re.finditer(r"url:\s*`([^`]+)`", blob)]
    firsts = Counter(p.lstrip("/").split("/")[0] if p.strip("/") else "(root)"
                     for p in paths)
    out(f"    distinct paths: {len(set(paths))} | total refs: {len(paths)}")
    out("    first path segments:")
    for seg, n in sorted(firsts.items(), key=lambda kv: -kv[1])[:20]:
        out(f"        /{seg:16s} {n}")
    out("    notable paths (mount-dedup decision):")
    for n in ("/login", "/register", "/seed-demo", "/landscapes", "/health",
              "/advise", "/chat"):
        out(f"        {n:12s} {'YES — frontend uses it' if n in set(paths) else 'no'}")
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
    steps = {"verify": verify, "unblock": unblock, "mainfix": mainfix,
             "offgit": offgit, "recon": recon}
    if cmd == "all":
        for name in ("verify", "unblock", "mainfix", "offgit", "recon"):
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