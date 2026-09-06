#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v10 — wiring & async-usage recon.

Which API surface is live (main.py) | await-on-sync-session audit across all
routers with async endpoints | AI 4-entry consolidation recon |
dependencies.py consumer check.

Usage:
    python eco_fix.py
    python eco_fix.py verify
    python eco_fix.py recon-main
    python eco_fix.py audit-async
    python eco_fix.py recon-ai
    python eco_fix.py deps-usage
"""
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

def read_lines(p):
    return Path(p).read_text(encoding="utf-8", errors="replace").splitlines()

def grep(pattern, *paths, extended=False):
    args = ["grep", "-n"]
    if extended:
        args.append("-E")
    args += [pattern, "--", *paths]
    r = git(*args)
    return [l for l in r.stdout.splitlines() if l.strip()]

def dump(p, max_lines=300, title=None):
    p = Path(p)
    if not p.exists():
        warn(f"not found: {p}")
        return
    lines = read_lines(p)
    out(f"--- {title or p} ({len(lines)} lines, showing {min(len(lines), max_lines)}) ---")
    for i, ln in enumerate(lines[:max_lines], 1):
        out(f"{i:4d}| {ln}")
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

# ---------------------------------------------------------- recon-main -----
def recon_main():
    out(LINE, "STEP 1 — which API surface is live?", LINE, sep="\n")
    dump(ROOT / "services" / "api_gateway" / "main.py", max_lines=320)
    out("\ninclude_router wiring (whole repo):")
    for l in grep("include_router", "services/")[:80]:
        out("    " + l)
    return True

# --------------------------------------------------------- audit-async -----
ROUTERS_WITH_ASYNC = [
    "services/api_gateway/auth.py",
    "services/api_gateway/routers/admin.py",
    "services/api_gateway/routers/ai_chat.py",
    "services/api_gateway/routers/nojin.py",
    "services/api_gateway/routers/satellite.py",
    "services/api_gateway/routers/simulation.py",
    "services/api_gateway/routers/soil.py",
    "services/api_gateway/routers/support.py",
]

DB_CALL = re.compile(
    r"\bawait\s+(db|session|self\.db)\b"
    r"|\b(db|session|self\.db)\.(query|execute|add|commit|refresh|scalar|scalars|get|delete)\b")

def audit_async():
    out(LINE, "STEP 2 — await-on-sync-session audit (async def endpoints)", LINE, sep="\n")
    any_hits = False
    for rel in ROUTERS_WITH_ASYNC:
        p = ROOT / rel
        if not p.exists():
            continue
        lines = read_lines(p)
        starts = [i for i, ln in enumerate(lines)
                  if re.match(r"\s*async def \w+", ln)]
        if not starts:
            continue
        out(f"\n### {rel} ({len(starts)} async endpoint(s))")
        gi = next((i for i, ln in enumerate(lines) if "def get_db" in ln), None)
        if gi is not None:
            out(f"  get_db at line {gi+1}: {lines[gi].strip()}")
        for i in starts:
            header = lines[i].strip()
            j, body = i + 1, []
            while j < len(lines) and not re.match(r"\s*(async )?def \w+", lines[j]):
                body.append(lines[j])
                j += 1
                if j - i > 80:
                    break
            hits = [ln.strip() for ln in body if DB_CALL.search(ln)]
            if hits:
                any_hits = True
                has_await = any("await" in h for h in hits)
                tag = ("  <== AWAIT ON SESSION (broken!)" if has_await
                       else "  (sync db calls inside async — blocks event loop)")
                out(f"  {header}{tag}")
                for h in hits[:5]:
                    out(f"      {h}")
    if not any_hits:
        ok("no async endpoint touches a session directly (all via services)")
    return True

# ------------------------------------------------------------- recon-ai ----
def recon_ai():
    out(LINE, "STEP 3 — AI surface (4 entry points) for consolidation", LINE, sep="\n")
    for rel in ("services/api_gateway/routers/ai.py",
                "services/api_gateway/routers/ai_advice_router.py",
                "services/api_gateway/routers/ai_chat.py"):
        p = ROOT / rel
        out(f"\n### {rel}")
        if not p.exists():
            warn("not found")
            continue
        lines = read_lines(p)
        out(f"({len(lines)} lines)")
        for i, ln in enumerate(lines, 1):
            if re.search(r"@\w+\.(get|post|put|delete|websocket)\(", ln):
                out(f"    L{i}: {ln.strip()}")
        out("    imports:")
        for i, ln in enumerate(lines, 1):
            if ln.startswith(("from ", "import ")):
                out(f"    L{i}: {ln.strip()}")
    out("\nadmin.py AI-related routes:")
    for l in grep("/ai|/chat", "services/api_gateway/routers/admin.py", extended=True):
        out("    " + l)
    out("\nservices/ai/ modules:")
    d = ROOT / "services" / "ai"
    if d.exists():
        for f in sorted(d.glob("*.py")):
            out(f"    {f.name:34s} {f.stat().st_size // 1024} KB")
    return True

# ---------------------------------------------------------- deps-usage -----
def deps_usage():
    out(LINE, "STEP 4 — dependencies.py & SessionLocal consumers", LINE, sep="\n")
    hits = []
    for pat in ("dependencies import",
                "from services.api_gateway import dependencies",
                "SessionLocal"):
        for l in grep(pat, "services/", "tests/")[:40]:
            if l not in hits:
                hits.append(l)
    for l in hits:
        out("    " + l)
    if not hits:
        warn(">>> dependencies.py imported by NOBODY — dead module with an "
             "import-time engine-creation side effect")
    return True

# --------------------------------------------------------------- chore -----
def chore():
    git("add", "--", "eco_fix.py")
    r = git("commit", "-m", "chore: update automation script")
    if r.returncode == 0:
        ok("script committed")
        r2 = git("push", "origin", "main")
        ok("pushed") if r2.returncode == 0 else warn("push failed")
    else:
        ok("nothing to commit")

# ------------------------------------------------------------------ main ---
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"verify": verify, "recon-main": recon_main,
             "audit-async": audit_async, "recon-ai": recon_ai,
             "deps-usage": deps_usage}
    if cmd == "all":
        for name in ("verify", "recon-main", "audit-async",
                     "recon-ai", "deps-usage"):
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