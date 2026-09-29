"""Usage collection for Eco Nojin cost control (cost plan phase 1: adapters).

What this does
--------------
Populates ``docs/cost/usage.json`` so ``scripts/cost_guard.py budget`` can
compare real spend against the ceiling in ``docs/cost/budget.json``.

Design
------
Adapters are pluggable and injectable. Each one takes a client or transport
that can be replaced in a test, so the suite never makes a network call and
never needs credentials. That is deliberate: a cost collector that can only be
verified by running it against a live bill is a collector nobody will run.

The invariant every adapter must uphold
---------------------------------------
Never fabricate. Three outcomes are legal: a measured figure, ``unavailable``
with the reason, or a failed read with the exception. A fourth outcome, a
plausible-looking zero, is forbidden. Zero would let the budget gate read
"0 spent of 150" and pass, which is the failure this repository keeps paying
for in a different guise.

Which adapters exist, and why
-----------------------------
The cost analysis recommends Supabase plus Vercel and explicitly advises
against AWS, but the current Helm manifest assumes AWS. Rather than block on
that decision, all three are implemented. Pick by setting credentials.

Run it with::

    .venv\\Scripts\\python.exe scripts\\cost_collect.py
    .venv\\Scripts\\python.exe scripts\\cost_collect.py --source aws --source vercel
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

REPO_ROOT = Path(__file__).resolve().parent.parent
USAGE_PATH = REPO_ROOT / "docs" / "cost" / "usage.json"

SCHEMA_VERSION = 1

# Transport signature: (method, url, headers, body) -> (status, decoded json)
Transport = Callable[[str, str, dict[str, str], dict[str, Any] | None], "HttpResponse"]


@dataclass(frozen=True)
class HttpResponse:
    status: int
    payload: dict[str, Any]
    error: str = ""


def urllib_transport(
    method: str, url: str, headers: dict[str, str], body: dict[str, Any] | None
) -> HttpResponse:
    """Real HTTP via the standard library. No third-party dependency."""
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return HttpResponse(response.status, json.loads(response.read() or b"{}"))
    except urllib.error.HTTPError as error:
        return HttpResponse(error.code, {}, f"HTTP {error.code}: {error.reason}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
        return HttpResponse(0, {}, f"{type(error).__name__}: {error}")


def _to_float(value: Any) -> float | None:
    """Coerce a provider's money field to a float.

    REST billing APIs return money as JSON strings ("12.34"), not numbers.
    An isinstance check on the raw value silently drops every real figure and
    makes a billed account look unbilled, which is the same fabrication by
    omission that this module exists to prevent.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip().replace(",", ""))
        except ValueError:
            return None
    return None


@dataclass
class Reading:
    """One measurement, or an explicit statement that it is unavailable."""

    source: str
    key: str
    value: float | None
    unit: str
    basis: str  # "derived" | "measured" | "unavailable"
    detail: str = ""
    tags: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "key": self.key,
            "value": self.value,
            "unit": self.unit,
            "basis": self.basis,
            "detail": self.detail,
            "tags": self.tags,
        }


class CostAdapter(Protocol):
    """What every adapter must provide."""

    name: str
    required_env: tuple[str, ...]
    purpose: str

    def read(self) -> list[Reading]: ...


class _BaseAdapter:
    name = "base"
    required_env: tuple[str, ...] = ()
    purpose = ""

    def missing_env(self) -> list[str]:
        return [name for name in self.required_env if not os.getenv(name)]

    def read(self) -> list[Reading]:  # pragma: no cover - interface only
        raise NotImplementedError

    def _unavailable(self, detail: str, **tags: str) -> Reading:
        return Reading(
            source=self.name,
            key="month_to_date",
            value=None,
            unit="usd",
            basis="unavailable",
            detail=detail,
            tags=tags,
        )

    def _measured(self, value: float, detail: str, **tags: str) -> Reading:
        return Reading(
            source=self.name,
            key="month_to_date",
            value=round(float(value), 2),
            unit="usd",
            basis="measured",
            detail=detail,
            tags=tags,
        )


class AWSCostAdapter(_BaseAdapter):
    """AWS Cost Explorer, grouped by service.

    Uses boto3 only when the credentials are present. The client is
    injectable so tests never touch the network.
    """

    name = "aws"
    required_env = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION")
    purpose = "EKS, NAT gateways, EBS volumes, data transfer"

    def __init__(self, client: Any = None, today: datetime | None = None) -> None:
        self._client = client
        self._today = today or datetime.now(UTC)

    def _build_client(self) -> tuple[Any | None, str]:
        if self._client is not None:
            return self._client, ""
        try:
            import boto3
        except ImportError:
            return None, (
                "boto3 is not installed. It is an optional dependency: "
                "pip install boto3. Declaring it in requirements would put an "
                "AWS SDK in every CI run and every dev environment for a cost "
                "read that most contributors never need."
            )
        return boto3.client("ce", region_name=os.getenv("AWS_REGION", "us-east-1")), ""

    def read(self) -> list[Reading]:
        missing = self.missing_env()
        if missing:
            return [
                self._unavailable(
                    f"{self.purpose}. Missing environment: {', '.join(missing)}. "
                    "Method once available: boto3 cost-explorer "
                    "GetCostAndUsage with Granularity=DAILY, GroupBy=SERVICE.",
                    needs_credentials=",".join(missing),
                )
            ]

        client, error = self._build_client()
        if client is None:
            return [self._unavailable(error, adapter_status="dependency_missing")]

        end = self._today.date().isoformat()
        start = (self._today - timedelta(days=30)).date().isoformat()
        try:
            response = client.get_cost_and_usage(
                TimePeriod={"Start": start, "End": end},
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )
        # Any SDK failure is a read failure, not a reason to report zero.
        except Exception as error:
            return [
                self._unavailable(
                    f"Cost Explorer call failed: {type(error).__name__}: {error}",
                    adapter_status="call_failed",
                )
            ]

        return self._parse(response, start, end)

    def _parse(self, response: dict[str, Any], start: str, end: str) -> list[Reading]:
        results = response.get("ResultsByTime")
        if not results:
            return [
                self._unavailable(
                    "Cost Explorer returned no results. Note that AWS bills "
                    "with 24-48h delay, so an empty window is normal for a new "
                    "account.",
                    adapter_status="empty_response",
                )
            ]

        by_service: dict[str, float] = {}
        total = 0.0
        for period in results:
            for group in period.get("Groups", []):
                keys = group.get("Keys", ["unknown"])
                amount = float(
                    group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0) or 0
                )
                by_service[keys[0]] = by_service.get(keys[0], 0.0) + amount
                total += amount

        readings = [
            self._measured(
                total,
                f"unblended cost {start}..{end}, {len(by_service)} services",
                window_days="30",
            )
        ]
        readings.extend(
            Reading(
                source=self.name,
                key=f"service_{service}",
                value=round(amount, 2),
                unit="usd",
                basis="measured",
                detail=f"{service} over {start}..{end}",
                tags={"dimension": "SERVICE"},
            )
            for service, amount in sorted(by_service.items(), key=lambda kv: -kv[1])
        )
        return readings


class SupabaseAdapter(_BaseAdapter):
    """Supabase project quota and size via the Management API."""

    name = "supabase"
    required_env = ("SUPABASE_ACCESS_TOKEN", "SUPABASE_PROJECT_REF")
    purpose = "Postgres size, egress, MAU, edge function invocations"

    def __init__(self, transport: Transport = urllib_transport) -> None:
        self._transport = transport

    def read(self) -> list[Reading]:
        missing = self.missing_env()
        if missing:
            return [
                self._unavailable(
                    f"{self.purpose}. Missing environment: {', '.join(missing)}. "
                    "Method once available: GET "
                    "https://api.supabase.com/v1/projects/{ref} with a personal "
                    "access token.",
                    needs_credentials=",".join(missing),
                )
            ]

        ref = os.environ["SUPABASE_PROJECT_REF"]
        token = os.environ["SUPABASE_ACCESS_TOKEN"]
        response = self._transport(
            "GET",
            f"https://api.supabase.com/v1/projects/{ref}",
            {"Authorization": f"Bearer {token}"},
            None,
        )
        if response.status != 200:
            return [
                self._unavailable(
                    f"Supabase Management API returned {response.status or 'no response'}"
                    f"{': ' + response.error if response.error else ''}",
                    adapter_status="call_failed",
                )
            ]

        database = response.payload.get("database") or {}
        size_mb = _to_float(database.get("size_mb"))
        return [
            Reading(
                source=self.name,
                key="database_size_mb",
                value=size_mb,
                unit="MiB",
                basis="measured" if size_mb is not None else "unavailable",
                detail="Supabase reports database size, not cost; map it to the "
                "plan's included quota before treating it as spend.",
                tags={"quotas": "database_size"},
            ),
            self._unavailable(
                "Supabase bills on a monthly invoice; per-service USD is not "
                "exposed by the public API. The database size above is the only "
                "directly measured figure, and it is not a bill.",
                adapter_status="no_bill_endpoint",
            ),
        ]


class VercelAdapter(_BaseAdapter):
    """Vercel plan usage via the v2 API."""

    name = "vercel"
    required_env = ("VERCEL_TOKEN", "VERCEL_TEAM_ID")
    purpose = "build minutes, bandwidth, function invocations"

    def __init__(self, transport: Transport = urllib_transport) -> None:
        self._transport = transport

    def read(self) -> list[Reading]:
        missing = self.missing_env()
        if missing:
            return [
                self._unavailable(
                    f"{self.purpose}. Missing environment: {', '.join(missing)}. "
                    "Method once available: GET https://api.vercel.com/v2/usage "
                    "with a team-scoped token.",
                    needs_credentials=",".join(missing),
                )
            ]

        team = os.environ["VERCEL_TEAM_ID"]
        token = os.environ["VERCEL_TOKEN"]
        response = self._transport(
            "GET",
            f"https://api.vercel.com/v2/usage?teamId={team}&limit=100",
            {"Authorization": f"Bearer {token}"},
            None,
        )
        if response.status != 200:
            return [
                self._unavailable(
                    f"Vercel usage API returned {response.status or 'no response'}"
                    f"{': ' + response.error if response.error else ''}",
                    adapter_status="call_failed",
                )
            ]

        readings: list[Reading] = []
        billable = [
            item
            for item in response.payload.get("billing", {}).get("items", [])
            if str(item.get("billable", "0")) not in {"0", "0.00"}
        ]
        for item in billable:
            amount = _to_float(item.get("amount", item.get("price")))
            if amount is not None:
                readings.append(
                    self._measured(
                        amount,
                        f"{item.get('resource', 'unknown')} for period "
                        f"{item.get('date', 'current')}",
                        resource=str(item.get("resource", "unknown")),
                    )
                )
        if not readings:
            readings.append(
                self._unavailable(
                    "Vercel reported no billable items. On the Hobby plan this "
                    "is expected: the included quota is not reported as spend.",
                    adapter_status="nothing_billable",
                )
            )
        return readings


class GitHubActionsAdapter(_BaseAdapter):
    """GitHub Actions minutes. Minutes are a cost driver even when free."""

    name = "github"
    required_env = ("GITHUB_TOKEN", "GITHUB_OWNER")
    purpose = "Actions minutes and artifact storage"

    def __init__(self, transport: Transport = urllib_transport) -> None:
        self._transport = transport

    def read(self) -> list[Reading]:
        missing = self.missing_env()
        if missing:
            return [
                self._unavailable(
                    f"{self.purpose}. Missing environment: {', '.join(missing)}. "
                    "Method once available: GitHub billing API for Actions usage.",
                    needs_credentials=",".join(missing),
                )
            ]

        owner = os.environ["GITHUB_OWNER"]
        response = self._transport(
            "GET",
            f"https://api.github.com/users/{owner}/settings/billing/actions",
            {
                "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                "Accept": "application/vnd.github+json",
            },
            None,
        )
        if response.status != 200:
            return [
                self._unavailable(
                    f"GitHub billing API returned {response.status or 'no response'}"
                    f"{': ' + response.error if response.error else ''}. Note that "
                    "this endpoint requires an owner-level token.",
                    adapter_status="call_failed",
                )
            ]

        total = _to_float((response.payload.get("total") or {}).get("total_minutes_used"))
        return [
            Reading(
                source=self.name,
                key="actions_minutes_used",
                value=total,
                unit="minutes",
                basis="derived" if total is not None else "unavailable",
                detail="minutes consumed in the current billing period",
                tags={"cost_driver": "ci"},
            )
        ]


ADAPTERS: dict[str, type[_BaseAdapter]] = {
    "aws": AWSCostAdapter,
    "supabase": SupabaseAdapter,
    "vercel": VercelAdapter,
    "github": GitHubActionsAdapter,
}


def collect_local() -> list[Reading]:
    """Measurements that need nothing but the repository."""
    readings: list[Reading] = []

    for name, path in (
        ("engine", REPO_ROOT / "engine"),
        ("services", REPO_ROOT / "services"),
        ("apps_web", REPO_ROOT / "apps" / "web"),
    ):
        size = None
        if path.is_dir():
            total = 0
            for entry in path.rglob("*"):
                if (
                    entry.is_file()
                    and ".git" not in entry.parts
                    and "node_modules" not in entry.parts
                ):
                    try:
                        total += entry.stat().st_size
                    except OSError:
                        continue
            size = round(total / (1024**3), 4)
        readings.append(
            Reading(
                source="local",
                key=f"repo_size_{name}",
                value=size,
                unit="GiB",
                basis="derived" if size is not None else "unavailable",
                detail="source tree size excluding .git and node_modules",
                tags={"cost_driver": "not_billed_locally"},
            )
        )

    workflows = REPO_ROOT / ".github" / "workflows"
    files = (
        list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml")) if workflows.is_dir() else []
    )
    step_lines = 0
    for workflow in files:
        try:
            step_lines += sum(
                1
                for line in workflow.read_text(encoding="utf-8").splitlines()
                if line.startswith("  ")
            )
        except OSError:
            continue
    readings.extend(
        [
            Reading(
                source="local",
                key="ci_workflow_files",
                value=float(len(files)) if files else None,
                unit="count",
                basis="derived" if files else "unavailable",
                detail="GitHub Actions workflow definitions in the repository",
                tags={"cost_driver": "ci"},
            ),
            Reading(
                source="local",
                key="ci_step_lines",
                value=float(step_lines),
                unit="count",
                basis="derived",
                detail="indented lines across workflows; an upper bound on step "
                "count, not billed minutes",
                tags={"cost_driver": "ci"},
            ),
        ]
    )
    return readings


def build_document(readings: list[Reading]) -> dict[str, Any]:
    measured = [r for r in readings if r.basis != "unavailable" and r.value is not None]
    unavailable = [r for r in readings if r.basis == "unavailable"]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "month_to_date_usd": None,
        "month_to_date_note": (
            "null means unknown, not zero. The budget gate treats null as "
            "'cannot evaluate' and says so out loud."
        ),
        "measured_count": len(measured),
        "unavailable_count": len(unavailable),
        "readings": [reading.as_dict() for reading in readings],
    }


def write_document(document: dict[str, Any], path: Path = USAGE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect Eco Nojin usage readings")
    parser.add_argument(
        "--source",
        action="append",
        choices=[*sorted(ADAPTERS), "local"],
        help="collector to run; repeatable. Defaults to local only.",
    )
    parser.add_argument("--out", default=str(USAGE_PATH))
    parser.add_argument("--print", dest="show", action="store_true")
    args = parser.parse_args(argv)

    readings: list[Reading] = []
    for source in args.source or ["local"]:
        if source == "local":
            readings.extend(collect_local())
        else:
            readings.extend(ADAPTERS[source]().read())

    document = build_document(readings)
    target = Path(args.out)
    write_document(document, target)

    print(f"wrote {target}")
    print(f"  measured:    {document['measured_count']}")
    print(f"  unavailable: {document['unavailable_count']}")
    if document["unavailable_count"]:
        print()
        print("unavailable sources (recorded, not zeroed):")
        for reading in readings:
            if reading.basis == "unavailable":
                print(f"  - {reading.source}: {reading.detail}")
    if args.show:
        print()
        print(json.dumps(document, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
