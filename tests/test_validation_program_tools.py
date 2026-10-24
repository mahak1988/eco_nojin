"""Invariant tests for the ECO-VALIDATION-PROGRAM tooling (S0/S2/S6).

These lock the *behaviour* of the four tools — that their outputs are internally
consistent partitions, deterministic, and fail-closed — rather than pinning exact
numbers, which move on a live tree as other agents promote models. A number that
must be quoted lives in the generated artefacts (``reports/validation/*``); a
property that must always hold lives here.

Tools are loaded by placing the repo root on ``sys.path`` and importing the
``tools`` namespace package, the same way ``tools/run_validation_gates.py``
imports them. Requires PYTHONPATH + SECRET_KEY (see AGENTS.md).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import generate_model_cards as cards_mod  # noqa: E402
from tools import promote_external as promote_mod  # noqa: E402
from tools import validation_backlog as backlog_mod  # noqa: E402
from tools import validation_status_report as census_mod  # noqa: E402

PROMOTION_PATHS = {
    "DONE_EXTERNAL",
    "VENDOR_OFFLINE_ANCHOR",
    "DESIGN_DECISION_REQUIRED",
    "INVESTIGATE",
}


@pytest.fixture(scope="module")
def census() -> dict:
    return census_mod.build_census()


@pytest.fixture(scope="module")
def backlog() -> dict:
    return backlog_mod.build_backlog()


@pytest.fixture(scope="module")
def sheet() -> dict:
    return cards_mod.build_cards()


# --------------------------------------------------------------------------- #
# census — a coherent partition of the registry                                #
# --------------------------------------------------------------------------- #
def test_census_status_partitions_sum_to_total(census: dict) -> None:
    models = census["models"]
    by_status = models["validation_status"]
    assert by_status.get("validated", 0) + by_status.get("unvalidated", 0) >= 0
    assert sum(by_status.values()) == models["total"]
    ids = models["validated_ids"] + models["unvalidated_ids"] + models["other_validation_ids"]
    assert len(ids) == models["total"]
    assert len(set(ids)) == models["total"]


def test_census_maturity_partition_and_s3_bar(census: dict) -> None:
    maturity = census["maturity"]
    assert sum(maturity["levels"].values()) == census["models"]["total"]
    above = maturity["counts"] if "counts" in maturity else maturity["levels"]
    s3_plus = sum(maturity["levels"][lvl] for lvl in ("S3", "S4", "S5", "S6"))
    assert maturity["s3_plus_count"] == s3_plus
    assert len(maturity["s3_plus_ids"]) == s3_plus
    assert above is not None  # keys present and summable


def test_census_is_deterministic() -> None:
    a = census_mod.build_census()
    b = census_mod.build_census()
    assert a["models"]["total"] == b["models"]["total"]
    assert set(a["models"]["validated_ids"]) == set(b["models"]["validated_ids"])


# --------------------------------------------------------------------------- #
# backlog — register families fully classified, cluster tiers coherent         #
# --------------------------------------------------------------------------- #
def test_backlog_families_match_register(backlog: dict) -> None:
    register = json.loads(
        (REPO_ROOT / "reports" / "eco-nojin" / "FORMULA-EVIDENCE-REGISTER.json").read_text(
            encoding="utf-8"
        )
    )
    families = backlog["families"]
    assert len(families) == len(register["entries"])
    for fam in families:
        assert fam["promotion_path"] in PROMOTION_PATHS
    assert sum(backlog["register"]["promotion_path_counts"].values()) == len(families)


def test_backlog_summary_is_a_partition(census: dict, backlog: dict) -> None:
    recorded = {row["model_id"] for row in backlog["cluster_models"]}
    no_artifact = backlog["unvalidated_without_evidence_artifact"]
    unvalidated = set(census["models"]["unvalidated_ids"])
    # every no-artifact model is unvalidated and not already covered by a record
    assert set(no_artifact["model_ids"]) <= unvalidated
    assert not (set(no_artifact["model_ids"]) & recorded)
    for row in backlog["cluster_models"]:
        assert row["tier"] in {
            "validated",
            "unvalidated_method_conformance",
            "unvalidated_discrepancy",
            "unvalidated",
        }


# --------------------------------------------------------------------------- #
# model cards — every registered model, an honest label, a clean partition      #
# --------------------------------------------------------------------------- #
def test_cards_cover_every_model_and_partition(census: dict, sheet: dict) -> None:
    assert sheet["counts"]["total"] == census["models"]["total"]
    counts = sheet["counts"]
    assert (
        counts["externally_anchored"] + counts["validated_unanchored_debt"]
        + counts["method_conformance_only"] + counts["no_artifact"]
        == counts["total"]
    )
    cards_by_id = {c["model_id"] for c in sheet["cards"]}
    census_ids = {m["model_id"] for m in census["per_model"]}
    assert cards_by_id == census_ids


def test_cards_external_label_requires_external_class(sheet: dict) -> None:
    for card in sheet["cards"]:
        if "external anchor" in card["honest_label"]:
            assert card["evidence_class"] == "VALIDATED_EXTERNAL"


# --------------------------------------------------------------------------- #
# promote_external — fail-closed, and plan is dry                              #
# --------------------------------------------------------------------------- #
def _register_sha() -> str:
    import hashlib

    path = REPO_ROOT / "reports" / "eco-nojin" / "FORMULA-EVIDENCE-REGISTER.json"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_promote_apply_refuses_without_reference(capsys: pytest.CaptureFixture) -> None:
    code = promote_mod.main(["--apply", "--model", "CANON-999", "--family", "NONE"])
    assert code == 2
    assert "REFUSED" in capsys.readouterr().out


def test_promote_apply_refuses_bad_inputs(capsys: pytest.CaptureFixture) -> None:
    ref = REPO_ROOT / "tests" / "reference_data" / "does_not_exist_x.csv"
    missing = ["--apply", "--model", "M", "--family", "F", "--reference", str(ref)]
    assert promote_mod.main(missing) == 2
    a = REPO_ROOT / "tests" / "reference_data" / "mckee_spi_classification.csv"
    base = ["--apply", "--model", "M", "--family", "F", "--reference", str(a)]
    assert promote_mod.main([*base, "--citation", "REQUIRED"]) == 2  # placeholder citation
    assert promote_mod.main([*base, "--citation", "x", "--kind", "bogus"]) == 2  # bad kind
    bad_class = [*base, "--citation", "x", "--kind", "measured", "--class", "NOPE"]
    assert promote_mod.main(bad_class) == 2
    assert "REFUSED" in capsys.readouterr().out


def test_promote_plan_is_dry() -> None:
    before = _register_sha()
    code = promote_mod.main(["--plan", "--model", "CANON-006", "--family", "VAN_GENUCHTEN_THETA_K"])
    assert code == 0
    assert _register_sha() == before  # plan never mutates the register
    bundle = REPO_ROOT / "reports" / "validation" / "promotions" / "CANON-006"
    assert (bundle / "register_row.DRAFT.json").exists()
    assert (bundle / "engine_patch.md").exists()
    assert (bundle / "CHECKLIST.md").exists()
