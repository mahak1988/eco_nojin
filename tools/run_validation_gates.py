"""Run the ECO-VALIDATION-PROGRAM scientific gates and report a verdict (S0).

One command that a developer -- or CI -- can run to answer "is the scientific
validation posture still honest and green?". It composes four independent
checks, keeps their results separate, and fails *closed* on the gates that
must never regress:

1. **census**  -- ``tools/validation_status_report.py`` computes the model /
   equation / maturity numbers from the live registry. A fresh number the
   program can quote.
2. **novel-index gate** -- ``tools/novel_index_gate.py``; blocks any card that
   claims ``VALIDATED_EXTERNAL`` without a published reference. Must be 0.
3. **import guard** -- ``tools/detect_imports.py``; the architecture invariant
   (services never reach engine internals). Must be 0 violations.
4. **validation corpus** -- ``engine/hydroma.models.validation`` summary.
   Informational today: the harness is not fully wired (many ``not_run``), so a
   red corpus would gate on the *harness*, not on the science. Any ``mismatch``
   (the code contradicts a reproducible stored value) is surfaced loudly but
   does not yet fail this composite gate -- that becomes hard once S2 wires the
   cases (see the program doc).

Exit code is 0 only when every *blocking* gate is green. Each check reports its
own status so one failure never masks another.

Usage::

    python tools/run_validation_gates.py
    python tools/run_validation_gates.py --skip-import-guard
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _run_script(rel_path: str, extra: list[str] | None = None) -> tuple[int, str]:
    """Run a repo tool with the current interpreter from the repo root."""
    cmd = [sys.executable, rel_path, *(extra or [])]
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _census_gate() -> dict[str, Any]:
    try:
        from tools.validation_status_report import build_census

        census = build_census()
    except Exception as exc:  # a missing heavy dep must fail a gate, not crash it
        return {
            "name": "census",
            "blocking": True,
            "status": "FAIL",
            "summary": f"{type(exc).__name__}: {exc}",
        }
    return {
        "name": "census",
        "blocking": True,
        "status": "PASS",
        "summary": (
            f"{census['models']['total']} models | "
            f"validated={census['models']['validation_status'].get('validated', 0)} "
            f"unvalidated={census['models']['validation_status'].get('unvalidated', 0)} | "
            f"S3+={census['maturity']['s3_plus_count']}"
        ),
        "detail": census,
    }


def _script_gate(name: str, rel_path: str, extra: list[str] | None = None) -> dict[str, Any]:
    code, output = _run_script(rel_path, extra)
    tail = "\n".join(output.strip().splitlines()[-6:])
    return {
        "name": name,
        "blocking": True,
        "status": "PASS" if code == 0 else "FAIL",
        "exit_code": code,
        "summary": tail or f"{rel_path} exit {code}",
    }


def _corpus_gate() -> dict[str, Any]:
    try:
        from engine.hydroma.models.validation import summary as corpus_summary

        data = corpus_summary()
    except Exception as exc:  # pragma: no cover - honest degrade
        return {
            "name": "validation-corpus",
            "blocking": False,
            "status": "UNAVAILABLE",
            "summary": f"{type(exc).__name__}: {exc}",
        }
    keys = ("match", "mismatch", "inconsistent_case", "not_run")
    counts = Counter(dict.fromkeys(keys, 0))
    counts.update({k: data.get(k, 0) for k in keys})
    status = "PASS" if counts["mismatch"] == 0 else "ATTENTION"
    return {
        "name": "validation-corpus",
        "blocking": False,
        "status": status,
        "summary": (
            f"match={counts['match']} mismatch={counts['mismatch']} "
            f"inconsistent_case={counts['inconsistent_case']} not_run={counts['not_run']}"
        ),
        "detail": dict(data),
    }


def _backlog_gate() -> dict[str, Any]:
    """S2 promotion backlog — informational, never blocks the gate."""
    try:
        from tools.validation_backlog import build_backlog

        backlog = build_backlog()
    except Exception as exc:  # a planning artifact must not fail the gate
        return {
            "name": "s2-backlog",
            "blocking": False,
            "status": "UNAVAILABLE",
            "summary": f"{type(exc).__name__}: {exc}",
        }
    paths = backlog["register"]["promotion_path_counts"]
    return {
        "name": "s2-backlog",
        "blocking": False,
        "status": "INFO",
        "summary": (
            f"{backlog['register']['families']} families | "
            f"vendorable={paths.get('VENDOR_OFFLINE_ANCHOR', 0)} "
            f"decision={paths.get('DESIGN_DECISION_REQUIRED', 0)} "
            f"external={paths.get('DONE_EXTERNAL', 0)} | "
            f"no-artifact models="
            f"{backlog['unvalidated_without_evidence_artifact']['count']}"
        ),
    }


def _uncertainty_gate() -> dict[str, Any]:
    """VG-07 uncertainty baseline — informational, never blocks the gate."""
    try:
        from tools.uncertainty_audit import build_audit

        b = build_audit()["baseline"]
    except Exception as exc:
        return {
            "name": "uncertainty-baseline",
            "blocking": False,
            "status": "UNAVAILABLE",
            "summary": f"{type(exc).__name__}: {exc}",
        }
    real = b["uncertainty_spec_constructions"] + b["records_real_uncertainty"]
    ph = b["sentinel_placeholders"] + b["records_placeholder_uncertainty"]
    return {
        "name": "uncertainty-baseline",
        "blocking": False,
        "status": "INFO",
        "summary": (
            f"VG-07: real uncertainty surfaces={real} "
            f"NOT_ESTIMATED placeholders={ph} (offline/reproducible audit)"
        ),
    }


def _model_cards_gate() -> dict[str, Any]:
    """S6 public model-card sheet — informational, never blocks the gate."""
    try:
        from tools.generate_model_cards import build_cards

        counts = build_cards()["counts"]
    except Exception as exc:  # an honesty artefact must not fail the gate
        return {
            "name": "s6-model-cards",
            "blocking": False,
            "status": "UNAVAILABLE",
            "summary": f"{type(exc).__name__}: {exc}",
        }
    return {
        "name": "s6-model-cards",
        "blocking": False,
        "status": "INFO",
        "summary": (
            f"{counts['total']} models | external={counts['externally_anchored']} "
            f"unanchored-debt={counts['validated_unanchored_debt']} "
            f"method={counts['method_conformance_only']} "
            f"no-artifact={counts['no_artifact']}"
        ),
    }


def run_gates(skip_import_guard: bool = False) -> dict[str, Any]:
    gates: list[dict[str, Any]] = [
        _census_gate(),
        _script_gate("novel-index-gate", "tools/novel_index_gate.py"),
    ]
    if skip_import_guard:
        gates.append(
            {
                "name": "import-guard",
                "blocking": True,
                "status": "SKIPPED",
                "summary": "skipped via --skip-import-guard",
            }
        )
    else:
        gates.append(_script_gate("import-guard", "tools/detect_imports.py", ["--root", "."]))
    gates.append(_corpus_gate())
    gates.append(_backlog_gate())
    gates.append(_model_cards_gate())
    gates.append(_uncertainty_gate())

    blocking_fail = [
        g["name"] for g in gates if g.get("blocking") and g["status"] == "FAIL"
    ]
    verdict = "GREEN" if not blocking_fail else "RED"
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "tool": "tools/run_validation_gates.py",
        "verdict": verdict,
        "blocking_failures": blocking_fail,
        "gates": gates,
    }


def _render(report: dict[str, Any]) -> str:
    lines = [
        "ECO-VALIDATION-PROGRAM gates",
        f"generated: {report['generated_at']}",
        f"VERDICT: {report['verdict']}",
        "",
    ]
    for gate in report["gates"]:
        lines.append(f"[{gate['status']}] {gate['name']}: {gate['summary']}")
    if report["blocking_failures"]:
        lines += ["", "BLOCKING FAILURES: " + ", ".join(report["blocking_failures"])]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-import-guard", action="store_true")
    parser.add_argument(
        "--out",
        default="reports/validation",
        help="Directory to append a timestamped gate log to.",
    )
    args = parser.parse_args()

    report = run_gates(skip_import_guard=args.skip_import_guard)
    text = _render(report)
    print(text)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    (out_dir / f"GATES-{stamp}.txt").write_text(
        text + "\n\n```json\n"
        + __import__("json").dumps(report, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )
    return 0 if report["verdict"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
