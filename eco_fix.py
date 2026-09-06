#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v6.

verify | gitignore audit | fix admin_assistant.py (ALL mangled indents,
parse-gated) | deep recon of sync/async session wiring.

Usage:
    python eco_fix.py              # all
    python eco_fix.py verify
    python eco_fix.py audit
    python eco_fix.py fix-assistant
    python eco_fix.py recon
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

# ------------------------------------------------------------- 1. verify ---
def verify():
    out(LINE, "STEP 0 — verify remote state", LINE, sep="\n")
    git("fetch", "origin", timeout=300)
    r = git("log", "--oneline", "origin/main..main")
    unpushed = [l for l in r.stdout.splitlines() if l.strip()]
    if unpushed:
        warn(f"{len(unpushed)} unpushed — pushing ...")
        r2 = git("push", "origin", "main")
        ok("pushed") if r2.returncode == 0 else \
            fail("push failed: " + (r2.stderr or "")[-400:])
    else:
        ok("everything pushed to origin/main")
    st = [l for l in git("status", "--porcelain").stdout.splitlines() if l.strip()]
    out(f"working-tree entries: {len(st)}")
    for l in st[:10]:
        out("    " + l)
    out("\n" + git("log", "--oneline", "-4").stdout)
    return True

# -------------------------------------------------------------- 2. audit ---
def audit():
    out(LINE, "STEP A — behavioral gitignore audit", LINE, sep="\n")
    out("dry-run of 'git add .':")
    r = git("add", "--dry-run", ".")
    would = [l.strip() for l in (r.stdout or "").splitlines() if l.strip()]
    for l in would[:15]:
        out("    " + l)
    if len(would) > 15:
        out(f"    ... {len(would) - 15} more")
    out(f"    total: {len(would)}")
    git("add", "--", ".gitignore", "eco_fix.py")
    r = git("commit", "-m", "chore: update automation script")
    if r.returncode == 0:
        ok("committed")
        r2 = git("push", "origin", "main")
        ok("pushed") if r2.returncode == 0 else warn("push failed")
    elif "nothing to commit" in (r.stdout + r.stderr):
        ok("nothing to commit")
    else:
        warn("commit failed: " + (r.stdout + r.stderr)[-400:])
    return True

# ----------------------------------------------------- 3. fix assistant ----
ASSISTANT = ROOT / "services" / "ai" / "admin_assistant.py"

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
    """unexpected-indent at lineno: walk up, find a column-zero IMPORT whose
    next non-blank line is indented (the formatter-mangled one), re-indent it."""
    lines = text.splitlines()
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

def fix_assistant():
    out(LINE, "STEP B — admin_assistant.py: repair ALL mangled indents", LINE, sep="\n")
    if not ASSISTANT.exists():
        fail("file not found"); return False
    with open(ASSISTANT, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")

    fixes = text.count(TWO_LINE_BUG)
    if fixes:
        text = text.replace(TWO_LINE_BUG, TWO_LINE_FIX)
        ok(f"exact two-line pattern: {fixes} instance(s) fixed")

    for attempt in range(1, 9):
        try:
            ast.parse(text)
            ok("file parses cleanly now")
            break
        except SyntaxError as e:
            if e.msg.startswith("unexpected indent"):
                res = _try_auto_fix(text, e.lineno)
                if res:
                    text, j = res
                    fixes += 1
                    out(f"[....] round {attempt}: re-indented line {j}")
                    continue
            fail(f"unfixable — line {e.lineno}: {e.msg}")
            lines = text.splitlines()
            ln = (e.lineno or 1) - 1
            for i in range(max(0, ln - 14), min(len(lines), ln + 10)):
                mark = ">>" if i == ln else "  "
                out(f"{mark}{i+1:4d}| {lines[i]}")
            out(">>> NOT written; report this context")
            return False
    else:
        fail("too many rounds — manual review needed"); return False

    if fixes == 0:
        ok("nothing to fix (already clean)")
        return True

    with open(ASSISTANT, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", "\r\n") if crlf else text)
    ok(f"total lines re-indented: {fixes}")
    git("add", "--", "services/ai/admin_assistant.py")
    r = git("commit", "-m",
            "fix(ai): repair formatter-mangled import indents in admin_assistant")
    if r.returncode == 0:
        ok("committed")
        git("push", "origin", "main")
    else:
        warn("commit failed: " + (r.stdout + r.stderr)[-400:])
    return True

# ------------------------------------------------------------- 4. recon ----
def recon():
    out(LINE, "STEP D — deep recon: sync/async session wiring", LINE, sep="\n")

    out("--- A) async infrastructure inside database/ layer ---")
    any_async = False
    for pat in ("async_sessionmaker", "create_async_engine", "AsyncSession",
                "async def get_session"):
        r = git("grep", "-n", pat, "--", "database/")
        hits = [l for l in r.stdout.splitlines() if l.strip()]
        out(f"    '{pat}': {len(hits)} hit(s)")
        for l in hits[:5]:
            out("        " + l)
        if hits:
            any_async = True
    if not any_async:
        warn(">>> NO async session support in database/ — the async-typed "
             "service layer has no engine behind it!")

    out("\n--- B) every get_db definition in services/ ---")
    r = git("grep", "-n", "def get_db", "--", "services/")
    hits = [l for l in r.stdout.splitlines() if l.strip()]
    for l in hits[:30]:
        out("    " + l)
    if len(hits) > 30:
        out(f"    ... {len(hits) - 30} more")

    out("\n--- C) services/reporting/repository.py (first 60) ---")
    p = ROOT / "services" / "reporting" / "repository.py"
    if p.exists():
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        out(f"({len(lines)} lines total)")
        for i, ln in enumerate(lines[:60], 1):
            out(f"{i:4d}| {ln}")

    out("\n--- D) comparison router: api_gateway/routers/land.py (first 55) ---")
    p2 = ROOT / "services" / "api_gateway" / "routers" / "land.py"
    if p2.exists():
        lines = p2.read_text(encoding="utf-8", errors="replace").splitlines()
        out(f"({len(lines)} lines total)")
        for i, ln in enumerate(lines[:55], 1):
            out(f"{i:4d}| {ln}")

    out("\n--- E) api_gateway/main.py — first session/get_db region ---")
    p3 = ROOT / "services" / "api_gateway" / "main.py"
    if p3.exists():
        lines = p3.read_text(encoding="utf-8", errors="replace").splitlines()
        idx = next((i for i, ln in enumerate(lines)
                    if "get_db" in ln or "Session" in ln), None)
        if idx is not None:
            for i in range(max(0, idx - 10), min(len(lines), idx + 25)):
                out(f"{i+1:4d}| {lines[i]}")
        else:
            warn("no session wiring visible in main.py")

    out("\n--- F) how many services type their db as AsyncSession? ---")
    r = git("grep", "-l", "AsyncSession", "--", "services/")
    files = [l for l in r.stdout.splitlines() if l.strip()]
    out(f"    {len(files)} file(s):")
    for l in files[:20]:
        out("    " + l)
    return True

# ------------------------------------------------------------------ main ---
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"verify": verify, "audit": audit,
             "fix-assistant": fix_assistant, "recon": recon}
    if cmd == "all":
        for name in ("verify", "audit", "fix-assistant", "recon"):
            try:
                steps[name]()
            except Exception as e:
                fail(f"{name} crashed: {e!r}")
    elif cmd in steps:
        try:
            steps[cmd]()
        except Exception as e:
            fail(f"{cmd} crashed: {e!r}")
    else:
        out(__doc__)

if __name__ == "__main__":
    main()