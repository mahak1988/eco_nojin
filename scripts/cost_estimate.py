#!/usr/bin/env python
"""Eco Nojin monthly cost estimator.

Reads helm/eco-nojin/values.yaml and estimates the monthly bill of the
deployment architecture AS WRITTEN in the manifest.

Honesty rules (see COST_OPTIMIZATION_RESEARCH_FA.md section 2.2):

- ``measured`` items use a rate taken from an official vendor pricing page.
- ``estimated`` items use an assumed instance class or storage rate.

The EC2 and EBS figures are estimates, not quoted rates: the AWS pricing
calculator renders client-side and could not be scraped for a rate table.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

VALUES_PATH = Path(__file__).resolve().parent.parent / "helm" / "eco-nojin" / "values.yaml"

# نرخ‌های مستندشده (منبع در سند تحقیق)
EKS_CLUSTER_HOUR_STD = 0.10
EKS_CLUSTER_HOUR_EXT = 0.60
NAT_GW_HOUR = 0.045
NAT_GW_PER_GB = 0.045
DTO_PER_GB = 0.09
PUBLIC_IPV4_HOUR = 0.005

# برآورد بازه‌ای (نه نرخ رسمی استخراج‌شده)
EC2_COST = {
    "t3.medium": 0.0416,
    "t3.small": 0.0208,
    "t3.large": 0.0832,
    "m5.large": 0.096,
    "m5.xlarge": 0.192,
    "m5.2xlarge": 0.384,
    "m5.4xlarge": 0.768,
    "c5.xlarge": 0.17,
    "c5.2xlarge": 0.34,
    "c5.4xlarge": 0.68,
    "r5.xlarge": 0.252,
    "r5.2xlarge": 0.504,
}
EBS_GP3_PER_GB = 0.08
ALB_HOUR = 0.0225
NLB_HOUR = 0.025
CLB_HOUR = 0.025

HOURS_PER_MONTH = 730


def parse_yaml_numbers(text: str) -> dict[str, dict[str, float | int]]:
    """استخراج ساختار helm values با parser سبک و بدون وابستگی."""
    out: dict[str, dict[str, float | int]] = {}
    section: str | None = None
    subsection: str | None = None

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        if indent == 0 and line.endswith(":"):
            section = line[:-1]
            subsection = None
            out.setdefault(section, {})
            continue
        if section is None:
            continue
        if indent == 2 and line.endswith(":"):
            subsection = line[:-1]
            out[section].setdefault(subsection, {})
            continue
        if ":" in line and subsection is not None:
            key, _, value = line.partition(":")
            value = value.split("#")[0].strip()
            if re.fullmatch(r"-?\d+", value):
                out[section][subsection][key.strip()] = int(value)
            elif re.fullmatch(r"-?\d+(\.\d+)?[mM]i?", value):
                millis = re.match(r"-?(\d+)([mM]i?)", value)
                if millis:
                    out[section][subsection][key.strip()] = int(millis.group(1))
                else:
                    out[section][subsection][key.strip()] = int(float(value))
    return out


@dataclass
class LineItem:
    component: str
    detail: str
    unit_cost: float
    quantity: float
    unit: str
    measured: bool
    note: str = ""
    per_month: bool = False

    @property
    def monthly(self) -> float:
        if self.per_month:
            return self.unit_cost * self.quantity
        return self.unit_cost * self.quantity * HOURS_PER_MONTH


@dataclass
class Report:
    items: list[LineItem] = field(default_factory=list)

    def add(self, *args, per_month: bool = False, **kwargs) -> None:
        self.items.append(LineItem(*args, **kwargs, per_month=per_month))

    @property
    def total(self) -> float:
        return sum(item.monthly for item in self.items)

    @property
    def measured_total(self) -> float:
        return sum(item.monthly for item in self.items if item.measured)

    def render(self) -> str:
        lines: list[str] = []
        header = f"{'component':<26} {'qty':>6} {'unit$/hr':>9} {'monthly$':>11}  basis"
        lines.append("=" * len(header))
        lines.append(header)
        lines.append("=" * len(header))
        for item in self.items:
            basis = "measured" if item.measured else "estimated"
            detail = f"{item.detail} [{item.unit}]"
            lines.append(
                f"{item.component:<26} {item.quantity:>6.0f} {item.unit_cost:>9.4f} "
                f"{item.monthly:>11,.2f}  {basis}"
            )
            if item.note:
                lines.append(f"{'':<26} {detail}")
        lines.append("=" * len(header))
        lines.append(f"{'TOTAL (all)':<26} {'':>9} {'':>9} {self.total:>11,.2f}")
        lines.append(f"{'TOTAL (measured only)':<26} {'':>9} {'':>9} {self.measured_total:>11,.2f}")
        return "\n".join(lines)


def build_report(values: dict[str, dict]) -> Report:
    report = Report()
    api = values.get("api-gateway", {})
    front = values.get("frontend", {})
    redis = values.get("redis", {})
    pg = values.get("postgresql", {})
    n8n = values.get("n8n", {})
    mon = values.get("monitoring", {})
    log = values.get("logging", {})
    trace = values.get("tracing", {})

    def g(section: dict, path: str, default: float = 0) -> float:
        cursor: object = section
        for part in path.split("."):
            if isinstance(cursor, dict) and part in cursor:
                cursor = cursor[part]
            else:
                return default
        return float(cursor) if isinstance(cursor, (int, float)) else default

    # --- control plane / managed services (measured rates) ---
    report.add(
        "EKS cluster (standard)",
        "1 cluster, standard support",
        EKS_CLUSTER_HOUR_STD,
        1,
        "cluster-hour",
        True,
        "0.10 USD/cluster/hour",
    )
    report.add(
        "EKS cluster (extended)",
        "if version past standard support",
        EKS_CLUSTER_HOUR_EXT,
        1,
        "cluster-hour",
        True,
        "0.60 USD/cluster/hour - AVOID by upgrading",
    )
    report.add(
        "NAT gateway",
        "3 AZ, hourly only (no data)",
        NAT_GW_HOUR,
        3,
        "gateway-hour",
        True,
        "0.045 USD/AZ-hour",
    )
    report.add(
        "Public IPv4",
        "3 NAT + ingress nodes",
        PUBLIC_IPV4_HOUR,
        6,
        "ip-hour",
        True,
        "0.005 USD/hour per address",
    )
    report.add(
        "ALB",
        "2 (api + frontend ingress)",
        ALB_HOUR,
        2,
        "lb-hour",
        True,
        "0.0225 USD/hour",
    )

    # --- compute from helm replicas (estimated) ---
    api_replicas = float(g(api, "replicas", 3))
    front_replicas = float(g(front, "replicas", 3))
    n8n_replicas = float(g(n8n, "replicas", 2))
    redis_replicas = float(g(redis, "replica.replicaCount", 2)) + 1
    pg_replicas = float(g(pg, "readReplicas.replicaCount", 2)) + 1
    pgpool_replicas = float(g(pg, "pgpool.replicas", 2))

    report.add(
        "api-gateway nodes",
        f"{api_replicas:.0f} replicas on m5.xlarge",
        EC2_COST["m5.xlarge"],
        api_replicas,
        "instance-hour",
        False,
        "helm requests 500m CPU/1Gi -> m5.xlarge",
    )
    report.add(
        "frontend nodes",
        f"{front_replicas:.0f} replicas on c5.xlarge",
        EC2_COST["c5.xlarge"],
        front_replicas,
        "instance-hour",
        False,
        "Next.js node 250m CPU/512Mi",
    )
    report.add(
        "n8n workers",
        f"{n8n_replicas:.0f} replicas on m5.large-ish",
        EC2_COST["t3.large"],
        n8n_replicas,
        "instance-hour",
        False,
        "workflow engine, usually idle",
    )
    report.add(
        "redis",
        f"master + {redis_replicas - 1:.0f} replica",
        EC2_COST["t3.medium"],
        redis_replicas,
        "instance-hour",
        False,
        "cache does not need 1Gi+2Gi limits",
    )
    report.add(
        "postgres primary",
        "1 primary on r5.2xlarge-class",
        EC2_COST["r5.2xlarge"],
        1,
        "instance-hour",
        False,
        "100Gi gp3 + pgpool",
    )
    report.add(
        "postgres read replicas",
        f"{pg_replicas - 1:.0f} replicas",
        EC2_COST["r5.xlarge"],
        pg_replicas - 1,
        "instance-hour",
        False,
        "each 100Gi gp3",
    )
    report.add(
        "pgpool",
        f"{pgpool_replicas:.0f} replicas",
        EC2_COST["t3.medium"],
        pgpool_replicas,
        "instance-hour",
        False,
        "connection pooler in front of 1 primary",
    )
    report.add(
        "prometheus",
        "1 dedicated, 100Gi, 30d retention",
        EC2_COST["m5.xlarge"],
        1,
        "instance-hour",
        False,
        "monitoring.prometheus.resources 1000m/2Gi",
    )
    report.add(
        "grafana",
        "1",
        EC2_COST["t3.medium"],
        1,
        "instance-hour",
        False,
        "100m CPU/256Mi requested",
    )
    report.add(
        "alertmanager",
        "1",
        EC2_COST["t3.medium"],
        1,
        "instance-hour",
        False,
        "monitoring.alertmanager",
    )
    report.add(
        "loki",
        "1, 50Gi",
        EC2_COST["m5.large"],
        1,
        "instance-hour",
        False,
        "logging.loki 500m/1Gi",
    )
    report.add(
        "tempo",
        "1, 50Gi, 720h retention",
        EC2_COST["m5.large"],
        1,
        "instance-hour",
        False,
        "tracing.tempo 500m/1Gi",
    )
    report.add(
        "otel collector",
        "1 (stateful set typically 3)",
        EC2_COST["t3.small"],
        1,
        "instance-hour",
        False,
        "collector per node in sidecar form",
    )
    report.add(
        "promtail",
        "1 DaemonSet per node",
        EC2_COST["t3.small"],
        6,
        "instance-hour",
        False,
        "runs on every node",
    )
    report.add(
        "istio gateway",
        "2 replicas + control plane",
        EC2_COST["m5.large"],
        2,
        "instance-hour",
        False,
        "istio.enabled gateway 100m/128Mi",
    )
    report.add(
        "istio control plane",
        "istiod + ingress/egress",
        EC2_COST["m5.xlarge"],
        2,
        "instance-hour",
        False,
        "istiod has real baseline cost",
    )
    report.add(
        "velero",
        "1 controller",
        EC2_COST["t3.small"],
        1,
        "instance-hour",
        False,
        "backup controller, always on",
    )
    report.add(
        "multi-region replicas",
        "us-east-1 x5, eu-west-1 x3, ap x2",
        EC2_COST["m5.xlarge"],
        10,
        "instance-hour",
        False,
        "multiRegion replicas 5+3+2 = 10",
    )

    # --- storage (estimated) ---
    storage_gb = (
        float(g(redis, "master.persistence.size", 20)) * 3
        + float(g(pg, "primary.persistence.size", 100)) * 3
        + float(
            g(
                mon,
                "prometheus.storageSpec.volumeClaimTemplate.spec.resources.requests.storage",
                100,
            )
        )
        + float(g(mon, "grafana.persistence.size", 10))
        + float(g(mon, "alertmanager.persistence.size", 10))
        + float(g(log, "loki.persistence.size", 50))
        + float(g(trace, "tempo.persistence.size", 50))
    )
    report.add(
        "EBS gp3 volumes",
        f"{storage_gb:.0f} GiB total",
        EBS_GP3_PER_GB,
        storage_gb,
        "GB-month",
        False,
        "0.08 USD/GB-month gp3 in us-east-1 (already monthly)",
        per_month=True,
    )

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Eco Nojin monthly cost estimate")
    parser.add_argument("--values", default=str(VALUES_PATH))
    args = parser.parse_args(argv)

    path = Path(args.values)
    if not path.is_file():
        print(f"values file not found: {path}", file=sys.stderr)
        return 1

    values = parse_yaml_numbers(path.read_text(encoding="utf-8"))
    report = build_report(values)
    print(report.render())
    print()
    print("measured  = rate from an official vendor pricing page (see research doc)")
    print("estimated = instance-class or storage assumption, not a quoted rate")
    print()
    print("NOTE: this is the cost of the manifest AS WRITTEN (3 replicas, 3 regions,")
    print("      full observability, service mesh). It is not a statement about what is")
    print("      currently running. AGENTS.md states staging and production are disabled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
