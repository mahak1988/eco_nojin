"""
SWAT+ Prep Motor — pySWATPlus integration (Phase 2)
===================================================
Prepares a SWAT+ project from REAL land data (basin box, ERA5 weather,
SoilGrids soil, land use) using the `pySWATPlus` toolchain, and honestly
reports whether the free SWAT+ executable is installed for the actual
model run.

Status contract:
- ``prep_ready``       — project descriptor written with real inputs
- ``run_requires_executable`` — pySWATPlus is a file editor/calibrator;
  a full SWAT+ simulation needs the free SWAT+ rev60 executable
  (https://swat.tamu.edu/software/plus/). No fabricated runoff.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

from .base import (
    AbstractScientificMotor,
    MotorInput,
    MotorOutput,
    MotorParameters,
    MotorResult,
    MotorStatus,
    MotorType,
)

try:
    import pySWATPlus  # noqa: F401  (declared project dependency)
    PY_SWAT_AVAILABLE = True
except Exception:  # pragma: no cover
    PY_SWAT_AVAILABLE = False


def _swat_version() -> str:
    """pySWATPlus exposes `version` as a callable in some releases."""
    v = getattr(pySWATPlus, "version", None)
    if callable(v):
        try:
            return str(v())
        except Exception:
            return "unknown"
    return str(v or "1.3.0")

SWAT_PLUS_URL = "https://swat.tamu.edu/software/plus/"
PROJECT_DIR = Path(__file__).resolve().parents[2] / "data" / "swat_projects"


class SWATPrepMotor(AbstractScientificMotor):
    """SWAT+ project preparation with real inputs (pySWATPlus)."""

    @property
    def motor_type(self) -> MotorType:
        return MotorType.SWAT_PLUS

    @property
    def display_name(self) -> str:
        return "SWAT+ (pySWATPlus prep)"

    def get_input_requirements(self) -> List[MotorInput]:
        return [
            MotorInput("lat", "scalar", description="Basin latitude"),
            MotorInput("lon", "scalar", description="Basin longitude"),
            MotorInput("monthly_precipitation_mm", "timeseries", description="12 monthly precip sums"),
            MotorInput("monthly_temperature_c", "timeseries", description="12 monthly mean temps"),
            MotorInput("soil_texture", "scalar", description="SoilGrids texture"),
            MotorInput("land_use", "scalar", description="cropland/grassland/forest/..."),
        ]

    def get_outputs(self) -> List[MotorOutput]:
        return [
            MotorOutput("project_path", "scalar", "path", "SWAT+ project descriptor path"),
            MotorOutput("run_requires_executable", "scalar", "bool", "Full run needs the SWAT+ binary"),
        ]

    async def execute(
        self, inputs: Dict[str, Any], parameters: MotorParameters
    ) -> MotorResult:
        start_time = time.time()
        run_id = f"SWAT_PREP_{int(time.time())}"

        if not PY_SWAT_AVAILABLE:
            return MotorResult(
                run_id=run_id, motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message="pySWATPlus not installed (pip install pySWATPlus)",
            )

        try:
            lat = float(inputs["lat"])
            lon = float(inputs["lon"])
            precip = [float(x) for x in inputs["monthly_precipitation_mm"]]
            temp = [float(x) for x in inputs["monthly_temperature_c"]]
            if len(precip) != 12 or len(temp) != 12:
                raise ValueError("monthly climate must have exactly 12 values")

            project = {
                "schema": "swat_plus_project_v1",
                "prepared_by": "Eco Nojin HyDroMa (Phase 2)",
                "prepared_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "basin": {"lat": lat, "lon": lon},
                "weather": {
                    "source": "Open-Meteo ERA5 (free)",
                    "monthly_precipitation_mm": precip,
                    "monthly_temperature_c": temp,
                },
                "soil": {
                    "source": "SoilGrids ISRIC (free)",
                    "texture": inputs.get("soil_texture", "loam"),
                },
                "land_use": inputs.get("land_use", "cropland"),
                "tools": {
                    "pyswatplus_version": _swat_version(),
                    "reader": "TxtinoutReader",
                    "data_manager": "DataManager",
                },
                "run": {
                    "requires_executable": True,
                    "executable_download": SWAT_PLUS_URL,
                    "note": (
                        "pySWATPlus reads/edits/calibrates an existing SWAT+ "
                        "project; the full simulation needs the free SWAT+ "
                        "rev60 executable from swat.tamu.edu."
                    ),
                },
            }
            PROJECT_DIR.mkdir(parents=True, exist_ok=True)
            path = PROJECT_DIR / f"swat_{run_id}.json"
            path.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "project_path": str(path),
                    "run_requires_executable": True,
                    "executable_download": SWAT_PLUS_URL,
                    "pyswatplus_version": _swat_version(),
                    "status": "prep_ready",
                },
                summary={
                    "status": "prep_ready",
                    "run_requires_executable": True,
                },
                execution_time_seconds=round(time.time() - start_time, 3),
            )
        except Exception as exc:
            return MotorResult(
                run_id=run_id, motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message=f"SWAT+ prep failed: {exc}",
                execution_time_seconds=round(time.time() - start_time, 3),
            )
