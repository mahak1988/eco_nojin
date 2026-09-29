"""Build and run the native unit tests, counting [FAIL] lines.

Every ``engine/cpp_core/tests/test_*.cpp`` is a standalone program that ends in
``return 0``, so a failing check still exits 0. Counting the ``[FAIL]`` lines is
therefore the only way these results can be honest, and this module is what the
CI gate would call.

Run directly:

    python scripts/run_cpp_tests.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

CPP_CORE = Path("engine/cpp_core")
OUT_DIR = CPP_CORE / "build" / "tests"
BUILD_SCRIPT = CPP_CORE / "build_tests.bat"

#: The test files are not uniform about the marker. Some print "[OK]", others
#: "  [ ok ]" and "  [ OK ]". Anything narrower silently reports zero checks,
#: which makes a red suite look green. Match case-insensitively with optional
#: internal spacing.
OK_RE = re.compile(r"\[\s*(?:OK|ok)\s*\]")
FAIL_RE = re.compile(r"\[\s*(?:FAIL|fail)\s*\]")


def run() -> int:
    if not BUILD_SCRIPT.is_file():
        print(f"missing {BUILD_SCRIPT}")
        return 2

    print("building native tests (kernels compiled once, then linked per test)...")
    proc = subprocess.run(
        ["cmd", "/c", str(BUILD_SCRIPT)],
        capture_output=True,
        text=True,
    )
    built = {
        line.split(maxsplit=1)[1].strip()
        for line in proc.stdout.splitlines()
        if line.startswith("BUILT ")
    }
    build_failed = [
        line.split(maxsplit=1)[1].strip()
        for line in proc.stdout.splitlines()
        if line.startswith("BUILD-FAIL ")
    ]

    for name in build_failed:
        log = OUT_DIR / f"{name}.build.log"
        print(f"\n=== {name}: BUILD FAILED ===")
        if log.is_file():
            errors = [ln for ln in log.read_text(errors="replace").splitlines() if "error" in ln]
            for line in errors[:6]:
                print("   ", line.strip())

    results: list[tuple[str, int, int, str]] = []
    for name in sorted(built):
        exe = OUT_DIR / f"{name}.exe"
        if not exe.is_file():
            results.append((name, 0, 0, "executable missing"))
            continue
        try:
            run_proc = subprocess.run([str(exe)], capture_output=True, text=True, timeout=120)
            text = run_proc.stdout + run_proc.stderr
        except subprocess.TimeoutExpired:
            text = "TIMEOUT after 120s"
            run_proc = None
        (OUT_DIR / f"{name}.out").write_text(text, encoding="utf-8", errors="replace")

        passed = len(OK_RE.findall(text))
        failed = len(FAIL_RE.findall(text))
        note = f"exit {run_proc.returncode}" if run_proc and run_proc.returncode else ""
        if run_proc is None:
            note = "timeout"
        results.append((name, passed, failed, note))

    width = max((len(n) for n, *_ in results), default=10)
    print(f"\n{'test'.ljust(width)}  passed  failed  status")
    print("-" * (width + 26))
    for name, passed, failed, note in results:
        if failed:
            status = "FAIL"
        elif passed:
            status = "OK"
        else:
            # No [OK]/[FAIL] markers: the binary ran but did not report in the
            # convention. Not a failure, but not evidence either.
            status = "NO CHECKS"
        if note:
            status += f" ({note})"
        print(f"{name.ljust(width)}  {passed:>6}  {failed:>6}  {status}")
        if failed:
            out_file = OUT_DIR / f"{name}.out"
            if out_file.is_file():
                for line in out_file.read_text(errors="replace").splitlines():
                    if FAIL_RE.search(line):
                        print(f"    {line.strip()}")

    total_fail = sum(f for _, _, f, _ in results) + len(build_failed)
    total_ok = sum(p for _, p, _, _ in results)
    print("-" * (width + 26))
    print(f"total: {total_ok} checks passed, {total_fail} failed across {len(results)} binaries")

    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(run())
