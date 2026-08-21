"""QA/QC validation for MRV observations (EM-01).

Physical plausibility bands follow agro-hydrological conventions:

- soil moisture ....... 0-100 %
- electrical cond. (EC) 0-20 dS/m
- temperature/LST ..... -40..60 degC
- flow ............... >= 0 (l/s or m3/s)
- NDVI ................ -1..1
- LAI ................. 0..10
- C-factor ............ 0..1

Each band defines a hard ``rejected`` bound and a soft ``suspect`` edge.
Rejected rows are still persisted (audit trail) but must never feed metrics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QAReport:
    """Outcome of a QA/QC check."""

    qa_status: str  # ok | suspect | rejected
    message: str


# band keys are the sensor_type / index names used by the API schemas.
PHYSICAL_RANGES: dict[str, dict] = {
    "soil_moisture": {"ok_min": 5.0, "ok_max": 95.0, "min": 0.0, "max": 100.0, "unit": "%"},
    "temp": {"ok_min": -20.0, "ok_max": 50.0, "min": -40.0, "max": 60.0, "unit": "degC"},
    "ec": {"ok_min": 0.1, "ok_max": 15.0, "min": 0.0, "max": 20.0, "unit": "dS/m"},
    "flow": {"ok_min": 0.0, "ok_max": 100000.0, "min": 0.0, "max": None, "unit": "l/s or m3/s"},
    "NDVI": {"ok_min": -0.2, "ok_max": 0.95, "min": -1.0, "max": 1.0, "unit": "-"},
    "LAI": {"ok_min": 0.0, "ok_max": 8.0, "min": 0.0, "max": 10.0, "unit": "-"},
    "C-factor": {"ok_min": 0.0, "ok_max": 0.8, "min": 0.0, "max": 1.0, "unit": "-"},
    "LST": {"ok_min": -20.0, "ok_max": 50.0, "min": -40.0, "max": 60.0, "unit": "degC"},
    "soil_moisture_sar": {"ok_min": 5.0, "ok_max": 95.0, "min": 0.0, "max": 100.0, "unit": "%"},
}


def validate_reading(
    sensor_type: str, value: float, unit: str | None = None
) -> QAReport:
    """Validate a reading against its physical plausibility band.

    Args:
        sensor_type: sensor or index name (see PHYSICAL_RANGES keys).
        value: measured value.
        unit: optional unit string, used only for the message.

    Returns:
        QAReport with qa_status in {"ok", "suspect", "rejected"} and a message.
    """
    band = PHYSICAL_RANGES.get(sensor_type)
    if band is None:
        return QAReport(
            "rejected", f"Unknown sensor_type '{sensor_type}'; cannot validate."
        )
    unit_str = unit or band["unit"]
    if band["max"] is None:
        hard_ok = value >= band["min"]
        bound_desc = f">= {band['min']}"
    else:
        hard_ok = band["min"] <= value <= band["max"]
        bound_desc = f"{band['min']}..{band['max']}"

    if not hard_ok:
        return QAReport(
            "rejected",
            f"{sensor_type}={value} {unit_str} outside physical range "
            f"({bound_desc}); rejected.",
        )
    if value < band["ok_min"] or value > band["ok_max"]:
        return QAReport(
            "suspect",
            f"{sensor_type}={value} {unit_str} near/outside plausible band "
            f"({band['ok_min']}..{band['ok_max']}); flag for manual review.",
        )
    return QAReport("ok", f"{sensor_type}={value} {unit_str} within plausible band.")


def validate_satellite_index(index: str, value: float) -> QAReport:
    """Validate a satellite index (NDVI/LAI/C-factor/LST/soil_moisture_sar)."""
    return validate_reading(index, value)


def is_usable(qa_status: str) -> bool:
    """Return True when the observation may feed dashboard metrics."""
    return qa_status in ("ok", "suspect")