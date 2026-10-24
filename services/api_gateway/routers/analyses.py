"""API Router for new analyses and designs."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.hub import hub
from services._gateway_facade import (
    CropWaterReqInput,
    CropWaterRequirementCalculator,
    GroundwaterInput,
    GroundwaterModel,
    RunoffCalculator,
    RunoffInput,
    TopographyAnalyzer,
    TopographyInput,
)
from services.design_engine.irrigation_design_service import (
    IrrigationDesigner,
    IrrigationDesignInput,
)
from services.design_engine.water_structure_design_service import (
    StructureDesigner,
    StructureDesignInput,
)


# Compatibility: get_db via hub
def get_db():
    with hub.get_session() as session:
        yield session  # Fixed import to get 'get_db' from the correct module



router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("/topography/")
def run_topography_analysis(input_data: TopographyInput, db: Annotated[Session, Depends(get_db)]):
    analyzer = TopographyAnalyzer(db_session=db)
    try:
        result = analyzer.execute(input_data)
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e!s}") from e


@router.post("/runoff/")
def run_runoff_calculation(input_data: RunoffInput):
    calculator = RunoffCalculator()
    try:
        result = calculator.execute(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {e!s}") from e


@router.post("/groundwater/")
def run_groundwater_model(input_data: GroundwaterInput):
    model = GroundwaterModel()
    try:
        result = model.execute(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model run failed: {e!s}") from e


@router.post("/crop-water-req/")
def run_crop_water_req_calculation(input_data: CropWaterReqInput):
    calculator = CropWaterRequirementCalculator()
    try:
        result = calculator.execute(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {e!s}") from e


@router.post("/structure-design/")
def run_structure_design(input_data: StructureDesignInput):
    designer = StructureDesigner()
    try:
        result = designer.execute(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Design failed: {e!s}") from e


@router.post("/irrigation-design/")
def run_irrigation_design(input_data: IrrigationDesignInput):
    designer = IrrigationDesigner()
    try:
        result = designer.execute(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Design failed: {e!s}") from e


# Note: Calibration requires a special runner instance, so its API might be more complex
# @router.post("/calibrate-model/")
# def run_calibration(input_data: CalibrationInput):
#     calibrator = Calibrator()
#     try:
#         result = calibrator.execute(input_data)
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Calibration failed: {str(e)}")
