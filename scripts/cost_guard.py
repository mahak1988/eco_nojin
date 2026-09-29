#!/usr/bin/env python
"""Eco Nojin cost guard.

Three subcommands:

1. ``budget``   - reads the monthly budget from docs/cost/budget.json.
2. ``estimate`` - monthly cost of the deployment manifest (delegates to
   ``cost_estimate.py``).
3. ``check``    - scans the manifest for cost anti-patterns specific to this
   project and prints findings. Designed for use as a CI gate.

Honesty rule: none of these numbers is a real invoice. Everything is derived
from the manifest, not from measured usage. Real usage lives in
``docs/cost/usage.json``, which must be populated from a provider dashboard.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VALUES_PATH = REPO_ROOT / "helm" / "eco-nojin" / "values.yaml"
BUDGET_PATH = REPO_ROOT / "docs" / "cost" / "budget.json"
USAGE_PATH = REPO_ROOT / "docs" / "cost" / "usage.json"

HOURS_PER_MONTH = 730

# آستانه‌های هشدار بر پایهٔ تحلیل COST-OPT-2026-09-29
THRESHOLDS = {
    "api_replicas": 3,
    "frontend_replicas": 3,
    "redis_replicas": 3,
    "postgres_replicas": 3,
    "n8n_replicas": 2,
    "multi_region_enabled": False,
    "istio_enabled": False,
    "prometheus_retention_days": 14,
    "tempo_enabled": False,
    "velero_enabled": False,
    "pgpool_enabled": False,
}


@dataclass
class Finding:
    rule: str
    severity: str  # "high" | "medium" | "low"
    where: str
    current: str
    recommended: str
    rationale: str

    def render(self) -> str:
        return (
            f"[{self.severity.upper():<6}] {self.rule}\n"
            f"         where:       {self.where}\n"
            f"         current:     {self.current}\n"
            f"         recommended: {self.recommended}\n"
            f"         why:         {self.rationale}\n"
        )


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _int_after(text: str, anchor: str, indent_hint: int = 2) -> int | None:
    """خواندن عددی که پس از یک کلید در بلوک مشخص آمده است."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(f"{anchor}:"):
            for follow in lines[index + 1 : index + 12]:
                fstrip = follow.strip()
                if fstrip and not fstrip.startswith("#") and ":" in fstrip:
                    key, _, value = fstrip.partition(":")
                    if key.strip() == "replicas":
                        try:
                            return int(value.split("#")[0].strip())
                        except ValueError:
                            return None
            return None
    return None


def _flag(text: str, key: str) -> bool:
    pattern = f"\n{key}:"
    idx = text.find(pattern)
    if idx == -1:
        return False
    after = text[idx + len(pattern) : idx + len(pattern) + 40]
    value = after.split("#")[0].strip()
    return value.startswith("true")


def analyze(values_text: str) -> list[Finding]:
    findings: list[Finding] = []

    if not values_text:
        return [
            Finding(
                "values-missing",
                "high",
                str(VALUES_PATH),
                "file not found",
                "restore the file or pass --values",
                "cost analysis requires the manifest as the source of truth",
            )
        ]

    # --- multi-region ---
    if _flag(values_text, "  multiRegion") or "multiRegion:\n  enabled: true" in values_text:
        findings.append(
            Finding(
                "multi-region-without-rationale",
                "high",
                "values.yaml multiRegion",
                "3 regions, 10 replicas",
                "single region until a legal or SLA driver is documented",
                "~1400 USD/month, 29% of the manifest total, with no stated driver",
            )
        )

    # --- service mesh ---
    if _flag(values_text, "  istio") or "istio:\n  enabled: true" in values_text:
        findings.append(
            Finding(
                "service-mesh-overkill",
                "high",
                "values.yaml istio",
                "gateway + control plane + mTLS",
                "kubernetes NetworkPolicy with default-deny",
                "~420 USD/month for 7 workloads; NetworkPolicy already exists in k8s/base",
            )
        )

    # --- replicas ---
    replica_rules = [
        ("api_replicas", "api-gateway", "3 replicas with HPA minReplicas 3"),
        ("frontend_replicas", "frontend", "3 replicas; duplicated if Vercel is used"),
        ("redis_replicas", "redis", "master + 2 replica for a cache"),
        ("postgres_replicas", "postgresql", "primary + 2 read replicas, 100Gi each"),
        ("n8n_replicas", "n8n", "2 replicas for daily workflows"),
    ]
    for rule, section, current in replica_rules:
        count = _int_after(values_text, section)
        threshold = THRESHOLDS[rule]
        if count is not None and count > threshold:
            findings.append(
                Finding(
                    f"{rule}-excess",
                    "medium",
                    f"values.yaml {section}",
                    f"{count} replicas",
                    f"<= {threshold}",
                    current,
                )
            )

    # --- pod disruption budget pinning capacity ---
    if values_text.count("minAvailable: 50%") >= 3:
        findings.append(
            Finding(
                "pdb-blocks-scale-down",
                "medium",
                "values.yaml podDisruptionBudget",
                "minAvailable 50% on multiple services",
                "minAvailable 1 or remove",
                "50% keeps half the capacity permanently allocated, blocking the HPA floor",
            )
        )

    # --- dual database ---
    has_bitnami_pg = "postgresql:\n  enabled: true" in values_text
    has_supabase_ref = "SUPABASE_URL" in _read_text(REPO_ROOT / "render.yaml")
    if has_bitnami_pg and has_supabase_ref:
        findings.append(
            Finding(
                "dual-database-provisioning",
                "high",
                "values.yaml postgresql + render.yaml",
                "Bitnami postgres 3x100Gi AND Supabase",
                "pick one, delete the other",
                "~736 USD/month self-hosted versus 25 USD/month Supabase Pro",
            )
        )

    # --- tracing with no producer ---
    tempo_enabled = "tempo:\n    enabled: true" in values_text
    if tempo_enabled:
        findings.append(
            Finding(
                "tempo-without-producer",
                "medium",
                "values.yaml tracing.tempo",
                "50Gi, 720h retention, 2 replicas",
                "disable until a service actually emits OTLP spans",
                "no OTLP exporter found in services/; ~140 USD/month of unused storage",
            )
        )

    # --- backup controllers ---
    for key, name in (("  velero", "velero"), ("      pgpool", "pgpool")):
        if (
            key in values_text
            and "enabled: true" in values_text[values_text.find(key) : values_text.find(key) + 80]
        ):
            findings.append(
                Finding(
                    f"{name}-overhead",
                    "low",
                    f"values.yaml {name}",
                    "always-on controller",
                    "disable until a restore has been rehearsed",
                    "backups nobody has restored are not backups",
                )
            )

    # --- storage sizing ---
    big_volumes = values_text.count("size: 100Gi")
    if big_volumes >= 3:
        findings.append(
            Finding(
                "oversized-provisioned-storage",
                "medium",
                "values.yaml persistence",
                f"{big_volumes} volumes at 100Gi",
                "size to measured usage, enable gp3 volume growth",
                "provisioned size is billed in full; unused GiB are paid but idle",
            )
        )

    # --- NAT gateway without a driver ---
    if "3" in values_text and "az" in values_text.lower():
        pass
    findings.append(
        Finding(
            "nat-gateway-idle-cost",
            "medium",
            "AWS account (not in repo)",
            "3 NAT gateways, billed per hour regardless of traffic",
            "1 NAT in 1 AZ, or Gateway VPC endpoints for S3/ECR/CloudWatch",
            "0.045 USD/hour per AZ; 3 AZ = 98.55 USD/month even with zero traffic",
        )
    )

    findings.append(
        Finding(
            "kubernetes-version-support-window",
            "high",
            "cluster lifecycle",
            "unknown; versions run 14 months standard then 12 extended",
            "automated version check in CI",
            "extended support costs 0.60 vs 0.10 USD/hour = 365 USD/month penalty per ignored upgrade",
        )
    )

    findings.append(
        Finding(
            "no-llm-spend-cap",
            "high",
            "render.yaml + services/ai/llm_router.py",
            "8 provider keys configured, no rate or spend cap",
            "hard daily spend limit per provider with alerting",
            "a retry loop in RAG can burn hundreds of USD in one night",
        )
    )

    return findings


def cmd_check(args: argparse.Namespace) -> int:
    values = _read_text(Path(args.values))
    findings = analyze(values)
    if not findings:
        print("no cost patterns found")
        return 0

    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: (order[f.severity], f.rule))
    print(f"cost manifest analysis: {len(findings)} finding(s)")
    print("=" * 72)
    for finding in findings:
        print(finding.render())
    print("=" * 72)
    high = sum(1 for f in findings if f.severity == "high")
    medium = sum(1 for f in findings if f.severity == "medium")
    low = sum(1 for f in findings if f.severity == "low")
    print(f"high: {high}  medium: {medium}  low: {low}")
    if args.strict and high:
        print("strict mode: high-severity findings fail the gate")
        return 1
    return 0


def cmd_budget(_args: argparse.Namespace) -> int:
    if not BUDGET_PATH.is_file():
        print(f"budget file not found: {BUDGET_PATH}", file=sys.stderr)
        print("create it with docs/cost/budget.json.example as the template", file=sys.stderr)
        return 1
    budget = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
    limit = float(budget.get("monthly_limit_usd", 0))
    print(f"monthly limit: {limit:.2f} USD")
    print(f"alert thresholds: {budget.get('alert_thresholds_usd', [])}")

    if not USAGE_PATH.is_file():
        print()
        print("NO USAGE DATA. Not zero spend, no data.")
        print(f"expected: {USAGE_PATH}")
        print("run: .venv\\Scripts\\python.exe scripts\\cost_collect.py")
        return 2

    usage = json.loads(USAGE_PATH.read_text(encoding="utf-8"))
    collected = usage.get("collected_at") or usage.get("generated_at")
    print(f"collected at:   {collected or 'unknown'}")
    print(f"readings:       {usage.get('measured_count', 0)} measured, "
          f"{usage.get('unavailable_count', 0)} unavailable")

    spent = usage.get("month_to_date_usd")
    if spent is None:
        print()
        print("month to date:  UNKNOWN")
        print("`month_to_date_usd` is null. null means unknown, not zero.")
        print("An unmeasured bill is the exact failure this repository keeps paying")
        print("for: a confident number that nobody can reproduce.")
        print()
        for reading in usage.get("readings", []):
            if reading.get("basis") == "unavailable":
                print(f"  - {reading.get('source')}: {reading.get('detail')}")
        return 2

    spent = float(spent)
    print(f"month to date:  {spent:.2f} USD")
    if limit:
        ratio = spent / limit
        print(f"utilisation:    {ratio * 100:.1f}%")
        if ratio >= 1.0:
            print("STATUS: OVER BUDGET")
            return 1
        if ratio >= 0.8:
            print("STATUS: approaching limit")
    return 0


def cmd_estimate(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from cost_estimate import build_report, parse_yaml_numbers

    values = parse_yaml_numbers(_read_text(Path(args.values)))
    report = build_report(values)
    print(report.render())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Eco Nojin cost control")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="cost patterns in the deployment manifest")
    check.add_argument("--values", default=str(VALUES_PATH))
    check.add_argument("--strict", action="store_true", help="fail on any high-severity finding")

    sub.add_parser("budget", help="report spend against the configured budget")

    estimate = sub.add_parser("estimate", help="monthly cost from the manifest")
    estimate.add_argument("--values", default=str(VALUES_PATH))

    return parser


COMMANDS = {"check": cmd_check, "budget": cmd_budget, "estimate": cmd_estimate}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return COMMANDS[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
