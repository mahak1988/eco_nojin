"""Run both test suites with the native one built once and the Python one parallel.

Two speed facts, measured rather than assumed:

* The native suite was rebuilding all eleven kernel sources for each of the thirteen
  test programs. ``build_tests.bat`` now compiles them once into a static library
  and links each test against it, which took the native suite from several
  minutes to about 44 seconds.
* The Python suite is dominated by a handful of slow API tests -- the slowest is
  12.6 s -- rather than by many cheap ones. Eight workers buy about 13%, because
  the expensive tests do crypto and I/O that does not parallelise. Per-test
  scheduling (``--dist load``) was tried and is not better than per-file.

Usage::

    python scripts/run_tests.py            # both suites
    python scripts/run_tests.py --unit     # Python only
    python scripts/run_tests.py --native   # native only
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"


def _env() -> dict[str, str]:
    env = dict(os.environ)
    # A per-run temp dir, so a stray locked file from an earlier run cannot fail
    # collection the way it did while investigating the warning escalation.
    tmp = Path(tempfile.mkdtemp(prefix="econojin-tests-"))
    env["TEMP"] = env["TMP"] = env["TMPDIR"] = str(tmp)
    return env


def run_unit(workers: int) -> int:
    cmd = [
        str(PYTHON), "-m", "pytest", "tests/unit",
        "-p", "no:cacheprovider", "-q", "--tb=line", "-n", str(workers),
        "--dist", "loadfile",
    ]
    print(f"--- python unit suite ({workers} workers) ---", flush=True)
    start = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, env=_env())
    print(f"    {time.perf_counter() - start:.1f}s")
    return proc.returncode


def run_native() -> int:
    print("--- native suite (kernels compiled once) ---", flush=True)
    start = time.perf_counter()
    proc = subprocess.run(
        [str(PYTHON), "scripts/run_cpp_tests.py"], cwd=ROOT, env=_env()
    )
    print(f"    {time.perf_counter() - start:.1f}s")
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit", action="store_true", help="Python unit suite only")
    ap.add_argument("--native", action="store_true", help="native suite only")
    ap.add_argument(
        "-j", "--workers", type=int, default=min(8, os.cpu_count() or 4),
        help="pytest workers for the Python suite",
    )
    args = ap.parse_args()

    both = not args.unit and not args.native
    code = 0
    if args.unit or both:
        code |= run_unit(args.workers)
    if args.native or both:
        code |= run_native()
    return code


if __name__ == "__main__":
    sys.exit(main())
