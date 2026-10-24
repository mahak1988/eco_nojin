#!/usr/bin/env python3
"""Coverage ratchet gate — remediation item C-3, safety brake SB-08.

Run the whole suite under ``coverage``, read the JSON totals and refuse to
regress below a recorded floor:

    python tools/coverage_gate.py                 # enforce, ~full suite
    python tools/coverage_gate.py --print         # report only, always 0
    python tools/coverage_gate.py --json cov.json # report an existing report

**The floor is a ratchet, not a target.** SB-08 (see
``engine/honesty/statuses.py``) records that coverage is currently unmeasured
and must never be allowed to fall. The recorded schedule is a floor of 55 %
overall and 45 % for the engine, **raised by +5 % per month up to 80 %**. The
gate never raises its own floor: raising it is a recorded decision by the
programme owner, made in a commit that also records the newly measured number.
That asymmetry is deliberate — a tool that self-raises its own floor turns a
measurement into an opinion.

**One floor today, two after the split.** The engine's *scientific* paths and
the services' wire-up paths are lumped into a single overall number here because
``engine/`` and ``services/`` still share one test tree. Item A-1 (the gateway
split) lands first, and once the scientific paths have their own package root
the engine's scientific coverage must be measured **separately** from the
services' — a services number lifted by thin router tests would otherwise hide
an uncovered scientific kernel, which is precisely the failure mode SB-08
exists to prevent. Until then the ``--engine-floor`` default is the only
engine-side guard this gate applies.

Stdlib and ``subprocess`` only: no third-party import, so the gate can run in
an environment where the dev extras are missing (it then reports the missing
``pytest-cov`` plugin instead of crashing).

Exit codes:

    0  measured and at or above every floor, or ``--print`` reporting
    1  below a floor (the gate's blocking failure)
    2  ``pytest-cov`` is absent — the gate cannot run, nothing was measured
    3  no coverage data to read (missing or unparseable JSON)

Code 2 is *not* a pass: a caller that treats "plugin missing" as green has
re-created the unmeasured state SB-08 names. It is reported distinctly so the
caller can decide.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: Repository root (this file lives in ``tools/``).
REPO_ROOT = Path(__file__).resolve().parents[1]

#: Overall floor enforced by default (SB-08: the starting rung of the ratchet).
DEFAULT_FLOOR = 55.0

#: Floor enforced over the ``engine/`` files alone. The engine is the
#: behaviour-preserving half of the tree; its floor starts lower because the
#: scientific parity suites measure differently from the service tests.
DEFAULT_ENGINE_FLOOR = 45.0

#: The ratchet step and its ceiling, recorded in SB-08 and in the
#: constitution's KPI table.
RATCHET_STEP = 5.0
RATCHET_TARGET = 80.0

#: The coverage plugin the suite needs. Named as an importable module so its
#: absence is detectable without importing it.
COVERAGE_PLUGIN = "pytest_cov"

#: The two roots the suite is measured over, and the pytest targets that name
#: them. ``--cov=engine --cov=services`` is what makes the JSON report carry
#: per-file data for exactly these two roots.
COVERAGE_ROOTS = ("engine", "services")

#: Areas whose coverage is reported separately from the overall number.
AREA_ORDER = ("engine", "services")

EXIT_OK = 0
EXIT_BELOW_FLOOR = 1
EXIT_PLUGIN_MISSING = 2
EXIT_NO_DATA = 3


@dataclass(frozen=True)
class Measurement:
    """Percentages and statement counts read out of a coverage JSON report."""

    overall: float
    engine: float | None
    services: float | None
    overall_statements: int
    engine_statements: int
    services_statements: int
    overall_covered: int
    engine_covered: int
    services_covered: int


def _pytest_cov_present() -> bool:
    """True when the coverage plugin is importable (stdlib probe, no import)."""
    try:
        return importlib.util.find_spec(COVERAGE_PLUGIN) is not None
    except (ImportError, ValueError):  # pragma: no cover - hostile sys.path
        return False


def _normalise(name: str) -> str:
    """``./engine\\hydroma`` -> ``engine/hydroma`` (coverage JSON path noise)."""
    text = name.replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text.lstrip("/")


def _summary_of(entry: Any) -> dict[str, Any]:
    """The ``summary`` mapping of one ``files`` entry, tolerating odd shapes."""
    if not isinstance(entry, dict):
        return {}
    summary = entry.get("summary")
    return summary if isinstance(summary, dict) else {}


def _int(mapping: dict[str, Any], key: str) -> int:
    value = mapping.get(key, 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def read_measurement(payload: Any) -> Measurement:
    """Turn a parsed coverage JSON document into a :class:`Measurement`.

    Both shapes are accepted: ``coverage.py``'s ``json`` report (a ``totals``
    mapping plus a ``files`` mapping), and a bare ``files`` mapping produced by
    hand for tests. The area percentages are recomputed from the per-file
    statement counts so that the reported engine number describes the engine
    and nothing else — ``totals.percent_covered`` is never used as the engine
    figure, because it describes every measured file in the run.
    """
    files: dict[str, Any] = {}
    if isinstance(payload, dict):
        candidate = payload.get("files")
        if isinstance(candidate, dict):
            files = candidate

    per_area: dict[str, list[int]] = {area: [0, 0] for area in AREA_ORDER}
    total_covered = 0
    total_statements = 0
    for name, entry in files.items():
        normalised = _normalise(str(name))
        area = normalised.split("/", 1)[0] if "/" in normalised else ""
        summary = _summary_of(entry)
        covered = _int(summary, "covered_lines")
        statements = _int(summary, "num_statements")
        bucket = per_area.get(area)
        if bucket is not None:
            bucket[0] += covered
            bucket[1] += statements
        total_covered += covered
        total_statements += statements

    def _pct(covered: int, statements: int) -> float | None:
        return (100.0 * covered / statements) if statements else None

    overall = (
        (100.0 * total_covered / total_statements) if total_statements else 0.0
    )
    engine_covered, engine_statements = per_area["engine"]
    services_covered, services_statements = per_area["services"]
    return Measurement(
        overall=overall,
        engine=_pct(engine_covered, engine_statements),
        services=_pct(services_covered, services_statements),
        overall_statements=total_statements,
        engine_statements=engine_statements,
        services_statements=services_statements,
        overall_covered=total_covered,
        engine_covered=engine_covered,
        services_covered=services_covered,
    )


def _fmt(value: float | None) -> str:
    return "not measured" if value is None else f"{value:.2f} %"


def _report(measurement: Measurement, floor: float, engine_floor: float) -> list[str]:
    lines = [
        "coverage gate — overall "
        f"{_fmt(measurement.overall)} "
        f"(engine {_fmt(measurement.engine)}, services {_fmt(measurement.services)})",
        f"  overall  : {_fmt(measurement.overall):>12} "
        f"({measurement.overall_covered}/{measurement.overall_statements} "
        f"statements)  floor {floor:.2f} %",
        f"  engine   : {_fmt(measurement.engine):>12} "
        f"({measurement.engine_covered}/{measurement.engine_statements} "
        f"statements)  floor {engine_floor:.2f} %",
        f"  services : {_fmt(measurement.services):>12} "
        f"({measurement.services_covered}/{measurement.services_statements} "
        "statements)",
        "  ratchet  : floor "
        f"{floor:.2f} % now, +{RATCHET_STEP:.0f} % per month to "
        f"{RATCHET_TARGET:.0f} % (SB-08); raising the floor is an owner decision",
    ]
    return lines


def _ratchet_plan() -> str:
    """The recording of how the floor is meant to move (SB-08)."""
    return (
        "    ratchet: floor "
        f"{DEFAULT_FLOOR:.0f} % overall / {DEFAULT_ENGINE_FLOOR:.0f} % engine now, "
        f"+{RATCHET_STEP:.0f} % per month to {RATCHET_TARGET:.0f} % (SB-08); "
        "raising the floor is a recorded owner decision, never a tool default"
    )


def _child_env() -> tuple[dict[str, str], list[str]]:
    """The environment pytest runs in, plus the defaults that were applied.

    ``PYTHONPATH`` and ``SECRET_KEY`` are supplied only when they are absent,
    so a caller that already set them (CI, the pre-edit hook, a shell where the
    operator exported them) is never overridden. The defaults mirror the
    repository's ``AGENTS.md``: the two path roots the engine and the services
    import across, and the non-secret test key the GBIF/data-pipeline suite
    requires.
    """
    env = dict(os.environ)
    applied: list[str] = []
    if not env.get("PYTHONPATH"):
        sibling = REPO_ROOT.parent / "eco_nojin"
        parts = [str(REPO_ROOT)]
        if sibling.is_dir():
            parts.append(str(sibling))
        env["PYTHONPATH"] = os.pathsep.join(parts)
        applied.append(f"PYTHONPATH={env['PYTHONPATH']}")
    if not env.get("SECRET_KEY"):
        env["SECRET_KEY"] = "test-secret-key"
        applied.append("SECRET_KEY=<default test key>")
    return env, applied


def run_suite(json_path: Path) -> bool:
    """Run the suite under ``--cov`` writing ``json_path``.

    Returns True when the report file exists afterwards. The suite's own exit
    status is deliberately not the gate's exit status: a failing test is the
    test suite's business, and this gate's business is the coverage number. A
    red suite still produces a JSON report, and refusing to read it would hide
    the regression the floor exists to catch.
    """
    command = [
        sys.executable,
        "-m",
        "pytest",
        *(f"{root}/" for root in COVERAGE_ROOTS),
        "--cov=engine",
        "--cov=services",
        f"--cov-report=json:{json_path}",
        "-q",
        "-p",
        "no:cacheprovider",
    ]
    env, applied = _child_env()
    for note in applied:
        print(f"note: defaulted {note}")
    print("coverage gate — running: " + " ".join(command[2:]))
    result = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=False,
        check=False,
    )
    print(f"coverage gate — pytest exit status {result.returncode}")
    return json_path.is_file()


def _load_json(path: Path) -> Any:
    """Read a coverage JSON document, raising :class:`ValueError` if unusable."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coverage_gate",
        description=(
            "Measure coverage for engine/ and services/ and enforce the SB-08 "
            "ratchet floor."
        ),
    )
    parser.add_argument(
        "--floor",
        type=float,
        default=DEFAULT_FLOOR,
        help="overall floor in percent (default: %(default)s)",
    )
    parser.add_argument(
        "--engine-floor",
        type=float,
        default=DEFAULT_ENGINE_FLOOR,
        help="floor for the engine/ files alone (default: %(default)s)",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        dest="report_only",
        help="report the measured percentages and exit 0 without enforcing",
    )
    parser.add_argument(
        "--json",
        metavar="PATH",
        default=None,
        help="read an existing coverage JSON report instead of running pytest",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.json is not None:
        json_path = Path(args.json)
        if not json_path.is_file():
            print(f"coverage gate — no coverage data: {json_path} does not exist")
            print(_ratchet_plan())
            return EXIT_NO_DATA
        try:
            payload = _load_json(json_path)
        except ValueError as exc:
            print(f"coverage gate — no coverage data: {exc}")
            return EXIT_NO_DATA
    else:
        if not _pytest_cov_present():
            print(
                f"coverage gate — SKIPPED: the {COVERAGE_PLUGIN} plugin is not "
                "installed, so coverage cannot be measured here."
            )
            print(
                "coverage gate — this is NOT a pass; install pytest-cov "
                "(pip install pytest-cov) and re-run to obtain the number."
            )
            print(_ratchet_plan())
            return EXIT_PLUGIN_MISSING
        with tempfile.TemporaryDirectory(prefix="coverage-gate-") as tmp:
            report = Path(tmp) / "coverage.json"
            if not run_suite(report):
                print(
                    "coverage gate — no coverage data: pytest produced no JSON "
                    f"report at {report}"
                )
                return EXIT_NO_DATA
            try:
                payload = _load_json(report)
            except ValueError as exc:
                print(f"coverage gate — no coverage data: {exc}")
                return EXIT_NO_DATA

    measurement = read_measurement(payload)
    for line in _report(measurement, args.floor, args.engine_floor):
        print(line)

    if args.report_only:
        print("coverage gate — report only (--print): no floor enforced")
        return EXIT_OK

    failures: list[str] = []
    if measurement.overall < args.floor:
        failures.append(
            f"overall {measurement.overall:.2f} % below floor {args.floor:.2f} %"
        )
    if measurement.engine is None:
        print("coverage gate — note: no engine/ statements measured; engine floor waived")
    elif measurement.engine < args.engine_floor:
        failures.append(
            f"engine {measurement.engine:.2f} % below floor "
            f"{args.engine_floor:.2f} %"
        )

    if failures:
        print("NOT-READY — coverage below floor: " + "; ".join(failures))
        return EXIT_BELOW_FLOOR
    print("READY — coverage at or above every floor")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
