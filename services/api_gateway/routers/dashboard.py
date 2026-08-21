"""
Dashboard API Router
"""
import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..dependencies import get_db
from ...models.user import User

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models for request/response
class FarmData(BaseModel):
    id: str
    name: str
    location: str
    size: float  # hectares
    crop_type: str
    last_update: str


class WeatherData(BaseModel):
    temperature: float
    humidity: float
    precipitation: float
    condition: str


class SatelliteData(BaseModel):
    ndvi: float
    evi: float
    soil_moisture: float
    image_date: str


class PredictionData(BaseModel):
    yield_prediction: float  # tons/hectare
    risk_level: str  # low, medium, high
    recommendations: List[str]


class DashboardData(BaseModel):
    farm: FarmData
    weather: WeatherData
    satellite: SatelliteData
    predictions: PredictionData


# Mock data for demonstration
MOCK_FARM_DATA = FarmData(
    id="farm-001",
    name="Farmer John's Field",
    location="Central Valley, CA",
    size=120.0,
    crop_type="Corn",
    last_update="2023-10-15"
)

MOCK_WEATHER_DATA = WeatherData(
    temperature=float(os.getenv('DEFAULT_TEMP', '22.5')),
    humidity=float(os.getenv('DEFAULT_HUMIDITY', '65.0')),
    precipitation=float(os.getenv('DEFAULT_PRECIP', '5.0')),
    condition="Partly Cloudy"
)

MOCK_SATELLITE_DATA = SatelliteData(
    ndvi=0.72,
    evi=0.45,
    soil_moisture=35.0,
    image_date="2023-10-14"
)

MOCK_PREDICTIONS = PredictionData(
    yield_prediction=12.5,
    risk_level="medium",
    recommendations=[
        "Increase irrigation by 15%",
        "Apply nitrogen fertilizer in 2 weeks",
        "Monitor for pest activity"
    ]
)


@router.get("/data", response_model=DashboardData)
async def get_dashboard_data(current_user: User = Depends(get_current_user)):
    """
    Retrieve dashboard data for the authenticated user.
    In a real implementation, this would fetch actual data from the database
    and external services (satellite, weather, AI models).
    """
    # In a real implementation, we would fetch data from:
    # 1. Database for user's farm data
    # 2. External weather API
    # 3. Satellite data service
    # 4. AI prediction models
    
    # For now, return mock data
    return DashboardData(
        farm=MOCK_FARM_DATA,
        weather=MOCK_WEATHER_DATA,
        satellite=MOCK_SATELLITE_DATA,
        predictions=MOCK_PREDICTIONS
    )


@router.post("/refresh-data")
async def refresh_dashboard_data(current_user: User = Depends(get_current_user)):
    """
    Trigger a refresh of dashboard data.
    This could initiate background jobs to fetch latest satellite images,
    weather data, or run new AI predictions.
    """
    # In a real implementation, this would trigger background tasks
    # to update data sources
    
    # For now, just return a success message
    return {
        "status": "success",
        "message": "Data refresh initiated",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/recommendations/{farm_id}")
async def get_recommendations(farm_id: str, current_user: User = Depends(get_current_user)):
    """
    Get specific recommendations for a given farm.
    """
    # In a real implementation, this would run AI models
    # with farm-specific data to generate recommendations
    
    # For now, return mock recommendations
    return {
        "farm_id": farm_id,
        "recommendations": [
            "Apply fungicide treatment in the next 3 days",
            "Adjust irrigation schedule based on forecasted rain",
            "Consider harvesting in 2 weeks for optimal yield"
        ],
        "updated_at": datetime.utcnow().isoformat()
    }