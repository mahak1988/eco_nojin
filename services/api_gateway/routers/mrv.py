from datetime import timezone
"""MRV (EM-01) three-level Measurement, Reporting, Verification router.

Endpoints:
- POST /api/v1/mrv/iot-reading          store an IoT sensor reading (level 2)
- POST /api/v1/mrv/citizen-report       store a citizen field report (level 3)
- POST /api/v1/mrv/citizen-reports/batch  offline queue sync (level 3)
- POST /api/v1/mrv/satellite-index      store a satellite index (level 1)
- POST /api/v1/mrv/satellite-refresh    live CDSE Sentinel-2 NDVI (level 1)
- POST /api/v1/mrv/lorawan-webhook      TTN v3 / LoRaWAN ingest (level 2)
- GET  /api/v1/mrv/observations         list stored observations
- GET  /api/v1/mrv/dashboard-metrics    transparency metrics with provenance
- GET  /api/v1/mrv/public/dashboard-summary  PII-free public aggregates
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import MRVObservation
from engine.hydroma.config.settings import get_settings
from engine.hydroma.mrv import iot_ingest, metrics, satellite_cdse
from engine.hydroma.mrv.qa import is_usable, validate_reading, validate_satellite_index
from engine.hydroma.mrv.schemas import (
    CitizenBatch,
    CitizenReport,
    IoTReading,
    SatelliteIndex,
    SatelliteRefreshRequest,
)

router = APIRouter(prefix="/api/v1/mrv", tags=["MRV"])


def _jsonable(data: dict) -> dict:
    """Convert datetime values to ISO strings so payload is JSON-serializable."""
    out: dict = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            out[key] = value.isoformat()
        elif isinstance(value, list):
            out[key] = [
                item.isoformat() if isinstance(item, datetime) else item for item in value
            ]
        else:
            out[key] = value
    return out


def _row_from_observation(obs: MRVObservation) -> dict:
    """Serialize one MRV observation row for API responses."""
    return {
        "id": obs.id,
        "site_id": obs.site_id,
        "level": obs.level,
        "source": obs.source,
        "sensor_type": obs.sensor_type,
        "category": obs.category,
        "value": obs.value,
        "unit": obs.unit,
        "payload": obs.payload or {},
        "data_source": obs.data_source,
        "qa_status": obs.qa_status,
        "qa_message": obs.qa_message,
        "observed_at": obs.observed_at.isoformat() if obs.observed_at else None,
        "created_at": obs.created_at.isoformat() if obs.created_at else None,
    }


@router.post("/iot-reading")
def store_iot_reading(reading: IoTReading, db: Session = Depends(get_db)):
    """Store an IoT sensor reading (level 2) after QA/QC screening.

    The row is always persisted (audit trail); rejected rows carry
    qa_status="rejected" and must not feed dashboard metrics.
    """
    obs = iot_ingest.persist_iot_reading(db, reading)
    return {
        **_row_from_observation(obs),
        "qa": {"qa_status": obs.qa_status, "message": obs.qa_message},
    }


@router.post("/citizen-report")
def store_citizen_report(report_in: CitizenReport, db: Session = Depends(get_db)):
    """Store a citizen field report (level 3)."""
    obs = MRVObservation(
        site_id=report_in.site_id,
        level=3,
        source="citizen",
        category=report_in.category,
        payload=_jsonable(report_in.model_dump()),
        data_source="real",
        qa_status="ok",
        qa_message="Citizen report accepted; geotag and photos preserved in payload.",
        observed_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return _row_from_observation(obs)


@router.post("/citizen-reports/batch")
def store_citizen_batch(batch: CitizenBatch, db: Session = Depends(get_db)):
    """Offline-first sync: persist a queue of citizen reports (level 3).

    Reports are stored per item; a schema-invalid report fails the whole
    request (422) while every accepted item returns its own row id.
    """
    rows = []
    for report_in in batch.reports:
        obs = MRVObservation(
            site_id=report_in.site_id,
            level=3,
            source="citizen",
            category=report_in.category,
            payload=_jsonable(report_in.model_dump()),
            data_source="real",
            qa_status="ok",
            qa_message="Citizen report accepted (batch sync).",
            observed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(obs)
        rows.append(obs)
    db.commit()
    for obs in rows:
        db.refresh(obs)
    return {
        "accepted": len(rows),
        "observations": [_row_from_observation(r) for r in rows],
    }


@router.post("/satellite-index")
def store_satellite_index(idx: SatelliteIndex, db: Session = Depends(get_db)):
    """Store a satellite index (level 1) with explicit provenance."""
    report = validate_satellite_index(idx.index, idx.value)
    obs = MRVObservation(
        site_id=idx.site_id,
        level=1,
        source="satellite",
        sensor_type=idx.index,
        value=idx.value,
        unit="-",
        payload=_jsonable(idx.model_dump()),
        data_source=idx.data_source,
        qa_status=report.qa_status,
        qa_message=report.message,
        observed_at=idx.ts,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return {
        **_row_from_observation(obs),
        "qa": {"qa_status": report.qa_status, "message": report.message},
    }


@router.post("/satellite-refresh")
def satellite_refresh(req: SatelliteRefreshRequest, db: Session = Depends(get_db)):
    """Fetch a live Sentinel-2 NDVI from CDSE and store it (level 1, real).

    Gated by ENABLE_SATELLITE_REAL. On failure this endpoint returns an
    explicit error instead of silently storing simulated data; the caller
    (frontend) decides whether to fall back to a labeled simulation.
    """
    if str(getattr(get_settings(), "enable_satellite_real", "false")).lower() != "true":
        raise HTTPException(
            status_code=503,
            detail="real satellite retrieval is disabled (ENABLE_SATELLITE_REAL != true)",
        )
    try:
        cfg = satellite_cdse.CdseConfig.from_env()
        with __import__("requests").Session() as session:
            result = satellite_cdse.retrieve_ndvi(
                session,
                cfg,
                satellite_cdse.build_bbox(req.lat, req.lon, req.half_side_km),
                req.start,
                req.end,
            )
    except (satellite_cdse.CdseUnavailable, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"CDSE retrieval failed: {exc}") from exc

    report = validate_satellite_index("NDVI", result["value"])
    obs = MRVObservation(
        site_id=req.site_id,
        level=1,
        source="satellite",
        sensor_type="NDVI",
        value=result["value"],
        unit="-",
        payload=_jsonable(result["payload"]),
        data_source="real",
        qa_status=report.qa_status,
        qa_message=report.message,
        observed_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return {
        **_row_from_observation(obs),
        "qa": {"qa_status": report.qa_status, "message": report.message},
    }


@router.post("/lorawan-webhook")
def lorawan_webhook(
    payload: dict,
    x_webhook_key: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """TTN v3 / LoRaWAN uplink webhook -> level-2 readings (X-Webhook-Key)."""
    if not iot_ingest.webhook_key_ok(x_webhook_key, get_settings().telco_webhook_key):
        raise HTTPException(status_code=401, detail="invalid or missing webhook key")
    readings = iot_ingest.parse_ttn_v3(payload)
    if not readings:
        raise HTTPException(status_code=422, detail="no readable readings in payload")
    rows = [iot_ingest.persist_iot_reading(db, r) for r in readings]
    return {
        "count": len(rows),
        "observations": [_row_from_observation(r) for r in rows],
    }


@router.get("/observations")
def list_observations(
    site_id: str | None = None,
    level: int | None = Query(None, ge=1, le=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List MRV observations, optionally filtered by site and level."""
    query = db.query(MRVObservation)
    if site_id:
        query = query.filter(MRVObservation.site_id == site_id)
    if level is not None:
        query = query.filter(MRVObservation.level == level)
    rows = query.order_by(MRVObservation.observed_at.desc()).limit(limit).all()
    return {"count": len(rows), "observations": [_row_from_observation(r) for r in rows]}


@router.get("/dashboard-metrics")
def dashboard_metrics(
    site_id: str = Query(..., min_length=1),
    area_ha: float | None = Query(None, gt=0),
    rusle_before_tha: float | None = Query(None, ge=0),
    rusle_after_tha: float | None = Query(None, ge=0),
    soc_before_pct: float | None = Query(None, ge=0),
    soc_after_pct: float | None = Query(None, ge=0),
    households: int | None = Query(None, ge=0),
    income_per_household_usd: float | None = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    """Transparency dashboard metrics for a site with provenance badges.

    Metrics are only computed when their inputs are supplied; otherwise the
    value is None (never fabricated). The provenance badge is downgraded to
    "simulated" whenever the site has simulated observations.
    """
    rows = (
        db.query(MRVObservation)
        .filter(MRVObservation.site_id == site_id)
        .order_by(MRVObservation.observed_at.desc())
        .all()
    )
    usable = [r for r in rows if is_usable(r.qa_status)]
    observed_sources = [r.data_source for r in usable]
    counts = {"satellite": 0, "iot": 0, "citizen": 0}
    for row in rows:
        counts[row.source] = counts.get(row.source, 0) + 1

    result = metrics.compute_dashboard(
        site_id=site_id,
        area_ha=area_ha,
        rusle_before_tha=rusle_before_tha,
        rusle_after_tha=rusle_after_tha,
        soc_before_pct=soc_before_pct,
        soc_after_pct=soc_after_pct,
        households=households,
        income_per_household_usd=income_per_household_usd,
        observed_sources=observed_sources,
    )
    result["observation_counts"] = counts
    result["data_sources_observed"] = sorted({r.data_source for r in rows})
    result["total_observations"] = len(rows)
    return result


@router.get("/public/dashboard-summary")
def public_dashboard_summary(db: Session = Depends(get_db)):
    """PII-free aggregates for the public transparency dashboard.

    Never includes observer names, notes, or photo URLs.
    """
    rows = db.query(MRVObservation).all()
    by_level = {1: 0, 2: 0, 3: 0}
    by_source: dict[str, int] = {}
    by_qa: dict[str, int] = {}
    latest_sat: dict[str, tuple] = {}
    for row in rows:
        by_level[row.level] = by_level.get(row.level, 0) + 1
        by_source[row.source] = by_source.get(row.source, 0) + 1
        by_qa[row.qa_status] = by_qa.get(row.qa_status, 0) + 1
        if row.level == 1:
            current = latest_sat.get(row.site_id)
            if current is None or (row.observed_at and current[0] < row.observed_at):
                latest_sat[row.site_id] = (row.observed_at, row.value, row.sensor_type, row.data_source)

    latest = [
        {
            "site_id": site_id,
            "observed_at": ts.isoformat() if ts else None,
            "value": value,
            "index": index,
            "data_source": data_source,
        }
        for site_id, (ts, value, index, data_source) in latest_sat.items()
    ]
    return {
        "total_observations": len(rows),
        "by_level": by_level,
        "by_source": by_source,
        "by_qa_status": by_qa,
        "latest_satellite_per_site": latest,
    }
