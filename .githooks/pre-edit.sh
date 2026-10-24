#!/bin/sh
# ---------------------------------------------------------------------------
# .githooks/pre-edit.sh — v3.1 Rule-5 Quick Scan (sh / bash / Git-for-Windows)
#
# Git launches hooks through `sh` on every platform, including Windows (Git for
# Windows ships an MSYS2 sh), so this is the file git executes once
# `core.hooksPath` points at .githooks/. The PowerShell twin
# (.githooks/pre-edit.ps1) exists because Windows developers also run the scan by
# hand, and `powershell -File` refuses any file not named *.ps1 — so a single
# polyglot cannot serve both. See .githooks/README.md.
#
# Five checks, then READY (exit 0) or NOT-READY (exit 1):
#     guard     tools/detect_imports.py --root .
#     ruff      -m ruff check . --statistics
#     unit      -m pytest engine/tests -q -p no:cacheprovider
#     services  -m pytest services/   -q -p no:cacheprovider
#     honesty   tools/phantom_path_check.py
#
# --quick / -quick / -q skips the services suite (the slow half). The hook is
# read-only: it never modifies the working tree.
#
# No external command is required except the interpreter itself: `dirname`,
# `cut`, `tr` and `exec sh` are all avoided, because a shell started from a
# Windows console does not inherit msys' /usr/bin and a hook that cannot start
# is worse than a hook that reports NOT-READY.
# ---------------------------------------------------------------------------
set -u

# Locate this file without dirname(1): ${0%/*} is enough, and the fallback
# covers a hook invoked with no slash in $0 (i.e. from inside .githooks/).
case "$0" in
    */*) HOOK_SOURCE=${0%/*} ;;
    *)   HOOK_SOURCE=. ;;
esac
HOOK_DIR=$(CDPATH= cd -- "$HOOK_SOURCE" && pwd)
ROOT=$(CDPATH= cd -- "$HOOK_DIR/.." && pwd)

QUICK=0
for arg in "$@"; do
    case "$arg" in
        -q | -quick | --quick | -Quick | --Quick) QUICK=1 ;;
        *) ;;
    esac
done

# ---------------------------------------------------------------------------
# Path translation
#
# Under msys a POSIX path (/d/HyDroMA) is handed to a native Windows program,
# which does not understand it. Windows accepts a lowercase drive letter and
# forward slashes, so /d/HyDroMA becomes d:/HyDroMA with no external command.
# Everything else (a real POSIX host, or an already-native path) is untouched.
# ---------------------------------------------------------------------------
to_native() {
    case "$1" in
        /[a-zA-Z]/*)
            _drive_rest=${1#/}
            _drive=${_drive_rest%%/*}
            _path=${_drive_rest#*/}
            printf '%s:/%s' "$_drive" "$_path"
            ;;
        *) printf '%s' "$1" ;;
    esac
}

NATIVE_ROOT=$(to_native "$ROOT")

# Resolved once so the reported PYTHONPATH carries no ".." segments.
SIBLING_DIR=''
if [ -d "$ROOT/../eco_nojin" ]; then
    SIBLING_DIR=$(CDPATH= cd -- "$ROOT/../eco_nojin" && pwd)
fi
NATIVE_SIBLING=''
if [ -n "$SIBLING_DIR" ]; then
    NATIVE_SIBLING=$(to_native "$SIBLING_DIR")
fi

# --- interpreter: the repo's own venv, then the sibling venv, then PATH -----
PY=''
for candidate in \
    "$ROOT/.venv/Scripts/python.exe" \
    "$ROOT/.venv/bin/python" \
    "$SIBLING_DIR/.venv/Scripts/python.exe"
do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
        PY=$candidate
        break
    fi
done
if [ -z "$PY" ]; then
    PY=python
fi

# --- environment the suite expects (AGENTS.md) -----------------------------
# Windows Python separates paths with ';'; POSIX with ':'. The separator
# follows the interpreter's platform, not the shell's.
case "$NATIVE_ROOT" in
    [A-Za-z]:*) SEP=';' ;;
    *) SEP=':' ;;
esac

_pythonpath_has() {
    case "${SEP}${PYTHONPATH:-}${SEP}" in
        *"$SEP$1$SEP"*) return 0 ;;
        *) return 1 ;;
    esac
}

if [ -n "${PYTHONPATH:-}" ]; then
    _pythonpath_has "$NATIVE_ROOT" || PYTHONPATH="$NATIVE_ROOT$SEP$PYTHONPATH"
else
    PYTHONPATH="$NATIVE_ROOT"
fi
if [ -n "$NATIVE_SIBLING" ]; then
    _pythonpath_has "$NATIVE_SIBLING" || PYTHONPATH="$PYTHONPATH$SEP$NATIVE_SIBLING"
fi
export PYTHONPATH

if [ -z "${SECRET_KEY:-}" ]; then
    SECRET_KEY='test-secret-key'
    export SECRET_KEY
fi

FAILED=''

# --- one check: name, detail, is-it-slow, probe-file, then the command -------
# Each check runs in a subshell so the `cd` does not leak, and its output goes
# straight to the terminal: capturing it would need cat/tail/temp files, none of
# which a shell started from a Windows console can be relied upon to find. The
# exit status is the subshell's, which is the interpreter's.
run_check() {
    name=$1
    detail=$2
    slower=$3
    probe=$4
    shift 4

    if [ "$slower" = yes ] && [ "$QUICK" -eq 1 ]; then
        printf '[ SKIP ] %-10s %s\n' "$name" "$detail"
        return 0
    fi
    if [ -n "$probe" ] && [ ! -f "$ROOT/$probe" ]; then
        printf '[ SKIP ] %-10s %s (not present in this tree)\n' "$name" "$detail"
        return 0
    fi

    (
        cd "$ROOT" || exit 1
        "$PY" "$@"
    )
    status=$?

    if [ "$status" -eq 0 ]; then
        printf '[ PASS ] %-10s %s\n' "$name" "$detail"
        return 0
    fi
    printf '[ FAIL ] %-10s %s (exit %d)\n' "$name" "$detail" "$status"
    FAILED="$FAILED$name ($detail); "
    return 0
}

echo "Rule-5 Quick Scan — repo $ROOT"
echo "interpreter: $PY"
echo "PYTHONPATH : $PYTHONPATH"
if [ "$QUICK" -eq 1 ]; then
    echo 'mode       : quick (services suite skipped)'
else
    echo 'mode       : full'
fi
echo ''

run_check guard 'tools/detect_imports.py --root .' no tools/detect_imports.py \
    tools/detect_imports.py --root .
run_check ruff 'ruff check . --statistics' no '' \
    -m ruff check . --statistics
run_check lintratchet 'tools/check_lint_ratchet.py --root .' no tools/check_lint_ratchet.py \
    tools/check_lint_ratchet.py --root .
run_check unit 'pytest engine/tests -q -p no:cacheprovider' no '' \
    -m pytest engine/tests -q -p no:cacheprovider
run_check services 'pytest services/ -q -p no:cacheprovider' yes '' \
    -m pytest services/ -q -p no:cacheprovider
run_check honesty 'tools/phantom_path_check.py' no tools/phantom_path_check.py \
    tools/phantom_path_check.py

echo ''
if [ -z "$FAILED" ]; then
    echo 'READY'
    exit 0
fi
printf 'NOT-READY (failing: %s)\n' "$FAILED"
exit 1
