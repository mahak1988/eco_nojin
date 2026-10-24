# .githooks — the Rule-5 pre-edit gate

One line: `.githooks/pre-edit` runs the v3.1 Rule-5 Quick Scan
(`pytest engine/tests`, `pytest services/`, `tools/detect_imports.py`,
`ruff check . --statistics`, `tools/phantom_path_check.py`) and prints
`READY` or `NOT-READY`, exiting 0 or 1.

| Entry point | Use it when |
|---|---|
| `.githooks/pre-edit` | the launcher; what git's `sh` would run, and what the tests call |
| `.githooks/pre-edit.sh` | any POSIX shell, or macOS/Linux |
| `.githooks/pre-edit.ps1` | Windows PowerShell (Windows PowerShell 5.1 or later) |

`--quick` / `-quick` / `-q` skips the services suite, which is the slow half of
the scan. The gate is read-only: it never writes to the working tree, never
stages anything, and never changes git configuration. Its job is to answer "is
the tree green right now?" before an edit starts, because an edit made on a red
tree cannot be proven behaviour-preserving.

Both implementations set `PYTHONPATH` and `SECRET_KEY` themselves (see
`AGENTS.md`) and prefer the repository's own virtualenv
(`<repo>/.venv/Scripts/python.exe`, then the sibling `eco_nojin` venv) over
whatever `python` happens to be first on `PATH`, so the scan measures the same
interpreter the suite runs under. The POSIX implementation depends on **no
external command at all** beyond the interpreter, so it cannot fail to start in
a shell that has no msys `/usr/bin` on its `PATH`.

## `pre-edit` is not a git event

**Git has no `pre-edit` hook.** Git runs hooks named after events
(`pre-commit`, `pre-push`, …), so `git config core.hooksPath .githooks` on its
own does not make this gate run. Making it a git gate needs one more file — a
`.githooks/pre-commit` that calls this scan — and that file is a *behaviour*
change to every commit in the repository, which is a recorded decision rather
than a default:

```powershell
# only after the owner has decided that commits should pay for the scan:
git config core.hooksPath .githooks
# and a .githooks/pre-commit that execs .githooks/pre-edit (not added here —
# committing a new commit-time gate is a separate, recorded decision)
```

Until that decision is taken, run the scan by hand. C-2 already adds the same
five commands to CI, which is the gate that runs whether or not a developer
remembers to.

## Read this before installing

`ruff check .` is one of the five checks and it is treated as blocking, because
C-1 specifies the command exactly. This tree carries ~770 pre-existing ruff
findings, so the gate prints `NOT-READY` on a tree that is otherwise green until
that debt is cleared or the step is converted into a count-ratchet (fail when
the count grows, with the count recorded). A gate that is always red is a gate
that gets bypassed, so settle that decision first — see
`reports/eco-nojin/COMMIT-LANDING-ORDER.md`, section "The decision the hook
forces".

## Encoding and the executable bit

`.githooks/pre-edit.ps1` must be saved as **UTF-8 with a byte-order mark**.
Windows PowerShell 5.1 has no UTF-8 default and decodes a BOM-less `.ps1` with
the machine's ANSI code page, where the three UTF-8 bytes of an em dash
(`E2 80 94`) include `0x94` — a right double quotation mark in cp1252 — so a
single em dash inside a double-quoted string terminates it and the file does not
parse at all. `sh` and CPython both default to UTF-8, so the bash and Python
entry points stay BOM-less.
`engine/tests/test_coverage_gate.py` pins the mark and parses the file with
PowerShell's own parser.

The executable bit is carried by git's index, not by the Windows file system:

```powershell
git update-index --chmod=+x .githooks/pre-edit .githooks/pre-edit.sh
```
