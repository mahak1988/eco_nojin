"""Scientific Validation API Router."""

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/v1/hydroma/validation", tags=["validation"])


@router.get("/run")
async def run_validation(
    check_id: Optional[str] = Query(None, description="Run specific check ID, or all if omitted"),
):
    """Run formula verification checks."""
    from services.validation.formula_checks import run_all

    result = run_all()

    if check_id:
        # Filter to specific check
        filtered = [c for c in result["checks"] if c["id"] == check_id]
        if not filtered:
            return {"error": f"Check '{check_id}' not found"}
        return {
            "checks": filtered,
            "total": 1,
            "passed": int(filtered[0]["passed"]),
            "failed": 1 - int(filtered[0]["passed"]),
        }

    return result


@router.get("/checks")
async def list_checks():
    """List available validation check IDs."""
    from services.validation.formula_checks import run_all

    result = run_all()
    return {
        "checks": [
            {"id": c["id"], "label": c["label"], "kind": c["kind"], "unit": c["unit"]}
            for c in result["checks"]
        ],
        "total": len(result["checks"]),
    }


@router.get("/reference-data")
async def get_reference_data():
    """Get reference data used in validation."""
    import json
    from pathlib import Path

    path = Path("docs/hydroma/scientific_reference_data.json")
    if not path.exists():
        return {"error": "Reference data file not found"}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
