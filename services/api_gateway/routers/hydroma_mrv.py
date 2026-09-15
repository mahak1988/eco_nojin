"""HyDroMa MRV-tools API — observation QA and transparent provenance metrics.

POST /api/v1/hydroma/mrv/mrv-qa/run        -> plausibility QA for a reading
POST /api/v1/hydroma/mrv/mrv-metrics/run   -> transparent MRV metrics (provenance-badged)

Pure computations over the provided inputs; no writes.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import APIRouter, HTTPException

from engine.hydroma.mrv.metrics import compute_dashboard
from engine.hydroma.mrv.qa import validate_reading, validate_satellite_index
from services.api_gateway.routers.hydroma_common import build_kwargs, jsonable

router = APIRouter(prefix="/api/v1/hydroma/mrv", tags=["hydroma-mrv"])


def _serialize(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    if hasattr(obj, '__dict__'):
        return jsonable(vars(obj))
    return str(obj)


_SPECS: list[dict[str, Any]] = [
    {
        "id": "mrv-qa",
        "name_en": "Observation QA/QC",
        "description": "Plausibility screening for sensor readings and satellite indices: "
                       "accepted / suspect / rejected with an audit message.",
        "reference": "EM-01 (QA bands)",
        "params": [
            {"name": "sensor_type", "label": "Sensor type", "unit": "", "kind": "select",
             "default": "soil_moisture",
             "options": ["soil_moisture", "temperature", "precipitation", "wind_speed", "humidity", "ph", "ec"]},
            {"name": "value", "label": "Reading value", "unit": "", "kind": "float", "default": 0.32},
            {"name": "unit", "label": "Unit", "unit": "", "kind": "str", "default": "", "optional": True},
            {"name": "satellite_index", "label": "Satellite index (optional)", "unit": "", "kind": "select",
             "default": "ndvi", "options": ["ndvi", "evi", "savi", "ndmi"], "optional": True},
        ],
    },
    {
        "id": "mrv-metrics",
        "name_en": "Transparent MRV metrics",
        "description": "Provenance-badged restoration metrics: erosion, SOC change, CO2e, area and income.",
        "reference": "EM-01 §3 (real / simulated / no_data)",
        "params": [
            {"name": "site_id", "label": "Site id", "unit": "", "kind": "str", "default": "site-1"},
            {"name": "area_ha", "label": "Area", "unit": "ha", "kind": "float", "default": 25.0, "optional": True},
            {"name": "rusle_before_tha", "label": "RUSLE before", "unit": "t/ha/yr", "kind": "float", "default": 18.0, "optional": True},
            {"name": "rusle_after_tha", "label": "RUSLE after", "unit": "t/ha/yr", "kind": "float", "default": 6.0, "optional": True},
        ],
    },
]

_SPEC_BY_ID: dict[str, dict[str, Any]] = {s['id']: s for s in _SPECS}


def _run_mrv_qa(kw: dict[str, Any]) -> dict[str, Any]:
    if kw.get('satellite_index'):
        report = validate_satellite_index(kw['satellite_index'], float(kw['value']))
        return _serialize(report) | {'mode': 'satellite_index', 'index': kw['satellite_index']}
    report = validate_reading(kw['sensor_type'], float(kw['value']), kw.get('unit') or None)
    return _serialize(report) | {'mode': 'sensor_reading', 'sensor_type': kw['sensor_type']}


def _run_mrv_metrics(kw: dict[str, Any]) -> dict[str, Any]:
    return compute_dashboard(**kw)


_RUNNERS = {
    'mrv-qa': _run_mrv_qa,
    'mrv-metrics': _run_mrv_metrics,
}


@router.get('')
def list_mrv_tools() -> dict[str, Any]:
    return {'count': len(_SPECS), 'models': _SPECS}


@router.get('/{model_id}')
def get_mrv_tool(model_id: str) -> dict[str, Any]:
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f'unknown HyDroMa MRV tool: {model_id}')
    return spec


@router.post('/{model_id}/run')
def run_mrv_tool(model_id: str, params: dict[str, Any]) -> dict[str, Any]:
    spec = _SPEC_BY_ID.get(model_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f'unknown HyDroMa MRV tool: {model_id}')
    if not isinstance(params, dict):
        raise HTTPException(status_code=400, detail='params must be an object')
    try:
        kwargs = build_kwargs(spec, params)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f'invalid parameters: {exc}') from exc
    try:
        result = _RUNNERS[model_id](kwargs)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=f'tool rejected inputs: {exc}') from exc
    except Exception as exc:  # noqa: BLE001 - explicit failure
        raise HTTPException(status_code=500, detail=f'tool execution failed: {exc}') from exc
    return {'id': model_id, 'result': jsonable(result)}
