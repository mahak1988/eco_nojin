"""MRV / Carbon budget router — فاز ۴ (رایگان)."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import MRVObservation
from engine.hydroma.mrv import satellite_cdse
from engine.hydroma.mrv.iot_ingest import parse_ttn_v3, persist_iot_reading, webhook_key_ok
from engine.hydroma.mrv.metrics import compute_dashboard
from engine.hydroma.mrv.qa import validate_satellite_index
from engine.hydroma.mrv.satellite_cdse import CdseUnavailable
from engine.hydroma.mrv.schemas import CitizenBatch, CitizenReport, IoTReading, SatelliteIndex
from services.mrv.kobo import average_measured_soc, fetch_kobo_submissions
from services.mrv.mrv_pdf import build_mrv_pdf
from services.scientific_motors.carbon_mrv import CarbonMrvMotor
from services.scientific_motors.chain_runner import run_scientific_chain

router = APIRouter(prefix="/mrv", tags=["mrv"])


def get_db():
    with hub.get_session() as session:
        yield session


def _observation_json(row: MRVObservation) -> dict[str, Any]:
    result = {
        "id": row.id,
        "site_id": row.site_id,
        "level": row.level,
        "source": row.source,
        "sensor_type": row.sensor_type,
        "value": row.value,
        "unit": row.unit,
        "payload": row.payload or {},
        "data_source": row.data_source,
        "qa_status": row.qa_status,
        "qa": {"message": row.qa_message or ""},
        "observed_at": row.observed_at.isoformat(),
    }
    if row.source == "citizen":
        result["category"] = row.sensor_type
    return result


@router.post("/iot-reading")
def store_iot_reading(reading: IoTReading, db: Session = Depends(get_db)) -> dict[str, Any]:
    row = persist_iot_reading(db, reading)
    return _observation_json(row)


@router.get("/observations")
def list_observations(
    site_id: str,
    level: int | None = Query(None, ge=1, le=3),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    query = db.query(MRVObservation).filter(MRVObservation.site_id == site_id)
    if level is not None:
        query = query.filter(MRVObservation.level == level)
    rows = query.order_by(MRVObservation.observed_at.desc()).all()
    return {"count": len(rows), "observations": [_observation_json(row) for row in rows]}


def _store_citizen(report: CitizenReport, db: Session) -> MRVObservation:
    row = MRVObservation(
        site_id=report.site_id,
        level=3,
        source="citizen",
        sensor_type=report.category,
        value=1.0,
        unit="report",
        payload=report.model_dump(mode="json"),
        data_source="real",
        qa_status="ok",
        qa_message="Citizen report accepted",
        observed_at=datetime.now(UTC),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/citizen-report")
def store_citizen_report(report: CitizenReport, db: Session = Depends(get_db)) -> dict[str, Any]:
    return _observation_json(_store_citizen(report, db))


@router.post("/citizen-reports/batch")
def store_citizen_batch(batch: CitizenBatch, db: Session = Depends(get_db)) -> dict[str, Any]:
    rows = [_store_citizen(report, db) for report in batch.reports]
    return {"accepted": len(rows), "observations": [_observation_json(row) for row in rows]}


@router.post("/satellite-index")
def store_satellite_index(index: SatelliteIndex, db: Session = Depends(get_db)) -> dict[str, Any]:
    report = validate_satellite_index(index.index, index.value)
    row = MRVObservation(
        site_id=index.site_id,
        level=1,
        source="satellite",
        sensor_type=index.index,
        value=index.value,
        unit="index",
        payload=index.model_dump(mode="json"),
        data_source=index.data_source,
        qa_status=report.qa_status,
        qa_message=report.message,
        observed_at=index.ts,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _observation_json(row)


@router.post("/lorawan-webhook")
def lorawan_webhook(
    payload: dict[str, Any],
    x_webhook_key: str | None = Header(None, alias="X-Webhook-Key"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from engine.hydroma.config.settings import get_settings

    expected = get_settings().telco_webhook_key
    if not expected or not webhook_key_ok(x_webhook_key, expected):
        raise HTTPException(status_code=401, detail="Invalid webhook key")
    readings = parse_ttn_v3(payload)
    if not readings:
        raise HTTPException(status_code=422, detail="Payload contains no readable observations")
    rows = [persist_iot_reading(db, reading) for reading in readings]
    return {"count": len(rows), "observations": [_observation_json(row) for row in rows]}


@router.get("/dashboard-metrics")
def dashboard_metrics(
    site_id: str,
    area_ha: float | None = Query(None, gt=0),
    rusle_before_tha: float | None = Query(None),
    rusle_after_tha: float | None = Query(None),
    soc_before_pct: float | None = Query(None),
    soc_after_pct: float | None = Query(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = (
        db.query(MRVObservation)
        .filter(
            MRVObservation.site_id == site_id,
            MRVObservation.qa_status.in_(["ok", "suspect"]),
        )
        .all()
    )
    observed_sources = sorted({row.data_source for row in rows})
    result = compute_dashboard(
        site_id=site_id,
        area_ha=area_ha,
        rusle_before_tha=rusle_before_tha,
        rusle_after_tha=rusle_after_tha,
        soc_before_pct=soc_before_pct,
        soc_after_pct=soc_after_pct,
        observed_sources=observed_sources,
    )
    result["observation_counts"] = {
        source: sum(1 for row in rows if row.source == source)
        for source in ("satellite", "iot", "citizen")
    }
    result["data_sources_observed"] = observed_sources
    return result


@router.get("/public/dashboard-summary")
def public_dashboard_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    rows = db.query(MRVObservation).filter(MRVObservation.qa_status.in_(["ok", "suspect"])).all()
    latest_satellite: dict[str, MRVObservation] = {}
    for row in rows:
        if row.source == "satellite" and row.site_id not in latest_satellite:
            latest_satellite[row.site_id] = row
    return {
        "total_observations": len(rows),
        "by_level": {
            str(level): sum(1 for row in rows if row.level == level) for level in (1, 2, 3)
        },
        "by_source": {
            source: sum(1 for row in rows if row.source == source)
            for source in ("satellite", "iot", "citizen")
        },
        "latest_satellite_per_site": [
            {
                "site_id": row.site_id,
                "index": row.sensor_type,
                "value": row.value,
                "data_source": row.data_source,
            }
            for row in latest_satellite.values()
        ],
    }


class CarbonBudgetRequest(BaseModel):
    lat: float = Field(35.5, ge=-90, le=90)
    lon: float = Field(51.5, ge=-180, le=180)
    area_ha: float = Field(100.0, gt=0)
    practice: str = "none"
    crop: str = "wheat"
    slope_pct: float = 10.0
    measured_soc_t_ha: float | None = None
    use_kobo: bool = False
    methodology: str = "vm0032"  # vm0032 | gold_standard
    measurements: list[dict] = Field(default_factory=list)  # [{year, soc_t_ha}] t0..tn


@router.post("/carbon-budget")
async def carbon_budget(req: CarbonBudgetRequest) -> dict[str, Any]:
    """Carbon budget: real RothC chain baseline + optional KoboToolbox field data.

    Honest statuses:
    - modelled_estimate: no field data (requires_field_data in summary)
    - field_verified: measured SOC from KoboToolbox used as baseline
    - kobo_requires_credentials: KOBO_TOKEN/KOBO_FORM_ID missing
    """
    # 1) real chain (RothC-26.3) for initial/final SOC — real ERA5/SoilGrids
    chain = await run_scientific_chain(
        lat=req.lat,
        lon=req.lon,
        crop=req.crop,
        slope_pct=req.slope_pct,
        optimize=False,
        years=20,
    )
    rothc = chain.get("rothc", {})
    soc_initial = float(rothc.get("outputs", {}).get("initial_soc_t_ha", 0.0) or 0.0)
    soc_final = float(rothc.get("outputs", {}).get("final_soc_t_ha", 0.0) or 0.0)

    # 2) optional field data (KoboToolbox, free tier)
    kobo = {"status": "skipped"}
    measured = req.measured_soc_t_ha
    if req.use_kobo:
        kobo = await fetch_kobo_submissions()
        if kobo.get("status") == "ok":
            measured = average_measured_soc(kobo)

    # 3) carbon accounting (Verra VM0032 or Gold Standard SOC Framework)
    motor = CarbonMrvMotor()
    result = motor.execute(
        {
            "soc_initial_t_ha": soc_initial,
            "soc_final_t_ha": soc_final,
            "area_ha": req.area_ha,
            "practice": req.practice,
            "measured_soc_t_ha": measured,
            "methodology": req.methodology,
            "measurements": req.measurements,
        }
    )

    return {
        "status": result.status.value,
        "location": {"lat": req.lat, "lon": req.lon},
        "rothc_chain_id": chain.get("chain_id"),
        "carbon": result.outputs,
        "summary": result.summary,
        "kobo": kobo,
        "data_sources": {
            "soc_initial": "RothC-26.3 (pyRothC) with real ERA5 + SoilGrids",
            "soc_final": "RothC-26.3 (pyRothC) 20-year projection",
            "field_data": "KoboToolbox (free tier)" if req.use_kobo else "not requested",
            "conversion": "IPCC t C -> tCO2e × 3.667",
            "methodology": "Gold Standard SOC Framework (simplified)"
            if req.methodology == "gold_standard"
            else "Verra VM0032 — simplified accounting (not a certification)",
        },
        "error": result.error_message,
    }


@router.post("/carbon-budget/report")
async def carbon_budget_report(req: CarbonBudgetRequest) -> Response:
    """MRV carbon-budget report as a Persian RTL PDF (free stack: reportlab)."""
    payload = await carbon_budget(req)
    pdf_bytes = build_mrv_pdf(payload)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=mrv_carbon_budget.pdf"},
    )


class SatelliteRefreshRequest(BaseModel):
    site_id: str
    lat: float
    lon: float
    start: str
    end: str


@router.post("/satellite-refresh")
async def satellite_refresh(req: SatelliteRefreshRequest) -> dict[str, Any]:
    """Refresh satellite NDVI data for a site."""
    from fastapi import HTTPException

    from engine.hydroma.config.settings import get_settings

    settings = get_settings()
    if str(getattr(settings, "enable_satellite_real", "false")).lower() == "false":
        raise HTTPException(status_code=503, detail="Satellite refresh disabled")

    import requests

    session = requests.Session()
    try:
        result = satellite_cdse.retrieve_ndvi(
            session=session,
            cfg=settings,
            bbox=[req.lon - 0.05, req.lat - 0.05, req.lon + 0.05, req.lat + 0.05],
            start=req.start,
            end=req.end,
        )
        return result
    except CdseUnavailable as exc:
        raise HTTPException(status_code=502, detail=f"CDSE retrieval failed: {exc}") from exc
