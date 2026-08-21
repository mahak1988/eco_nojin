"""Smart alert engine (Phase 2, ⭐5) — rule evaluation + formatting.

Rules are evaluated against a data row (e.g. the latest soil moisture of a
farm). The dispatch itself lives in the runner so alerts go to every enabled
platform; this module stays pure and unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass

OPERATORS = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b,
}


@dataclass(frozen=True)
class AlertRule:
    metric: str            # data key, e.g. "soil_moisture_pct"
    op: str                # one of OPERATORS
    threshold: float
    severity: str          # "info" | "warning" | "critical"
    label: str             # Persian label shown to the farmer


def evaluate_rules(rules: list[AlertRule], data: dict[str, float]) -> list[AlertRule]:
    """Return the rules that fire for the given data row.

    Missing metrics never fire (no fabricated alerts).
    """
    fired: list[AlertRule] = []
    for rule in rules:
        value = data.get(rule.metric)
        if value is None:
            continue
        op = OPERATORS.get(rule.op)
        if op is None:
            continue
        try:
            if op(float(value), float(rule.threshold)):
                fired.append(rule)
        except (TypeError, ValueError):
            continue
    return fired


def format_alert(rule: AlertRule, data: dict[str, float], farm_name: str = "") -> str:
    """Human-readable alert text (Persian), honest about the value seen."""
    value = data.get(rule.metric)
    emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(rule.severity, "⚠️")
    farm = f"مزرعه «{farm_name}»: " if farm_name else ""
    value_txt = f"مقدار فعلی: {value}" if value is not None else "مقدار: نامشخص"
    return f"{emoji} {farm}{rule.label}\n{value_txt} (حد آستانه {rule.threshold})"


def ndvi_alert_rules() -> list[AlertRule]:
    """Real NDVI alert rules (Phase 4) — fire ONLY on real satellite data.

    The rules themselves are pure; callers must only pass rows whose
    ``data_source == "copernicus"`` so simulated values never trigger a
    farm alert (missing metric rule in evaluate_rules already guards
    against absent data).
    """
    return [
        AlertRule("ndvi", "<=", 0.25, "critical",
                  "پوشش گیاهی بسیار ضعیف است (NDVI واقعی)" ),
        AlertRule("ndvi", "<=", 0.40, "warning",
                  "پوشش گیاهی در حال تنش است (NDVI واقعی)"),
        AlertRule("ndvi", ">=", 0.65, "info",
                  "پوشش گیاهی خوب است (NDVI واقعی)"),
    ]


def satellite_row_to_metrics(row) -> dict[str, float] | None:
    """Extract metrics from a stored SatelliteAnalysis row.

    Returns None when the row is not REAL data (data_source != copernicus)
    so the alert engine can never fire on simulated values.
    """
    source = getattr(row, "data_source", "simulated")
    if source != "copernicus":
        return None
    ndvi = getattr(row, "ndvi", None)
    if ndvi is None:
        return None
    return {"ndvi": float(ndvi)}
