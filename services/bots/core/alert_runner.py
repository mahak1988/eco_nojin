"""
Alert Runner (Phase 4 — real-data alert evaluation)
=====================================================
Bridges the pure alert rules in :mod:`alerts` with real stored satellite
rows. Alerts are evaluated ONLY against rows whose
``data_source == "copernicus"`` — simulated values can never fire a farm
alert (see ``satellite_row_to_metrics``).

The bot runner calls :func:`evaluate_farm_alerts` periodically; actual
message dispatch to farmers requires the farm→chat mapping which is
documented in docs/en/14_telegram_bot.md.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence

from sqlalchemy.orm import Session

from database import models
from services.bots.core.alerts import (
    AlertRule,
    evaluate_rules,
    format_alert,
    ndvi_alert_rules,
    satellite_row_to_metrics,
)

logger = logging.getLogger(__name__)


def latest_real_satellite_row(
    db: Session, farm_id: int
) -> models.SatelliteAnalysis | None:
    """Newest REAL (copernicus) satellite analysis row for a farm."""
    return (
        db.query(models.SatelliteAnalysis)
        .filter(
            models.SatelliteAnalysis.farm_id == farm_id,
            models.SatelliteAnalysis.data_source == "copernicus",
        )
        .order_by(models.SatelliteAnalysis.analyzed_at.desc())
        .first()
    )


def evaluate_farm_alerts(
    db: Session, farm_id: int, rules: Sequence[AlertRule] | None = None
) -> list[str]:
    """Evaluate real NDVI alerts for a farm and return formatted messages.

    Args:
        db: database session.
        farm_id: target farm.
        rules: alert rules; defaults to :func:`ndvi_alert_rules`.

    Returns:
        List of Persian alert messages. Empty when there is no real
        satellite data (honest: nothing to alert about).
    """
    row = latest_real_satellite_row(db, farm_id)
    if row is None:
        return []
    metrics = satellite_row_to_metrics(row)
    if metrics is None:
        return []
    farm = db.get(models.Farm, farm_id)
    farm_name = farm.name if farm else ""
    fired = evaluate_rules(rules or ndvi_alert_rules(), metrics)
    return [format_alert(rule, metrics, farm_name) for rule in fired]


def run_all_farm_alerts(db: Session) -> list[str]:
    """Evaluate real NDVI alerts for every farm; return all fired messages.

    Runs inside the API's periodic alert loop. Dispatch to farmers (the
    farm → chat mapping) lands with bot integration (docs 14).
    """
    fired_all: list[str] = []
    farms = db.query(models.Farm).all()
    for farm in farms:
        try:
            fired = evaluate_farm_alerts(db, farm.id)
        except Exception:
            logger.exception("alert evaluation failed for farm %s", farm.id)
            continue
        for msg in fired:
            logger.warning("ALERT farm=%s: %s", farm.id, msg)
            fired_all.append(msg)
    return fired_all
