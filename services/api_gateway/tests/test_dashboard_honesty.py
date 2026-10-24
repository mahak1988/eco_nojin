"""Honesty guards for the model-validation dashboard — G-H2 / AR-08 "fail closed".

The dashboard used to report a model as ``passed`` merely because a case file
contained an ``expected`` value: it never executed the case, so cases that had
never run came back green ("nothing green without a run" was violated).

The ``/api/v1/hydroma/models/{id}/validation`` endpoint now runs the engine's
own validation corpus in-process
(``engine/hydroma/models/validation/runner.py::machine_summary``) and reports
what *actually* executed:

* a case that never ran carries status ``not_run`` and is never counted as
  passed, and ``overall_status`` is never ``passed`` — only ``executed`` /
  ``partial`` / ``not_run``;
* ``test_cases_passed`` counts only executed-and-matched cases;
* every model identity cites the real, published source (or the honest
  ``no published definition — project composite``), never a
  ``"<ACRONYM> methodology"`` tautology or a false acronym expansion.

The engine's verdicts are read directly here: ``is_test_file`` exempts tests
from the services import guard, so a test may compare the endpoint against the
runner's own ``machine_summary()`` with no bridging.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from engine.hydroma.models.validation import runner as validation_runner

# --- The response shape the endpoint returned before G-H2 -------------------
# test_response_shape_is_unchanged_or_documented asserts every one of these keys
# is still present; the endpoint only ADDS keys (never renames or drops).
_OLD_REPORT_KEYS = {
    "model_id",
    "overall_status",
    "test_cases_total",
    "test_cases_passed",
    "test_cases_failed",
    "test_cases_skipped",
    "details",
    "generated_at",
}
_OLD_DETAIL_KEYS = {"test_case", "status", "message"}

# Forbidden identity strings: a false acronym expansion, a mis-naming, or a
# tautological "<ACRONYM> methodology" citation must never appear in the block.
_FORBIDDEN_IDENTITY_SUBSTRINGS = (
    "Hybrid Latin Hypercube",
    "Evapotranspiration Performance Index",
    "Evapotranspiration Stress Ratio Index",
    "Evapotranspiration Water Stress Index",
    "Hydro-Drought Vegetation Index",
    "methodology",
)

_BASE = "/api/v1/hydroma/models"


@pytest.fixture(scope="module")
def client():
    from services.api_gateway.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        c.get("/health")  # materialise the lazily-built middleware stack
        yield c


@pytest.fixture(scope="module")
def machine():
    """The engine's own verdicts — the ground truth the endpoint must match."""
    return validation_runner.machine_summary()


@pytest.fixture(scope="module")
def richards_report(client):
    """A real family whose corpus verdicts are all ``not_run``.

    ``richards_1d`` is chosen programmatically below (``match == 0`` and
    ``not_run > 0``) rather than hard-coded blindly, so the test fails loudly if
    the corpus ever wires it to an executed verdict.
    """
    response = client.get(f"{_BASE}/richards_1d/validation")
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="module")
def scs_report(client):
    """``scs_cn`` — a family with real, executed-and-matched cases."""
    response = client.get(f"{_BASE}/scs_cn/validation")
    assert response.status_code == 200
    return response.json()


def test_unrun_cases_are_never_reported_passed(richards_report, machine):
    # 1. confirm the family really is 100% not_run per the engine's own runner
    by_status = machine["models"]["richards_1d"]["by_status"]
    assert by_status.get("match", 0) == 0, "richards_1d must have no matched case"
    assert by_status.get("not_run", 0) > 0, "richards_1d must have unrun cases"

    # 2. the endpoint reports not_run — never a pass for a case that never ran
    assert richards_report["runner_key"] == "richards_1d"
    assert richards_report["overall_status"] == "not_run"
    assert richards_report["overall_status"] != "passed"
    assert richards_report["test_cases_passed"] == 0
    assert richards_report["test_cases_total"] == sum(by_status.values())
    # every case that exists is reported as not_run, not passed
    detail_statuses = {d["status"] for d in richards_report["details"]}
    assert detail_statuses == {"not_run"}, detail_statuses
    assert richards_report["test_cases_skipped"] == richards_report["test_cases_total"]


def test_executed_cases_are_counted(scs_report, machine):
    bucket = machine["models"]["scs_cn"]
    match_count = bucket["by_status"]["match"]
    assert match_count >= 1, "scs_cn must have at least one matched case"

    report = scs_report
    # the aggregate counts equal the runner's, and only executed-and-matched
    # cases are counted as passed
    assert report["test_cases_total"] == bucket["cases"]
    assert report["test_cases_passed"] == match_count
    assert report["test_cases_failed"] == bucket["by_status"].get("mismatch", 0)
    assert report["test_cases_inconsistent"] == bucket["by_status"].get("inconsistent_case", 0)
    # the passed aggregate equals the per-case rows the runner marked 'match'
    detail_matches = sum(1 for d in report["details"] if d["status"] == "match")
    assert detail_matches == report["test_cases_passed"] == match_count
    # a model with a real executed match is never reported as not_run
    assert report["overall_status"] in {"executed", "partial"}
    assert report["corpus_status"]["match"] == match_count


def test_model_names_are_correct(client):
    response = client.get(_BASE)
    assert response.status_code == 200
    models = {m["id"]: m for m in response.json()}
    assert models, "the catalog must be non-empty"

    # No forbidden acronym expansion or tautology anywhere in the identity block.
    for mid, meta in models.items():
        identity = " ".join(
            str(meta.get(field, "")) for field in ("name", "description", "reference")
        )
        for bad in _FORBIDDEN_IDENTITY_SUBSTRINGS:
            assert bad not in identity, f"{mid}: identity still contains {bad!r}"

    # The register's specific corrections are applied.
    hlhs = models["hlhs"]
    assert "Landscape Health Score" in hlhs["name"]
    assert hlhs["category"] != "optimization"
    assert "Precision Irrigation Advisor" in models["epia"]["name"]
    assert "Evapotranspiration" not in models["epia"]["name"]
    assert "Water Stress Index" in models["ewsi"]["name"]


def test_response_shape_is_unchanged_or_documented(scs_report):
    # All previous ValidationReport keys survive; the endpoint only ADDS keys.
    present = set(scs_report)
    assert _OLD_REPORT_KEYS <= present, f"missing old keys: {_OLD_REPORT_KEYS - present}"
    # the additive keys G-H2 introduces (documented, not a rename)
    assert {"test_cases_inconsistent", "runner_key", "corpus_status"} <= present
    # overall_status stays within the fail-closed vocabulary
    assert scs_report["overall_status"] in {"executed", "partial", "not_run"}

    # each detail row still carries the previous per-case keys
    assert scs_report["details"], "expected per-case details"
    for row in scs_report["details"]:
        assert _OLD_DETAIL_KEYS <= set(row), f"detail row missing keys: {row}"
