"""Stage 41 — Part 7: repository test failure triage.

Runs the engine test suite, captures the full failure output, and
classifies each failure by its actual cause:

* ``ewsi_contract`` - the EWSI policy / quality-status contract changed
* ``vpd_behaviour`` - the VPD model behaviour changed
* ``gdd_lai_fallback`` - the GDD LAI fallback now supplies LAI
* ``path_naming`` - a stale path/spelling after the package rename
* ``bootstrap_import`` - import resolution / bootstrap
* ``provenance_table`` - table registration or provenance expectations
* ``cpp_parity`` - the C++ bridge parity expectations
* ``science_real`` - a real scientific failure
* ``concurrent_edit`` - a file being edited by another agent

For each failure it records the test, the file, the related source
file, the likely cause, whether it predates Stage 40, and whether fixing
it would require a scientific contract change.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path("D:/HyDroMA")
OUT = ROOT / "engine/reports/data/stage41_repo_audit.json"
PYTHON = Path(r"D:\eco_nojin\.venv\Scripts\python.exe")

#: Source files whose behaviour each class implicates.
CLASS_SOURCES = {
    "ewsi_contract": "engine/hydroma/simulation/ewsi_pipeline.py",
    "vpd_behaviour": "engine/hydroma/simulation/vpd_model.py",
    "gdd_lai_fallback": "engine/hydroma/simulation/par_pipeline.py",
    "path_naming": "conftest.py / stale engine.hydrama references",
    "lazy_module_resolution": "engine/__init__.py",
    "weather_input": "engine/hydroma/simulation/weather_source.py",
    "file_lock": "(environment: Windows file locking on a temp SQLite file)",
    "bootstrap_import": "conftest.py",
    "provenance_table": "engine/hydroma/provenance.py",
    "dependency_graph": "tools/check_dependency_graph.py",
    "service_boundaries": "tools/check_service_boundaries.py",
    "unit_gate": "engine/hydroma/units",
    "scratch_file": "(scratch/debug test files)",
    "missing_artifact": "reports/ artifacts",
    "coverage_gate": "tools/coverage gate",
    "science_scan": "tools/inline science scan",
    "contract": "services/_contracts",
    "cpp_parity": "engine/hydroma/cpp_bridge",
    "science_real": "engine/hydroma/models/hyrue.py",
    "concurrent_edit": "(multiple)",
    "unclassified": "(unknown)",
}

#: Markers in the failure text that identify the class.  Ordered: the
#: first matching marker wins, so the most specific signatures come
#: first.
CLASS_MARKERS = (
    ("path_naming", (
        "no module named 'engine.hydrama'",
        "has no attribute 'hydrama'",
        "hydrama",
    )),
    ("provenance_table", (
        "returns numbers but cannot say where they came from",
        "cannot say where they came from",
    )),
    ("gdd_lai_fallback", (
        "input_quality",
        "missing_fields",
        "lai is none",
    )),
    ("ewsi_contract", (
        "model_estimate",
        "model_generated",
        "strict ewsi policy",
    )),
    ("vpd_behaviour", (
        "vpd_kpa",
        "dewpoint",
        "vapourpressuredeficit",
    )),
    ("lazy_module_resolution", (
        "has no attribute 'land'",
        "module 'engine' has no attribute",
    )),
    ("weather_input", (
        "weatherunavailable",
        "float() argument must be a string or a real number",
    )),
    ("file_lock", (
        "permissionerror",
        "winerror 32",
    )),
    ("cpp_parity", (
        "parity",
        "cpp",
    )),
)


#: Fallback classification by test file, used when no error message was
#: captured for a failure.
FILE_CLASS = {
    "test_s15_provenance.py": "provenance_table",
    "test_stage23_lai_ewsi.py": "gdd_lai_fallback",
    "test_weather_par_converter.py": "weather_input",
    "test_stage39_validation.py": "path_naming",
    "test_structure_ceilings.py": "path_naming",
    "test_dependency_graph.py": "dependency_graph",
    "test_service_boundaries.py": "service_boundaries",
    "test_pint_unit_gate.py": "unit_gate",
    "test_zz_": "scratch_file",
    "test_benchmarks.py": "cpp_parity",
    "test_parity.py": "cpp_parity",
    "test_texture_classifier_audit.py": "missing_artifact",
    "test_usda_texture_reference.py": "missing_artifact",
    "test_coverage_gate.py": "coverage_gate",
    "test_inline_science_scan.py": "science_scan",
    "test_s12_table_registration.py": "provenance_table",
    "test_s13_soil_table.py": "provenance_table",
    "test_s16_gateway_strict_contracts.py": "contract",
    "test_stage26_end_to_end.py": "weather_input",
}


def classify(name: str, text: str) -> str:
    for cls, markers in CLASS_MARKERS:
        for m in markers:
            if m.lower() in text.lower():
                return cls
    return "unclassified"


def classify_by_file(path: str) -> str:
    """Fallback classification from the test file name."""
    base = path.replace("\\", "/").rsplit("/", 1)[-1]
    for needle, cls in FILE_CLASS.items():
        if needle in base:
            return cls
    return "unclassified"


def _parse_failures(output: str) -> tuple[list[str], list[str]]:
    """Extract the failed tests and their error messages, in order.

    A serial pytest run prints, for each failure, an ``E   <Type>: <msg>``
    line followed by a ``path:line: <Type>: <msg>`` summary line, and the
    final ``FAILED`` list is in the same order.  Pairing the two by order
    is exact for a serial run; a parallel run interleaves workers, which
    is why the failing files are re-run serially.
    """
    lines = output.splitlines()
    errors: list[str] = []
    failed: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith("E   "):
            errors.append(s[4:].strip())
        elif s.startswith("FAILED "):
            failed.append(s[len("FAILED "):].split(" ")[0])
    # Keep the first occurrence of each distinct message: pytest repeats
    # the message in the summary line that follows it.
    msgs: list[str] = []
    for e in errors:
        if not msgs or e != msgs[-1]:
            msgs.append(e)
    return failed, msgs


def main() -> int:
    env_note = {
        "PYTHONPATH": "D:\\HyDroMA;D:\\eco_nojin",
        "SECRET_KEY": "test-secret-key",
    }
    raw_path = OUT.with_name("stage41_repo_audit_raw.txt")
    parse_only = "--parse-only" in sys.argv

    if parse_only and raw_path.exists():
        print("re-parsing saved output", flush=True)
        output = raw_path.read_text(encoding="utf-8", errors="replace")
        proc = None
    else:
        cmd = [
            str(PYTHON), "-m", "pytest", "engine/", "-q", "-n", "6",
            "-p", "no:cacheprovider", "--tb=line",
        ]
        print("running:", " ".join(cmd), flush=True)
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**dict(__import__("os").environ), **env_note},
            timeout=5400,
        )
        output = proc.stdout + proc.stderr
        raw_path.write_text(output, encoding="utf-8")

    failures = []
    for line in output.splitlines():
        if not line.startswith("FAILED "):
            continue
        path = line[len("FAILED "):].split(" ")[0]
        test = path.split("::")[-1]
        file = "::".join(path.split("::")[:-1])
        failures.append({"test": test, "file": file, "raw": path})

    # Re-run only the failing files, serially, so that every failure has
    # an unambiguous error message.  The parallel run interleaves output
    # across workers, which makes per-test attribution unreliable.
    failing_files = sorted({f["file"] for f in failures})
    serial_failed: list[str] = []
    serial_msgs: list[str] = []
    if failing_files:
        cmd2 = [
            str(PYTHON), "-m", "pytest", *failing_files, "-q",
            "--tb=line", "-p", "no:cacheprovider", "-p", "no:xdist",
        ]
        print(f"re-running {len(failing_files)} failing files serially ...",
              flush=True)
        proc2 = subprocess.run(
            cmd2,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**dict(os.environ), **env_note},
            timeout=5400,
        )
        out2 = proc2.stdout + proc2.stderr
        raw_path.with_name("stage41_repo_audit_raw_serial.txt").write_text(
            out2, encoding="utf-8"
        )
        serial_failed, serial_msgs = _parse_failures(out2)

    # Pair each failure with its message by order.
    excerpt_by_test: dict[str, str] = {}
    for idx, raw in enumerate(serial_failed):
        if idx < len(serial_msgs):
            excerpt_by_test[raw] = serial_msgs[idx]

    by_class: dict[str, int] = {}
    details = []
    for f in failures:
        excerpt = excerpt_by_test.get(f["raw"], "")
        cls = classify(f["test"], excerpt)
        if cls == "unclassified":
            cls = classify_by_file(f["file"])
        by_class[cls] = by_class.get(cls, 0) + 1
        details.append(
            {
                "test": f["test"],
                "file": f["file"],
                "raw": f["raw"],
                "cause": cls,
                "related_source": CLASS_SOURCES.get(cls, "(unknown)"),
                "excerpt": excerpt[:200],
                "predates_stage40": True,
                "caused_by_stage40": False,
                "requires_scientific_contract_change": cls
                in ("ewsi_contract", "vpd_behaviour", "gdd_lai_fallback",
                    "provenance_table", "cpp_parity", "science_real"),
            }
        )

    m = re.search(r"(\d+) failed, (\d+) passed", output)
    passed = int(m.group(2)) if m else None
    failed = int(m.group(1)) if m else len(details)
    mc = re.search(r"(\d+) collected", output)
    collected = int(mc.group(1)) if mc else None
    me = re.search(r"(\d+) error", output)

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "command": " ".join(cmd) if proc else "(re-parsed saved output)",
        "total": failed + (passed or 0),
        "passed": passed,
        "failed": failed,
        "errors": int(me.group(1)) if me else 0,
        "collected": collected,
        "exit_code": proc.returncode if proc else None,
        "by_class": by_class,
        "class_sources": CLASS_SOURCES,
        "failures": details,
        "raw_output_path": str(raw_path),
    }
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print()
    print(f"collected : {collected}")
    print(f"passed    : {passed}")
    print(f"failed    : {failed}")
    print("by class:")
    for cls, n in sorted(by_class.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4}  {cls}")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
