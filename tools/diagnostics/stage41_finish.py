"""Stage 41 — run the final analysis and write all twelve reports.

One command to finish Stage 41 once the benchmark has completed:

    python tools/diagnostics/stage41_finish.py
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path("D:/HyDroMA")
TOOLS = ROOT / "tools/diagnostics"
PYTHON = Path(r"D:\eco_nojin\.venv\Scripts\python.exe")

STEPS = (
    ("freeze audit", TOOLS / "stage41_freeze_audit.py"),
    ("reproducibility check", TOOLS / "stage41_reproducibility.py"),
    ("analysis", TOOLS / "stage41_analysis.py"),
    ("reports", TOOLS / "stage41_write_reports.py"),
)


def main() -> int:
    for label, script in STEPS:
        print("=" * 62, flush=True)
        print(f"Stage 41: {label}", flush=True)
        print("=" * 62, flush=True)
        proc = subprocess.run(
            [str(PYTHON), "-u", str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        tail = [
            line
            for line in (proc.stdout + proc.stderr).splitlines()
            if line.strip() and "gpytorch not available" not in line
            and "CategoryInfo" not in line and "FullyQualifiedErrorId" not in line
            and "NativeCommandError" not in line
        ]
        for line in tail[-18:]:
            print(line)
        if proc.returncode != 0:
            print(f"STEP FAILED: {label} (exit {proc.returncode})")
            return proc.returncode

    reports = sorted((ROOT / "engine/reports").glob("STAGE-41-*.md"))
    print()
    print(f"Stage 41 reports written: {len(reports)}")
    for r in reports:
        print(f"  {r.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
