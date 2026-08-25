"""API Router for new analyses and designs."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.config import get_db # Fixed import to get 'get_db' from the correct module
from engine.hydroma.analyses.topography_analysis import TopographyAnalyzer, TopographyInput
from engine.hydroma.models.runoff_model import RunoffCalculator, RunoffInput
from engine.hydroma.models.groundwater_model import GroundwaterModel, GroundwaterInput
from engine.hydroma.calculations.crop_water_req_calc import CropWaterRequirementCalculator, CropWaterReqInput
from services.design_engine.water_structure_design_service import StructureDesigner, StructureDesignInput
from services.design_engine.irrigation_design_service import IrrigationDesigner, IrrigationDesignInput
from engine.hydroma.calibration.model_calibrator import Calibrator, CalibrationInput

router = APIRouter(prefix="/analyses", tags=["analyses"])

@router.post("/topography/")
def run_topography_analysis(input_data: TopographyInput, db: Session = Depends(get_db)):
    analyzer = TopographyAnalyzer(db_session=db)
    try:
        result = analyzer.execute(input_data)
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/runoff/")
def run_runoff_calculation(input_data: RunoffInput):
    calculator = RunoffCalculator()
    try:
        result = calculator.execute(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")

@router.post("/groundwater/")
def run_groundwater_model(input_data: GroundwaterInput):
    model = GroundwaterModel()
    try:
        result = model.execute(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model run failed: {str(e)}")

@router.post("/crop-water-req/")
def run_crop_water_req_calculation(input_data: CropWaterReqInput):
    calculator = CropWaterRequirementCalculator()
    try:
        result = calculator.execute(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")

@router.post("/structure-design/")
def run_structure_design(input_data: StructureDesignInput):
    designer = StructureDesigner()
    try:
        result = designer.execute(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Design failed: {str(e)}")

@router.post("/irrigation-design/")
def run_irrigation_design(input_data: IrrigationDesignInput):
    designer = IrrigationDesigner()
    try:
        result = designer.execute(input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Design failed: {str(e)}")

# Note: Calibration requires a special runner instance, so its API might be more complex
# @router.post("/calibrate-model/")
# def run_calibration(input_data: CalibrationInput):
#     calibrator = Calibrator()
#     try:
#         result = calibrator.execute(input_data)
#         return result
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Calibration failed: {str(e)}")
