"""Usage collection for Eco Nojin cost control (cost plan wave C0-1).

What this does
--------------
Populates ``docs/cost/usage.json`` so ``scripts/cost_guard.py budget`` has
real numbers to compare against the ceiling in ``docs/cost/budget.json``.

Honest scope
------------
No infrastructure is deployed, so there is no bill to read. This module
therefore does two different things and is explicit about which is which:

- **local** collectors measure things that exist in the repository right now
  (repository size, CI workflow shape, tracked manifests). These produce real
  numbers immediately.
- **external** collectors need an account and credentials that are not in
  this repository (AWS Cost Explorer, Render, Vercel, GitHub). They report
  ``unavailable`` with the reason, never a fabricated zero. A zero would let
  the budget gate read "0 spent" and pass, which is exactly the failure mode
  this repository keeps paying for.

Run it with::

    .venv\\Scripts\\python.exe scripts\\cost_collect.py
    .venv\\Scripts\\python.exe scripts\\cost_collect.py --source aws
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
USAGE_PATH = REPO_ROOT / "docs" / "cost" / "usage.json"
BUDGET_PATH = REPO_ROOT / "docs" / "cost" / "budget.json"

SCHEMA_VERSION = 1

# Sources that need an account this repository does not have. Each entry
# records what credential is missing so the operator knows exactly what to do.
EXTERNAL_SOURCES = {
    "aws": {
        "required_env": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
        "why": "AWS Cost Explorer API needs credentials and a billing-enabled account",
        "method": "boto3 cost-explorer GetCostAndUsage",
    },
    "render": {
        "required_env": ["RENDER_API_KEY"],
        "why": "Render has no free public usage endpoint for a Blueprint service",
        "method": "Render API v1 /services",
    },
    "vercel": {
        "required_env": ["VERCEL_TOKEN"],
        "why": "Vercel usage requires an authenticated team account",
        "method": "Vercel API /v2/usage",
    },
    "github": {
        "required_env": ["GITHUB_TOKEN"],
        "why": "Actions minutes are only visible to an authenticated owner",
        "method": "GitHub API /users/{owner}/settings/billing/actions",
    },
    "supabase": {
        "required_env": ["SUPABASE_ACCESS_TOKEN", "SUPABASE_PROJECT_REF"],
        "why": "Project usage requires a personal access token",
        "method": "Supabase Management API /v1/projects/{ref}/billing",
    },
}


@dataclass
class Reading:
    """One measurement, or an explicit statement that it is unavailable."""

    source: str
    key: str
    value: float | None
    unit: str
    basis: str  # "measured" | "derived" | "unavailable"
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


def _dir_size_gb(path: Path) -> float | None:
    if not path.is_dir():
        return None
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file() and ".git" not in entry.parts and "node_modules" not in entry.parts:
            try:
                total += entry.stat().st_size
            except OSError:
                continue
    return round(total / (1024**3), 4)


def collect_local() -> list[Reading]:
    """Measurements that need nothing but the repository."""
    readings: list[Reading] = []

    for name, path in (
        ("engine", REPO_ROOT / "engine"),
        ("services", REPO_ROOT / "services"),
        ("apps_web", REPO_ROOT / "apps" / "web"),
    ):
        size = _dir_size_gb(path)
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

    # A rough CI shape estimate. This is deliberately labelled derived: it is
    # a count of declared jobs, not billed minutes.
    workflows = REPO_ROOT / ".github" / "workflows"
    job_count = 0
    for workflow in workflows.glob("*.yml") if workflows.is_dir() else []:
        try:
            job_count += workflow.read_text(encoding="utf-8").count("\n  ")
        except OSError:
            continue
    readings.append(
        Reading(
            source="local",
            key="ci_workflow_files",
            value=float(len(list(workflows.glob("*.yml")))) if workflows.is_dir() else None,
            unit="count",
            basis="derived" if workflows.is_dir() else "unavailable",
            detail="GitHub Actions workflow definitions in the repository",
            tags={"cost_driver": "ci"},
        )
    )
    readings.append(
        Reading(
            source="local",
            key="ci_step_lines",
            value=float(job_count),
            unit="count",
            basis="derived",
            detail="indented lines across workflows; an upper bound on step count, "
            "not billed minutes",
            tags={"cost_driver": "ci"},
        )
    )

    return readings


def collect_external(name: str) -> Reading:
    """Attempt one external source; report honestly when it is unavailable."""
    spec = EXTERNAL_SOURCES.get(name)
    if spec is None:
        return Reading(
            source=name,
            key="unknown_source",
            value=None,
            unit="usd",
            basis="unavailable",
            detail=f"unknown source {name!r}; known: {sorted(EXTERNAL_SOURCES)}",
        )

    missing = [env for env in spec["required_env"] if not os.getenv(env)]
    if missing:
        return Reading(
            source=name,
            key="month_to_date",
            value=None,
            unit="usd",
            basis="unavailable",
            detail=(
                f"{spec['why']}. Missing environment: {', '.join(missing)}. "
                f"Method once available: {spec['method']}."
            ),
            tags={"needs_credentials": ",".join(missing)},
        )

    return Reading(
        source=name,
        key="month_to_date",
        value=None,
        unit="usd",
        basis="unavailable",
        detail=(
            f"credentials for {name} are present but no adapter is implemented in "
            "this repository yet. The correct next step is to add the adapter "
            f"rather than to record a number nobody can reproduce."
        ),
        tags={"adapter_status": "not_implemented"},
    )


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
        choices=[*sorted(EXTERNAL_SOURCES), "local"],
        help="collector to run; repeatable. Defaults to local only.",
    )
    parser.add_argument("--out", default=str(USAGE_PATH))
    parser.add_argument(
        "--print", dest="show", action="store_true", help="print the document to stdout"
    )
    args = parser.parse_args(argv)

    sources = args.source or ["local"]
    readings: list[Reading] = []
    for source in sources:
        if source == "local":
            readings.extend(collect_local())
        else:
            readings.append(collect_external(source))

    document = build_document(readings)
    target = Path(args.out)
    write_document(document, target)

    measured = document["measured_count"]
    unavailable = document["unavailable_count"]
    print(f"wrote {target}")
    print(f"  measured:    {measured}")
    print(f"  unavailable: {unavailable}")
    if unavailable:
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
