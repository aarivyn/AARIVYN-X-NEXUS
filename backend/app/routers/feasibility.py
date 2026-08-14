from fastapi import APIRouter
from schemas import FeasibilityFilterRequest, FeasibilityFilterResponse
from services.feasibility_service import run_feasibility_filters

router = APIRouter(prefix="/feasibility", tags=["Module 5: Feasibility Filter Engine"])

@router.post("/filter", response_model=FeasibilityFilterResponse)
def filter_candidate_interventions(payload: FeasibilityFilterRequest):
    return run_feasibility_filters(payload)
