from fastapi import APIRouter, HTTPException, Path
from schemas import NexusAnalyzeRequest, NexusJobStatusResponse
from services.job_service import submit_nexus_job, get_job_status
from services.aoi_validator import validate_aoi_bounds

router = APIRouter(prefix="/nexus", tags=["Master Orchestration & Background Jobs"])

@router.post("/analyze", response_model=NexusJobStatusResponse)
def submit_master_nexus_analysis(request: NexusAnalyzeRequest):
    """
    POST /api/v1/nexus/analyze
    Orchestrates end-to-end NEXUS Pipeline:
    EO Acquisition -> Processing -> Water Intelligence -> Problem Detection ->
    Intervention Graph Discovery -> Feasibility Filtering -> NSGA-II Optimization ->
    Portfolio Generation -> Implementation Plan.
    Returns job_id, status, progress, stage.
    """
    if request.bbox:
        validate_aoi_bounds(request.bbox)
    return submit_nexus_job(request)

@router.get("/jobs/{job_id}", response_model=NexusJobStatusResponse)
def get_nexus_job_progress(job_id: str = Path(..., description="Unique orchestration job ID")):
    """
    GET /api/v1/nexus/jobs/{job_id}
    Polls background job execution status, progress percentage, current stage, and final complete result payload.
    """
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job ID '{job_id}' not found.")
    return status
