"""S2 execution backlog: turn the evidence register's gaps into a per-family,
owner-ready promotion plan (ECO-VALIDATION-PROGRAM S2).

This tool is a *planner*, not a promoter. It never changes a status, never
invents a reference, and never fabricates a numeric anchor. It reads three
machine sources and cross-references them so the honest next action per item is
explicit:

* the census (``tools/validation_status_report.build_census``) — which of the 70
  models are ``validated`` / ``unvalidated`` and their maturity level;
* the evidence register (``reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json``) —
  the ``evidence_class``, the ``basis`` and the ``gap`` for every formula family,
  which is the machine source that decides whether a model may claim
  ``validated``;
* the validation records (``engine/validation/*.md``) — the models that already
  re-run through the gateway and reproduce an independently-derived reference.

Each register family is classified into one of four promotion paths, derived
only from the register's own ``gap`` / ``basis`` text (no judgement is added):

* ``DONE_EXTERNAL``            — already ``VALIDATED_EXTERNAL``.
* ``VENDOR_OFFLINE_ANCHOR``    — method/regression evidence, but the gap names a
  missing *published numeric/table*; an owner can vendor it offline and add the
  register row + card row.
* ``DESIGN_DECISION_REQUIRED`` — the gap names project-invented weights, an
  uncited convention, a conflicting convention, an unattributed regression or a
  withdrawn citation. A numeric anchor cannot fix these; they are STOP-brake
  decisions (SB-05/SB-07) that need a named owner first.
* ``INVESTIGATE``              — none of the above; a reader must resolve it.

Read-only except for its ``--out`` artefacts. Offline, stdlib-only.

Usage::

    python tools/validation_backlog.py --out reports/validation
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPO_ROOT / "reports" / "eco-nojin" / "FORMULA-EVIDENCE-REGISTER.json"
RECORDS_DIR = REPO_ROOT / "engine" / "validation"
RECORD_SCHEMA = "hydroma.validation.record@1"
_JSON_FENCE = re.compile(r"```json\n(.*?)```", re.DOTALL)
#: The sentence in each record's Limitations §6.1 that names the *exact*
#: external artifact that would move the model, e.g. "The row that would move it
#: is a published measured irrigation depth against a metered application."
_MOVE_HINT = re.compile(r"would move it is ([^.]+)\.", re.IGNORECASE)

#: Gap-text markers that mean a numeric anchor can close the gap.
_VENDORABLE = (
    "no published value",
    "no published numeric",
    "published numeric",
    "table pending",
    "no published table",
    "unavailable offline",
    "no external anchor",
    "no published",
    "published ... table",
    "needs one is a",
    "value printed",
)
#: Gap-text markers that mean a human decision must precede any anchor.
_DECISION = (
    "project-invented",
    "weights",
    "convention",
    "conflict",
    "unattributed",
    "uncited",
    "withdrawn",
    "design assumption",
    "calibrat",
    "self-declared",
    "0.85",
    "0.95 ceiling",
    "proxy",
    "no citation",
    "unsourced",
    "project's own",
    "projects own",
    "composite of composites",
    "contradicted",
    "false pretext",
)


def _classify(entry: dict[str, Any]) -> str:
    """Promotion path for one register family, from its own text only."""
    cls = str(entry.get("evidence_class", "")).upper()
    if cls == "VALIDATED_EXTERNAL":
        return "DONE_EXTERNAL"
    gap = str(entry.get("gap") or "").lower()
    basis = str(entry.get("basis") or "").lower()
    text = f"{gap} {basis}"
    if any(m in text for m in _DECISION):
        return "DESIGN_DECISION_REQUIRED"
    if any(m in text for m in _VENDORABLE) or gap.strip():
        # A named gap with no decision marker is normally a missing numeric.
        return "VENDOR_OFFLINE_ANCHOR"
    return "INVESTIGATE"


def _load_records() -> list[dict[str, Any]]:
    """Every validation record's machine block + the §6.1 "what would move it".

    The move hint is the record author's own exact statement of the *external*
    artifact required to promote the model; it is surfaced verbatim (asterisks
    stripped) so an owner sources the real thing instead of a fabricated value.
    """
    out: list[dict[str, Any]] = []
    for path in sorted(RECORDS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        hint = _MOVE_HINT.search(text)
        move_hint = hint.group(1).replace("*", "").strip() if hint else None
        for block in _JSON_FENCE.findall(text):
            try:
                payload = json.loads(block)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and payload.get("schema") == RECORD_SCHEMA:
                payload["move_hint"] = move_hint
                out.append(payload)
                break
    return out


def build_backlog() -> dict[str, Any]:
    from tools.validation_status_report import build_census

    census = build_census()
    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    entries = register.get("entries", [])

    families = []
    for entry in entries:
        families.append(
            {
                "indicator_id": entry.get("indicator_id"),
                "evidence_class": entry.get("evidence_class"),
                "gap": entry.get("gap"),
                "reference": entry.get("reference"),
                "promotion_path": _classify(entry),
            }
        )

    klass_counts = Counter(str(e.get("evidence_class")) for e in entries)
    path_counts = Counter(f["promotion_path"] for f in families)

    records = _load_records()
    validated_models = set(census["models"]["validated_ids"])
    unvalidated_models = set(census["models"]["unvalidated_ids"])

    record_rows = []
    for rec in records:
        mid = rec.get("model_id")
        cases = rec.get("cases", [])
        matches = sum(1 for c in cases if c.get("verdict") == "match")
        discrepancies = sum(1 for c in cases if c.get("verdict") == "discrepancy")
        if mid in validated_models:
            tier = "validated"
        elif discrepancies:
            tier = "unvalidated_discrepancy"
        elif matches and rec.get("validation_status") == "unvalidated":
            tier = "unvalidated_method_conformance"  # one anchor away
        else:
            tier = "unvalidated"
        record_rows.append(
            {
                "model_id": mid,
                "record_status": rec.get("validation_status"),
                "vocabulary_label": rec.get("status_vocabulary_label"),
                "matches": matches,
                "discrepancies": discrepancies,
                "registry_gap": rec.get("registry_gap"),
                "move_hint": rec.get("move_hint"),
                "registry_validation_status": rec.get("validation_status"),
                "tier": tier,
            }
        )

    recorded_ids = {r["model_id"] for r in record_rows}
    # Models with neither a validation record nor (best-effort) a family pointer:
    no_artifact = sorted(unvalidated_models - recorded_ids)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "tool": "tools/validation_backlog.py",
        "census": {
            "total": census["models"]["total"],
            "validated": len(validated_models),
            "unvalidated": len(unvalidated_models),
            "s3_plus": census["maturity"]["s3_plus_count"],
        },
        "register": {
            "families": len(families),
            "evidence_class_counts": dict(klass_counts),
            "promotion_path_counts": dict(path_counts),
        },
        "families": families,
        "cluster_models": record_rows,
        "unvalidated_without_evidence_artifact": {
            "count": len(no_artifact),
            "model_ids": no_artifact,
        },
    }


def _render(backlog: dict[str, Any]) -> str:
    cen = backlog["census"]
    reg = backlog["register"]
    lines = [
        "# S2 Validation Execution Backlog",
        "",
        f"*Generated {backlog['generated_at']} by `{backlog['tool']}`. "
        "A planner, not a promoter: it never changes a status or invents a "
        "reference. Re-generate it; do not hand-edit.*",
        "",
        "> **DECISION D-V-01 (2026-10-15):** the `unvalidated_method_conformance` "
        "families below sit at their honest standard-based ceiling. EXTERNAL "
        "promotion is **BLOCKED_ON_OWNER_PUBLISHED_NUMERIC** — it needs a genuine "
        "published/measured value (never a re-derivation); each `move_hint` names it. "
        "See ECO-VALIDATION-PROGRAM.md §11.",
        "",
        "## Headline",
        "",
        f"- models: {cen['total']} — validated {cen['validated']} / "
        f"unvalidated {cen['unvalidated']} (S3+ {cen['s3_plus']})",
        f"- register families: {reg['families']}",
        f"- unvalidated models with **no** evidence artifact yet: "
        f"**{backlog['unvalidated_without_evidence_artifact']['count']}**",
        "",
        "## Evidence-class census (register)",
        "",
        "| evidence_class | families |",
        "|---|---:|",
    ]
    for cls, n in sorted(reg["evidence_class_counts"].items()):
        lines.append(f"| {cls} | {n} |")
    lines += [
        "",
        "## Promotion paths (register, from each family's own gap text)",
        "",
        "| promotion_path | families |",
        "|---|---:|",
    ]
    for path, n in sorted(reg["promotion_path_counts"].items()):
        lines.append(f"| {path} | {n} |")
    lines += [
        "",
        "### 1. Closest to promotion — `VENDOR_OFFLINE_ANCHOR`",
        "",
        "Method/regression evidence exists; the gap names a missing *published "
        "numeric/table*. An owner can vendor it offline (CSV+meta, ZED), add the "
        "register row and the card `validation_status` row, then flip to "
        "`VALIDATED_EXTERNAL`.",
        "",
        "| family | current class | gap to close |",
        "|---|---|---|",
    ]
    for fam in backlog["families"]:
        if fam["promotion_path"] == "VENDOR_OFFLINE_ANCHOR":
            lines.append(
                f"| {fam['indicator_id']} | {fam['evidence_class']} | "
                f"{fam['gap'] or '—'} |"
            )
    lines += [
        "",
        "### 2. Decision first — `DESIGN_DECISION_REQUIRED`",
        "",
        "A numeric anchor cannot close these: they rest on project-invented "
        "weights, an uncited/conflicting convention, an unattributed regression "
        "or a withdrawn citation. Each is a public STOP brake (SB-05/SB-07) with a "
        "named owner before any validation is possible.",
        "",
        "| family | current class | decision needed |",
        "|---|---|---|",
    ]
    for fam in backlog["families"]:
        if fam["promotion_path"] == "DESIGN_DECISION_REQUIRED":
            lines.append(
                f"| {fam['indicator_id']} | {fam['evidence_class']} | "
                f"{fam['gap'] or fam['basis'] or '—'} |"
            )
    lines += [
        "",
        "## Cluster models (validation records — re-run through the gateway)",
        "",
        "| model | registry status | matches | discrepancies | tier | what moves it |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in backlog["cluster_models"]:
        if row["tier"] == "validated":
            moves = "already validated"
        elif row.get("move_hint"):
            moves = row["move_hint"]
        elif row["registry_gap"]:
            moves = row["registry_gap"]
        elif row["tier"] == "unvalidated_discrepancy":
            moves = "recorded discrepancy — resolve it before any promotion"
        else:
            moves = "add an external register anchor + card row"
        lines.append(
            f"| {row['model_id']} | {row['record_status']} | {row['matches']} | "
            f"{row['discrepancies']} | {row['tier']} | {moves} |"
        )
    lines += [
        "",
        "## How a method-conformance model is promoted (owner steps, no fabrication)",
        "",
        "For each `unvalidated_method_conformance` row above the `move_hint` is the",
        "**exact external artifact to source** (a *published* worked/tabulated value or",
        "a *measured* dataset — never a re-derivation of the formula, which is already",
        "what method-conformance means). To promote, wire in this order:",
        "",
        "1. Vendor the published artifact offline: `tests/reference_data/<X>.csv` +",
        "   `<X>.meta.json` + checksum (ZED, no live download).",
        "2. Add a register row `VALIDATED_EXTERNAL` in",
        "   `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` citing that artifact.",
        "3. Wire `engine/tests/test_machine_evidence_consistency.py`",
        "   (`EXTERNALLY_ANCHORED_MODELS[model] = <row>`) and deliberately raise the",
        "   `len(external) == 9` cap in `test_corpus_external_anchors_are_reported_distinctly`.",
        "4. Set the card `validation_status` row (engine/models/cards/<MODEL>.md) and",
        "   update `CLUSTER_MODELS_MOVED_TO_VALIDATED` in",
        "   `engine/validation/test_validation_records.py`.",
        "5. Re-run the gate; the registry then derives `validated` from the card row.",
        "",
        "Steps 3-4 are in-flight engine/** surfaces (STOP brakes SB-03/SB-10):",
        "coordinate with the owning agent, do not edit out of band.",
    ]
    lines += [
        "",
        "## Unvalidated models with no evidence artifact yet (S2 authoring to-do)",
        "",
        "These need a validation record (engine/validation/<MODEL>.md) and a "
        "register row created before any anchor is meaningful.",
        "",
        "```",
        " ".join(backlog["unvalidated_without_evidence_artifact"]["model_ids"]),
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/validation")
    args = parser.parse_args()

    backlog = build_backlog()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    (out_dir / f"BACKLOG-{stamp}.json").write_text(
        json.dumps(backlog, indent=2), encoding="utf-8"
    )
    (out_dir / "BACKLOG.md").write_text(_render(backlog), encoding="utf-8")
    (out_dir / "BACKLOG.json").write_text(
        json.dumps(backlog, indent=2), encoding="utf-8"
    )

    reg = backlog["register"]["promotion_path_counts"]
    print(
        f"backlog: {backlog['register']['families']} families | "
        f"vendorable={reg.get('VENDOR_OFFLINE_ANCHOR', 0)} "
        f"decision={reg.get('DESIGN_DECISION_REQUIRED', 0)} "
        f"done_external={reg.get('DONE_EXTERNAL', 0)} | "
        f"no-artifact models={backlog['unvalidated_without_evidence_artifact']['count']}"
    )
    print(f"wrote {out_dir}/BACKLOG.md, BACKLOG.json, BACKLOG-{stamp}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
