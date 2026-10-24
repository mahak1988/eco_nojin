"""Single source of truth for the scientific validation census (SVHP phase S0).

Computes -- never hand-writes -- every model / equation validation number the
ECO-VALIDATION-PROGRAM quotes, straight from the live registry
(``engine.models.registry``), the maturity view
(``engine.models.maturity``) and, when importable, the formula registry
(``engine.hydroma.formulas``).

This resolves the historical 13-vs-18 drift: the count of
``validation_status == "validated"`` models is *computed here*, so
``AGENTS.md``, ``docs/project/*`` and every report must reference this number
and the JSON this tool writes, never a remembered one. A number that cannot be
produced by re-running this tool is not a number the program may quote.

Read-only: this tool reads the registry and writes only to ``--out``. It never
sets or promotes a status (mirrors ``engine/models/maturity.py`` policy).

Usage::

    python tools/validation_status_report.py --out reports/validation
    python tools/validation_status_report.py --out -      # stdout, JSON only
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.models.maturity import S_LEVELS, maturity_of, maturity_summary
from engine.models.registry import get_model, get_registry


def _opt(import_paths: str | list[str], attr: str) -> Any:
    """Import ``attr`` from the first importable path; degrade honestly if none.

    Accepts one path or an ordered list of candidate paths so a companion import
    works whether this module is run directly (``python tools/...`` puts ``tools/``
    on ``sys.path``) or imported as ``tools.validation_status_report`` (only the
    repo root is on ``sys.path``). Instead of crashing, a module that cannot be
    imported in either mode returns a self-describing marker so the census stays
    computable and reports *why* a companion is missing.
    """
    candidates = [import_paths] if isinstance(import_paths, str) else list(import_paths)
    last_exc: Exception | None = None
    for path in candidates:
        try:
            module = __import__(path, fromlist=[attr])
            return getattr(module, attr)
        except Exception as exc:  # try the next candidate; degrade only after all fail
            last_exc = exc
    reason = f"{type(last_exc).__name__}: {last_exc}" if last_exc else "no candidates"
    return _Unavailable(reason, candidates[-1], attr, tried=candidates)


class _Unavailable:
    """A recorded, self-describing failure of an optional import."""

    def __init__(
        self, reason: str, import_path: str, attr: str, tried: list[str] | None = None
    ) -> None:
        self.reason = reason
        self.import_path = import_path
        self.attr = attr
        self.tried = tried or [import_path]

    def __call__(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "available": False,
            "reason": self.reason,
            "source": f"{self.import_path}.{self.attr}",
            "tried": self.tried,
        }

    def __bool__(self) -> bool:  # pragma: no cover
        return False


def build_census() -> dict[str, Any]:
    """Compute the census from the live registry. Pure w.r.t. the registry."""
    registry = get_registry()
    ids = list(registry.list_ids())

    validation_counts: Counter[str] = Counter()
    implementation_counts: Counter[str] = Counter()
    verification_counts: Counter[str] = Counter()
    per_model: list[dict[str, Any]] = []

    for model_id in ids:
        statuses = registry.status_of(model_id) or {}
        impl = statuses["implementation_status"].value
        ver = statuses["verification_status"].value
        val = statuses["validation_status"].value
        spec = get_model(model_id)
        implementation_counts[impl] += 1
        verification_counts[ver] += 1
        validation_counts[val] += 1
        per_model.append(
            {
                "model_id": model_id,
                "domain": spec.domain,
                "model_type": str(getattr(spec, "model_type", "")),
                "implementation_status": impl,
                "verification_status": ver,
                "validation_status": val,
                "maturity": maturity_of(model_id),
            }
        )

    validated_ids = [m["model_id"] for m in per_model if m["validation_status"] == "validated"]
    unvalidated_ids = [
        m["model_id"] for m in per_model if m["validation_status"] == "unvalidated"
    ]
    other_ids = [
        m["model_id"]
        for m in per_model
        if m["validation_status"] not in {"validated", "unvalidated"}
    ]

    maturity = maturity_summary()

    formula_summary = _opt("engine.hydroma.formulas", "summary")()
    # The triage table is a companion import that must resolve in BOTH run
    # modes: `tools/` on sys.path when run directly, repo root when imported as
    # `tools.validation_status_report`. Try the bare name first, then the
    # package-qualified name, so the census JSON is identical either way.
    triage_rows = _opt(["engine_model_triage", "tools.engine_model_triage"], "build_rows")()
    triage_counts: dict[str, Any]
    if isinstance(triage_rows, list):
        triage_counts = dict(Counter(r["decision"] for r in triage_rows))
        triage_counts["total"] = len(triage_rows)
    else:
        triage_counts = triage_rows  # the honest _Unavailable() marker

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "tool": "tools/validation_status_report.py",
        "models": {
            "total": len(ids),
            "validation_status": dict(validation_counts),
            "implementation_status": dict(implementation_counts),
            "verification_status": dict(verification_counts),
            "validated_ids": validated_ids,
            "unvalidated_ids": unvalidated_ids,
            "other_validation_ids": other_ids,
        },
        "maturity": {
            "levels": {level: maturity["counts"][level] for level in S_LEVELS},
            "s3_plus_count": len(maturity["s3_plus"]),
            "s3_plus_ids": maturity["s3_plus"],
        },
        "formula_registry": formula_summary,
        "triage": triage_counts,
        "per_model": per_model,
    }


def _render_markdown(census: dict[str, Any]) -> str:
    models = census["models"]
    maturity = census["maturity"]
    formula = census["formula_registry"]
    triage = census["triage"]
    lines = [
        "# Scientific validation census",
        "",
        f"*Generated {census['generated_at']} by `{census['tool']}`. "
        "This file is a computed artefact; re-generate it, never hand-edit it.*",
        "",
        "## Models (live registry)",
        "",
        f"- total registered: **{models['total']}**",
        f"- validation `validated`: **{models['validation_status'].get('validated', 0)}**",
        f"- validation `unvalidated`: **{models['validation_status'].get('unvalidated', 0)}**",
        "",
        "| validation_status | count |",
        "|---|---:|",
    ]
    for status, count in sorted(models["validation_status"].items()):
        lines.append(f"| {status} | {count} |")
    lines += [
        "",
        "## Maturity (S0..S6)",
        "",
        f"- S3+ models (ECO-06 bar): **{maturity['s3_plus_count']}**",
        "",
        "| level | count |",
        "|---|---:|",
    ]
    for level in S_LEVELS:
        lines.append(f"| {level} | {maturity['levels'][level]} |")
    lines += ["", "## Formula registry", ""]
    if formula.get("available") is False:
        lines.append(f"- unavailable: {formula.get('reason', 'unknown')}")
    else:
        for key, value in formula.items():
            lines.append(f"- {key}: {value}")
    lines += ["", "## Triage decisions", ""]
    if triage.get("available") is False:
        lines.append(f"- unavailable: {triage.get('reason', 'unknown')}")
    else:
        for key, value in triage.items():
            lines.append(f"- {key}: {value}")
    lines += ["", "## Validated model ids", ""]
    lines += [f"- `{mid}`" for mid in models["validated_ids"]] or ["- (none)"]
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="reports/validation",
        help="Output directory, or '-' for stdout (JSON only).",
    )
    args = parser.parse_args()

    census = build_census()
    validated = census["models"]["validation_status"].get("validated", 0)
    total = census["models"]["total"]
    unvalidated = census["models"]["validation_status"].get("unvalidated", 0)

    if args.out == "-":
        print(json.dumps(census, indent=2))
        return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    json_path = out_dir / f"CENSUS-{stamp}.json"
    md_path = out_dir / f"CENSUS-{stamp}.md"
    # Deterministic latest-copy so docs can link a stable path.
    latest_json = out_dir / "LATEST.json"
    latest_md = out_dir / "LATEST.md"

    payload = json.dumps(census, indent=2)
    rendered = _render_markdown(census)
    json_path.write_text(payload, encoding="utf-8")
    md_path.write_text(rendered, encoding="utf-8")
    latest_json.write_text(payload, encoding="utf-8")
    latest_md.write_text(rendered, encoding="utf-8")

    print(
        f"census: {total} models | validated={validated} unvalidated={unvalidated} "
        f"| S3+={census['maturity']['s3_plus_count']}"
    )
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"updated {latest_json} and {latest_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
