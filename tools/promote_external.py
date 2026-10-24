"""Turnkey, fail-closed promoter: vendor a *genuine* external anchor and wire the
registry row, handing the in-flight engine/** edits to the owner as a patch.

This is the machinery behind ECO-VALIDATION-PROGRAM D-V-01 / S2. It exists so the
FIRST real EXTERNAL promotion is turnkey and honest — and so it *cannot* be used
to fake one:

* **fail-closed.** It does nothing unless a real reference file exists on disk and
  a non-empty citation is supplied. It never invents a number (SB-06) and never
  claims a value it was not given.
* **vendors offline.** It copies the CSV into ``tests/reference_data`` (or records
  its committed path), writes/refreshes the ``*.meta.json`` provenance sidecar with
  a sha256 checksum — the ZED-offline pattern used by the existing anchors.
* **registry row only, in scope.** It appends a well-formed row to
  ``reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json``. It does NOT edit
  ``engine/**`` (cards, EXTERNALLY_ANCHORED_MODELS, the ``len(external)==9`` cap,
  CLUSTER_MODELS_MOVED_TO_VALIDATED): those are in-flight STOP-brake surfaces, so
  it emits a reviewable patch + checklist for the owning agent instead.
* **aware of the cap.** Adding a 10th ``VALIDATED_EXTERNAL`` row breaks
  ``test_corpus_external_anchors_are_reported_distinctly`` (``len(external)==9``)
  until the cap is raised in the same change; the plan names this explicitly.

Modes:
* ``--plan``      : dry. Prints the exact steps + writes a clearly-marked DRAFT
  bundle (register row with REQUIRED placeholders + engine patch) under
  ``reports/validation/promotions/<MODEL>/``. No register or engine file changes.
* ``--apply``     : requires ``--reference`` (existing CSV) + ``--citation`` +
  ``--kind in {published_table, measured, worked_example, class_edges}`. Vendors
  the file, appends the register row, and (still) emits — not applies — the engine
  patch.

Usage::
    python tools/promote_external.py --plan --model CANON-006 --family VAN_GENUCHTEN_THETA_K
    python tools/promote_external.py --apply --model M --family F \
        --reference data/ref.csv --citation "Van Genuchten 1980, SSSAJ 44:892-898, Table X" \
        --kind published_table --class VALIDATED_EXTERNAL
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPO_ROOT / "reports" / "eco-nojin" / "FORMULA-EVIDENCE-REGISTER.json"
REFDATA_DIR = REPO_ROOT / "tests" / "reference_data"
CAP_TEST = (
    REPO_ROOT
    / "engine"
    / "tests"
    / "test_machine_evidence_consistency.py"
)

_VALID_CLASSES = {
    "VALIDATED_EXTERNAL",
    "VALIDATED_METHOD_CONFORMANCE",
    "REGRESSION_ANCHOR_STABLE",
    "PARTIAL",
    "UNVALIDATED",
    "BLOCKED",
}
_VALID_KINDS = {"published_table", "measured", "worked_example", "class_edges"}


class PromotionError(RuntimeError):
    """A fail-closed refusal with the reason a human can act on."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_register() -> dict[str, Any]:
    return json.loads(REGISTER_PATH.read_text(encoding="utf-8"))


def _model_status(model_id: str) -> dict[str, Any] | None:
    from tools.validation_status_report import build_census

    for model in build_census()["per_model"]:
        if model["model_id"] == model_id:
            return model
    return None


def _family(register: dict[str, Any], family_id: str) -> dict[str, Any] | None:
    for entry in register.get("entries", []):
        if entry.get("indicator_id") == family_id:
            return entry
    return None


def _draft_row(
    model_id: str, family_id: str, reference: str | None, kind: str | None
) -> dict[str, Any]:
    published = bool(reference) and "REQUIRED" not in reference
    return {
        "indicator_id": family_id,
        "evidence_class": "VALIDATED_EXTERNAL" if published else "REQUIRED: set on --apply",
        "basis": (
            f"published {kind} anchor vendored offline for {model_id}; "
            "engine reproduces the published value"
            if published
            else "REQUIRED: describe the external evidence"
        ),
        "reference": reference or "REQUIRED: full citation + vendored file path",
        "gap": None,
    }


def _engine_patch_text(model_id: str, family_id: str) -> str:
    return f"""# Engine patch — DRAFT, apply by the owning agent (NOT auto-applied)

Promoting `{model_id}` to a registry `validated` claim needs four engine
edits, all in-flight STOP-brake surfaces (KN-22/39; SB-03/SB-10). Coordinate with
the engine owner; do not edit out of band.

1. `engine/models/cards/{model_id}_*.md`
   Set the `validation_status` row to claim the model matches its published
   reference (`validated` / `benchmarked` — a whole-word positive the registry
   derivation recognises).

2. `engine/tests/test_machine_evidence_consistency.py`
   Add to `EXTERNALLY_ANCHORED_MODELS`:
       "{model_id}": "{family_id}",
   And deliberately raise the external-anchor cap in
   `test_corpus_external_anchors_are_reported_distinctly`:
       assert len(external) == <current+1>

3. `engine/validation/test_validation_records.py`
   - Add the independently re-derived `reference` for `{model_id}` (a
     published value, not a re-derivation you typed from the model).
   - If a record already exists, set its `validation_status` to `validated` and
     add `{model_id}` to `CLUSTER_MODELS_MOVED_TO_VALIDATED`.

4. Re-run the gate; the registry then derives `validated` from the card row, and
   `test_no_validated_claim_without_external_anchor` passes with `{model_id}`
   out of `KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR`.
"""


def _cap_count() -> int:
    text = CAP_TEST.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "len(external) ==" in line:
            return int("".join(ch for ch in line if ch.isdigit()))
    return -1


def _plan(args: argparse.Namespace) -> int:
    register = _load_register()
    model = _model_status(args.model)
    family = _family(register, args.family)
    out_dir = REPO_ROOT / "reports" / "validation" / "promotions" / args.model
    out_dir.mkdir(parents=True, exist_ok=True)

    draft = _draft_row(args.model, args.family, args.reference, args.kind)
    (out_dir / "register_row.DRAFT.json").write_text(
        json.dumps(draft, indent=2), encoding="utf-8"
    )
    (out_dir / "engine_patch.md").write_text(
        _engine_patch_text(args.model, args.family), encoding="utf-8"
    )
    (out_dir / "CHECKLIST.md").write_text(
        "# Promotion checklist (dry-run, no changes applied)\n\n"
        f"- model: `{args.model}` — registry status "
        f"`{(model or {}).get('validation_status', 'UNKNOWN')}`, "
        f"maturity `{(model or {}).get('maturity', '?')}`\n"
        f"- family: `{args.family}` — current class "
        f"`{(family or {}).get('evidence_class', 'ABSENT (new row)')}`, gap "
        f"`{(family or {}).get('gap', '—')}`\n"
        f"- external-anchor cap today: {_cap_count()} (raise on apply)\n\n"
        "## Required input (the honest gate)\n"
        "1. A genuine published value for "
        f"`{args.model}` (published table / measured / worked example), from the "
        "source — NOT a re-derivation.\n"
        "2. A CSV in `tests/reference_data/` carrying the published value(s), with "
        "`*.meta.json` (citation + kind + sha256).\n\n"
        "## Then run\n"
        "```\n"
        f"python tools/promote_external.py --apply --model {args.model} "
        f"--family {args.family} --reference <csv> --citation \"...\" --kind <kind>\n"
        "```\n"
        "and hand `engine_patch.md` to the engine owner.\n",
        encoding="utf-8",
    )
    print(f"[PLAN] {args.model} -> {args.family}")
    print(f"  registry status now: {(model or {}).get('validation_status', 'UNKNOWN')}")
    print(f"  family class now   : {(family or {}).get('evidence_class', 'ABSENT (new row)')}")
    print(f"  external cap today : {_cap_count()} (must be raised on a real apply)")
    print(f"  draft bundle       : {out_dir}")
    print("  files: register_row.DRAFT.json, engine_patch.md, CHECKLIST.md")
    print("  NO register or engine file changed (dry-run).")
    return 0


def _apply(args: argparse.Namespace) -> int:
    if not args.reference:
        raise PromotionError("fail-closed: --reference <csv> is required (no invented numbers)")
    if not args.citation or "REQUIRED" in args.citation:
        raise PromotionError("fail-closed: a real --citation is required")
    if args.kind not in _VALID_KINDS:
        raise PromotionError(f"--kind must be one of {sorted(_VALID_KINDS)}")
    if args.evidence_class not in _VALID_CLASSES:
        raise PromotionError(f"--class must be one of {sorted(_VALID_CLASSES)}")

    ref = Path(args.reference)
    if not ref.is_absolute():
        ref = (REPO_ROOT / ref).resolve()
    if not ref.exists():
        raise PromotionError(f"fail-closed: reference file not found: {ref}")

    # Vendor into tests/reference_data with an offline provenance sidecar.
    REFDATA_DIR.mkdir(parents=True, exist_ok=True)
    vendored = REFDATA_DIR / ref.name
    if ref.resolve() != vendored.resolve():
        shutil.copyfile(ref, vendored)
    checksum = _sha256(vendored)
    meta = {
        "source": args.citation,
        "kind": args.kind,
        "checksum_sha256": checksum,
        "vendored_at": datetime.now(UTC).isoformat(),
        "offline": True,
        "promoted_model": args.model,
        "register_family": args.family,
    }
    (REFDATA_DIR / f"{vendored.stem}.meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    register = _load_register()
    if _family(register, args.family) is not None:
        # Promote the existing row in place (class -> the requested class).
        for entry in register["entries"]:
            if entry.get("indicator_id") == args.family:
                entry["evidence_class"] = args.evidence_class
                entry["basis"] = (
                    f"published {args.kind} anchor vendored offline; "
                    f"{vendored.name} (sha256 {checksum[:12]}…)"
                )
                entry["reference"] = f"{args.citation}; tests/reference_data/{vendored.name}"
                entry["gap"] = None
                break
    else:
        register["entries"].append(
            {
                "indicator_id": args.family,
                "evidence_class": args.evidence_class,
                "basis": f"published {args.kind} anchor vendored offline; {vendored.name}",
                "reference": f"{args.citation}; tests/reference_data/{vendored.name}",
                "gap": None,
            }
        )
    register["generated_at"] = datetime.now(UTC).isoformat()
    REGISTER_PATH.write_text(json.dumps(register, indent=2), encoding="utf-8")

    (REPO_ROOT / "reports" / "validation" / "promotions" / args.model).mkdir(
        parents=True, exist_ok=True
    )
    patch_path = (
        REPO_ROOT / "reports" / "validation" / "promotions" / args.model / "engine_patch.md"
    )
    patch_path.write_text(_engine_patch_text(args.model, args.family), encoding="utf-8")

    external_now = sum(
        1
        for e in register["entries"]
        if e.get("evidence_class") == "VALIDATED_EXTERNAL"
    )
    print(f"[APPLY] vendored {vendored.name} (sha256 {checksum[:12]}…) → tests/reference_data/")
    print(f"[APPLY] register row {args.family} set to {args.evidence_class}")
    print(f"[APPLY] external rows now: {external_now}; cap test asserts {_cap_count()}")
    print("[APPLY] engine/** NOT touched; hand this patch to the engine owner:")
    print(f"        {patch_path}")
    print("        + raise the cap in test_corpus_external_anchors_are_reported_distinctly")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true", help="dry-run; write a DRAFT bundle")
    parser.add_argument("--apply", action="store_true", help="vendor + append register row")
    parser.add_argument("--model", required=True)
    parser.add_argument("--family", required=True)
    parser.add_argument("--reference", default=None, help="CSV with the published value(s)")
    parser.add_argument("--citation", default=None, help="full published citation")
    parser.add_argument("--kind", default=None)
    parser.add_argument("--class", dest="evidence_class", default="VALIDATED_EXTERNAL")
    args = parser.parse_args(argv)

    if args.plan == args.apply:
        parser.error("choose exactly one of --plan or --apply")
    try:
        return _plan(args) if args.plan else _apply(args)
    except PromotionError as exc:
        print(f"REFUSED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
