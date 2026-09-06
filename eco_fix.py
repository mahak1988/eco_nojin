#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_nojin automation runner v3.

Removes the broken Windows gitleaks hook, repairs .gitignore syntax bugs,
moves secret-scanning to CI, commits the staged cleanup, applies the XSS
patch, and prints repo diagnostics.

Usage:
    python eco_fix.py            # full run
    python eco_fix.py unhook     # only remove pre-commit hook
    python eco_fix.py commit     # gitignore fix + index rebuild + commit/push/tag
    python eco_fix.py patch      # only XSS patch
    python eco_fix.py report     # only diagnostics
"""
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

def sh(cmd, timeout=900):
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)

def git(*a, **kw):
    if GIT_EXE is None:
        raise RuntimeError("git.exe not found")
    return sh([GIT_EXE, *a], **kw)

def pymod(m, *a, **kw):
    return sh([sys.executable, "-m", m, *a], **kw)

# ------------------------------------------------------------- constants ---
INLINE_COMMENT = re.compile(r"^(?!\s*#)(\S.*?)\s+#.*$")

ROOT_ANCHOR_DIRS = ["benchmarks/", "DELIVERY/", "analysis.json/", "logs/",
                    "html/", "lib/", "lib64/", "build/", "dist/", "var/",
                    "parts/", "downloads/", "eggs/", "sdist/", "wheels/",
                    "develop-eggs/"]

REQUIRED_PATTERNS = [
    "engine/cpp_core/build*/", "*.iobj", "*.ipdb", "*.pdb", "**/*.tsbuildinfo",
    ".turbo/", "__pycache__/", "data/*.duckdb", "data/maps/",
    "data/motors/cache/", "data/_archived_excel_data/",
    "backups/", "_backups/", ".benchmarks/",
    ".env", "contracts/.env", "*.local",
    "*.tmp", "reports/temp_*",
]

EXT_ARTIFACTS = (".iobj", ".ipdb", ".pdb", ".tlog", ".lastbuildstate", ".recipe",
                 ".tsbuildinfo", ".duckdb", ".gpkg", ".tif", ".tiff", ".zip",
                 ".coverage")
DIR_ARTIFACTS = ("engine/cpp_core/build", "data/maps/", "data/_archived",
                 "data/motors/cache", "_backups/", "backups/",
                 "reports/temp_", ".turbo/")
INTENT_DIRS = ("benchmarks/", "DELIVERY/", "analysis.json/", "logs/")

CI_SECURITY_YML = """name: Security

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  gitleaks:
    name: gitleaks (detect hardcoded secrets)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout (full history)
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
"""

# ---------------------------------------------------- 1. remove the hook ---
def unhook():
    out(LINE, "STEP 1 — remove broken pre-commit hook (Windows blocker)", LINE, sep="\n")
    r = pymod("pre_commit", "uninstall")
    ok("pre-commit uninstalled") if r.returncode == 0 else \
        warn(f"pre_commit uninstall rc={r.returncode} (continuing)")
    hook = ROOT / ".git" / "hooks" / "pre-commit"
    if hook.exists():
        try:
            hook.unlink()
            ok(".git/hooks/pre-commit removed")
        except OSError as e:
            fail(f"cannot remove hook: {e}")
            return False
    else:
        ok("no hook file present")
    cfg = ROOT / ".pre-commit-config.yaml"
    if cfg.exists():
        cfg.unlink()
        ok(".pre-commit-config.yaml removed (secret scanning moves to CI)")
    return True

# ---------------------------------------------------- 2. fix .gitignore ---
def fix_gitignore():
    out(LINE, "STEP 2 — repair .gitignore", LINE, sep="\n")
    gi = ROOT / ".gitignore"
    text = gi.read_text(encoding="utf-8", errors="replace") if gi.exists() else ""
    fixed, anchored, new_lines = [], [], []
    for ln in text.splitlines():
        m = INLINE_COMMENT.match(ln)
        if m and m.group(1).strip():
            fixed.append(m.group(1).strip())
            new_lines.append(m.group(1).rstrip())
            continue
        s = ln.strip()
        if s in ROOT_ANCHOR_DIRS and not ln.lstrip().startswith("/"):
            anchored.append(s)
            new_lines.append("/" + s)
            continue
        new_lines.append(ln)
    if fixed:
        ok(f"fixed {len(fixed)} dead pattern(s) — inline '#' comments are NOT valid:")
        for f in fixed:
            out(f"    {f}")
    if anchored:
        ok(f"root-anchored {len(anchored)} dir pattern(s) — protects nested dirs like tests/benchmarks/:")
        for a in anchored:
            out(f"    {a}  ->  /{a}")
    present = {ln.strip() for ln in new_lines}
    missing = [p for p in REQUIRED_PATTERNS if p not in present]
    if missing:
        new_lines += ["", "# --- eco_fix v3 ---"] + missing
        ok(f"appended {len(missing)} pattern(s): {', '.join(missing)}")
    gi.write_text("\n".join(new_lines) + "\n", encoding="utf-8", newline="\n")
    ok(".gitignore written")
    return True

# ------------------------------------------------- 3. CI security workflow -
def ensure_ci():
    out(LINE, "STEP 3 — CI-side secret scanning (GitHub Actions)", LINE, sep="\n")
    wf_dir = ROOT / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    wf = wf_dir / "security.yml"
    if wf.exists():
        ok(".github/workflows/security.yml already exists (left untouched)")
        return True
    wf.write_text(CI_SECURITY_YML, encoding="utf-8", newline="\n")
    ok("created .github/workflows/security.yml (gitleaks on every push/PR)")
    return True

# ------------------------------------------------ 4. rebuild + commit -----
def is_artifact(p):
    p = p.replace("\\", "/")
    return p.lower().endswith(EXT_ARTIFACTS) or any(d in p for d in DIR_ARTIFACTS)

def is_user_intent(p):
    return p.replace("\\", "/").startswith(INTENT_DIRS)

def commit_cleanup():
    out(LINE, "STEP 4 — rebuild index, commit, push, tag", LINE, sep="\n")
    if not (ROOT / ".git").exists():
        fail("no .git directory")
        return False
    ok("git " + git("--version").stdout.strip())

    out("rebuilding index — may take a minute or two ...")
    git("rm", "-r", "--cached", ".")
    git("add", ".")

    r = git("diff", "--cached", "--name-only", "--diff-filter=D")
    deletions = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    on_disk = [f for f in deletions if (ROOT / f).exists()]
    out(f"staged deletions: {len(deletions)} | real files on disk: {len(on_disk)}")

    keep, drop_i = [], []
    for f in on_disk:
        if not is_artifact(f) and not is_user_intent(f):
            keep.append(f)
        elif is_user_intent(f):
            drop_i.append(f)
    for f in keep:
        rr = git("add", "-f", "--", f)
        if rr.returncode != 0:
            fail(f"git add -f failed: {f}")
            return False
    ok(f"kept tracked (source/placeholder files): {len(keep)}")
    for f in keep:
        out("    + " + f)
    out(f"untracked by YOUR ignore-intent (stay on disk, not in git): {len(drop_i)}")
    for f in drop_i:
        out("    ~ " + f)

    r = git("diff", "--cached", "--name-only", "--diff-filter=D")
    bad = [f for f in r.stdout.splitlines() if f.strip()
           and (ROOT / f).exists()
           and not is_artifact(f) and not is_user_intent(f)]
    if bad:
        fail(f"{len(bad)} real files still untracked — ABORT:")
        for f in bad[:40]:
            out("    " + f)
        return False
    ok("safety check passed")

    git("add", ".")
    r = git("commit", "-m",
            "chore: repair .gitignore syntax, untrack build artifacts, heavy "
            "data, backups and stale temp files; add CI security workflow")
    if r.returncode == 0:
        ok("cleanup commit created")
    elif "nothing to commit" in (r.stdout + r.stderr):
        ok("nothing to commit (already done)")
    else:
        warn("commit failed:")
        out((r.stdout + r.stderr)[-800:])
        return False

    r = git("push", "origin", "main")
    if r.returncode == 0:
        ok("pushed origin/main")
    else:
        warn("push failed — push manually later with: git push origin main")
        out((r.stderr or r.stdout)[-500:])

    if git("tag", "v0.2-clean").returncode == 0:
        git("push", "origin", "v0.2-clean")
        ok("tag v0.2-clean created & pushed")
    else:
        warn("tag v0.2-clean not created (already exists?)")
    out("\n" + git("log", "--oneline", "-3").stdout)
    return True

# ------------------------------------------------------- 5. XSS patch -----
EDITOR = ROOT / "frontend" / "packages" / "ui" / "src" / "primitives" / "rich-text-editor.tsx"
EDITOR_GIT = "frontend/packages/ui/src/primitives/rich-text-editor.tsx"

REACT_IMPORT = "import { useRef } from 'react'"
DOMPURIFY_IMPORT = "import DOMPurify from 'dompurify'"
SANITIZE_CONFIG = (
    "\nconst SANITIZE_CONFIG = {\n"
    "  ALLOWED_TAGS: ['b', 'strong', 'i', 'em', 'u', 's', 'strike', 'del',\n"
    "                 'ul', 'ol', 'li', 'br', 'p', 'div', 'span'],\n"
    "  ALLOWED_ATTR: ['style', 'align'],\n"
    "}\n"
)
OLD_SYNC = ("  const sync = () => {\n"
            "    if (editorRef.current) onChange(editorRef.current.innerHTML)\n"
            "  }")
NEW_SYNC = ("  const sync = () => {\n"
            "    if (editorRef.current) {\n"
            "      onChange(DOMPurify.sanitize(editorRef.current.innerHTML, SANITIZE_CONFIG))\n"
            "    }\n"
            "  }")
OLD_DSI = "dangerouslySetInnerHTML={{ __html: value }}"
NEW_DSI = "dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(value, SANITIZE_CONFIG) }}"

def patch_editor():
    out(LINE, "STEP 5 — XSS patch (input + render paths)", LINE, sep="\n")
    if not EDITOR.exists():
        fail("editor file not found")
        return False
    with open(EDITOR, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")

    out("--- current file (full) ---")
    for i, ln in enumerate(text.splitlines(), 1):
        out(f"{i:4d}| {ln}")
    out("--- end of file ---")

    if "DOMPurify" in text:
        ok("already patched")
        return True
    if REACT_IMPORT not in text:
        fail("anchor 'import { useRef }' not found — paste the file above for me")
        return False

    text = text.replace(REACT_IMPORT,
                        REACT_IMPORT + "\n" + DOMPURIFY_IMPORT + SANITIZE_CONFIG, 1)
    applied = ["import"]
    if OLD_SYNC in text:
        text = text.replace(OLD_SYNC, NEW_SYNC, 1)
        applied.append("sync()")
    else:
        warn("sync() block not matched — input-side NOT patched")
    if OLD_DSI in text:
        text = text.replace(OLD_DSI, NEW_DSI, 1)
        applied.append("render")
    else:
        warn("dangerouslySetInnerHTML not matched — render-side NOT patched")

    with open(EDITOR, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", "\r\n") if crlf else text)
    ok("patched: " + ", ".join(applied))
    out("\ngit diff:\n" + (git("diff", "--", EDITOR_GIT).stdout[:2500] or "(none)"))

    if not ({"sync()", "render"} & set(applied)):
        warn("nothing critical applied — not committing")
        return False
    git("add", "--", "frontend/packages/ui")
    for line in git("status", "--porcelain").stdout.splitlines():
        p = line[3:].strip().strip('"')
        if "pnpm-lock.yaml" in p:
            git("add", "--", p)
    r = git("commit", "-m", "fix(ui): sanitize rich-text-editor HTML (XSS, input+render)")
    if r.returncode == 0:
        ok("editor fix committed")
        git("push", "origin", "main")
    else:
        warn("commit failed:")
        out((r.stdout + r.stderr)[-800:])
    return True

# ------------------------------------------------------- 6. diagnostics ---
def report():
    out(LINE, "STEP 6 — diagnostics", LINE, sep="\n")
    out("remotes:\n" + (git("remote", "-v").stdout.strip() or "(none!)"))
    files = [l.strip() for l in git("ls-files").stdout.splitlines() if l.strip()]
    out(f"tracked files: {len(files)}")
    cnt = Counter(Path(f).suffix.lower() or "(no-ext)" for f in files)
    out("tracked files by extension (top 25):")
    for ext, n in cnt.most_common(25):
        out(f"    {ext:12s} {n}")
    for pattern in (".zst", ".bak", ".csv", ".xlsx", ".zip", ".log"):
        hits = [f for f in files if f.lower().endswith(pattern)]
        if hits:
            out(f"still tracked {pattern}: {len(hits)} file(s), e.g.:")
            for h in hits[:5]:
                out("    " + h)
    out("repo object store size (includes full history):")
    out(git("count-objects", "-vH").stdout.strip())
    out(f"hook present: {(ROOT / '.git' / 'hooks' / 'pre-commit').exists()} | "
        f"tag v0.2-clean: {bool(git('tag', '-l', 'v0.2-clean').stdout.strip())}")

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "all":
        for fn in (unhook, fix_gitignore, ensure_ci, commit_cleanup, patch_editor):
            if fn() is False:
                fail(f"aborted in {fn.__name__}() — re-run or report output")
                break
        report()
    elif cmd == "unhook": unhook()
    elif cmd == "commit":
        for fn in (fix_gitignore, ensure_ci, commit_cleanup):
            if fn() is False:
                break
    elif cmd == "patch": patch_editor()
    elif cmd == "report": report()
    else:
        out(__doc__)

if __name__ == "__main__":
    main()