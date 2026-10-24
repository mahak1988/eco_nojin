"""S6: generate the public, honest Model Card sheet for every registered model.

A single artefact a reader (user, investor, auditor, new engineer) can trust
without opening the engine: for each of the 70 models it states the registry
status, the maturity level, what it is validated *against*, and the honest
limitations — never claiming more than the machine evidence supports.

It is built only from authoritative sources already in the tree, and it *reads*
the external-anchor mapping straight out of the repo's own gate rather than
re-declaring it:

* the census (``tools/validation_status_report.build_census``) — status + maturity;
* the evidence register (``reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json``) —
  evidence class + citation per family;
* the ``EXTERNALLY_ANCHORED_MODELS`` dict parsed from
  ``engine/tests/test_machine_evidence_consistency.py`` — the repo's own declared
  model->family mapping (parsed with ``ast``; the module is never imported);
* the validation records (``engine/validation/*.md``) — per-model match /
  discrepancy and the sentence naming what would externally promote it.

Honesty rules it obeys: a model with no register row and no record is reported as
"no evidence artifact yet" — it is never given a borrowed citation. Offline,
stdlib-only + the census (which owns the registry import). Read-only except its
``--out`` artefact.

Usage::

    python tools/generate_model_cards.py --out reports/validation
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPO_ROOT / "reports" / "eco-nojin" / "FORMULA-EVIDENCE-REGISTER.json"
EVIDENCE_TEST = (
    REPO_ROOT / "engine" / "tests" / "test_machine_evidence_consistency.py"
)
RECORDS_DIR = REPO_ROOT / "engine" / "validation"
RECORD_SCHEMA = "hydroma.validation.record@1"
_JSON_FENCE = re.compile(r"```json\n(.*?)```", re.DOTALL)
_MOVE_HINT = re.compile(r"would move it is ([^.]+)\.", re.IGNORECASE)


def _externally_anchored_mapping() -> dict[str, str]:
    """model_id -> register indicator_id, parsed from the repo's own gate."""
    tree = ast.parse(EVIDENCE_TEST.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "EXTERNALLY_ANCHORED_MODELS":
                    mapping: dict[str, str] = ast.literal_eval(node.value)
                    return mapping
    return {}


def _load_register() -> dict[str, dict[str, Any]]:
    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    return {e["indicator_id"]: e for e in register.get("entries", [])}


def _load_records() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
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
                mid = payload.get("model_id")
                cases = payload.get("cases", [])
                out[mid] = {
                    "citation": (payload.get("reference") or {}).get("citation"),
                    "matches": sum(1 for c in cases if c.get("verdict") == "match"),
                    "discrepancies": sum(1 for c in cases if c.get("verdict") == "discrepancy"),
                    "move_hint": move_hint,
                }
                break
    return out


def _honest_label(
    validation_status: str, has_external: bool, has_record: bool
) -> str:
    """A short, defensible phrase — the ceiling, never an inflation.

    A registry ``validated`` model with no external anchor is labelled as the
    repo's own gate labels it: a known unanchored claim (the shrinking debt set
    in ``test_machine_evidence_consistency.py``), not a clean external validation.
    """
    if validation_status == "validated":
        return "VALIDATED (external anchor)" if has_external else (
            "validated (unanchored — known debt)"
        )
    if has_external:
        return "external row, not registry-validated"
    if has_record:
        return "METHOD_CONFORMANCE (honest ceiling)"
    return "UNVALIDATED — no artifact yet"


def build_cards() -> dict[str, Any]:
    from tools.validation_status_report import build_census

    census = build_census()
    register = _load_register()
    anchored = _externally_anchored_mapping()
    records = _load_records()

    cards = []
    for model in census["per_model"]:
        mid = model["model_id"]
        family_id = anchored.get(mid)
        family = register.get(family_id) if family_id else None
        record = records.get(mid)
        cards.append(
            {
                "model_id": mid,
                "domain": model["domain"],
                "model_type": model.get("model_type"),
                "validation_status": model["validation_status"],
                "maturity": model["maturity"],
                "external_family": family_id,
                "evidence_class": (family or {}).get("evidence_class"),
                "citation": (family or {}).get("reference")
                or (record or {}).get("citation"),
                "record_matches": (record or {}).get("matches"),
                "record_discrepancies": (record or {}).get("discrepancies"),
                "move_hint": (record or {}).get("move_hint"),
                "honest_label": _honest_label(
                    model["validation_status"],
                    bool(family and family.get("evidence_class") == "VALIDATED_EXTERNAL"),
                    bool(record),
                ),
            }
        )

    # Counts for the summary line (informational, computed).
    by_status: dict[str, int] = {}
    by_class: dict[str, int] = {}
    externally_anchored = 0
    validated_unanchored = 0
    method_only = 0
    no_artifact = 0
    for c in cards:
        has_external = c["evidence_class"] == "VALIDATED_EXTERNAL"
        by_status[c["validation_status"]] = by_status.get(c["validation_status"], 0) + 1
        cls = c["evidence_class"] or "none"
        by_class[cls] = by_class.get(cls, 0) + 1
        if c["validation_status"] == "validated" and has_external:
            externally_anchored += 1
        elif c["validation_status"] == "validated":
            validated_unanchored += 1
        elif c["record_matches"] is not None:
            method_only += 1
        else:
            no_artifact += 1

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "tool": "tools/generate_model_cards.py",
        "counts": {
            "total": len(cards),
            "by_validation_status": by_status,
            "by_evidence_class": by_class,
            "externally_anchored": externally_anchored,
            "validated_unanchored_debt": validated_unanchored,
            "method_conformance_only": method_only,
            "no_artifact": no_artifact,
        },
        "cards": cards,
    }


def _render(sheet: dict[str, Any]) -> str:
    c = sheet["counts"]
    lines = [
        "# Public Model Card Sheet — Eco Nojin / HyDroMA",
        "",
        f"*Generated {sheet['generated_at']} by `{sheet['tool']}`. "
        "The honest public surface: status, maturity, what each model is validated "
        "against, and its limits — never more than the machine evidence supports. "
        "Re-generate it; do not hand-edit.*",
        "",
        "## Summary",
        "",
        f"- models: **{c['total']}** — externally anchored **{c['externally_anchored']}** · "
        f"validated-but-unanchored (known debt) **{c['validated_unanchored_debt']}** · "
        f"method-conformance **{c['method_conformance_only']}** · "
        f"no artifact yet **{c['no_artifact']}**",
        "",
        "| validation_status | models |",
        "|---|---:|",
    ]
    for k, v in sorted(c["by_validation_status"].items()):
        lines.append(f"| {k} | {v} |")
    lines += [
        "",
        "## Model cards",
        "",
        "| model | domain | status | class | validated against / limit |",
        "|---|---|---|---|---|",
    ]
    for card in sheet["cards"]:
        if card["evidence_class"] == "VALIDATED_EXTERNAL":
            against = (card["citation"] or "external register row")[:90]
        elif card["move_hint"]:
            against = f"published relation; needs: {card['move_hint']}"
        elif card["record_matches"] is not None:
            against = "published relation (method-conformance)"
        else:
            against = "no evidence artifact yet — see BACKLOG"
        lines.append(
            f"| {card['model_id']} | {card['domain']} | {card['honest_label']} | "
            f"{card['evidence_class'] or '-'} | {against} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/validation")
    args = parser.parse_args()

    sheet = build_cards()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "MODEL-CARDS.md").write_text(_render(sheet), encoding="utf-8")
    (out_dir / "MODEL-CARDS.json").write_text(
        json.dumps(sheet, indent=2), encoding="utf-8"
    )

    c = sheet["counts"]
    print(
        f"model cards: {c['total']} | external={c['externally_anchored']} "
        f"unanchored-debt={c['validated_unanchored_debt']} "
        f"method={c['method_conformance_only']} no-artifact={c['no_artifact']}"
    )
    print(f"wrote {out_dir}/MODEL-CARDS.md and MODEL-CARDS.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
