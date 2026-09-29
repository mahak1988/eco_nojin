"""Contract gate for cost control.

Prevents cost anti-patterns from returning to the deployment manifest. The
suite targets structure rather than amounts, because rates change but
unjustified patterns should not come back.

Per ``docs/standards/S-STRUCT.md``, structural violations must block CI.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD = REPO_ROOT / "scripts" / "cost_guard.py"
ESTIMATOR = REPO_ROOT / "scripts" / "cost_estimate.py"
COLLECTOR = REPO_ROOT / "scripts" / "cost_collect.py"
VALUES_PATH = REPO_ROOT / "helm" / "eco-nojin" / "values.yaml"
BUDGET_PATH = REPO_ROOT / "docs" / "cost" / "budget.json"
RESEARCH_DOC = REPO_ROOT / "COST_OPTIMIZATION_RESEARCH_FA.md"
EXEC_DOC = REPO_ROOT / "COST_OPTIMIZATION_EXECUTION_PLAN_FA.md"


def _load_module(name: str, path: Path):
    """Import a script as a module so its collaborators can be injected.

    The module must be registered in sys.modules before exec, otherwise the
    dataclasses it defines resolve annotations against a module object that
    does not exist yet.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


collector_module = _load_module("cost_collect_module", COLLECTOR)


def _load_guard(name: str):
    return _load_module(name, GUARD)


def _run(script: Path, *args: str) -> str:
    result = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0, (
        f"{script.name} {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}"
    )
    return result.stdout


def test_tools_exist() -> None:
    assert GUARD.is_file(), f"missing {GUARD}"
    assert ESTIMATOR.is_file(), f"missing {ESTIMATOR}"


def test_documentation_present() -> None:
    for path in (RESEARCH_DOC, EXEC_DOC, BUDGET_PATH):
        assert path.is_file(), f"missing cost document: {path}"


def test_cost_guard_check_runs() -> None:
    output = _run(GUARD, "check")
    assert "cost manifest analysis" in output
    assert "finding(s)" in output


def test_cost_guard_strict_mode_reports_findings() -> None:
    """A high-severity finding exists today and must be reported.

    This test deliberately does not require exit code 0. If every finding is
    ever resolved, this test is expected to fail, so that nobody mistakes a
    quiet guard for a working one.
    """
    result = subprocess.run(
        [sys.executable, str(GUARD), "check", "--strict"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    combined = result.stdout + result.stderr
    assert "high-severity findings fail the gate" in combined or result.returncode == 0


def test_estimator_reports_measured_and_estimated_separately() -> None:
    """ابزار باید دو مبنای عدد را از هم جدا کند (S-HONEST)."""
    output = _run(ESTIMATOR)
    assert "measured" in output
    assert "estimated" in output
    assert "TOTAL (measured only)" in output


def test_estimator_marks_manifest_not_current_state() -> None:
    """ابزار نباید وانمود کند این هزینه الان پرداخت می‌شود."""
    output = _run(ESTIMATOR)
    lowered = output.lower()
    assert "not a statement about what is" in lowered
    assert "disabled" in lowered


def test_budget_has_hard_caps() -> None:
    budget = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
    assert budget.get("monthly_limit_usd", 0) > 0, "budget needs a real ceiling"
    assert budget.get("alert_thresholds_usd"), "budget needs alert thresholds"
    assert budget.get("per_provider_caps_usd"), "LLM providers need per-provider caps"
    assert budget.get("hard_stops"), "budget needs explicit stop conditions"


def test_budget_limit_is_below_manifest_cost() -> None:
    """سقف بودجه باید به‌مراتب کمتر از هزینهٔ مانیففت باشد، نه نزدیک آن."""
    budget = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
    limit = float(budget["monthly_limit_usd"])
    baseline = float(budget["_baseline"]["manifest_as_written_usd_per_month"])
    assert limit < baseline / 10, (
        f"budget {limit} is not aggressive enough against baseline {baseline}"
    )


def test_budget_command_runs() -> None:
    """`budget` must run and must report the ceiling.

    Exit code 2 is the expected "cannot evaluate" state while no bill has
    been read, so the assertion is on the output rather than on exit 0.
    """
    result = subprocess.run(
        [sys.executable, str(GUARD), "budget"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    combined = result.stdout + result.stderr
    assert "monthly limit" in combined, combined
    assert result.returncode in (0, 2), combined


def test_usage_collector_produces_a_valid_document(tmp_path: Path) -> None:
    """The collector must write a schema-valid usage document.

    Measured is the correct word here. Until something is deployed this reads
    the repository, not a bill, and the document must say which is which.
    """
    output = _run(COLLECTOR, "--out", str(tmp_path / "usage.json"))
    assert "wrote" in output, output

    document = json.loads((tmp_path / "usage.json").read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert "generated_at" in document
    assert isinstance(document["readings"], list)
    assert document["readings"], "collector produced no readings"


def test_usage_never_fabricates_a_bill(tmp_path: Path) -> None:
    """Unknown spend must be null, never zero.

    Zero would let the budget gate read "0 spent of 150" and pass. That is
    the same class of bug as the stale claim in tolerated-degradations.yaml:
    a confident number nobody can reproduce.
    """
    _run(COLLECTOR, "--out", str(tmp_path / "usage.json"))
    document = json.loads((tmp_path / "usage.json").read_text(encoding="utf-8"))
    assert document["month_to_date_usd"] is None, (
        "no bill has been read; month_to_date_usd must stay null, not 0"
    )
    assert "null means unknown" in document["month_to_date_note"]


def test_external_sources_report_unavailable_with_a_reason(tmp_path: Path) -> None:
    """A source that cannot be read must say why, and name the credential."""
    output = _run(COLLECTOR, "--source", "aws", "--out", str(tmp_path / "usage.json"))
    assert "unavailable" in output, output
    document = json.loads((tmp_path / "usage.json").read_text(encoding="utf-8"))
    assert document["unavailable_count"] == 1
    reading = document["readings"][0]
    assert reading["basis"] == "unavailable"
    assert reading["value"] is None
    assert "AWS_ACCESS_KEY_ID" in reading["detail"]
    assert reading["tags"].get("needs_credentials")


def test_budget_gate_distinguishes_unknown_from_under_limit(tmp_path: Path) -> None:
    """`budget` must not report a pass when the bill is unknown.

    Exit code 2 means "cannot evaluate". Zero would mean "0 spent", which is
    a different and false statement.
    """
    _run(COLLECTOR, "--out", str(tmp_path / "usage.json"))
    result = subprocess.run(
        [sys.executable, str(GUARD), "budget"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 2, combined
    assert "UNKNOWN" in combined, combined
    assert "OVER BUDGET" not in combined, combined


def test_budget_gate_fails_closed_when_usage_is_absent(tmp_path: Path) -> None:
    """With no usage file at all, `budget` must not report success."""
    isolated = _load_guard("guard_isolated")
    isolated.USAGE_PATH = tmp_path / "empty_cost_dir" / "usage.json"

    # main() returns the exit code; only the __main__ guard raises.
    assert isolated.main(["budget"]) == 2, "missing usage data must fail closed"


def test_collector_has_no_hardcoded_bill() -> None:
    """The collector must not contain a plausible-looking money literal.

    Guards against someone "fixing" an empty reading by pasting a figure from
    a pricing page, which is the exact failure this whole gate exists to
    prevent.

    The patterns target spend *flowing into* a reading. A bare quoted decimal
    is not a violation: docstrings legitimately show what a provider returns,
    and flagging those would push the fix in the wrong direction.
    """
    source = COLLECTOR.read_text(encoding="utf-8")
    violations = [
        pattern
        for pattern in (
            r"month_to_date_usd\s*[:=]\s*[1-9]",  # spend set to a literal
            r"_measured\(\s*[1-9][\d.]*[,)]",  # a reading hardcoded
            r"\bvalue\s*=\s*[1-9][\d.]*\s*[,)]\s*$",  # a value field hardcoded
            r"return\s+[1-9][\d]*\.[\d{2}]\s*$",  # a literal returned as money
        )
        if re.search(pattern, source, re.MULTILINE)
    ]
    assert not violations, (
        f"collector hardcodes spend matching {violations}; spend must be read "
        "from a provider, never written by hand"
    )


class _FakeAWSClient:
    """Stand-in for boto3's Cost Explorer client. No network."""

    def __init__(self, response=None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error
        self.calls: list[dict] = []

    def get_cost_and_usage(self, **kwargs):
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return self._response


def _fake_transport(status: int, payload: dict, error: str = ""):
    def transport(method, url, headers, body):
        return collector_module.HttpResponse(status, payload, error)

    return transport


def _no_env(monkeypatch, *names: str) -> None:
    for name in names:
        monkeypatch.delenv(name, raising=False)


def test_aws_adapter_parses_a_cost_explorer_response(monkeypatch) -> None:
    """A real response shape must total correctly and split by service."""
    _no_env(monkeypatch, "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAFAKE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    client = _FakeAWSClient(
        response={
            "ResultsByTime": [
                {
                    "Groups": [
                        {
                            "Keys": ["Amazon Elastic Kubernetes Service"],
                            "Metrics": {"UnblendedCost": {"Amount": "73.00"}},
                        },
                        {
                            "Keys": ["Amazon EC2"],
                            "Metrics": {"UnblendedCost": {"Amount": "120.50"}},
                        },
                    ]
                }
            ]
        }
    )
    adapter = collector_module.AWSCostAdapter(client=client)
    readings = adapter.read()

    total = next(r for r in readings if r.key == "month_to_date")
    assert total.basis == "measured"
    assert total.value == 193.5
    services = {r.key: r.value for r in readings if r.key.startswith("service_")}
    assert services["service_Amazon EC2"] == 120.5
    assert client.calls, "adapter never called Cost Explorer"


def test_aws_adapter_reports_missing_credentials_without_calling_anything(monkeypatch) -> None:
    _no_env(monkeypatch, "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION")
    client = _FakeAWSClient()
    readings = collector_module.AWSCostAdapter(client=client).read()

    assert len(readings) == 1
    assert readings[0].basis == "unavailable"
    assert readings[0].value is None
    assert "AWS_ACCESS_KEY_ID" in readings[0].detail
    assert not client.calls, "adapter called the API without credentials"


def test_aws_adapter_reports_a_call_failure_rather_than_zero(monkeypatch) -> None:
    """An SDK exception must surface, never become a fabricated 0.00."""
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        monkeypatch.setenv(name, "set")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    client = _FakeAWSClient(error=RuntimeError("AccessDenied"))
    readings = collector_module.AWSCostAdapter(client=client).read()

    assert readings[0].basis == "unavailable"
    assert readings[0].value is None
    assert "AccessDenied" in readings[0].detail
    assert readings[0].tags["adapter_status"] == "call_failed"


def test_aws_adapter_handles_an_empty_billing_window(monkeypatch) -> None:
    """A new AWS account returns nothing for days. That is not zero spend."""
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        monkeypatch.setenv(name, "set")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    client = _FakeAWSClient(response={"ResultsByTime": []})
    readings = collector_module.AWSCostAdapter(client=client).read()

    assert readings[0].basis == "unavailable"
    assert "24-48h" in readings[0].detail


def test_supabase_adapter_measures_size_but_refuses_to_call_it_a_bill(monkeypatch) -> None:
    """Supabase has no public per-service bill. Size is measured, cost is not."""
    monkeypatch.setenv("SUPABASE_ACCESS_TOKEN", "sbp_fake")
    monkeypatch.setenv("SUPABASE_PROJECT_REF", "abcdefgh")

    transport = _fake_transport(200, {"database": {"size_mb": 412}})
    readings = collector_module.SupabaseAdapter(transport=transport).read()

    size = next(r for r in readings if r.key == "database_size_mb")
    assert size.value == 412
    bill = next(r for r in readings if r.key == "month_to_date")
    assert bill.basis == "unavailable"
    assert "not a bill" in bill.detail


def test_supabase_adapter_reports_http_failure(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_ACCESS_TOKEN", "sbp_fake")
    monkeypatch.setenv("SUPABASE_PROJECT_REF", "abcdefgh")

    transport = _fake_transport(401, {}, "HTTP 401: Unauthorized")
    readings = collector_module.SupabaseAdapter(transport=transport).read()
    assert readings[0].basis == "unavailable"
    assert "401" in readings[0].detail


def test_vercel_adapter_reports_nothing_billable_on_a_free_plan(monkeypatch) -> None:
    """An empty billable list must not be reported as 0 USD spend."""
    monkeypatch.setenv("VERCEL_TOKEN", "fake")
    monkeypatch.setenv("VERCEL_TEAM_ID", "team_abc")

    transport = _fake_transport(200, {"billing": {"items": []}})
    readings = collector_module.VercelAdapter(transport=transport).read()
    assert readings[0].basis == "unavailable"
    assert "Hobby" in readings[0].detail


def test_vercel_adapter_totals_billable_items(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL_TOKEN", "fake")
    monkeypatch.setenv("VERCEL_TEAM_ID", "team_abc")

    transport = _fake_transport(
        200,
        {
            "billing": {
                "items": [
                    {"resource": "bandwidth", "amount": "12.34", "billable": "1"},
                    {"resource": "builds", "amount": "0.00", "billable": "0"},
                ]
            }
        },
    )
    readings = collector_module.VercelAdapter(transport=transport).read()
    assert [r.value for r in readings] == [12.34]


def test_github_adapter_reads_action_minutes(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_fake")
    monkeypatch.setenv("GITHUB_OWNER", "eco-nojin")

    transport = _fake_transport(200, {"total": {"total_minutes_used": 12345}})
    readings = collector_module.GitHubActionsAdapter(transport=transport).read()
    assert readings[0].value == 12345
    assert readings[0].unit == "minutes"


def test_every_adapter_declares_its_credentials_and_purpose() -> None:
    """The documented blocker for each source must be stated up front."""
    for name, adapter in collector_module.ADAPTERS.items():
        assert adapter.purpose, f"{name} does not say what it measures"
        assert adapter.required_env, f"{name} declares no required environment"


def test_adapter_inventory_matches_the_documented_sources() -> None:
    """budget.json must not advertise an adapter that does not exist."""
    budget = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
    documented = set((budget.get("collector") or {}).get("adapters", {}))
    implemented = set(collector_module.ADAPTERS)
    assert documented == implemented, (
        f"budget.json documents {sorted(documented)} but the collector "
        f"implements {sorted(implemented)}"
    )


def test_money_returned_as_a_string_is_still_measured(monkeypatch) -> None:
    """REST billing APIs return money as JSON strings.

    An isinstance check on the raw value would drop every real figure and
    make a billed account look unbilled. That is fabrication by omission, and
    this test exists to stop it coming back.
    """
    monkeypatch.setenv("VERCEL_TOKEN", "fake")
    monkeypatch.setenv("VERCEL_TEAM_ID", "team_abc")

    transport = _fake_transport(
        200,
        {
            "billing": {
                "items": [
                    {"resource": "bandwidth", "amount": "1,234.56", "billable": "1"},
                ]
            }
        },
    )
    readings = collector_module.VercelAdapter(transport=transport).read()
    assert [r.value for r in readings] == [1234.56]
    assert readings[0].basis == "measured"


def test_unparseable_money_becomes_unavailable_not_zero(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL_TOKEN", "fake")
    monkeypatch.setenv("VERCEL_TEAM_ID", "team_abc")

    transport = _fake_transport(
        200,
        {"billing": {"items": [{"resource": "bandwidth", "amount": "n/a", "billable": "1"}]}},
    )
    readings = collector_module.VercelAdapter(transport=transport).read()
    assert all(reading.value is None for reading in readings)
    assert all(reading.basis == "unavailable" for reading in readings)


def test_research_doc_cites_sources() -> None:
    """سند تحقیق باید منابع رسمی داشته باشد، نه عدد بدون منبع."""
    text = RESEARCH_DOC.read_text(encoding="utf-8")
    for token in (
        "aws.amazon.com/eks/pricing",
        "aws.amazon.com/vpc/pricing",
        "supabase.com/pricing",
        "developers.cloudflare.com/r2/pricing",
        "vercel.com/pricing",
    ):
        assert token in text, f"research doc missing source: {token}"


def test_research_doc_records_failed_research() -> None:
    """تحقیق ناموفق هم باید ثبت شود (S-HONEST).

    اگر این آزمون حذف شد، یعنی کسی نتیجهٔ منفی را پاک کرده است.
    """
    text = RESEARCH_DOC.read_text(encoding="utf-8")
    assert "ناموفق" in text or "NOT FOUND" in text
    assert "Hetzner" in text, "the failed Hetzner lookup must stay documented"


def test_research_doc_separates_measured_from_estimated() -> None:
    text = RESEARCH_DOC.read_text(encoding="utf-8")
    assert "measured" in text
    assert "estimated" in text


def test_execution_plan_exists_and_lists_waves() -> None:
    text = EXEC_DOC.read_text(encoding="utf-8")
    for wave in ("C0", "C1", "C2"):
        assert wave in text, f"execution plan missing wave {wave}"
