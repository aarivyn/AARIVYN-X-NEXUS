from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from schemas import WaterAnalyzeRequest, WaterAnalyzeResponse
from services.water_service import run_water_analysis
from services.aoi_validator import validate_aoi_bounds

router = APIRouter(prefix="/water", tags=["Module 3: Water Intelligence Engine"])

@router.post("/analyze", response_model=WaterAnalyzeResponse)
def analyze_water_intelligence(payload: WaterAnalyzeRequest):
    """
    Core Water Intelligence Endpoint
    Accepts location/AOI, date range, data sources, budget & risk tolerance.
    Generates water indicators, problem signals, satellite observations, and confidence metadata.
    """
    if payload.bbox:
        validate_aoi_bounds(payload.bbox)
    return run_water_analysis(payload)
