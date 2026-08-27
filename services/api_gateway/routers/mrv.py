"""MRV / Carbon budget router — فاز ۴ (رایگان)."""

from typing import Any

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel, Field

from services.mrv.kobo import average_measured_soc, fetch_kobo_submissions
from services.mrv.mrv_pdf import build_mrv_pdf
from services.scientific_motors.carbon_mrv import CarbonMrvMotor
from services.scientific_motors.chain_runner import run_scientific_chain

router = APIRouter(prefix="/api/mrv", tags=["mrv"])


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
            "methodology": "Gold Standard SOC Framework (simplified)" if req.methodology == "gold_standard" else "Verra VM0032 — simplified accounting (not a certification)",
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
